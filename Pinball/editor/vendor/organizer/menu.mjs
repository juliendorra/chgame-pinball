import {ascii, crc32, equal, string, view} from './serial.mjs';

export const MAX_ENTRIES = 240;
export const CATEGORY_TITLE_LIMIT = 19;
const MAX_INDEX = 8192;
const PICTURE = 8704;
const indexPath = folder => folder.path + '/MENU.IDX';
const byTitle = entry => entry.title.toUpperCase().replace(/[^ -_]/g, '?').slice(0, 19);
export const sfn = /^[A-Z0-9!#$%&'()@^_`{}~-]{1,8}(\.[A-Z0-9!#$%&'()@^_`{}~-]{1,3})?$/;

function shortKey(name) {
  const [base, ext = ''] = name.split('.');
  return base.padEnd(8) + ext.padEnd(3);
}

export function uniqueShortName(name, occupied) {
  const [stem, ext] = name.split('.');
  const suffix = ext ? '.' + ext : '';
  const reserved = /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/;
  let candidate = name;
  for (let n = 2; occupied.has(candidate) || reserved.test(candidate.split('.')[0]); n++) {
    candidate = stem.slice(0, 8 - String(n).length) + n + suffix;
  }
  return candidate;
}

export function parseIndex(bytes) {
  const records = new Map();
  if (!bytes || bytes.length < 32 || bytes.length % 32 || string(bytes.subarray(0, 4)) !== 'CHX1') return records;
  for (let i = 32; i < bytes.length; i += 32) {
    const key = string(bytes.subarray(i, i + 11));
    if (!records.has(key)) records.set(key, bytes.slice(i, i + 32));
  }
  return records;
}

export function encodeIndex(entries) {
  const bytes = new Uint8Array(32 * (entries.length + 1));
  bytes.set(ascii('CHX1'));
  for (const [i, entry] of entries.entries()) {
    const at = 32 * (i + 1);
    if (entry.record) bytes.set(entry.record, at);
    bytes.set(ascii(shortKey(entry.name)), at);
    if (categoryRenamed(entry)) {
      bytes.fill(0, at + 12, at + 32);
      bytes.set(ascii(entry.title), at + 12);
    }
  }
  return bytes;
}

export function cartHeader(bytes, size) {
  if (bytes.length !== 512) return {};
  const header = view(bytes);
  if (string(bytes.subarray(0, 4)) !== 'CHG1' || header.getUint16(4, true) !== 1 ||
      header.getUint16(6, true) !== 512 || header.getUint32(508, true) !== crc32(bytes.subarray(0, 508))) return {};
  const payload = header.getUint32(16, true);
  const offset = header.getUint32(96, true);
  const picture = offset >= 512 + payload && offset < 0x20000 && offset % 512 === 0 &&
    header.getUint32(100, true) === PICTURE && offset + PICTURE <= size;
  return {
    title: string(bytes.subarray(32, 64)),
    author: string(bytes.subarray(64, 80)),
    version: string(bytes.subarray(80, 88)),
    headerCrc: header.getUint32(508, true),
    compatible: header.getUint32(8, true) === 0x35335843 && header.getUint32(12, true) === 0x003000f7 &&
      payload >= 4 && payload <= 50944 && payload % 4 === 0 && 512 + payload <= size,
    picture: picture ? {offset, crc: header.getUint32(104, true)} : null,
  };
}

export function decodePicture(bytes) {
  if (bytes.length !== PICTURE || string(bytes.subarray(0, 4)) !== 'CHB1') throw new Error('Invalid SD poster');
  const palette = Array.from({length: 16}, (_, i) => {
    const color = view(bytes).getUint16(8 + i * 2, true);
    return [Math.round((color >>> 11) * 255 / 31), Math.round(((color >>> 5) & 63) * 255 / 63),
      Math.round((color & 31) * 255 / 31), 255];
  });
  const pixels = new Uint8ClampedArray(128 * 128 * 4);
  for (let i = 512, out = 0; i < bytes.length; i++, out += 8) {
    pixels.set(palette[bytes[i] >> 4], out);
    pixels.set(palette[bytes[i] & 15], out + 4);
  }
  return pixels;
}

async function takeIndex(card, folder, files) {
  const meta = files.find(entry => !entry.directory && entry.name === 'MENU.IDX');
  if (!meta) return null;
  if (meta.size > MAX_INDEX) throw new Error(`${folder.path}/MENU.IDX exceeds the supported menu size`);
  return card.read(indexPath(folder), 0, meta.size);
}

export async function scanMenu(card, onFolder = () => {}) {
  const root = {path: 'GAMES', title: 'Main Menu', directory: true, depth: 0};
  const folders = [root];

  for (const folder of folders) {
    onFolder(folder);
    const files = await card.list(folder.path);
    folder.files = files.map(entry => ({...entry}));
    folder.index = await takeIndex(card, folder, files);
    const records = parseIndex(folder.index);
    if (folder.index && !records.size && !equal(folder.index, encodeIndex([]))) {
      folder.editBlocked = true;
    }
    const order = new Map([...records.keys()].map((key, i) => [key, i]));
    const entries = files.filter(entry => !/^[._]/.test(entry.name) &&
      (entry.directory || entry.name.endsWith('.CHG')));
    // LIST v1 includes dot/underscore names, but does not expose FAT hidden/system attributes.
    folder.overLimit = entries.length > MAX_ENTRIES;
    folder.entries = entries.slice(0, MAX_ENTRIES);

    for (const entry of folder.entries) {
      if (!sfn.test(entry.name)) throw new Error(`Unsupported short name in ${folder.path}: ${entry.name}`);
      const key = shortKey(entry.name);
      entry.record = records.get(key);
      entry.order = order.get(key) ?? Infinity;
      entry.path = folder.path + '/' + entry.name;
      entry.title = entry.directory ? string(entry.record?.subarray(12) ?? new Uint8Array()) || entry.name : entry.name;
      if (!entry.directory) {
        if (entry.size >= 512) {
          const header = cartHeader(await card.read(entry.path, 0, 512), entry.size);
          Object.assign(entry, {...header, title: header.title || entry.name, compatible: Boolean(header.compatible)});
        } else entry.compatible = false;
      } else {
        entry.originalTitle = entry.title;
        if (folder.depth < 4) {
          entry.depth = folder.depth + 1;
          folders.push(entry);
        }
      }
    }
    folder.entries.sort((a, b) => (a.order - b.order) || (byTitle(a) < byTitle(b) ? -1 : byTitle(a) > byTitle(b) ? 1 : 0));
    folder.original = folder.entries.slice();
    folder.cover = files.some(entry => !entry.directory && entry.name === 'COVER.PIC' && entry.size === PICTURE);
    folder.system = files.some(entry => !entry.directory && entry.name === 'SYSTEM.PIC' && entry.size === PICTURE * 9);
  }
  return {root, folders, removals: []};
}

export async function readPoster(card, entry, root) {
  let bytes;
  if (entry.cover) bytes = await card.read(entry.path + '/COVER.PIC', 0, PICTURE);
  else if (entry.picture) {
    bytes = await card.read(entry.path, entry.picture.offset, PICTURE);
    if (crc32(bytes) !== entry.picture.crc) throw new Error('SD poster checksum mismatch');
  } else if (root.system) {
    root.fallbacks ??= new Map();
    const slot = entry.directory ? 3 : 2;
    if (!root.fallbacks.has(slot)) {
      root.fallbacks.set(slot, decodePicture(await card.read('GAMES/SYSTEM.PIC', slot * PICTURE, PICTURE)));
    }
    return root.fallbacks.get(slot);
  }
  return bytes ? decodePicture(bytes) : null;
}

function categoryRenamed(entry) {
  return entry.originalTitle !== undefined && entry.title !== entry.originalTitle;
}

function categoryTitle(title) {
  const name = title.trim();
  if (!/^[ -~]+$/.test(name) || name.length > CATEGORY_TITLE_LIMIT || name.includes('/')) {
    throw new Error(`Use 1–${CATEGORY_TITLE_LIMIT} printable ASCII characters, without a slash`);
  }
  return name;
}

export function renameCategory(parent, entry, title) {
  if (!entry.directory || !parent.entries.includes(entry) || parent.editBlocked || parent.overLimit) {
    throw new Error('This category cannot be renamed');
  }
  entry.title = categoryTitle(title);
}

export function newCategory(menu, title) {
  const root = menu.root;
  if (root.editBlocked || root.overLimit || root.entries.length >= MAX_ENTRIES) {
    throw new Error('The main menu cannot accept another category');
  }
  const label = categoryTitle(title);
  if (root.entries.some(entry => entry.directory && entry.title.toUpperCase() === label.toUpperCase())) {
    throw new Error('A top-level category already has that name');
  }
  const name = uniqueShortName(label.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8) || 'CATEGORY',
    new Set([...root.files, ...root.entries].map(entry => entry.name)));
  return {
    name, title: label, originalTitle: '', path: 'GAMES/' + name, directory: true,
    depth: 1, new: true, entries: [], original: [], index: null, files: [],
  };
}

