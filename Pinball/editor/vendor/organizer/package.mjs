import {CATEGORY_TITLE_LIMIT, MAX_ENTRIES, encodeIndex, sfn, uniqueShortName} from './menu.mjs';
import {ascii, crc32, equal, view} from './serial.mjs';
import {PACKAGE_LIMIT, unzipPackage} from './zip.mjs';

const validText = /^[ -~]*(?![\s\S])/;
const uiColors = {text: '#FFF4D6', disabled: '#808080', selectedText: '#000000', mark: '#D62020'};
const screens = new Set(['installed', 'game', 'folder', 'error-1', 'error-2', 'error-3', 'error-4', 'error-5']);
const gameFields = ['version', 'author', 'description', 'genre', 'license', 'url', 'sourceUrl'];
const pngSignature = Uint8Array.of(137, 80, 78, 71, 13, 10, 26, 10);

function cartError(where, message) {
  throw new Error(`${where}: ${message}`);
}

function object(value, where) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) cartError(where, 'expected an object');
  return value;
}

function text(data, key, where, fallback) {
  const value = Object.hasOwn(data, key) ? data[key] : fallback;
  if (typeof value !== 'string') cartError(where + key, 'expected text');
  return value;
}

function list(value, where) {
  if (!Array.isArray(value)) cartError(where, 'expected an array');
  return value;
}

function fileAt(files, path, where) {
  if (typeof path !== 'string' || !files.has(path)) cartError(where, `missing package file ${path ?? ''}`);
  return files.get(path);
}

function base64(bytes) {
  let value = '';
  for (let offset = 0; offset < bytes.length; offset += 16384) {
    value += String.fromCharCode(...bytes.subarray(offset, offset + 16384));
  }
  return btoa(value);
}

function canonicalJson(value) {
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(',') + ']';
  if (typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(key => canonicalJson(key) + ':' + canonicalJson(value[key])).join(',') + '}';
  }
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g, char => '\\u' + char.charCodeAt(0).toString(16).padStart(4, '0'));
}

async function browserPixels(bytes) {
  const image = await createImageBitmap(new Blob([bytes], {type: 'image/png'}),
    {colorSpaceConversion: 'none', premultiplyAlpha: 'none'});
  try {
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 128;
    const context = canvas.getContext('2d', {willReadFrequently: true});
    context.drawImage(image, 0, 0);
    return context.getImageData(0, 0, 128, 128).data;
  } finally {
    image.close();
  }
}

async function picture(bytes, colors, decode, where, optional = false) {
  if (bytes.length < 33 || !equal(bytes.subarray(0, 8), pngSignature) ||
      view(bytes).getUint32(8) !== 13 || view(bytes).getUint32(12) !== 0x49484452 ||
      view(bytes).getUint32(16) !== 128 || view(bytes).getUint32(20) !== 128) {
    cartError(where, 'expected a 128×128 PNG');
  }
  let pixels;
  try {
    pixels = await decode(bytes);
    if (pixels.length !== 128 * 128 * 4) throw new Error('incorrect decoded size');
  } catch {
    cartError(where, 'could not decode PNG');
  }

  const result = new Uint8Array(8704);
  result.set(ascii('CHB1'));
  const palette = view(result);
  const used = new Map();
  function color(rgb, index) {
    if (!used.has(rgb)) used.set(rgb, index);
    palette.setUint16(8 + index * 2, ((rgb >> 8) & 0xf800) | ((rgb >> 5) & 0x7e0) | ((rgb >> 3) & 31), true);
  }
  color(0xff00ff, 15);
  Object.values(colors).forEach((hex, index) => color(parseInt(hex.slice(1), 16), 11 + index));
  let next = 0;
  for (let i = 0; i < 128 * 128; i++) {
    const offset = i * 4;
    if (pixels[offset + 3] !== 255) {
      if (optional) return null;
      cartError(where, 'menu artwork must be opaque');
    }
    const rgb = (pixels[offset] << 16) | (pixels[offset + 1] << 8) | pixels[offset + 2];
    if (!used.has(rgb)) {
      if (next === 11) {
        if (optional) return null;
        cartError(where, 'menu artwork has more than 11 custom colors');
      }
      color(rgb, next++);
    }
    result[512 + (i >>> 1)] |= used.get(rgb) << (i & 1 ? 0 : 4);
  }
  return result;
}

