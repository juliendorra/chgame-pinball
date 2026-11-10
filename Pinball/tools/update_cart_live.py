#!/usr/bin/env python3
"""Atomically replace only the existing MIDNIGHT.CHG cart under GAMES/ through Pinball's USB SD API.

Uses the editor's tested FAT allocator. No mounted drive or reader firmware
is needed. FAT links are batched per sector and flushed before publication. All payload bytes are read back before the directory is changed.
"""
import argparse,hashlib,importlib.util,json,math,struct,sys
from pathlib import Path
G=Path(__file__).resolve().parents[1];R=G.parent
sys.path[:0]=[str(R/'CHGame/tools/chsim'),str(R/'CHGame/tools'),str(G/'editor')]
from fat import BoardCard,u32
from chcart import zipio,runtime
from chcart.backup import game_from_chg
from protocol import LiveClient
from chdrivelib import SerialTransport
import chgpack

class CartCard(BoardCard):
    def __init__(self,device):
        super().__init__(device);self.pending_fat={}
    def set(self,n,value):
        if not 2<=n<self.cluster_count+2:raise ValueError('Invalid cluster')
        offset=n*(self.bits//8)
        for copy in range(self.copies):
            lba=self.fat_base+copy*self.fat_size+offset//512;b=bytearray(self.read(lba))
            if self.bits==16:struct.pack_into('<H',b,offset%512,value)
            else:struct.pack_into('<I',b,offset%512,(u32(b,offset%512)&0xf0000000)|value)
            self.pending_fat[lba]=self.cache[lba]=bytes(b)
    def flush_fat(self):
        # Coalesce adjacent cluster links: over USB, rewriting a 512-byte
        # FAT sector per link costs much more than writing the cart itself.
        for sector,data in sorted(self.pending_fat.items()):self.write(sector,data)
        self.pending_fat.clear()
    def file(self,e):
        size=u32(e,28)
        if size>8*1024*1024:raise ValueError('Unexpectedly large SD file')
        if not size:return b''
        out=bytearray()
        for cluster in self.chain(self.cluster(e)):
            for sector in range(self.sector(cluster),self.sector(cluster)+self.spc):
                out.extend(self.read(sector))
                if len(out)>=size:return bytes(out[:size])
        raise ValueError('Truncated file')
    def path(self,path):
        directory=self.root
        for part in path.split('/'):
            stem,_,ext=part.upper().partition('.')
            if len(stem)>8 or len(ext)>3:raise ValueError('Short names required')
            found=self.find(directory,stem.encode().ljust(8,b' ')+ext.encode().ljust(3,b' '))
            if found is None:raise ValueError('Missing '+path)
            directory=self.cluster(found[2])
        return found
    def files(self,directory,path):
        for sector in self.directory(directory):
            data=self.read(sector)
            for at in range(0,512,32):
                entry=data[at:at+32]
                if not entry[0]:return
                if entry[0] in (46,229) or entry[11]==15 or entry[11]&8:continue
                name=entry[:8].decode('ascii').rstrip();ext=entry[8:11].decode('ascii').rstrip()
                full=path+'/'+name+('.'+ext if ext else '')
                if entry[11]&16:yield from self.files(self.cluster(entry),full)
                else:yield full,entry
    def install(self,payload,destination='GAMES/MIDNIGHT.CHG'):
        if not destination.startswith('GAMES/') or not destination.endswith('/MIDNIGHT.CHG') or '..' in destination:raise ValueError('Expected the existing Pinball cart under GAMES/')
        title=chgpack.parse(payload)['title']
        if title!='MIDNIGHT PINBALL':raise ValueError('Wrong cart title')
        sector,at,entry=self.path(destination)
        old=self.file(entry)
        if chgpack.parse(old)['title']!=title:raise ValueError('Destination contains another game')
        # Allocate/write a fresh chain. The installed cart remains intact
        # until its complete replacement has passed uncached readback.
        clusters=self.allocate(math.ceil(len(payload)/(512*self.spc)))
        publishing=False
        try:
            self.flush_fat()
            for i in range(math.ceil(len(payload)/512)):
                self.write(self.sector(clusters[i//self.spc])+i%self.spc,payload[i*512:(i+1)*512].ljust(512,b'\0'))
            new=bytearray(entry);struct.pack_into('<H',new,26,clusters[0]&65535)
            if self.bits==32:struct.pack_into('<H',new,20,clusters[0]>>16)
            struct.pack_into('<I',new,28,len(payload))
            self.cache.clear()
            if self.file(new)!=payload:raise IOError('Unpublished cart readback differs')
            publishing=True;self.publish((sector,at),new)
            self.cache.clear()
            if self.file(self.path(destination)[2])!=payload:raise IOError('Published cart readback differs')
        except Exception:
            if not publishing:
                for cluster in clusters:self.set(cluster,0)
                self.flush_fat()
            raise
        for cluster in self.chain(self.cluster(entry)):self.set(cluster,0)
        self.flush_fat()
        for sector in set(s for s in (self.fsinfo,self.backup_fsinfo) if s is not None):
            b=bytearray(self.read(sector))
            if b[:4]==b'RRaA' and b[484:488]==b'rrAa':b[488:496]=b'\xff'*8;self.write(sector,b)
        self.cache.clear()
        return {'path':destination,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'previous_sha256':hashlib.sha256(old).hexdigest(),'uncached_readback':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',required=True);p.add_argument('--destination',default='GAMES/MIDNIGHT.CHG');a=p.parse_args()
    issues=[];cart=zipio.load(G/'build/Pinball.chgame',issues)
    assert not any(i.error for i in issues) and len(cart.games)==1,issues
    game=cart.games[0];payload=runtime.chg_file(game,'rev0')
    assert runtime.flash_image(game,'rev0')==(G/'build/release/Pinball.ino.bin').read_bytes()
    save_config=json.loads((R/'save-config.json').read_text())
    spec=importlib.util.spec_from_file_location('pinball_save_prepare',R/'chgame-sd-saves/tools/prepare.py')
    saves=importlib.util.module_from_spec(spec);spec.loader.exec_module(saves)
    save_name=saves.filename(save_config['id'])
    out=G/'out/device';out.mkdir(parents=True,exist_ok=True)
    t=SerialTransport(a.port);c=LiveClient(t);paused=None
    try:
        assert game.version in c.hello();paused=c.state()['paused'];c.request('K 0');c.request('Q 1');c.request('I');card=CartCard(c)
        # User layouts are not expected to equal the shipped templates. Keep
        # every current board/checkpoint and the namespaced save unchanged.
        folder=card.cluster(card.path('PINBALL')[2])
        baseline={name:card.file(entry) for name,entry in card.files(folder,'PINBALL')}
        save=card.file(card.path(save_name)[2]);saves.validate(save,save_config['id'])
        games_folder=card.cluster(card.path('GAMES')[2])
        entries={name:entry for name,entry in card.files(games_folder,'GAMES') if name!=a.destination}
        previous=card.file(card.path(a.destination)[2]);old_hash=hashlib.sha256(previous).hexdigest()
        (out/('previous-'+old_hash[:12]+'.CHG')).write_bytes(previous)
        report=card.install(payload,a.destination);report['version']=game.version;print('Cart written and verified',report,flush=True)
        actual=card.file(card.path(a.destination)[2]);loaded,_,issues=game_from_chg(actual,device='rev0')
        assert loaded.binaries['rev0']==game.binaries['rev0'] and not any(i.error for i in issues)
        card.cache.clear()
        for name,expected in baseline.items():assert card.file(card.path(name)[2])==expected,name
        assert card.file(card.path(save_name)[2])==save,'Save journal changed'
        assert {name:entry for name,entry in card.files(games_folder,'GAMES') if name!=a.destination}==entries,'Other game entries changed'
        (G/'build/MIDNIGHT.CHG').write_bytes(payload)
        report.update(result='passed',firmware_sha256=hashlib.sha256(runtime.flash_image(game,'rev0')).hexdigest(),
                      preserved_board_files=len(baseline),preserved_other_game_entries=len(entries),
                      save_file=save_name,save_sha256=hashlib.sha256(save).hexdigest(),save_journal_preserved=True,
                      transport='Pinball USB sector API')
        (out/'sd-installed.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'PASS: exact cart/firmware, {len(baseline)} existing board files, save journal and {len(entries)} other game entries preserved',flush=True)
    finally:
        try:
            c.request('K 0');c.request('L')
            if paused is not None:c.request('Q '+str(paused))
        finally:t.close()
if __name__=='__main__':main()