const alphabetical = new Intl.Collator('en', {sensitivity: 'base', numeric: true});

export function organizeFolder(folder, order) {
  if (order === 'restore') {
    if (!folder.manualOrder) return;
    const current = new Set(folder.entries);
    folder.entries = folder.manualOrder.filter(entry => current.delete(entry)).concat([...current]);
    delete folder.manualOrder;
    return;
  }
  folder.manualOrder ??= folder.entries.slice();
  folder.entries.sort((a, b) => (order === 'newest' ? (b.modified ?? 0) - (a.modified ?? 0) : 0) ||
    alphabetical.compare(a.title, b.title));
}

export function changedFolders(menu) {
  return menu.folders.filter(folder => folder.new || folder.original.length !== folder.entries.length ||
    folder.entries.some((entry, i) => entry !== folder.original[i] || categoryRenamed(entry)));
}

const below = (path, prefix) => path === prefix || path.startsWith(prefix + '/');
const menuFiles = new Set(['MENU.IDX', 'MENU.BG', 'COVER.PIC']);

async function isAppleDouble(card, path, file) {
  if (file.directory || !file.name.startsWith('_') || !sfn.test(file.name) || file.size < 26) return false;
  const header = view(await card.read(path, 0, 8));
  return header.getUint32(0) === 0x00051607 && header.getUint32(4) === 0x00020000;
}

