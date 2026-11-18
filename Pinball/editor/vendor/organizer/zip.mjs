import {crc32, equal, view} from './serial.mjs';

export const PACKAGE_LIMIT = 64 * 1024 * 1024;

function zipError(reason) {
  return new Error(`Invalid .chgame ZIP: ${reason}`);
}

async function inflate(data, size) {
  const reader = new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw')).getReader();
  const bytes = new Uint8Array(size);
  let offset = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      if (offset + value.length > size) throw zipError('a file exceeds its declared size');
      bytes.set(value, offset);
      offset += value.length;
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  if (offset !== size) throw zipError('a compressed file is truncated');
  return bytes;
}

export async function unzipPackage(bytes) {
  const fields = view(bytes);
  const u16 = at => fields.getUint16(at, true);
  const u32 = at => fields.getUint32(at, true);

  let end = bytes.length - 22;
  const minimum = Math.max(0, end - 0xffff);
  while (end >= minimum && (u32(end) !== 0x06054b50 || end + 22 + u16(end + 20) !== bytes.length)) end--;
  if (end < minimum) throw zipError('ZIP directory missing');
  const count = u16(end + 10);
  const central = u32(end + 16);
  if (u16(end + 4) || u16(end + 6) || u16(end + 8) !== count ||
      count > 4096 || central + u32(end + 12) !== end) throw zipError('unsupported ZIP directory');
  let pos = central;
  let total = 0;
  const entries = [];
  const seen = new Set();
  for (let i = 0; i < count; i++) {
    if (pos + 46 > end || u32(pos) !== 0x02014b50) throw zipError('truncated directory entry');
    const flags = u16(pos + 8);
    const method = u16(pos + 10);
    const checksum = u32(pos + 16);
    const packed = u32(pos + 20);
    const size = u32(pos + 24);
    const nameLength = u16(pos + 28);
    const local = u32(pos + 42);
    const nameBytes = bytes.subarray(pos + 46, pos + 46 + nameLength);
    const disk = u16(pos + 34);
    pos += 46 + nameLength + u16(pos + 30) + u16(pos + 32);
    if (pos > end || disk || !nameLength || [...nameBytes].some(ch => ch < 32 || ch > 126)) throw zipError('invalid entry name');
    const name = new TextDecoder().decode(nameBytes);
    const directory = name.endsWith('/');
    const segments = (directory ? name.slice(0, -1) : name).split('/');
    if (/[\\:]/.test(name) || segments.some(part => !part || part === '.' || part === '..')) throw zipError(`unsafe path ${name}`);
    if (flags & 0x2041 || ![0, 8].includes(method)) throw zipError(`unsupported compression or encryption for ${name}`);
    if (directory) continue;
    const folded = name.toLowerCase();
    if (seen.has(folded)) throw zipError(`duplicate path ${name}`);
    seen.add(folded);
    total += size;
    if (total > PACKAGE_LIMIT) throw zipError('the uncompressed package exceeds 64 MiB');
    if (local + 30 > central || u32(local) !== 0x04034b50 || u16(local + 6) !== flags || u16(local + 8) !== method) {
      throw zipError(`invalid local header for ${name}`);
    }
    const localNameSize = u16(local + 26);
    const start = local + 30 + localNameSize + u16(local + 28);
    if (start + packed > central || !equal(nameBytes, bytes.subarray(local + 30, local + 30 + localNameSize))) {
      throw zipError(`invalid file bounds for ${name}`);
    }
    entries.push({name, size, method, checksum, data: bytes.subarray(start, start + packed)});
  }
  if (pos !== end) throw zipError('directory size mismatch');

  const files = new Map();
  for (const {name, size, method, checksum, data} of entries) {
    const result = method ? await inflate(data, size) : data;
    if (result.length !== size || crc32(result) !== checksum) throw zipError(`checksum or size mismatch for ${name}`);
    files.set(name, result);
  }
  return files;
}
