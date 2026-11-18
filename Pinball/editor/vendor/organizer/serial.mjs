export const ascii = text => new TextEncoder().encode(text);
export const string = bytes => new TextDecoder().decode(bytes).split('\0')[0];
export const view = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
export const equal = (a, b) => a === b || Boolean(a && b && a.length === b.length && a.every((n, i) => n === b[i]));

export function join(...parts) {
  const output = new Uint8Array(parts.reduce((size, bytes) => size + bytes.length, 0));
  let offset = 0;
  for (const bytes of parts) {
    output.set(bytes, offset);
    offset += bytes.length;
  }
  return output;
}

export function word(value) {
  const bytes = new Uint8Array(4);
  view(bytes).setUint32(0, value, true);
  return bytes;
}

export function crc16(bytes) {
  let crc = 0xffff;
  for (const byte of bytes) {
    crc ^= byte << 8;
    for (let bit = 0; bit < 8; bit++) crc = ((crc << 1) ^ (crc & 0x8000 ? 0x1021 : 0)) & 0xffff;
  }
  return crc;
}

export function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

export function frame(protocol, command, payload) {
  const bytes = join(ascii(protocol), Uint8Array.of(1, command, payload.length & 255, payload.length >> 8), payload, new Uint8Array(2));
  view(bytes).setUint16(bytes.length - 2, crc16(bytes.subarray(2, -2)), true);
  return bytes;
}

export class Frames {
  #buffer = new Uint8Array();
  feed(chunk, emit) {
    this.#buffer = join(this.#buffer, chunk);
    while (this.#buffer.length >= 6) {
      const bytes = this.#buffer;
      const length = view(bytes).getUint16(4, true);
      if (bytes[0] !== 67 || ![71, 83].includes(bytes[1]) || bytes[2] !== 1 || length > 512) {
        this.#buffer = bytes.subarray(1);
        continue;
      }
      const end = length + 8;
      if (bytes.length < end) return;
      if (view(bytes).getUint16(end - 2, true) === crc16(bytes.subarray(2, end - 2))) {
        emit(String.fromCharCode(bytes[0], bytes[1]), bytes[3], bytes.subarray(6, end - 2));
        this.#buffer = bytes.subarray(end);
      } else {
        this.#buffer = bytes.subarray(1);
      }
    }
  }
}

const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const chooser = {filters: [{usbVendorId: 0x16c0, usbProductId: 0x27dd}]};
const isCHGame = port => {
  const id = port.getInfo();
  return id.usbVendorId === 0x16c0 && id.usbProductId === 0x27dd && port.connected !== false;
};

export async function grantedCHGame(serial, previous) {
  const ports = (await serial.getPorts()).filter(isCHGame);
  return ports.includes(previous) ? previous : ports.length === 1 ? ports[0] : null;
}

export class Link {
  static async open(port) {
    await port.open({baudRate: 115200});
    try {
      await port.setSignals({dataTerminalReady: true});
      return new Link(port);
    } catch (error) {
      await port.close().catch(() => {});
      throw error;
    }
  }

  constructor(port) {
    this.port = port;
    this.reader = port.readable.getReader();
    this.writer = port.writable.getWriter();
    this.parser = new Frames();
    this.id = (Date.now() >>> 0) >>> 1;
    this.pump = this.read();
  }

  async read() {
    try {
      while (true) {
        const {value, done} = await this.reader.read();
        if (done) break;
        this.parser.feed(value, (protocol, command, payload) => {
          const pending = this.pending;
          if (!pending || protocol !== pending.protocol || command !== (pending.command | 128)) return;
          if (protocol === 'CS' && (payload.length < 5 || view(payload).getUint32(0, true) !== pending.id)) return;
          pending.resolve(payload);
        });
      }
    } catch (error) {
      this.pending?.reject(error);
    } finally {
      this.disconnected = true;
      this.pending?.reject(new Error('CHGame disconnected'));
      this.reader.releaseLock();
    }
  }

  async request(protocol, command, data = new Uint8Array(), timeout = 1800) {
    if (this.pending || this.disconnected) throw new Error('The serial connection is unavailable');
    const id = ++this.id;
    const bytes = frame(protocol, command, protocol === 'CS' ? join(word(id), data) : data);
    for (let attempt = 0; attempt < (protocol === 'CS' ? 2 : 1); attempt++) {
      let timer;
      try {
        const answer = new Promise((resolve, reject) => {
          this.pending = {protocol, command, id, resolve, reject};
          timer = setTimeout(() => reject(new Error('CHGame response timed out')), timeout);
        });
        const [, payload] = await Promise.all([this.writer.write(bytes), answer]);
        return payload;
      } catch (error) {
        if (attempt || protocol === 'CG' || this.disconnected) throw error;
      } finally {
        clearTimeout(timer);
        this.pending = null;
      }
    }
  }