function chgFile(game, image, art, record) {
  const payloadLength = (image.length + 3) & ~3;
  const pictureOffset = Math.ceil((512 + payloadLength) / 512) * 512;
  const recordOffset = pictureOffset + (art?.length ?? 0);
  const result = new Uint8Array(recordOffset + record.length);
  const fields = view(result);
  result.set(ascii('CHG1'));
  fields.setUint16(4, 1, true);
  fields.setUint16(6, 512, true);
  fields.setUint32(8, 0x35335843, true); // CX35, Rev0
  fields.setUint32(12, 0x003000f7, true);
  fields.setUint32(16, payloadLength, true);
  result.set(image, 512);
  result.fill(255, 512 + image.length, 512 + payloadLength);
  fields.setUint32(20, crc32(result.subarray(512, 512 + payloadLength)), true);
  for (const [key, at, limit] of [['title', 32, 31], ['author', 64, 15], ['version', 80, 7]]) {
    if (validText.test(game[key] ?? '')) result.set(ascii((game[key] ?? '').slice(0, limit)), at);
  }
  const sections = [[108, recordOffset, record]];
  if (art) sections.unshift([96, pictureOffset, art]);
  for (const [field, offset, bytes] of sections) {
    fields.setUint32(field, offset, true);
    fields.setUint32(field + 4, bytes.length, true);
    fields.setUint32(field + 8, crc32(bytes), true);
    result.set(bytes, offset);
  }
  fields.setUint32(508, crc32(result.subarray(0, 508)), true);
  return result;
}

function validSdPath(path) {
  return path.length <= 120 && !/^(GAMES(?:\/|$)|SAVES(?:\/|$)|_CHWEB)/.test(path) &&
    path.split('/').every(part => sfn.test(part));
}

function loadAssets(game, archive, assets, where) {
  if (!Object.hasOwn(game, 'sdcard')) return [];
  const prefix = text(game, 'sdcard', where);
  if (!prefix.endsWith('/')) cartError(where + 'sdcard', 'expected an archive folder ending in /');
  const own = [];
  for (const [name, bytes] of archive) {
    if (!name.startsWith(prefix)) continue;
    const path = name.slice(prefix.length);
    if (!validSdPath(path)) cartError(where + 'sdcard', `unsupported SD path ${path}`);
    if (assets.has(path) && !equal(assets.get(path), bytes)) cartError(where + 'sdcard', `conflicting data for ${path}`);
    assets.set(path, bytes);
    own.push({path, bytes: bytes.length, crc32: crc32(bytes).toString(16).padStart(8, '0')});
  }
  return own.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
}

