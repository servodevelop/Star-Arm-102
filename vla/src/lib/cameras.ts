export type Role = "external" | "wrist";
export type Binding = {
  deviceId: string;
  label: string;
  width: number;
  height: number;
  fps: number;
};
export type CameraFrame = {
  role: Role;
  captured_at: string;
  width: number;
  height: number;
  dataURL: string;
};
// Real UVC startup inspection showed a dark first frame. Let subsequent
// frames arrive before publishing the stream as ready; running streams reuse it.
export const CAMERA_STARTUP_MS = 500;
export class Cameras {
  private ready = new Set<Role>();
  private streams = new Map<Role, MediaStream>();
  private videos = new Map<Role, HTMLVideoElement>();
  private generations = new Map<Role, number>();
  bindings: Partial<Record<Role, Binding>> = {};
  constructor(
    private changed: (role: Role, status: string) => void = () => {},
  ) {}
  attach(role: Role, video: HTMLVideoElement | null) {
    if (video) {
      this.videos.set(role, video);
      const stream = this.streams.get(role) ?? null;
      if (video.srcObject !== stream) video.srcObject = stream;
    } else this.videos.delete(role);
  }
  async start(role: Role, binding: Binding) {
    this.stop(role);
    const generation = this.generations.get(role);
    if (!binding.deviceId) throw Error("请先选择摄像头");
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        deviceId: { exact: binding.deviceId },
        width: { ideal: binding.width },
        height: { ideal: binding.height },
        frameRate: { ideal: binding.fps },
      },
      audio: false,
    });
    if (generation !== this.generations.get(role)) {
      stream.getTracks().forEach((t) => t.stop());
      return;
    }
    this.streams.set(role, stream);
    const track = stream.getVideoTracks()[0];
    track.addEventListener("ended", () => {
      if (generation === this.generations.get(role)) {
        this.stop(role);
        this.changed(role, "信号已断开");
      }
    });
    const video = this.videos.get(role);
    try {
      if (video) {
        video.srcObject = stream;
        await video.play();
        if (generation !== this.generations.get(role)) return;
        await new Promise<void>((resolve) => setTimeout(resolve, CAMERA_STARTUP_MS));
      }
    } catch (error) {
      if (generation !== this.generations.get(role)) return;
      this.stop(role);
      throw error;
    }
    if (generation !== this.generations.get(role)) return;
    this.ready.add(role);
    const settings = track.getSettings();
    this.changed(
      role,
      `${settings.width} × ${settings.height} · ${Math.round(settings.frameRate ?? 0)} FPS`,
    );
    return settings;
  }
  stop(role: Role) {
    this.ready.delete(role);
    this.generations.set(role, (this.generations.get(role) ?? 0) + 1);
    this.streams
      .get(role)
      ?.getTracks()
      .forEach((t) => t.stop());
    this.streams.delete(role);
    const video = this.videos.get(role);
    if (video) video.srcObject = null;
    this.changed(role, "未开启");
  }
  async activate(role: Role, exclusive: boolean) {
    const active = this.available().includes(role);
    const binding = this.bindings[role];
    if (!active && !binding?.deviceId) throw Error("此角色没有相机绑定");
    if (exclusive)
      for (const other of ["external", "wrist"] as Role[])
        if (other !== role) this.stop(other);
    if (active)
      return this.streams.get(role)!.getVideoTracks()[0].getSettings();
    return this.start(role, binding!);
  }
  stopAll() {
    this.stop("external");
    this.stop("wrist");
  }
  available() {
    return [...this.streams]
      .filter(([role, s]) =>
        this.ready.has(role) && s.getVideoTracks().some((t) => t.readyState === "live"),
      )
      .map(([role]) => role);
  }
  async capturePair(signal: AbortSignal, exclusive = this.available().length < 2) {
    const started = performance.now();
    const observations: CameraFrame[] = [];
    const observation_errors: Partial<Record<Role, string>> = {};
    // With one-camera capture, finish on the external view so the next task
    // can reuse it. Two already-running cameras keep their streams open.
    const roles: Role[] = exclusive ? ["wrist", "external"] : ["external", "wrist"];
    for (const role of roles) {
      signal.throwIfAborted();
      try {
        if (!this.available().includes(role) && !this.bindings[role]?.deviceId)
          throw Error("尚未绑定摄像头");
        await this.activate(role, exclusive);
        signal.throwIfAborted();
        observations.push(this.capture(role));
      } catch (error) {
        signal.throwIfAborted();
        observation_errors[role] = error instanceof Error ? error.message : String(error);
      }
    }
    return {
      observations,
      observation_ms: Math.round(performance.now() - started),
      ...(Object.keys(observation_errors).length ? { observation_errors } : {}),
    };
  }
  capture(role: Role): CameraFrame {
    const video = this.videos.get(role);
    if (
      !this.available().includes(role) ||
      !video?.videoWidth ||
      video.readyState < 2
    )
      throw Error(`${role === "wrist" ? "腕部" : "外部"}摄像头没有有效画面`);
    const stream = this.streams.get(role)!;
    const deviceId = stream.getVideoTracks()[0].getSettings().deviceId;
    if (video.srcObject !== stream ||
      (deviceId && this.bindings[role]?.deviceId && deviceId !== this.bindings[role]!.deviceId))
      throw Error(`${role} 摄像头画面来源与当前绑定不一致`);
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) throw Error("浏览器无法创建取图画布");
    context.drawImage(video, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    let hasSignal = false;
    for (let i = 0; i < pixels.length; i += 4)
      if (pixels[i] || pixels[i + 1] || pixels[i + 2]) { hasSignal = true; break; }
    if (!hasSignal) throw Error(`${role} 摄像头当前为全黑图，请检查画面或照明`);
    return {
      role,
      captured_at: new Date().toISOString(),
      width: canvas.width,
      height: canvas.height,
      dataURL: canvas.toDataURL("image/webp", 0.9),
    };
  }
}