  close() {
    this.closing ??= this.shutdown();
    return this.closing;
  }

  async shutdown() {
    await this.reader.cancel().catch(() => {});
    await this.pump;
    this.writer.releaseLock();
    await this.port.close().catch(() => {});
  }
}

export class CardError extends Error {
  constructor(status) {
    const messages = {
      1: 'SD card I/O error', 4: 'File missing', 5: 'Folder missing', 7: 'Card is full or the file is read-only',
      10: 'SD card is write-protected', 13: 'A FAT16 or FAT32 card is required', 32: 'Helper rejected the request',
      33: 'Helper is busy', 34: 'SD verification failed', 35: 'SD journal needs recovery', 36: 'Transfer cancelled on the console'
    };
    super(messages[status] ?? `Helper error ${status}`);
    this.status = status;
  }
}

const path = name => ascii(name + '\0');

export class SerialCard {
  static async identify(link) {
    try {
      const card = new SerialCard(link);
      return string(await card.call(16, undefined, 450)) === 'SDtoSerial/1' ? card : null;
    } catch (error) {
      if (link.disconnected) throw error;
      return null;
    }
  }

  constructor(link) {
    this.link = link;
  }

  async call(command, data, timeout) {
    const bytes = await this.link.request('CS', command, data, timeout);
    if (bytes[4]) throw new CardError(bytes[4]);
    return bytes.subarray(5);
  }

  async start() {
    const hello = await this.call(1, undefined, 12000);
    if (hello.length !== 14 || hello[0] !== 1 || view(hello).getUint16(10, true) !== 512) {
      throw new Error('Unsupported SD helper');
    }
    const caps = await this.call(13);
    if (caps.length < 4 || caps[0] !== 1 || !(caps[1] & 1)) throw new Error('The SD helper needs bounded reads');
    this.maxRead = Math.min(480, view(caps).getUint16(2, true));
    this.timestamps = Boolean(caps[1] & 16);
    if (!this.maxRead) throw new Error('The SD helper reported an invalid read size');
  }

  async list(folder) {
    const entries = [];
    const header = this.timestamps ? 9 : 5;
    for (let index = 0; index <= 4095; index++) {
      const bytes = await this.call(this.timestamps ? 17 : 3, join(word(index), path(folder)));
      if (!bytes.length) return entries;
      if (bytes.length <= header) throw new Error('Invalid SD directory response');
      const fields = view(bytes);
      const timestamp = this.timestamps ? fields.getUint32(5, true) : 0;
      const legacyTimestamp = ((2025 - 1980) << 25) | (1 << 21) | (1 << 16);
      entries.push({
        name: string(bytes.subarray(header)), directory: bytes[4] === 1,
        size: fields.getUint32(0, true), modified: timestamp === legacyTimestamp ? 0 : timestamp,
      });
    }
    throw new Error('This category has too many files to scan over USB');
  }

  async read(name, offset, length, progress) {
    const bytes = new Uint8Array(length);
    for (let position = 0; position < length;) {
      const count = Math.min(length - position, this.maxRead);
      const answer = await this.call(12, join(word(offset + position), Uint8Array.of(count & 255, count >> 8), path(name)));
      const data = answer.subarray(9);
      if (data.length !== count || view(answer).getUint32(0, true) !== offset + position ||
          view(answer).getUint32(4, true) !== crc32(data)) throw new Error(`Read verification failed for ${name}`);
      bytes.set(data, position);
      position += count;
      progress?.(position);
    }
    return bytes;
  }

  async replace(name, bytes, progress) {
    await this.setClock();
    try {
      await this.call(5, join(word(bytes.length), word(crc32(bytes)), path(name)), 15000);
      for (let offset = 0; offset < bytes.length; offset += 504) {
        const chunk = bytes.subarray(offset, offset + 504);
        await this.call(6, join(word(offset), chunk));
        progress?.(offset + chunk.length, 'Writing to SD');
      }
      progress?.(bytes.length, 'Committing to SD');
      await this.call(7, undefined, 30000);
    } catch (error) {
      await this.call(8).catch(() => {});
      throw error;
    }
    progress?.(bytes.length, 'Verifying readback');
    if (!equal(await this.read(name, 0, bytes.length,
      progress && (done => progress(bytes.length + done, 'Verifying readback'))), bytes)) {
      throw new Error(`Readback differs for ${name}`);
    }
  }

