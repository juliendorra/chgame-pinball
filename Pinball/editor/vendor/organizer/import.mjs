import {cartHeader, encodeIndex, MAX_ENTRIES, parseIndex, sameListing, sfn, uniqueShortName} from './menu.mjs';
import {ascii, crc32, equal, string} from './serial.mjs';
import {prepareArchive} from './package.mjs';
import {PACKAGE_LIMIT} from './zip.mjs';

const parent = path => path.slice(0, Math.max(0, path.lastIndexOf('/')));
const github = 'https://github.com';
const latestReleasePath = /^\/([a-z0-9-]+\/[a-z0-9_.-]+)\/releases\/latest\/?$/i;
const releaseAssetPath = /^\/([^/]+\/[^/]+)\/releases\/(?:download\/[^/]+|latest\/download)\/[^/]+\.chgame$/i;

export function packageSourceUrl(value, page) {
  const url = URL.parse(value ?? '');
  if (url?.protocol !== 'https:' || url.username || url.password ||
      url.origin === page.origin || ['juliendorra.com', 'www.juliendorra.com'].includes(url.hostname)) return null;
  return url;
}

export async function preparePackage(file) {
  if (!/\.chgame$/i.test(file.name)) throw new Error('Choose a .chgame package');
  if (file.size > PACKAGE_LIMIT) throw new Error('The package exceeds 64 MiB');
  return prepareArchive(new Uint8Array(await file.arrayBuffer()));
}

export function linkedPackageUrl(location) {
  const params = new URL(location);
  const value = new URLSearchParams(params.hash.slice(1)).get('import') ?? params.searchParams.get('import');
  if (value === null) return null;
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error('The import link needs an absolute HTTPS URL');
  }
  const local = url.protocol === 'http:' && url.origin === params.origin &&
    ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((!local && url.protocol !== 'https:') || url.username || url.password) {
    throw new Error('The import link needs an HTTPS URL without credentials');
  }
  return url;
}