async function loadGame(game, archive, assets, decode, where) {
  object(game, where);
  const id = text(game, 'id', where);
  const title = text(game, 'title', where);
  if (!/^[a-z0-9][a-z0-9-]{0,31}(?![\s\S])/.test(id)) cartError(where + 'id', 'invalid game ID');
  if (!title.trim() || title.length > 31 || !validText.test(title)) cartError(where + 'title', 'expected 1–31 printable ASCII characters');
  const record = {game: {id, title}, chgRecord: 1};
  for (const key of gameFields) {
    const value = text(game, key, where, '');
    if (value) record.game[key] = value;
  }
  if (Object.hasOwn(game, 'buttons')) {
    const buttons = list(game.buttons, where + 'buttons').map(button => {
      object(button, where + 'buttons');
      const control = text(button, 'control', where);
      const action = text(button, 'action', where);
      if (!control || !action) cartError(where + 'buttons', 'button text is empty');
      return {control, action};
    });
    if (buttons.length) record.game.buttons = buttons;
  }
  const binaries = new Map();
  for (const binary of list(game.binaries, where + 'binaries')) {
    object(binary, where + 'binaries');
    const device = text(binary, 'device', where);
    if (!/^[a-z][a-z0-9-]{0,31}(?![\s\S])/.test(device) || binaries.has(device)) cartError(where + 'binaries', 'invalid or duplicate device');
    binaries.set(device, fileAt(archive, binary.filename, where + 'binaries'));
  }
  const image = binaries.get('rev0');
  if (!image) cartError(where + 'binaries', 'a Rev0 binary is required');
  if (!image.length || image.length > 50944) cartError(where + 'binaries', 'Rev0 binary is outside the supported size');
  if (image.length >= 12 && view(image).getUint32(8, true) === 0x4c424843) cartError(where + 'binaries', 'expected an application, found a bootloader');
  record.binaryBytes = image.length;
  const licenses = Object.create(null);
  for (const path of list(game.licenseFiles === undefined ? [] : game.licenseFiles, where + 'licenseFiles')) {
    const bytes = fileAt(archive, path, where + 'licenseFiles');
    const name = path.split('/').at(-1);
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(name)) cartError(where + 'licenseFiles', `invalid name ${name}`);
    licenses[name] = base64(bytes);
  }
  if (Object.keys(licenses).length) record.licenseFiles = licenses;
  const ownAssets = loadAssets(game, archive, assets, where);
  if (ownAssets.length) record.sdcard = ownAssets;
  let png;
  let art;
  if (Object.hasOwn(game, 'cartImage')) {
    png = fileAt(archive, game.cartImage, where + 'cartImage');
    art = await picture(png, uiColors, decode, where + 'cartImage', true);
    record.cartImage = base64(png);
  }
  const metadata = ascii(canonicalJson(record));
  if (metadata.length > 1048576) cartError(where, 'game archive metadata exceeds 1 MiB');
  const folder = text(game, 'folder', where, '');
  const parts = folder ? folder.split('/') : [];
  if (parts.length > 4 || parts.some(part => !part || part.length > CATEGORY_TITLE_LIMIT || part !== part.trim() || !validText.test(part))) {
    cartError(where + 'folder', 'invalid category path');
  }
  return {id, title, parts, previewArt: png, bytes: chgFile(record.game, image, art, metadata)};
}