  async check(name, size) {
    let offset = 0;
    let crc = 0xffffffff;
    while (offset < size) {
      const bytes = await this.call(11, join(word(offset), word(crc), path(name)), 12000);
      if (bytes.length !== 9) throw new Error(`Invalid checksum response for ${name}`);
      const next = view(bytes).getUint32(0, true);
      if (next <= offset || next > size || Boolean(bytes[8]) !== (next === size)) {
        throw new Error(`Checksum verification failed for ${name}`);
      }
      offset = next;
      crc = view(bytes).getUint32(4, true);
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  remove(name) { return this.call(14, path(name)); }
  async setClock() {
    if (!this.timestamps) return;
    const now = new Date();
    const year = Math.max(1980, Math.min(now.getFullYear(), 2107));
    const timestamp = ((year - 1980) << 25) | ((now.getMonth() + 1) << 21) | (now.getDate() << 16) |
      (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
    if (timestamp === this.clock) return;
    await this.call(18, word(timestamp));
    this.clock = timestamp;
  }

  async mkdir(name) {
    await this.setClock();
    return this.call(4, path(name));
  }
  sync() { return this.call(9); }
  menu() { return this.call(10); }
}

async function bootCall(link, command, data, timeout) {
  const answer = await link.request('CG', command, data, timeout);
  if (!answer.length || answer[0]) throw new Error(`Bootloader command ${command} failed (${answer[0] ?? 'no status'})`);
  return answer;
}

async function reconnect(serial, original, probe, duration) {
  const until = performance.now() + duration;
  while (performance.now() < until) {
    const port = await grantedCHGame(serial, original);
    if (port) {
      let link;
      try {
        link = await Link.open(port);
        const value = await probe(link);
        if (value) return [link, value];
      } catch {
        // The port may be between USB disconnect and re-enumeration.
      }
      await link?.close();
    }
    await pause(150);
  }
  throw new Error('CHGame did not reconnect in the expected USB mode. Select it again once it appears.');
}

export async function chooseCHGame(serial) {
  const port = await serial.requestPort(chooser);
  return Link.open(port);
}

export function installHelper(serial, current, source, progress) {
  return flashApplication(serial, current, source, progress, {helper: true});
}

export async function flashApplication(serial, current, source, progress, {helper = false} = {}) {
  const {port} = current;
  const image = new Uint8Array(Math.ceil(source.length / 4) * 4).fill(255);
  image.set(source);
  if (image.length < 16 || image.length > (helper ? 50432 : 50944) || string(image.subarray(8, 12)) === 'CHBL') {
    throw new Error('Invalid Rev0 application image');
  }
  const permitted = (await serial.getPorts()).filter(isCHGame);
  if (permitted.some(other => other !== port)) {
    throw new Error('Disconnect other CHGame consoles before uploading the application');
  }

  const hello = link => bootCall(link, 1, undefined, 450);
  let link = current;
  let info;
  try {
    info = await hello(link);
  } catch {
    await link.close();
    await port.open({baudRate: 1200});
    try {
      await port.setSignals({dataTerminalReady: true});
      await port.setSignals({dataTerminalReady: false});
    } finally {
      await port.close().catch(() => {});
    }
    await pause(400);
    [link, info] = await reconnect(serial, port, hello, 10000);
  }

  let began = false;
  try {
    const fields = view(info);
    if (info.length < 30 || info[1] !== 1 || info[2] !== 1 || fields.getUint16(4, true) < 3 ||
        fields.getUint32(6, true) !== 0x3000 || fields.getUint32(10, true) < image.length ||
        (info.length >= 34 && string(info.subarray(30, 34)) !== 'CX35')) {
      throw new Error('Application upload requires a Rev0 CHGame with menu bootloader version 3 or newer');
    }
    const page = fields.getUint16(14, true);
    if (page !== 256 || fields.getUint16(16, true) < page + 4) throw new Error('Unexpected CHGame flash geometry');
    began = true;
    await bootCall(link, 2, join(word(image.length), word(crc32(image))), 10000);
    for (let offset = 0; offset < image.length; offset += page) {
      const chunk = image.subarray(offset, offset + page);
      await bootCall(link, 3, join(word(offset), chunk), 2500);
      progress(offset + chunk.length, image.length);
    }
    await bootCall(link, 4, undefined, 10000);
    began = false;
    await bootCall(link, 5);
  } catch (error) {
    if (began) await bootCall(link, 7).catch(() => {});
    throw error;
  } finally {
    await link.close();
  }
  await pause(350);
  if (!helper) return port;
  const [, card] = await reconnect(serial, port, SerialCard.identify, 7000);
  try {
    await card.start();
    return card;
  } catch (error) {
    await card.link.close();
    throw error;
  }
}
