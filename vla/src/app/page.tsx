"use client";

import { t, setLocale, type Locale } from "../lib/i18n";
import { useLocale } from "./locale";
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
          {t("实际回读")}
          <i className="dot amber" />
          {t("目标预览")}
        </span>
        <select
          aria-label={t("姿态预览视角")}
          value={view}
          onChange={(e) => setView(e.target.value)}
        >
          <option value="space">{t("空间")}</option>
          <option value="side">{t("侧视")}</option>
          <option value="top">{t("俯视")}</option>
        </select>
      </div>
      <svg
        viewBox="0 0 420 340"
        role="img"
        aria-label={t("实际机械臂与目标的运动学预览")}
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
            {t("连接从臂后显示实际姿态")}
          </text>
        )}
      </svg>
    </div>
  );
}

export default function Page() {
  const locale = useLocale();
  const [ready, setReady] = useState(false);
  const [secure, setSecure] = useState(true);
  const [serialSupported, setSerialSupported] = useState(true);
  const [config, setConfig] = useState<Config>(defaults);
  const [saved, setSaved] = useState("");
  const key = config.apiKey ?? "";
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [cameraStatus, setCameraStatus] = useState<Record<Role, string>>({
    external: t("未开启"),
    wrist: t("未开启"),
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
      reportError(t("请使用 HTTPS 或 localhost 连接相机与机械臂。"));
    else if (!("serial" in navigator))
      reportError(t("当前浏览器不支持串口连接，请使用 Chrome 或 Edge。"));
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
            if (mounted) reportError(t("会话保存失败：{0}", message(e)));
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
        if (mounted) reportError(t("本地数据读取失败：{0}", message(e)));
      } finally {
        if (mounted) {
          initDone.current = true;
          setReady(true);
        }
      }
    })();
    const changed = () => {
      void navigator.mediaDevices
        .enumerateDevices()
        .then((v) => {
          if (mounted) setDevices(v.filter((d) => d.kind === "videoinput"));
        })
        .catch((e) => {
          if (mounted) reportError(t("相机列表读取失败：{0}", message(e)));
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
      if (e instanceof Error && e.name === "AbortError")
        toast.info(t("请求已停止"));
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
      throw Error(t("相机需要 HTTPS 或 localhost 安全上下文"));
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
    toast.success(t("配置已保存"));
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
            {t("看见，判断，行动")}
            <span className="accent">{locale === "zh" ? "。" : "."}</span>
          </h1>
          <p>{t("连接相机与机械臂，用自然语言完成任务。")}</p>
        </div>
        <div className="top-actions">
          <select
            className="language-select"
            aria-label="Language / 语言"
            value={locale}
            onChange={(e) => setLocale(e.target.value as Locale)}
          >
            <option value="en">English</option>
            <option value="zh">简体中文</option>
          </select>
          <span className={`badge ${state.connected ? "on" : ""}`}>
            <i className="dot" />
            {state.connected ? t("从臂已连接") : t("从臂未连接")}
          </span>
          <button
            className="stop"
            disabled={!ready}
            onClick={() =>
              void action("stop", () => {
                modelRequest.current?.abort();
                return agent.current!.stop();
              })
            }
          >
            {t("停止 AI 与运动")}
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
              {t("连接与观察")}
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  d="m5 8 5 5 5-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
              </svg>
            </button>
          </h2>
          <p>{t("连接机械臂，绑定外部与腕部相机。")}</p>
        </div>
        <button
          className={dirty ? "primary" : undefined}
          disabled={!ready || Boolean(pending)}
          onClick={() => void action("save", saveConfig)}
        >
          {dirty ? t("保存配置") : t("配置已保存")}
        </button>
      </section>
      <div id="device-panel" hidden={!devicesOpen}>
        <div className="device-grid">
          <section className="card arm-card">
            <div className="card-title">
              <h3>{t("从臂连接")}</h3>
            </div>
            <div className="fields two">
              <label>
                {t("串口波特率")}
                <input
                  type="number"
                  aria-label={t("串口波特率")}
                  value={config.baudRate}
                  disabled={state.connected}
                  onChange={(e) =>
                    setConfig((v) => ({ ...v, baudRate: +e.target.value }))
                  }
                />
              </label>
              <label>
                {t("默认动作时长 / ms")}
                <input
                  type="number"
                  aria-label={t("默认动作时长")}
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
                  ? t("正在连接…")
                  : state.connected
                    ? t("断开从臂")
                    : t("选择串口并连接")}
              </button>
              <button
                disabled={disabled || !state.connected}
                aria-busy={pending === "refresh"}
                onClick={() =>
                  void action("refresh", () => robot.current!.refresh())
                }
              >
                {pending === "refresh" ? t("回读中…") : t("回读姿态")}
              </button>
            </div>
            <p className="caption">{t("连接后读取当前姿态。")}</p>
            <dl className="stats">
              <div>
                <dt>{t("执行状态")}</dt>
                <dd>
                  {state.busy
                    ? t("执行中")
                    : pending === "refresh"
                      ? t("回读中")
                      : state.connected
                        ? t("就绪")
                        : t("未连接")}
                </dd>
              </div>
              <div>
                <dt>{t("夹爪实际开口角")}</dt>
                <dd>
                  {state.gripper_deg == null
                    ? "—"
                    : `${state.gripper_deg.toFixed(1)}°`}
                </dd>
              </div>
              <div>
                <dt>{t("夹爪功率回读")}</dt>
                <dd>
                  {state.monitors[6] ? `${state.monitors[6].power} mW` : "—"}
                </dd>
              </div>
            </dl>
            <details>
              <summary>{t("关节映射与零点")}</summary>
              <p className="caption">
                {t("方向与零点用于校准关节角度，修改后会更新姿态与预览。")}
              </p>
              <div className="mapping-grid">
                <span>{t("关节")}</span>
                <span>{t("方向")}</span>
                <span>{t("零点 / °")}</span>
                {config.mapping.directions.map((v, i) => (
                  <div className="mapping-row" key={i}>
                    <span>J{i + 1}</span>
                    <select
                      aria-label={t("J{0} 方向", i + 1)}
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
                      <option value={1}>{t("同向")}</option>
                      <option value={-1}>{t("反向")}</option>
                    </select>
                    <input
                      aria-label={t("J{0} 零点", i + 1)}
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
                <h3>{t(titles[role])}</h3>
                <span className="muted camera-status">
                  {t(cameraStatus[role])}
                </span>
              </div>
              <div className="camera-video">
                <video
                  ref={(node) => videoRef(role, node)}
                  autoPlay
                  muted
                  playsInline
                  aria-label={t("{0}实时画面", titles[role])}
                />
                <span>
                  {!cameras.current?.available().includes(role)
                    ? t("选择设备并开启预览")
                    : ""}
                </span>
              </div>
              <label>
                {t("绑定设备")}
                <select
                  aria-label={t("{0}设备", titles[role])}
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
                  <option value="">{t("未绑定")}</option>
                  {config.cameras[role].deviceId &&
                    !devices.some(
                      (d) => d.deviceId === config.cameras[role].deviceId,
                    ) && (
                      <option value={config.cameras[role].deviceId} disabled>
                        {config.cameras[role].label || t("已绑定设备")}
                        {t("（当前不可用）")}
                      </option>
                    )}
                  {devices.map((d, i) => (
                    <option key={d.deviceId || i} value={d.deviceId}>
                      {d.label || t("摄像头 {0}", i + 1)}
                    </option>
                  ))}
                </select>
              </label>
              <div className="fields two">
                <label>
                  {t("采集分辨率")}
                  <select
                    aria-label={t("{0}分辨率", titles[role])}
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
                  {t("期望帧率")}
                  <select
                    aria-label={t("{0}帧率", titles[role])}
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
                  {cameraBusy[role] ? t("开启中…") : t("开启预览")}
                </button>
                <button
                  disabled={!ready}
                  onClick={() => {
                    cameras.current!.stop(role);
                    setCameraStatus((v) => ({ ...v, [role]: t("未开启") }));
                  }}
                >
                  {t("关闭")}
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
            {t("授权并刷新摄像头")}
          </button>
          <p>{t("画面卡顿时，可关闭暂不使用的一路相机。")}</p>
        </div>
      </div>

      <section className="section-heading">
        <span>02</span>
        <div>
          <h2>{t("AI 与任务")}</h2>
          <p>{t("保留上下文，运行中可继续发送提醒和补充。")}</p>
        </div>
        <span className={`badge ${running ? "on" : ""}`}>
          {running ? t("正在处理") : t("等待任务")}
        </span>
      </section>
      <div className="work-grid">
        <section className="card ai-card">
          <details className="settings">
            <summary>{t("模型与动作配置")}</summary>
            <div className="fields">
              <label>
                {t("OpenAI 兼容 API 地址")}
                <input
                  aria-label={t("AI API 地址")}
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
                  placeholder={t("保存 AI 配置后将自动记住")}
                />
              </label>
              <div className="fields two">
                <label>
                  {t("模型")}
                  <input
                    aria-label={t("AI 模型")}
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
                  {t("思考强度")}
                  <input
                    aria-label={t("AI 思考强度")}
                    list="efforts"
                    value={config.ai.effort}
                    placeholder={t("模型默认")}
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
                {t("原生上下文压缩阈值 / token")}
                <input
                  type="number"
                  min="0"
                  aria-label={t("原生上下文压缩阈值")}
                  value={config.ai.compactTokens ?? DEFAULT_AI.compactTokens}
                  onChange={(e) => editAI("compactTokens", +e.target.value)}
                />
                <span className="caption">
                  {t("达到后由模型原生压缩，0 关闭；思考强度保持不变。")}
                </span>
              </label>
              <label>
                {t("夹爪默认功率上限 / mW")}
                <input
                  type="number"
                  aria-label={t("夹爪功率上限")}
                  value={config.ai.gripperPowerMw}
                  onChange={(e) => editAI("gripperPowerMw", +e.target.value)}
                />
              </label>
            </div>
            <p className="caption">
              {t(
                "模型需支持看图和工具调用。配置修改从下次任务生效。夹爪功率填 0 使用默认值。",
              )}
            </p>
            {session.usage && (
              <p className="caption" aria-label={t("AI 请求性能")}>
                {t("最近模型响应")}
                {session.usage.responseMs == null
                  ? t("未回报")
                  : t("{0} 秒", (session.usage.responseMs / 1000).toFixed(1))}
                {" · "}
                {t("输入")}
                {session.usage.inputTokens ?? t("未回报")} token
                {" · "}
                {t("缓存命中")}
                {session.usage.inputTokens && session.usage.cachedTokens != null
                  ? `${((100 * session.usage.cachedTokens) / session.usage.inputTokens).toFixed(1)}%`
                  : t("未回报")}
              </p>
            )}
            <div className="actions">
              <button
                className={dirty ? "primary" : undefined}
                disabled={!ready || Boolean(pending) || !dirty}
                onClick={() => void action("save", saveConfig)}
              >
                {t("保存 AI 配置")}
              </button>
              <button
                disabled={!ready || Boolean(pending) || running}
                onClick={() =>
                  void action("models", async () => {
                    const request = new AbortController();
                    modelRequest.current = request;
                    setCatalog(await models(config.ai, key, request.signal));
                    toast.success(t("模型列表已更新"));
                  })
                }
              >
                {t("刷新模型列表")}
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
                {pending === "check" ? t("正在验证…") : t("验证连接与能力")}
              </button>
            </div>
          </details>
          <div className="composer">
            {!entries.length && (
              <div className="task-intro">
                <h3>{t("用一句话定义任务")}</h3>
                <p>
                  {t(
                    "例如：观察两路画面，把紫色海绵放到中心标记，然后回到工作位。",
                  )}
                </p>
              </div>
            )}
            <label htmlFor="task">
              {hasConversation ? t("追加对话") : t("AI 任务")}
            </label>
            <p className="caption" id="task-hint">
              {hasConversation
                ? t("新任务建议先开启新会话。")
                : t("开启外部相机预览后，任务会附带其当前画面。")}
            </p>
            <textarea
              id="task"
              aria-label={t("AI 任务")}
              aria-describedby="task-hint"
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={3}
              placeholder={t(
                "描述目标；仅观察时请说明。Ctrl / ⌘ + Enter 发送。",
              )}
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
                {hasConversation ? t("追加对话") : t("开始会话")}
              </button>
              <button
                disabled={!ready || running}
                onClick={() => agent.current!.reset()}
              >
                {t("新会话")}
              </button>
            </div>
          </div>
          {entries.length > 0 && (
            <div
              className="conversation"
              ref={flowList}
              aria-label={t("AI 流程")}
              aria-live="polite"
              onScroll={(e) => {
                const flow = e.currentTarget;
                followFlow.current =
                  Math.ceil(flow.scrollTop + flow.clientHeight) >=
                  flow.scrollHeight;
              }}
            >
              {orderedEntries.map(({ entry: e, order }) =>
                e.kind === "tool" ? (
                  <details
                    className="tool-entry"
                    data-entry-order={order}
                    key={e.id}
                  >
                    <summary>
                      <span className="step-title" title={t(e.text)}>
                        {t(e.text)}
                      </span>
                    </summary>
                    <pre>{e.detail}</pre>
                  </details>
                ) : (
                  <div
                    className={`entry ${e.kind}`}
                    data-entry-order={order}
                    key={e.id}
                  >
                    <div className="entry-label">
                      {e.kind === "user"
                        ? t("你")
                        : e.kind === "assistant"
                          ? "AI"
                          : t("状态")}
                      <time>
                        {new Date(e.at).toLocaleTimeString(
                          locale === "zh" ? "zh-CN" : "en",
                          {
                            hour12: false,
                          },
                        )}
                      </time>
                    </div>
                    <div className="entry-text">
                      {e.kind === "status" ? t(e.text) : e.text}
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </section>
        <section className="card control-card">
          <div className="card-title">
            <h3>{t("姿态与手动控制")}</h3>
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
            <span>{t("实际 TCP / mm")}</span>
            <strong>
              {state.actual
                ? state.actual.tcp_mm.map((v) => v.toFixed(1)).join(" / ")
                : "—"}
            </strong>
          </div>
          <details>
            <summary>{t("关节目标与夹爪")}</summary>
            <div className="joint-inputs">
              {draft.map((v, i) => (
                <label key={i}>
                  J{i + 1} / °
                  <input
                    type="number"
                    step="1"
                    aria-label={t("J{0} 目标角度", i + 1)}
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
                {t("预览目标")}
              </button>
              <button
                disabled={disabled || !state.actual}
                onClick={() => setDraft([...state.actual!.joints_deg])}
              >
                {t("使用实际角度")}
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
                {t("执行关节目标")}
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
                {t("回工作位")}
              </button>
            </div>
            <div className="gripper-input">
              <label>
                {t("夹爪开口角 / °")}
                <input
                  type="number"
                  aria-label={t("夹爪目标开口角")}
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
                {t("执行夹爪")}
              </button>
            </div>
            <p className="caption">
              {t(
                "工作位会闭合夹爪。开口参考：30°约 71 mm，60°约 129 mm（测量深度不同）。",
              )}
            </p>
          </details>
          <details>
            <summary>{t("TCP 位置逆解")}</summary>
            <p className="caption">
              {t(
                "输入目标位置，先预览，再执行。未找到解时，可先调整关节角度。",
              )}
            </p>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={relative}
                onChange={(e) => setRelative(e.target.checked)}
              />
              {t("相对当前 TCP 的增量")}
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
                      t(
                        "IK 未找到解：{0}，位置误差 {1} mm",
                        solved.reason,
                        solved.error_mm?.toFixed(2),
                      ),
                    );
                  setDraft(solved.joints_deg);
                  robot.current!.preview(solved.joints_deg);
                  toast.success(
                    t(
                      "位置逆解已预览，误差 {0} mm；在关节控制中点击执行",
                      solved.error_mm?.toFixed(3),
                    ),
                  );
                })
              }
            >
              {t("求解并预览")}
            </button>
          </details>
          <details>
            <summary>{t("实际舵机反馈")}</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>{t("原始角度")}</th>
                    <th>{t("电压")}</th>
                    <th>{t("电流")}</th>
                    <th>{t("功率")}</th>
                    <th>{t("状态")}</th>
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
        <h2 id="append-title">{t("追加到当前会话？")}</h2>
        <p id="append-description">
          {t("会继续使用当前聊天记录。新任务建议先开启新会话。")}
        </p>
        <div className="dialog-message">{text.trim()}</div>
        <div className="actions dialog-actions">
          <button onClick={() => appendDialog.current?.close()}>
            {t("取消")}
          </button>
          <button
            className="primary"
            onClick={() => {
              appendDialog.current?.close();
              void send();
            }}
          >
            {t("确认追加")}
          </button>
        </div>
      </dialog>
    </main>
  );
}
