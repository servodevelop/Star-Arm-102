// Typed FL transport adapted from star-arm-studio 71114a0 serial_servo_bus.js
// and servo_readback.js. One reader, one monitor request per bus owner.
import {
  PacketParser,
  parseMonitor,
  ServoProtocol,
  type Monitor,
} from "./protocol";
export interface SerialPortLike {
  readable: ReadableStream<Uint8Array> | null;
  writable: WritableStream<Uint8Array> | null;
  open(options: {
    baudRate: number;
    dataBits: number;
    stopBits: number;
    parity: string;
    flowControl: string;
  }): Promise<void>;
  close(): Promise<void>;
}
type SerialAPI = EventTarget & { requestPort(): Promise<SerialPortLike> };
type Waiter = {
  resolve: (monitor: Monitor | null) => void;
  timer: ReturnType<typeof setTimeout>;
};
export class SerialServoBus {
  private port: SerialPortLike | null = null;
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private writer: WritableStreamDefaultWriter<Uint8Array> | null = null;
  private waiters = new Map<number, Waiter>();
  private lost = false;
  private opened = false;
  private epoch = 0;
  private parser = new PacketParser();
  private onLost: (error: Error) => void;
  private serial?: SerialAPI;
  constructor(
    private name: string,
    options: { onLost?: (error: Error) => void; serial?: SerialAPI } = {},
  ) {
    this.onLost = options.onLost ?? (() => {});
    this.serial =
      options.serial ??
      (globalThis.navigator as Navigator & { serial?: SerialAPI })?.serial;
  }
  get connected() {
    return Boolean(this.port && this.writer && !this.lost);
  }
  async connect(
    port: SerialPortLike | null = null,
    { baudRate = 1000000 } = {},
  ) {
    // A lost stream can still own its Web Serial locks. Release that old
    // connection before opening again; otherwise the UI cannot reconnect.
    if (this.lost) await this.disconnect();
    if (this.port) throw Error("串口已经打开");
    if (!port && !this.serial)
      throw Error(
        "Web Serial 不可用，请使用 HTTPS / localhost 下的 Chrome 或 Edge",
      );
    this.port = port ?? (await this.serial!.requestPort());
    this.lost = false;
    try {
      await this.port.open({
        baudRate,
        dataBits: 8,
        stopBits: 1,
        parity: "none",
        flowControl: "none",
      });
      this.opened = true;
      this.reader = this.port.readable!.getReader();
      this.writer = this.port.writable!.getWriter();
      this.parser = new PacketParser();
      void this.readLoop(this.reader, ++this.epoch);
    } catch (error) {
      await this.disconnect().catch(() => {});
      throw error;
    }
  }
  private fail(error: Error) {
    if (this.lost || !this.port) return;
    this.lost = true;
    this.flush();
    this.onLost(error);
  }
  private async readLoop(
    reader: ReadableStreamDefaultReader<Uint8Array>,
    epoch: number,
  ) {
    try {
      while (epoch === this.epoch) {
        const { done, value } = await reader.read();
        if (epoch !== this.epoch) return;
        if (done) throw Error(`${this.name} 串口已断开`);
        if (!value) continue;
        for (const packet of this.parser.push(value)) {
          const monitor = parseMonitor(packet);
          if (!monitor) continue;
          const waiter = this.waiters.get(monitor.id);
          if (waiter) {
            clearTimeout(waiter.timer);
            this.waiters.delete(monitor.id);
            waiter.resolve(monitor);
          }
        }
      }
    } catch (e) {
      if (epoch === this.epoch)
        this.fail(e instanceof Error ? e : Error(String(e)));
    }
  }
  async write(frame: Uint8Array) {
    if (!this.writer || this.lost) throw Error("从臂串口未连接");
    try {
      await this.writer.write(frame);
    } catch (e) {
      this.fail(e instanceof Error ? e : Error(String(e)));
      throw e;
    }
  }
  private flush() {
    for (const waiter of this.waiters.values()) {
      clearTimeout(waiter.timer);
      waiter.resolve(null);
    }
    this.waiters.clear();
  }
  async feedback(ids: number[], signal?: AbortSignal) {
    const found: Record<number, Monitor> = {};
    for (let attempt = 0; attempt < 3; attempt++) {
      signal?.throwIfAborted();
      const missing = ids.filter((id) => !found[id]);
      if (!missing.length) break;
      this.flush();
      this.parser.buffer = [];
      const replies = missing.map(
        (id) =>
          new Promise<Monitor | null>((resolve) => {
            const timer = setTimeout(() => {
              this.waiters.delete(id);
              resolve(null);
            }, 800);
            this.waiters.set(id, { resolve, timer });
          }),
      );
      const abort = () => this.flush();
      signal?.addEventListener("abort", abort, { once: true });
      try {
        await this.write(ServoProtocol.syncServoMonitor(missing));
        for (const m of await Promise.all(replies)) if (m) found[m.id] = m;
        signal?.throwIfAborted();
      } finally {
        signal?.removeEventListener("abort", abort);
        this.flush();
      }
    }
    return { monitors: found, missingIds: ids.filter((id) => !found[id]) };
  }
  async disconnect() {
    ++this.epoch;
    this.flush();
    const reader = this.reader,
      writer = this.writer,
      port = this.port,
      opened = this.opened;
    this.reader = null;
    this.writer = null;
    this.port = null;
    this.opened = false;
    if (reader) {
      try {
        await reader.cancel();
      } catch {
      } finally {
        reader.releaseLock();
      }
    }
    writer?.releaseLock();
    if (port && opened) await port.close();
    this.lost = false;
  }
}