async function latestReleaseAsset(repo, fetcher) {
  const endpoint = new URL(`https://api.github.com/repos/${repo}/releases/latest`);
  let release;
  try {
    const response = await fetcher(endpoint, {
      credentials: 'omit', referrerPolicy: 'no-referrer', signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    release = await response.json();
  } catch (error) {
    throw new Error(`Could not look up the latest GitHub release (${error.message})`);
  }
  const carts = (Array.isArray(release?.assets) ? release.assets : [])
    .filter(asset => asset?.state === 'uploaded' && typeof asset.name === 'string' && /\.chgame$/i.test(asset.name));
  if (!carts.length) throw new Error('The latest GitHub release has no .chgame file');
  if (carts.length > 1) throw new Error('The latest release has several .chgame files. Link to a specific cart.');
  const url = URL.parse(carts[0].browser_download_url ?? '');
  const match = url && releaseAssetPath.exec(url.pathname);
  if (url?.origin !== github || url.username || url.password || match?.[1].toLowerCase() !== repo.toLowerCase()) {
    throw new Error('GitHub returned an invalid cart download URL');
  }
  return url;
}

export async function prepareLinkedPackage(url, fetcher = fetch, releaseEndpoint) {
  const latest = url.origin === github && latestReleasePath.exec(url.pathname);
  if (latest && !releaseEndpoint) throw new Error('Use the hosted organizer to preview the latest GitHub release');
  const isRelease = url.origin === github && releaseAssetPath.test(url.pathname);
  const asset = latest ? await latestReleaseAsset(latest[1], fetcher) : url;
  const download = releaseEndpoint && (latest || isRelease) ? new URL(releaseEndpoint) : url;
  if (download !== url) download.searchParams.set('url', asset.href);
  let response;
  try {
    response = await fetcher(download, {
      credentials: download === url ? 'omit' : 'same-origin',
      referrerPolicy: 'no-referrer', signal: AbortSignal.timeout(30000),
    });
  } catch {
    throw new Error('Could not download the linked cart. Check that the file host allows cross-origin downloads.');
  }
  if (!response.ok || !response.body) throw new Error(`Could not download the linked cart (HTTP ${response.status})`);
  if (response.url) {
    const target = new URL(response.url);
    if (target.protocol !== 'https:' && target.origin !== download.origin) throw new Error('The cart download redirected away from HTTPS');
  }
  if (Number(response.headers.get('Content-Length')) > PACKAGE_LIMIT) throw new Error('The package exceeds 64 MiB');
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.length;
      if (size > PACKAGE_LIMIT) throw new Error('The package exceeds 64 MiB');
      chunks.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  return prepareArchive(new Uint8Array(await new Blob(chunks).arrayBuffer()));
}

function packageTree(pkg) {
  const files = new Map(pkg.files.map(file => {
    if (file.path.length > 120 || !file.path.split('/').every(part => sfn.test(part)) ||
        /^(SAVES(?:\/|$)|_CHWEB)/.test(file.path)) throw new Error(`Unsupported SD path: ${file.path}`);
    return [file.path, file.data];
  }));
  function walk(path) {
    const entries = [...parseIndex(files.get(path + '/MENU.IDX')).values()].map(record => {
      const base = string(record.subarray(0, 8)).trimEnd();
      const ext = string(record.subarray(8, 11)).trimEnd();
      const name = ext ? base + '.' + ext : base;
      if (!sfn.test(name)) throw new Error('Invalid package menu entry');
      const full = path + '/' + name;
      if (ext === 'CHG' && files.has(full)) return {name, bytes: files.get(full)};
      if (!files.has(full + '/MENU.IDX')) throw new Error(`Missing package entry ${full}`);
      return {name, title: string(record.subarray(12)) || name, tree: walk(full)};
    });
    const art = ['MENU.BG', 'COVER.PIC'].filter(name => files.has(path + '/' + name))
      .map(name => ({name, bytes: files.get(path + '/' + name)}));
    return {entries, art};
  }
  return {
    tree: walk('GAMES'),
    assets: [...files].filter(([name]) => !name.startsWith('GAMES/')).map(([path, bytes]) => ({path, bytes})),
  };
}

function gameCount(tree) {
  return tree.entries.reduce((n, entry) => n + (entry.tree ? gameCount(entry.tree) : 1), 0);
}

export function describePackage(pkg) {
  const {tree, assets} = packageTree(pkg);
  const games = [];
  function collect(group, folders) {
    for (const entry of group.entries) {
      if (entry.tree) {
        collect(entry.tree, [...folders, entry.title]);
      } else {
        const header = cartHeader(entry.bytes.subarray(0, 512), entry.bytes.length);
        games.push({title: header.title || entry.name, version: header.version, folders});
      }
    }
  }
  collect(tree, []);
  return {games, assets: assets.map(asset => asset.path).sort()};
}

async function planAssets(card, assets) {
  const dirs = new Set();
  for (const file of assets) for (let dir = parent(file.path); dir; dir = parent(dir)) dirs.add(dir);
  const existing = new Map();
  if (assets.length) existing.set('', await card.list(''));
  const directories = [];
  for (const dir of [...dirs].sort((a, b) => a.length - b.length)) {
    const found = existing.get(parent(dir))?.find(file => file.name === dir.split('/').at(-1));
    if (found && !found.directory) throw new Error(`A file blocks the package folder ${dir}`);
    if (found) existing.set(dir, await card.list(dir));
    else directories.push(dir);
  }
  const files = [];
  for (const file of assets) {
    const found = existing.get(parent(file.path))?.find(entry => entry.name === file.path.split('/').at(-1));
    if (!found) files.push(file);
    else if (found.directory || found.size !== file.bytes.length ||
             (found.size && await card.check(file.path, found.size) !== crc32(file.bytes))) {
      throw new Error(`The package conflicts with an existing SD item at ${file.path}`);
    }
  }
  return {directories, files};
}

export async function planImport(card, menu, pkg, destination, makeCover) {
  const {tree, assets} = packageTree(pkg);
  const {directories, files} = await planAssets(card, assets);
  const working = new Map();
  let added = 0;

  async function open(folder) {
    if (working.has(folder.path)) return working.get(folder.path);
    if (folder.overLimit || folder.editBlocked) throw new Error(`${folder.title} cannot be edited`);
    const listing = await card.list(folder.path);
    const indexPath = folder.path + '/MENU.IDX';
    const index = listing.find(file => file.name === 'MENU.IDX' && !file.directory);
    if ((index?.size ?? 0) !== (folder.index?.length ?? 0) ||
        !equal(index ? await card.read(indexPath, 0, index.size) : null, folder.index) ||
        !sameListing(folder.files, listing)) {
      throw new Error(`${folder.title} changed on the SD. Rescan first.`);
    }
    const state = {path: folder.path, depth: folder.depth, title: folder.title, entries: folder.entries.slice(),
      listing: new Map(listing.map(file => [file.name, file])), changed: false};
    working.set(state.path, state);
    return state;
  }

  function append(state, entry) {
    if (state.entries.length >= MAX_ENTRIES) throw new Error(`${state.title} has no room for another entry`);
    state.entries.push(entry);
    state.listing.set(entry.name, entry);
    state.changed = true;
  }

  async function openCategory(state, entry) {
    const matches = state.entries.filter(item => item.directory &&
      item.title.toUpperCase() === entry.title.toUpperCase());
    if (matches.length > 1) throw new Error(`More than one category is named ${entry.title} in ${state.title}`);
    const [match] = matches;
    if (match) {
      const folder = working.get(match.path) ?? menu.folders.find(item => item.path === match.path);
      if (!folder) throw new Error(`${match.title} exceeds the supported category depth`);
      return working.get(match.path) ?? open(folder);
    }
    if (state.depth >= 4) throw new Error('The package has too many nested categories for this menu');
    const name = uniqueShortName(entry.name, state.listing);
    const path = state.path + '/' + name;
    const record = new Uint8Array(32);
    record.set(ascii(entry.title).subarray(0, 20), 12);
    append(state, {name, path, title: entry.title, directory: true, record});
    const created = {path, depth: state.depth + 1, title: entry.title, entries: [], listing: new Map(), changed: true};
    working.set(path, created);
    directories.push(path);
    for (const art of entry.tree.art) files.push({path: path + '/' + art.name, bytes: art.bytes});
    if (makeCover && !entry.tree.art.some(item => item.name === 'COVER.PIC')) {
      files.push({path: path + '/COVER.PIC', bytes: makeCover(entry.title)});
    }
    return created;
  }

  async function addEntries(state, group, flatten) {
    for (const entry of group.entries) {
      if (entry.tree) {
        await addEntries(flatten ? state : await openCategory(state, entry), entry.tree, flatten);
        continue;
      }
      const existing = state.listing.get(entry.name);
      if (existing && !existing.directory && existing.size === entry.bytes.length &&
          !existing.planned && await card.check(state.path + '/' + entry.name, existing.size) === crc32(entry.bytes)) continue;
      const name = uniqueShortName(entry.name, state.listing);
      files.push({path: state.path + '/' + name, bytes: entry.bytes});
      append(state, {name, size: entry.bytes.length, planned: true});
      added++;
    }
  }

  const target = await open(destination ?? menu.root);
  await addEntries(target, tree, Boolean(destination));
  const indexes = [...working.values()].filter(state => state.changed).sort((a, b) => b.depth - a.depth)
    .map(state => ({path: state.path + '/MENU.IDX', bytes: encodeIndex(state.entries)}));
  for (const {path} of [...files, ...indexes]) {
    if (path.length > 120) throw new Error(`The SD path is too long: ${path}`);
  }
  return {games: gameCount(tree), added, target: target.path, directories, files, indexes};
}

export async function writeImport(card, plan, progress) {
  if (plan.directories.length) progress('Creating categories and SD folders');
  for (const dir of plan.directories) await card.mkdir(dir);
  const files = [...plan.files, ...plan.indexes];
  for (const [index, {path, bytes}] of files.entries()) {
    const update = (done, phase) => progress(phase, {
      file: path, fileNumber: index + 1, fileCount: files.length, done, total: bytes.length * 2,
    });
    update(0, 'Copying to SD');
    await card.replace(path, bytes, update);
  }
  if (plan.directories.length || files.length) {
    progress('Finishing SD writes');
    await card.sync();
  }
}