export async function planRemoval(menu, folder, entry, card) {
  if (!folder.entries.includes(entry) || entry.path !== folder.path + '/' + entry.name) {
    throw new Error('Save or reset the pending move before removing this entry');
  }
  if (entry.record?.[11] & 1) throw new Error('This entry belongs to the startup menu path');
  const descendants = menu.folders.filter(item => below(item.path, entry.path));
  if (changedFolders(menu).some(item => descendants.includes(item))) {
    throw new Error('Save or reset edits within this category before removing it');
  }
  const files = [];
  let carts = Number(!entry.directory);
  let hiddenCarts = 0;
  let metadata = 0;
  if (entry.directory && !entry.entries) throw new Error('This category is too deep to remove here');
  for (const dir of descendants.slice().sort((a, b) => b.depth - a.depth)) {
    if (dir.overLimit || dir.editBlocked || dir.original.some(item => item.record?.[11] & 1)) {
      throw new Error(`${dir.title} has a startup entry or an unsupported index`);
    }
    const listed = new Set(dir.original.filter(item => !item.directory || item.entries).map(item => item.name));
    for (const file of dir.files) {
      if (file.name === '.' || file.name === '..') continue;
      const path = dir.path + '/' + file.name;
      if (!listed.has(file.name) && (file.directory || !menuFiles.has(file.name))) {
        if (await isAppleDouble(card, path, file)) {
          metadata++;
        } else if (!file.directory && file.name.startsWith('_') && file.name.endsWith('.CHG') && sfn.test(file.name)) {
          hiddenCarts++;
        } else {
          throw new Error(`${dir.title} contains an extra SD item (${file.name}). Move it elsewhere before removing the category.`);
        }
      }
      if (!file.directory) files.push(path);
    }
    carts += dir.original.filter(item => !item.directory).length;
    files.push(dir.path);
  }
  if (!entry.directory) files.push(entry.path);
  return {entry, descendants, paths: files, carts, hiddenCarts, metadata};
}

export function stageRemoval(menu, folder, plan) {
  folder.entries = folder.entries.filter(entry => entry !== plan.entry);
  menu.removals.push(plan);
}

export function resetMenu(menu) {
  menu.folders = menu.folders.filter(folder => !folder.new);
  for (const folder of menu.folders) {
    folder.entries = folder.original.slice();
    delete folder.manualOrder;
    for (const entry of folder.entries) if (categoryRenamed(entry)) entry.title = entry.originalTitle;
  }
  if (menu.removals) menu.removals.length = 0;
}

export function sameListing(a, b) {
  return a.length === b.length &&
    a.every(old => b.some(current => old.name === current.name && old.directory === current.directory && old.size === current.size));
}

export function sameMenuSnapshot(previous, fresh) {
  const existing = previous.folders.filter(folder => !folder.new);
  return existing.length === fresh.folders.length && existing.every(folder => {
    const current = fresh.folders.find(item => item.path === folder.path);
    return current && equal(folder.index, current.index) && sameListing(folder.files, current.files) &&
      folder.original.every(entry => entry.headerCrc === current.original.find(item => item.name === entry.name)?.headerCrc);
  });
}

