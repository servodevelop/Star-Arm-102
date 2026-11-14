"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  Agent,
  checkAI,
  DEFAULT_AI,
  models,
  type AISettings,
  type Session,
} from "@/lib/agent";
import { Cameras, type Binding, type Role } from "@/lib/cameras";
import {
  DEFAULT_MAPPING,
  inverse,
  limits,
  WORK_POSE,
  type Mapping,
} from "@/lib/model";
import { Robot, type RobotState } from "@/lib/robot";
import { load, save } from "@/lib/storage";
import { emptySession } from "@/lib/types";

const blankBinding = (): Binding => ({
  deviceId: "",
  label: "",
  width: 1920,
  height: 1080,
  fps: 30,
});
type Config = {
  ai: AISettings;
  apiKey?: string;
  cameras: Record<Role, Binding>;
  mapping: Mapping;
  baudRate: number;
};
const defaults: Config = {
  ai: DEFAULT_AI,
  apiKey: "",
  cameras: { external: blankBinding(), wrist: blankBinding() },
  mapping: DEFAULT_MAPPING,
  baudRate: 1000000,
};
const initial: RobotState = {
  connected: false,
  busy: false,
  sampledAt: null,
  actual: null,
  gripper_deg: null,
  monitors: [],
  preview: null,
  error: null,
};
const titles: Record<Role, string> = {
  external: "外部相机",
  wrist: "腕部相机",
};
const message = (error: unknown) =>
  error instanceof Error ? error.message : String(error);
const reportError = (text: string) =>
  toast.error(text, { id: "operation-error", duration: 10000 });

function ArmPreview({ state }: { state: RobotState }) {
  const [view, setView] = useState("space");
  const point = (p: number[]) => {
    if (view === "top") return [210 + p[0] * 470, 210 - p[1] * 470];
    if (view === "side") return [210 + p[0] * 470, 290 - p[2] * 470];
    return [210 + (p[0] - p[1]) * 360, 290 - p[2] * 470 + (p[0] + p[1]) * 140];
  };
  const render = (points: number[][], preview: boolean) => (
    <g opacity={preview ? 0.65 : 1}>
      <polyline
        points={points.map((p) => point(p).join(",")).join(" ")}
        fill="none"
        stroke={preview ? "#ffc880" : "#61d7cc"}
        strokeWidth={preview ? 7 : 10}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={preview ? "7 6" : undefined}
      />
      {points.map((p, i) => (
        <circle
          key={i}
          cx={point(p)[0]}
          cy={point(p)[1]}
          r={i === points.length - 1 ? 7 : 5}
          fill={preview ? "#ffc880" : "#d2f1ec"}
        />
      ))}
    </g>
  );
  return (
    <div className="pose-view">
      <div className="preview-tools">
        <span>
          <i className="dot" />
          实际回读 <i className="dot amber" />
          目标预览
        </span>
        <select
          aria-label="姿态预览视角"
          value={view}
          onChange={(e) => setView(e.target.value)}
        >
          <option value="space">空间</option>
          <option value="side">侧视</option>
          <option value="top">俯视</option>
        </select>
      </div>
      <svg
        viewBox="0 0 420 340"
        role="img"
        aria-label="实际机械臂与目标的运动学预览"
      >
        <defs>
          <pattern
            id="grid"
            width="28"
            height="28"
            patternUnits="userSpaceOnUse"
          >
            <path d="M28 0H0V28" fill="none" stroke="#253237" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="420" height="340" fill="url(#grid)" />
        {[
          [0.18, 0, 0],
          [0, 0.18, 0],
          [0, 0, 0.18],
        ].map((p, i) => (
          <g key={i}>
            <line
              x1={point([0, 0, 0])[0]}
              y1={point([0, 0, 0])[1]}
              x2={point(p)[0]}
              y2={point(p)[1]}
              stroke={["#f98d8d", "#89ca8e", "#79aef4"][i]}
            />
            <text
              x={point(p)[0]}
              y={point(p)[1] - 7}
              fill={["#f98d8d", "#89ca8e", "#79aef4"][i]}
            >
              {"XYZ"[i]}
            </text>
          </g>
        ))}
        {state.preview && render(state.preview.points, true)}
        {state.actual && render(state.actual.points, false)}
        {!state.actual && (
          <text x="210" y="120" textAnchor="middle" fill="#92a3a8">
            连接从臂后显示实际姿态
          </text>
        )}
      </svg>
    </div>
  );
}