async function menuArtwork(manifest, archive, decode) {
  const menu = object(manifest.menu === undefined ? {} : manifest.menu, 'menu');
  const colors = {...uiColors};
  for (const [key, value] of Object.entries(object(menu.colors === undefined ? {} : menu.colors, 'menu.colors'))) {
    if (!Object.hasOwn(colors, key)) continue;
    if (typeof value !== 'string' || value.length !== 7 || !/^#[0-9a-f]{6}$/i.test(value)) cartError('menu.colors.' + key, 'expected #RRGGBB');
    colors[key] = value;
  }
  async function art(entry, key, where) {
    if (!Object.hasOwn(entry, key)) return null;
    return picture(fileAt(archive, entry[key], where), key === 'background' ? colors : uiColors, decode, where);
  }

  // Import preserves the destination's root art and system screens.
  for (const key of ['background', 'cover', 'about']) await art(menu, key, 'menu.' + key);
  const system = object(menu.systemImages === undefined ? {} : menu.systemImages, 'menu.systemImages');
  const extension = manifest['x-chgame-web'];
  const oldScreens = extension?.version === 1 ? extension.systemImages : undefined;
  for (const group of [oldScreens ?? {}, system]) {
    for (const [name, path] of Object.entries(group)) {
      if (screens.has(name)) await picture(fileAt(archive, path, 'menu.systemImages.' + name), uiColors, decode, 'menu.systemImages.' + name);
    }
  }
  const metadata = new Map();
  for (const folder of list(menu.folders === undefined ? [] : menu.folders, 'menu.folders')) {
    object(folder, 'menu.folders');
    const name = text(folder, 'name', 'menu.folders.');
    const entry = metadata.get(name) ?? {};
    for (const key of ['background', 'cover']) {
      const bytes = await art(folder, key, `menu.folders[${name}].${key}`);
      if (bytes) entry[key] = bytes;
    }
    metadata.set(name, entry);
  }
  return {metadata, cover: Object.hasOwn(menu, 'cover') ? archive.get(menu.cover) : undefined};
}

function runtimeFiles(games, assets, artwork, launch) {
  const tree = new Map([['', []]]);
  for (const game of games) {
    let folder = '';
    for (const title of game.parts) {
      const child = folder ? folder + '/' + title : title;
      if (!tree.has(child)) {
        tree.set(child, []);
        tree.get(folder).push({title, child});
      }
      folder = child;
    }
    tree.get(folder).push(game);
  }
  const target = games.find(game => game.id === launch);
  const launchFolders = new Set(target?.parts.map((_, i) => target.parts.slice(0, i + 1).join('/')));
  const paths = new Map([['', 'GAMES']]);
  const results = [];
  const add = (path, data) => results.push({path, data});
  for (const [folder, entries] of tree) {
    const path = paths.get(folder);
    if (entries.length > MAX_ENTRIES) cartError(folder || 'Main Menu', 'more than 240 entries');
    const taken = new Set();
    const index = entries.map(entry => {
      const stem = entry.title.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8);
      const name = uniqueShortName(entry.child ? stem || 'FOLDER' : (stem || 'GAME') + '.CHG', taken);
      taken.add(name);
      const record = new Uint8Array(32);
      if (entry.child) {
        paths.set(entry.child, path + '/' + name);
        record[11] = Number(launchFolders.has(entry.child));
        record.set(ascii(entry.title), 12);
      } else {
        record[11] = Number(entry === target);
        add(path + '/' + name, entry.bytes);
      }
      return {name, record};
    });
    add(path + '/MENU.IDX', encodeIndex(index));
    const art = artwork.get(folder);
    if (art?.background) add(path + '/MENU.BG', art.background);
    if (art?.cover) add(path + '/COVER.PIC', art.cover);
  }
  for (const [path, bytes] of assets) {
    for (let slash = path.lastIndexOf('/'); slash >= 0; slash = path.lastIndexOf('/', slash - 1)) {
      if (assets.has(path.slice(0, slash))) cartError('sdcard', `file blocks folder in ${path}`);
    }
    add(path, bytes);
  }
  if (results.reduce((total, file) => total + file.data.length, 0) > PACKAGE_LIMIT) {
    cartError('Package', 'prepared SD files exceed 64 MiB');
  }
  return results;
}

export async function prepareArchive(bytes, decode = browserPixels) {
  if (bytes.length > PACKAGE_LIMIT) cartError('Package', 'the compressed package exceeds 64 MiB');
  const archive = await unzipPackage(bytes);
  const manifestBytes = fileAt(archive, 'info.json', 'Package');
  let manifest;
  try {
    manifest = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(manifestBytes));
  } catch {
    cartError('info.json', 'invalid UTF-8 JSON');
  }
  object(manifest, 'info.json');
  if (manifest.schemaVersion !== 1) cartError('info.json', 'expected schema version 1');
  const title = text(manifest, 'title', '');
  if (!title.trim()) cartError('title', 'the package needs a title');
  for (const key of ['version', 'author', 'description', 'date', 'license', 'url', 'sourceUrl']) text(manifest, key, '', '');
  if (manifest.date && !/^\d{4}-\d{2}-\d{2}([T ][0-9:.+\-Z]+)?$/.test(manifest.date)) cartError('date', 'expected an ISO 8601 date');
  const launch = text(manifest, 'launch', '', '');
  const items = list(manifest.games, 'games');
  if (!items.length) cartError('games', 'a package needs at least one game');
  const games = [];
  const assets = new Map();
  const ids = new Set();
  for (const [index, item] of items.entries()) {
    const game = await loadGame(item, archive, assets, decode, `games[${index}].`);
    if (ids.has(game.id)) cartError('games', `duplicate game ID ${game.id}`);
    games.push(game);
    ids.add(game.id);
  }
  if (launch && !ids.has(launch)) cartError('launch', 'the selected game does not exist');
  const {metadata, cover} = await menuArtwork(manifest, archive, decode);
  return {
    title,
    files: runtimeFiles(games, assets, metadata, launch),
    cover: cover ?? games.find(game => game.previewArt)?.previewArt,
    sourceUrl: manifest.sourceUrl || (items.length === 1 ? items[0].sourceUrl : ''),
  };
}
