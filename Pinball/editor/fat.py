"""Small host-side FAT16/32 file writer, restricted to PINBALL/*.PBT.

A save allocates a new chain and verifies its bytes before committing one
short-name directory entry. The previous chain is released only afterward.
No drive is mounted by the operating system while the game owns the SD card.
"""
import math
import re
import struct
from protocol import decode
from boards import MAX_BYTES

u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
u32=lambda b,o:struct.unpack_from('<I',b,o)[0]

class BoardCard:
    def __init__(self,device):
        self.device=device;self.cache={};self.dirty_fsinfo=False
        b=self.read(0);self.base=0
        if u16(b,11)!=512 or not b[13] or b[13]&(b[13]-1):
            self.base=next((u32(b,446+i*16+8) for i in range(4) if b[450+i*16] in (4,6,11,12,14)),None)
            if self.base is None:raise ValueError('A FAT16 or FAT32 SD card is required')
            b=self.read(self.base)
        if b[510:512]!=b'\x55\xaa' or u16(b,11)!=512:raise ValueError('Invalid FAT boot sector')
        self.spc=b[13];self.reserved=u16(b,14);self.copies=b[16];self.root_count=u16(b,17)
        self.total=u16(b,19) or u32(b,32);self.fat_size=u16(b,22) or u32(b,36)
        if not self.spc or self.spc&(self.spc-1) or self.spc>128 or not 1<=self.copies<=2 or not self.fat_size:raise ValueError('Unsupported FAT geometry')
        self.fat_base=self.base+self.reserved;self.root_base=self.fat_base+self.copies*self.fat_size
        self.root_sectors=(self.root_count*32+511)//512;self.data_base=self.root_base+self.root_sectors
        self.cluster_count=(self.total-(self.data_base-self.base))//self.spc
        self.bits=16 if 4085<=self.cluster_count<65525 else 32 if self.cluster_count>=65525 else 0
        if not self.bits or self.cluster_count*self.bits//8>self.fat_size*512:raise ValueError('Unsupported FAT type or size')
        if self.bits==32 and u16(b,40)&128:raise ValueError('FAT32 with disabled FAT mirroring is not supported')
        self.root=0 if self.bits==16 else u32(b,44)
        self.fsinfo=self.base+u16(b,48) if self.bits==32 and u16(b,48)<self.reserved else None
        self.backup_fsinfo=self.base+u16(b,50)+u16(b,48) if self.bits==32 and u16(b,50)+u16(b,48)<self.reserved else None
        self.end=0xffff if self.bits==16 else 0x0fffffff
        self.next_free=2
    def read(self,lba):
        if lba not in self.cache:
            data=self.device.read(lba)
            if len(data)!=512:raise IOError('Short SD sector')
            self.cache[lba]=bytes(data)
        return self.cache[lba]
    def write(self,lba,data):
        if not self.base<=lba<self.base+self.total:raise ValueError('Write outside FAT volume')
        self.device.write(lba,bytes(data));self.cache[lba]=bytes(data)
    def get(self,n):
        if not 2<=n<self.cluster_count+2:raise ValueError('Invalid cluster')
        offset=n*(self.bits//8);data=self.read(self.fat_base+offset//512)
        return (u16(data,offset%512) if self.bits==16 else u32(data,offset%512)&0x0fffffff)
    def set(self,n,value):
        if not 2<=n<self.cluster_count+2:raise ValueError('Invalid cluster')
        offset=n*(self.bits//8)
        for copy in range(self.copies):
            lba=self.fat_base+copy*self.fat_size+offset//512;b=bytearray(self.read(lba))
            if self.bits==16:struct.pack_into('<H',b,offset%512,value)
            else:struct.pack_into('<I',b,offset%512,(u32(b,offset%512)&0xf0000000)|value)
            self.write(lba,b)
    def chain(self,start):
        result=[];seen=set();n=start
        while n:
            if n in seen or not 2<=n<self.cluster_count+2:raise ValueError('Broken FAT chain')
            result.append(n);seen.add(n);n=self.get(n)
            if n>=self.end-7:return result
        raise ValueError('Truncated FAT chain')
    def sector(self,n):return self.data_base+(n-2)*self.spc
    def allocate(self,count):
        chosen=[]
        for n in range(self.next_free,self.cluster_count+2):
            if self.get(n)==0:chosen.append(n)
            if len(chosen)==count:break
        if len(chosen)!=count:raise IOError('The SD card is full')
        self.next_free=chosen[-1]+1
        for i,n in enumerate(chosen):self.set(n,chosen[i+1] if i+1<count else self.end)
        return chosen
    def directory(self,cluster):
        if cluster==0:
            yield from range(self.root_base,self.root_base+self.root_sectors)
        else:
            for c in self.chain(cluster):yield from range(self.sector(c),self.sector(c)+self.spc)
    def find(self,cluster,name):
        for sector in self.directory(cluster):
            b=self.read(sector)
            for at in range(0,512,32):
                if b[at]==0:return None
                if b[at]!=229 and b[at+11]!=15 and b[at:at+11]==name:return sector,at,bytes(b[at:at+32])
        return None
    def slot(self,cluster):
        for sector in self.directory(cluster):
            b=self.read(sector)
            for at in range(0,512,32):
                if b[at] in (0,229):return sector,at
        if cluster==0:raise IOError('The FAT16 root directory is full')
        extra=self.allocate(1)[0]
        for s in range(self.sector(extra),self.sector(extra)+self.spc):self.write(s,bytes(512))
        self.set(self.chain(cluster)[-1],extra)
        return self.sector(extra),0
    def entry(self,name,cluster,size,folder=False):
        e=bytearray(32);e[:11]=name;e[11]=16 if folder else 32
        struct.pack_into('<H',e,26,cluster&65535)
        if self.bits==32:struct.pack_into('<H',e,20,cluster>>16)
        struct.pack_into('<I',e,28,size);return e
    def publish(self,slot,entry):
        sector,at=slot;b=bytearray(self.read(sector));b[at:at+32]=entry;self.write(sector,b)
    def cluster(self,e):return u16(e,26)|((u16(e,20)<<16) if self.bits==32 else 0)
    def folder(self):
        found=self.find(self.root,b'PINBALL    ')
        if found:
            if not found[2][11]&16:raise ValueError('PINBALL exists but is not a folder')
            return self.cluster(found[2])
        slot=self.slot(self.root);cluster=self.allocate(1)[0];first=self.sector(cluster)
        for s in range(first,first+self.spc):self.write(s,bytes(512))
        b=bytearray(512);b[:32]=self.entry(b'.          ',cluster,0,True);b[32:64]=self.entry(b'..         ',self.root,0,True);self.write(first,b)
        self.publish(slot,self.entry(b'PINBALL    ',cluster,0,True));return cluster
    def file(self,e):
        size=u32(e,28);out=bytearray()
        if size>MAX_BYTES:raise ValueError('Existing PBT file is oversized')
        for c in self.chain(self.cluster(e)):
            for s in range(self.sector(c),self.sector(c)+self.spc):
                out.extend(self.read(s))
                if len(out)>=size:return bytes(out[:size])
        raise ValueError('Incomplete file')
    def save(self,stem,data):
        if not re.fullmatch('[A-Z0-9_]{1,8}',stem):raise ValueError('Use a 1–8 character uppercase SD filename')
        decode(data,stem)  # Validate before the first SD mutation.
        folder=self.folder();name=stem.encode().ljust(8,b' ')+b'PBT';old=self.find(folder,name)
        if old:
            if old[2][11]&16:raise ValueError('Destination is a folder')
            decode(self.file(old[2]),stem)
        slot=old[:2] if old else self.slot(folder)
        clusters=self.allocate(math.ceil(len(data)/(512*self.spc)))
        attempted_commit=False
        try:
            for i in range((len(data)+511)//512):
                sector=self.sector(clusters[i//self.spc])+i%self.spc
                self.write(sector,data[i*512:(i+1)*512].ljust(512,b'\0'))
            entry=self.entry(name,clusters[0],len(data))
            # Read through the device, not the write cache, before publication.
            self.cache={k:v for k,v in self.cache.items() if not any(self.sector(c)<=k<self.sector(c)+self.spc for c in clusters)}
            if self.file(entry)!=data:raise IOError('SD board readback differs')
            attempted_commit=True;self.publish(slot,entry)
        except Exception:
            # An uncertain directory write might have committed: leave the
            # new chain allocated rather than risk freeing a published file.
            if not attempted_commit:
                for n in clusters:self.set(n,0)
            raise
        if old:
            for n in self.chain(self.cluster(old[2])):self.set(n,0)
        # FAT32's advisory counters become unknown; OS readers recompute them.
        for sector in set(s for s in (self.fsinfo,self.backup_fsinfo) if s is not None):
            b=bytearray(self.read(sector))
            if b[:4]==b'RRaA' and b[484:488]==b'rrAa':
                b[488:496]=b'\xff'*8;self.write(sector,b)
        self.cache.clear()
        return {'path':f'PINBALL/{stem}.PBT','bytes':len(data),'verified':True}