export function moveCarts(source, destination, entries) {
  if (source === destination || !entries.length || entries.some(entry => entry.directory || !source.entries.includes(entry))) return;
  if (source.editBlocked || source.overLimit || destination.editBlocked || destination.overLimit ||
      destination.entries.length + entries.length > MAX_ENTRIES) throw new Error('This category cannot accept the move');
  const taken = new Set([...destination.files, ...destination.entries].map(entry => entry.name));
  for (const entry of entries) {
    if (taken.has(entry.name) && entry.path !== destination.path + '/' + entry.name) {
      throw new Error(`${entry.name} already exists in ${destination.title}`);
    }
    if (entry.record?.[11] & 1) throw new Error('The startup cart must stay in its current category');
    taken.add(entry.name);
  }
  const moving = new Set(entries);
  source.entries = source.entries.filter(entry => !moving.has(entry));
  destination.entries.push(...entries);
}

export async function saveMenu(card, menu, progress = () => {}) {
  const changes = changedFolders(menu).sort((a, b) => b.depth - a.depth);
  const moves = [];
  for (const folder of changes) {
    if (folder.editBlocked || folder.overLimit || folder.entries.length > MAX_ENTRIES) throw new Error(`${folder.title} cannot be edited`);
    const files = folder.new ? [] : await card.list(folder.path);
    if (!equal(await takeIndex(card, folder, files), folder.index)) throw new Error(`${folder.title} changed on the SD. Rescan first.`);
    const onCard = files.filter(entry => !/^[._]/.test(entry.name) && (entry.directory || entry.name.endsWith('.CHG')));
    if (!sameListing(folder.original, onCard)) {
      throw new Error(`${folder.title} changed on the SD. Rescan first.`);
    }
    if (folder.entries.some(entry => entry.new && files.some(file => file.name === entry.name))) {
      throw new Error(`${folder.title} changed on the SD. Rescan first.`);
    }
    for (const entry of folder.entries) {
      const destination = folder.path + '/' + entry.name;
      if (entry.path === destination) continue;
      if (entry.directory || files.some(file => file.name === entry.name)) throw new Error(`${destination} already exists`);
      if (entry.size > 0x130000) throw new Error(`${entry.name} exceeds the supported cartridge size`);
      moves.push({entry, destination});
    }
  }
  for (const removal of menu.removals) {
    for (const folder of removal.descendants) {
      if (!sameListing(folder.files, await card.list(folder.path))) {
        throw new Error(`${folder.title} changed on the SD. Rescan first.`);
      }
    }
  }

  // Copy each moved CHG completely before publishing new index files. An
  // interruption can leave duplicates, with the original still available.
  if (changes.some(folder => folder.new)) progress('Creating categories');
  for (const folder of changes) if (folder.new) await card.mkdir(folder.path);
  const covers = changes.filter(folder => folder.coverBytes).map(folder => ({
    file: folder.path + '/COVER.PIC', bytes: folder.coverBytes, phase: 'Writing category cover',
  }));
  const indexes = changes.map(folder => ({
    file: indexPath(folder), bytes: encodeIndex(folder.entries), phase: 'Saving menu order',
  }));
  let fileNumber = 0;
  const fileCount = moves.length + covers.length + indexes.length;
  for (const {entry, destination} of moves) {
    fileNumber++;
    const update = (done, phase) => progress(phase, {
      file: destination, fileNumber, fileCount, done, total: entry.size * 3,
    });
    update(0, 'Reading source cart');
    const bytes = await card.read(entry.path, 0, entry.size, done => update(done, 'Reading source cart'));
    update(entry.size, 'Writing to SD');
    await card.replace(destination, bytes, (done, phase) => update(entry.size + done, phase));
  }
  for (const {file, bytes, phase} of [...covers, ...indexes]) {
    fileNumber++;
    const update = (done, phase) => progress(phase, {file, fileNumber, fileCount, done, total: bytes.length * 2});
    update(0, phase);
    await card.replace(file, bytes, update);
  }
  for (const {entry} of moves) await card.remove(entry.path);
  for (const removal of menu.removals) {
    progress(`Removing ${removal.entry.title}…`);
    for (const path of removal.paths) {
      try {
        await card.remove(path);
      } catch (error) {
        throw new Error(`Could not remove ${path}. ${error.message}`, {cause: error});
      }
    }
  }
  if (changes.length) {
    progress('Finishing SD writes');
    await card.sync();
  }
}