export default function Page() {
  const [ready, setReady] = useState(false);
  const [secure, setSecure] = useState(true);
  const [serialSupported, setSerialSupported] = useState(true);
  const [config, setConfig] = useState<Config>(defaults);
  const [saved, setSaved] = useState("");
  const key = config.apiKey ?? "";
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [cameraStatus, setCameraStatus] = useState<Record<Role, string>>({
    external: "未开启",
    wrist: "未开启",
  });
  const [cameraBusy, setCameraBusy] = useState<Partial<Record<Role, boolean>>>(
    {},
  );
  const [state, setState] = useState(initial);
  const [session, setSession] = useState<Session>(emptySession);
  const [running, setRunning] = useState(false);
  const [devicesOpen, setDevicesOpen] = useState(true);
  const [pending, setPending] = useState("");
  const [text, setText] = useState("");
  const [catalog, setCatalog] = useState<string[]>([]);
  const [draft, setDraft] = useState([...WORK_POSE]);
  const [gripper, setGripper] = useState(0);
  const [target, setTarget] = useState([0, 0, 0]);
  const [relative, setRelative] = useState(true);
  const robot = useRef<Robot | null>(null);
  const cameras = useRef<Cameras | null>(null);
  const agent = useRef<Agent | null>(null);
  const modelRequest = useRef<AbortController | null>(null);
  const sessionSave = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  const flowList = useRef<HTMLDivElement>(null);
  const followFlow = useRef(true);
  const appendDialog = useRef<HTMLDialogElement>(null);
  const initDone = useRef(false);

  useEffect(() => {
    setSecure(window.isSecureContext);
    setSerialSupported("serial" in navigator);
    if (!window.isSecureContext)
      reportError("请使用 HTTPS 或 localhost 连接相机与机械臂。");
    else if (!("serial" in navigator))
      reportError("当前浏览器不支持串口连接，请使用 Chrome 或 Edge。");
    let mounted = true;
    let previousError: string | null = null;
    const r = new Robot((v) => {
      if (mounted) {
        setState(v);
        if (v.error && v.error !== previousError) reportError(v.error);
        previousError = v.error;
      }
    });
    const c = new Cameras((role, status) => {
      if (mounted) setCameraStatus((v) => ({ ...v, [role]: status }));
    });
    const a = new Agent(r, c, (s, active) => {
      if (!mounted) return;
      setSession(s);
      setRunning(active);
      // Throttle writes so a continuous reply still persists periodically.
      if (active && sessionSave.current !== undefined) return;
      clearTimeout(sessionSave.current);
      sessionSave.current = setTimeout(
        () => {
          sessionSave.current = undefined;
          void save("session", a.session).catch((e) => {
            if (mounted) reportError(`会话保存失败：${message(e)}`);
          });
        },
        active ? 500 : 0,
      );
    });
    robot.current = r;
    cameras.current = c;
    agent.current = a;
    void (async () => {
      try {
        const existing = await load<Config>("config");
        if (!mounted) return;
        const cfg = existing ?? defaults;
        setConfig(cfg);
        setSaved(JSON.stringify(cfg));
        r.setMapping(cfg.mapping);
        const history = await load<Session>("session");
        if (history && mounted) a.restore(history);
        const listed = await navigator.mediaDevices?.enumerateDevices();
        if (mounted)
          setDevices(listed?.filter((d) => d.kind === "videoinput") ?? []);
      } catch (e) {
        if (mounted) reportError(`本地数据读取失败：${message(e)}`);
      } finally {
        if (mounted) {
          initDone.current = true;
          setReady(true);
        }
      }
    })();
    const changed = () => {
      void navigator.mediaDevices.enumerateDevices()
        .then((v) => {
          if (mounted) setDevices(v.filter((d) => d.kind === "videoinput"));
        })
        .catch((e) => {
          if (mounted) reportError(`相机列表读取失败：${message(e)}`);
        });
    };
    navigator.mediaDevices?.addEventListener("devicechange", changed);
    return () => {
      mounted = false;
      a.cancel();
      modelRequest.current?.abort();
      c.stopAll();
      void r.disconnect();
      navigator.mediaDevices?.removeEventListener("devicechange", changed);
      clearTimeout(sessionSave.current);
    };
  }, []);

  useEffect(() => {
    if (initDone.current) robot.current?.setMapping(config.mapping);
  }, [config.mapping]);
  useEffect(() => {
    if (cameras.current) cameras.current.bindings = config.cameras;
  }, [config.cameras]);
  useEffect(() => {
    const flow = flowList.current;
    if (!flow) followFlow.current = true;
    else if (followFlow.current) flow.scrollTo({ top: flow.scrollHeight });
  }, [session.entries]);
  const videoRef = useCallback(
    (role: Role, node: HTMLVideoElement | null) =>
      cameras.current?.attach(role, node),
    [],
  );

  async function action(name: string, fn: () => Promise<unknown> | unknown) {
    toast.dismiss("operation-error");
    setPending(name);
    try {
      await fn();
    } catch (e) {
      if (e instanceof Error && e.name === "AbortError") toast.info("请求已停止");
      else reportError(message(e));
    } finally {
      setPending("");
    }
  }
  function editAI<K extends keyof AISettings>(name: K, value: AISettings[K]) {
    setConfig((v) => ({ ...v, ai: { ...v.ai, [name]: value } }));
  }
  function binding(role: Role, value: Partial<Binding>) {
    cameras.current?.stop(role);
    setConfig((v) => ({
      ...v,
      cameras: { ...v.cameras, [role]: { ...v.cameras[role], ...value } },
    }));
  }
  async function refreshCameras() {
    if (!navigator.mediaDevices)
      throw Error("相机需要 HTTPS 或 localhost 安全上下文");
    let listed = await navigator.mediaDevices.enumerateDevices();
    if (!listed.some((d) => d.kind === "videoinput" && d.label)) {
      const permission = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false,
      });
      permission.getTracks().forEach((t) => t.stop());
      listed = await navigator.mediaDevices.enumerateDevices();
    }
    setDevices(listed.filter((d) => d.kind === "videoinput"));
  }
  async function startCamera(role: Role) {
    setCameraBusy((v) => ({ ...v, [role]: true }));
    try {
      await cameras.current!.start(role, config.cameras[role]);
    } finally {
      setCameraBusy((v) => ({ ...v, [role]: false }));
    }
  }
  async function saveConfig() {
    const snapshot = structuredClone(config);
    await save("config", snapshot);
    setSaved(JSON.stringify(snapshot));
    toast.success("配置已保存");
  }
  async function send() {
    const input = text.trim();
    if (!input) return;
    setText("");
    toast.dismiss("operation-error");
    try {
      await agent.current!.run(input, structuredClone(config.ai), key);
    } catch (e) {
      reportError(message(e));
      setText(input);
    }
  }
  function requestSend() {
    if (!ready || !text.trim()) return;
    if (hasConversation) appendDialog.current?.showModal();
    else void send();
  }
  const disabled = !ready || Boolean(pending) || running || state.busy;
  const dirty = JSON.stringify(config) !== saved;
  const entries = session.entries;
  const hasConversation = entries.length > 0 || session.messages.length > 0;
  const orderedEntries = entries
    .map((entry, order) => ({ entry, order }))
    .sort((a, b) => a.entry.at - b.entry.at || a.order - b.order);

  return (
    <main>
      <header className="topbar">
        <div>
          <span className="eyebrow">vla-arms-agent</span>
          <h1>
            看见，判断，行动<span className="accent">。</span>
          </h1>
          <p>连接相机与机械臂，用自然语言完成任务。</p>
        </div>
        <div className="top-actions">
          <span className={`badge ${state.connected ? "on" : ""}`}>
            <i className="dot" />
            {state.connected ? "从臂已连接" : "从臂未连接"}
          </span>
          <button
            className="stop"
            disabled={!ready}
            onClick={() => void action("stop", () => {
              modelRequest.current?.abort();
              return agent.current!.stop();
            })}
          >
            停止 AI 与运动
          </button>
        </div>
      </header>

      <section className="section-heading">
        <span>01</span>
        <div>
          <h2>
            <button
              className="section-toggle"
              aria-expanded={devicesOpen}
              aria-controls="device-panel"
              onClick={() => setDevicesOpen((open) => !open)}
            >
              连接与观察
              <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
                <path d="m5 8 5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.5" />
              </svg>
            </button>
          </h2>
          <p>连接机械臂，绑定外部与腕部相机。</p>
        </div>
        <button
          className={dirty ? "primary" : undefined}
          disabled={!ready || Boolean(pending)}
          onClick={() => void action("save", saveConfig)}
        >
          {dirty ? "保存配置" : "配置已保存"}
        </button>
      </section>
      <div id="device-panel" hidden={!devicesOpen}>
        <div className="device-grid">
          <section className="card arm-card">
            <div className="card-title">
              <h3>从臂连接</h3>
            </div>
            <div className="fields two">
              <label>
                串口波特率
                <input
                  type="number"
                  aria-label="串口波特率"
                  value={config.baudRate}
                  disabled={state.connected}
                  onChange={(e) =>
                    setConfig((v) => ({ ...v, baudRate: +e.target.value }))
                  }
                />
              </label>
              <label>
                默认动作时长 / ms
                <input
                  type="number"
                  aria-label="默认动作时长"
                  value={config.ai.durationMs}
                  onChange={(e) => editAI("durationMs", +e.target.value)}
                />
              </label>
            </div>
            <div className="actions">
              <button
                className="primary"
                disabled={
                  !ready ||
                  Boolean(pending) ||
                  running ||
                  !serialSupported ||
                  !secure
                }
                onClick={() =>
                  void action("serial", () =>
                    state.connected
                      ? robot.current!.disconnect()
                      : robot.current!.connect(config.baudRate),
                  )
                }
              >
                {pending === "serial"
                  ? "正在连接…"
                  : state.connected
                    ? "断开从臂"
                    : "选择串口并连接"}
              </button>
              <button
                disabled={disabled || !state.connected}
                aria-busy={pending === "refresh"}
                onClick={() =>
                  void action("refresh", () => robot.current!.refresh())
                }
              >
                {pending === "refresh" ? "回读中…" : "回读姿态"}
              </button>
            </div>
            <p className="caption">
              连接后读取当前姿态。
            </p>
            <dl className="stats">
              <div>
                <dt>执行状态</dt>
                <dd>
                  {state.busy
                    ? "执行中"
                    : pending === "refresh"
                      ? "回读中"
                      : state.connected
                        ? "就绪"
                        : "未连接"}
                </dd>
              </div>
              <div>
                <dt>夹爪实际开口角</dt>
                <dd>
                  {state.gripper_deg == null
                    ? "—"
                    : `${state.gripper_deg.toFixed(1)}°`}
                </dd>
              </div>
              <div>
                <dt>夹爪功率回读</dt>
                <dd>
                  {state.monitors[6] ? `${state.monitors[6].power} mW` : "—"}
                </dd>
              </div>
            </dl>
            <details>
              <summary>关节映射与零点</summary>
              <p className="caption">
                方向与零点用于校准关节角度，修改后会更新姿态与预览。
              </p>
              <div className="mapping-grid">
                <span>关节</span>
                <span>方向</span>
                <span>零点 / °</span>
                {config.mapping.directions.map((v, i) => (
                  <div className="mapping-row" key={i}>
                    <span>J{i + 1}</span>
                    <select
                      aria-label={`J${i + 1} 方向`}
                      value={v}
                      disabled={running || state.busy}
                      onChange={(e) =>
                        setConfig((c) => ({
                          ...c,
                          mapping: {
                            ...c.mapping,
                            directions: c.mapping.directions.map((d, n) =>
                              n === i ? +e.target.value : d,
                            ),
                          },
                        }))
                      }
                    >
                      <option value={1}>同向</option>
                      <option value={-1}>反向</option>
                    </select>
                    <input
                      aria-label={`J${i + 1} 零点`}
                      type="number"
                      value={config.mapping.offsets[i]}
                      disabled={running || state.busy}
                      onChange={(e) =>
                        setConfig((c) => ({
                          ...c,
                          mapping: {
                            ...c.mapping,
                            offsets: c.mapping.offsets.map((d, n) =>
                              n === i ? +e.target.value : d,
                            ),
                          },
                        }))
                      }
                    />
                  </div>
                ))}
              </div>
            </details>
          </section>
          {(["external", "wrist"] as Role[]).map((role) => (
            <section className="card camera-card" key={role}>
              <div className="card-title">
                <h3>{titles[role]}</h3>
                <span className="muted camera-status">{cameraStatus[role]}</span>
              </div>
              <div className="camera-video">
                <video
                  ref={(node) => videoRef(role, node)}
                  autoPlay
                  muted
                  playsInline
                  aria-label={`${titles[role]}实时画面`}
                />
                <span>
                  {cameraStatus[role] === "未开启" ? "选择设备并开启预览" : ""}
                </span>
              </div>
              <label>
                绑定设备
                <select
                  aria-label={`${titles[role]}设备`}
                  value={config.cameras[role].deviceId}
                  onChange={(e) =>
                    binding(role, {
                      deviceId: e.target.value,
                      label:
                        devices.find((d) => d.deviceId === e.target.value)
                          ?.label ?? "",
                    })
                  }
                >
                  <option value="">未绑定</option>
                  {config.cameras[role].deviceId &&
                    !devices.some(
                      (d) => d.deviceId === config.cameras[role].deviceId,
                    ) && (
                      <option value={config.cameras[role].deviceId} disabled>
                        {config.cameras[role].label || "已绑定设备"}（当前不可用）
                      </option>
                    )}
                  {devices.map((d, i) => (
                    <option key={d.deviceId || i} value={d.deviceId}>
                      {d.label || `摄像头 ${i + 1}`}
                    </option>
                  ))}
                </select>
              </label>
              <div className="fields two">
                <label>
                  采集分辨率
                  <select
                    aria-label={`${titles[role]}分辨率`}
                    value={`${config.cameras[role].width}x${config.cameras[role].height}`}
                    onChange={(e) => {
                      const [width, height] = e.target.value
                        .split("x")
                        .map(Number);
                      binding(role, { width, height });
                    }}
                  >
                    <option value="1920x1080">1920 × 1080</option>
                    <option value="1280x720">1280 × 720</option>
                  </select>
                </label>
                <label>
                  期望帧率
                  <select
                    aria-label={`${titles[role]}帧率`}
                    value={config.cameras[role].fps}
                    onChange={(e) => binding(role, { fps: +e.target.value })}
                  >
                    <option value={30}>30 FPS</option>
                    <option value={60}>60 FPS</option>
                  </select>
                </label>
              </div>
              <div className="actions">
                <button
                  disabled={
                    !ready ||
                    !secure ||
                    cameraBusy[role] ||
                    !config.cameras[role].deviceId
                  }
                  onClick={() =>
                    void action(`camera-${role}`, () => startCamera(role))
                  }
                >
                  {cameraBusy[role] ? "开启中…" : "开启预览"}
                </button>
                <button
                  disabled={!ready}
                  onClick={() => {
                    cameras.current!.stop(role);
                    setCameraStatus((v) => ({ ...v, [role]: "未开启" }));
                  }}
                >
                  关闭
                </button>
              </div>
            </section>
          ))}
        </div>
        <div className="section-foot">
          <button
            disabled={!ready || Boolean(pending)}
            onClick={() => void action("cameras", refreshCameras)}
          >
            授权并刷新摄像头
          </button>
          <p>
            画面卡顿时，可关闭暂不使用的一路相机。
          </p>
        </div>
      </div>

      <section className="section-heading">
        <span>02</span>
        <div>
          <h2>AI 与任务</h2>
          <p>保留上下文，运行中可继续发送提醒和补充。</p>
        </div>
        <span className={`badge ${running ? "on" : ""}`}>
          {running ? "正在处理" : "等待任务"}
        </span>
      </section>
      <div className="work-grid">
        <section className="card ai-card">
          <details className="settings">
            <summary>模型与动作配置</summary>
            <div className="fields">
              <label>
                OpenAI 兼容 API 地址
                <input
                  aria-label="AI API 地址"
                  value={config.ai.baseURL}
                  onChange={(e) => editAI("baseURL", e.target.value)}
                  placeholder="http://127.0.0.1:8317/v1"
                />
              </label>
              <label>
                API Key
                <input
                  type="password"
                  autoComplete="off"
                  aria-label="AI API Key"
                  value={key}
                  onChange={(e) =>
                    setConfig((value) => ({ ...value, apiKey: e.target.value }))
                  }
                  placeholder="保存 AI 配置后将自动记住"
                />
              </label>
              <div className="fields two">
                <label>
                  模型
                  <input
                    aria-label="AI 模型"
                    list="models"
                    value={config.ai.model}
                    onChange={(e) => editAI("model", e.target.value)}
                  />
                  <datalist id="models">
                    {catalog.map((v) => (
                      <option key={v} value={v} />
                    ))}
                  </datalist>
                </label>
                <label>
                  思考强度
                  <input
                    aria-label="AI 思考强度"
                    list="efforts"
                    value={config.ai.effort}
                    placeholder="模型默认"
                    onChange={(e) => editAI("effort", e.target.value)}
                  />
                  <datalist id="efforts">
                    {["none", "low", "medium", "high", "xhigh", "max"].map(
                      (v) => (
                        <option key={v} value={v} />
                      ),
                    )}
                  </datalist>
                </label>
              </div>
              <label>
                原生上下文压缩阈值 / token
                <input type="number" min="0" aria-label="原生上下文压缩阈值"
                  value={config.ai.compactTokens ?? DEFAULT_AI.compactTokens}
                  onChange={(e) => editAI("compactTokens", +e.target.value)} />
                <span className="caption">达到后由模型原生压缩，0 关闭；思考强度保持不变。</span>
              </label>
              <label>
                夹爪默认功率上限 / mW
                <input
                  type="number"
                  aria-label="夹爪功率上限"
                  value={config.ai.gripperPowerMw}
                  onChange={(e) => editAI("gripperPowerMw", +e.target.value)}
                />
              </label>
            </div>
            <p className="caption">
              模型需支持看图和工具调用。配置修改从下次任务生效。夹爪功率填 0 使用默认值。
            </p>
            {session.usage && <p className="caption" aria-label="AI 请求性能">
              最近模型响应 {session.usage.responseMs == null ? "未回报" : `${(session.usage.responseMs / 1000).toFixed(1)} 秒`}
              {" · "}输入 {session.usage.inputTokens ?? "未回报"} token
              {" · "}缓存命中 {session.usage.inputTokens && session.usage.cachedTokens != null
                ? `${(100 * session.usage.cachedTokens / session.usage.inputTokens).toFixed(1)}%` : "未回报"}
            </p>}
            <div className="actions">
              <button
                className={dirty ? "primary" : undefined}
                disabled={!ready || Boolean(pending) || !dirty}
                onClick={() => void action("save", saveConfig)}
              >
                保存 AI 配置
              </button>
              <button
                disabled={!ready || Boolean(pending) || running}
                onClick={() =>
                  void action("models", async () => {
                    const request = new AbortController();
                    modelRequest.current = request;
                    setCatalog(await models(config.ai, key, request.signal));
                    toast.success("模型列表已更新");
                  })
                }
              >
                刷新模型列表
              </button>
              <button
                disabled={!ready || Boolean(pending) || running}
                onClick={() =>
                  void action("check", async () => {
                    const request = new AbortController();
                    modelRequest.current = request;
                    const role = cameras.current!.available()[0];
                    toast.info(
                      await checkAI(
                        config.ai,
                        key,
                        role ? cameras.current!.capture(role) : undefined,
                        request.signal,
                      ),
                    );
                  })
                }
              >
                {pending === "check" ? "正在验证…" : "验证连接与能力"}
              </button>
            </div>
          </details>
          <div className="composer">
            {!entries.length && (
              <div className="task-intro">
                <h3>用一句话定义任务</h3>
                <p>例如：观察两路画面，把紫色海绵放到中心标记，然后回到工作位。</p>
              </div>
            )}
            <label htmlFor="task">{hasConversation ? "追加对话" : "AI 任务"}</label>
            <p className="caption" id="task-hint">
              {hasConversation
                ? "新任务建议先开启新会话。"
                : "开启外部相机预览后，任务会附带其当前画面。"}
            </p>
            <textarea
              id="task"
              aria-label="AI 任务"
              aria-describedby="task-hint"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={3}
              placeholder="描述目标；仅观察时请说明。Ctrl / ⌘ + Enter 发送。"
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                  e.preventDefault();
                  requestSend();
                }
              }}
            />
            <div className="actions">
              <button
                className="primary"
                disabled={!ready || !text.trim()}
                onClick={requestSend}
              >
                {hasConversation ? "追加对话" : "开始会话"}
              </button>
              <button
                disabled={!ready || running}
                onClick={() => agent.current!.reset()}
              >
                新会话
              </button>
            </div>
          </div>
          {entries.length > 0 && (
            <div
              className="conversation"
              ref={flowList}
              aria-label="AI 流程"
              aria-live="polite"
              onScroll={(e) => {
                const flow = e.currentTarget;
                followFlow.current =
                  Math.ceil(flow.scrollTop + flow.clientHeight) >= flow.scrollHeight;
              }}
            >
              {orderedEntries.map(({ entry: e, order }) =>
                e.kind === "tool" ? (
                  <details className="tool-entry" data-entry-order={order} key={e.id}>
                    <summary><span className="step-title" title={e.text}>{e.text}</span></summary>
                    <pre>{e.detail}</pre>
                  </details>
                ) : (
                  <div className={`entry ${e.kind}`} data-entry-order={order} key={e.id}>
                    <div className="entry-label">
                      {e.kind === "user"
                        ? "你"
                        : e.kind === "assistant"
                          ? "AI"
                          : "状态"}
                      <time>
                        {new Date(e.at).toLocaleTimeString("zh-CN", {
                          hour12: false,
                        })}
                      </time>
                    </div>
                    <div className="entry-text">{e.text}</div>
                  </div>
                ),
              )}
            </div>
          )}
        </section>
        <section className="card control-card">
          <div className="card-title">
            <h3>姿态与手动控制</h3>
          </div>
          <ArmPreview state={state} />
          <div className="joint-readings">
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i}>
                <span>J{i + 1}</span>
                <strong>
                  {state.actual
                    ? `${state.actual.joints_deg[i].toFixed(1)}°`
                    : "—"}
                </strong>
              </div>
            ))}
          </div>
          <div className="tcp-line">
            <span>实际 TCP / mm</span>
            <strong>
              {state.actual
                ? state.actual.tcp_mm.map((v) => v.toFixed(1)).join(" / ")
                : "—"}
            </strong>
          </div>
          <details>
            <summary>关节目标与夹爪</summary>
            <div className="joint-inputs">
              {draft.map((v, i) => (
                <label key={i}>
                  J{i + 1} / °
                  <input
                    type="number"
                    step="1"
                    aria-label={`J${i + 1} 目标角度`}
                    value={v}
                    onChange={(e) =>
                      setDraft((values) =>
                        values.map((d, n) => (n === i ? +e.target.value : d)),
                      )
                    }
                  />
                  <span className="caption">
                    {limits[i].map((v) => v.toFixed(0)).join(" ～ ")}°
                  </span>
                </label>
              ))}
            </div>
            <div className="actions">
              <button
                disabled={disabled}
                onClick={() =>
                  void action("preview", () => robot.current!.preview(draft))
                }
              >
                预览目标
              </button>
              <button
                disabled={disabled || !state.actual}
                onClick={() => setDraft([...state.actual!.joints_deg])}
              >
                使用实际角度
              </button>
              <button
                className="primary"
                disabled={disabled || !state.connected}
                onClick={() =>
                  void action("move", () =>
                    robot.current!.move(draft, config.ai.durationMs),
                  )
                }
              >
                执行关节目标
              </button>
              <button
                disabled={disabled || !state.connected}
                onClick={() =>
                  void action("work", () =>
                    robot.current!.workPose(
                      config.ai.durationMs,
                      config.ai.gripperPowerMw,
                    ),
                  )
                }
              >
                回工作位
              </button>
            </div>
            <div className="gripper-input">
              <label>
                夹爪开口角 / °
                <input
                  type="number"
                  aria-label="夹爪目标开口角"
                  value={gripper}
                  onChange={(e) => setGripper(+e.target.value)}
                />
              </label>
              <button
                disabled={disabled || !state.connected}
                onClick={() =>
                  void action("gripper", () =>
                    robot.current!.gripper(
                      gripper,
                      config.ai.durationMs,
                      config.ai.gripperPowerMw,
                    ),
                  )
                }
              >
                执行夹爪
              </button>
            </div>
            <p className="caption">
              工作位会闭合夹爪。开口参考：30°约 71 mm，60°约 129 mm（测量深度不同）。
            </p>
          </details>
          <details>
            <summary>TCP 位置逆解</summary>
            <p className="caption">
              输入目标位置，先预览，再执行。未找到解时，可先调整关节角度。
            </p>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={relative}
                onChange={(e) => setRelative(e.target.checked)}
              />
              相对当前 TCP 的增量
            </label>
            <div className="fields three">
              {target.map((v, i) => (
                <label key={i}>
                  {"XYZ"[i]} / mm
                  <input
                    type="number"
                    aria-label={`TCP ${"XYZ"[i]}`}
                    value={v}
                    onChange={(e) =>
                      setTarget((a) =>
                        a.map((d, n) => (n === i ? +e.target.value : d)),
                      )
                    }
                  />
                </label>
              ))}
            </div>
            <button
              disabled={disabled || !state.actual}
              onClick={() =>
                void action("ik", () => {
                  const actual = state.actual!;
                  const position = target.map(
                    (v, i) => v + (relative ? actual.tcp_mm[i] : 0),
                  );
                  const solved = inverse(position, actual.joints_deg);
                  if (!solved.joints_deg)
                    throw Error(
                      `IK 未找到解：${solved.reason}，位置误差 ${solved.error_mm?.toFixed(2)} mm`,
                    );
                  setDraft(solved.joints_deg);
                  robot.current!.preview(solved.joints_deg);
                  toast.success(
                    `位置逆解已预览，误差 ${solved.error_mm?.toFixed(3)} mm；在关节控制中点击执行`,
                  );
                })
              }
            >
              求解并预览
            </button>
          </details>
          <details>
            <summary>实际舵机反馈</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>原始角度</th>
                    <th>电压</th>
                    <th>电流</th>
                    <th>功率</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {state.monitors.map((m) => (
                    <tr key={m.id}>
                      <td>{m.id}</td>
                      <td>{m.angle.toFixed(1)}°</td>
                      <td>{m.voltage} mV</td>
                      <td>{m.current} mA</td>
                      <td>{m.power} mW</td>
                      <td>{m.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>
      </div>
      <dialog
        className="confirm-dialog"
        ref={appendDialog}
        aria-labelledby="append-title"
        aria-describedby="append-description"
      >
        <h2 id="append-title">追加到当前会话？</h2>
        <p id="append-description">会继续使用当前聊天记录。新任务建议先开启新会话。</p>
        <div className="dialog-message">{text.trim()}</div>
        <div className="actions dialog-actions">
          <button onClick={() => appendDialog.current?.close()}>取消</button>
          <button
            className="primary"
            onClick={() => {
              appendDialog.current?.close();
              void send();
            }}
          >
            确认追加
          </button>
        </div>
      </dialog>
    </main>
  );
}
