import { getLocale, translate, type Locale } from "./i18n";
import { tool } from "ai";
import { z } from "zod";
import { Robot } from "./robot";
import { Cameras, type CameraFrame, type Role } from "./cameras";
import { JOINT_ANGLE_TOLERANCE_DEG, limits, poseSummary } from "./model";
import {
  createMotionSchemas,
  runMotion,
  type MotionInput,
} from "./actions";
import { GRIPPER_REFERENCE } from "./gripper";
import type { AISettings, Entry } from "./types";

// One image contract for observations and motion results. Keep pixels out of
// the DOM log, and leave the frame metadata in text for history compaction.
function splitFrames(value: unknown): { info: unknown; frames: CameraFrame[] } {
  if (!value || typeof value !== "object") return { info: value, frames: [] };
  if ("dataURL" in value && typeof value.dataURL === "string") {
    const { dataURL: _, ...info } = value;
    return { info, frames: [value as CameraFrame] };
  }
  if ("observations" in value && Array.isArray(value.observations)) {
    const frames = value.observations as CameraFrame[];
    return { info: { ...value, observations: frames.map(({ dataURL: _, ...info }) => info) }, frames };
  }
  return { info: value, frames: [] };
}
function toModelOutput({ output }: { output: unknown }) {
  const { info, frames } = splitFrames(output);
  if (!frames.length) return { type: "text" as const, value: JSON.stringify(info) };
  return {
    type: "content" as const,
    value: [
      { type: "text" as const, text: JSON.stringify(info) },
      ...frames.map((frame) => ({
        type: "file" as const,
        mediaType: frame.dataURL.slice(5, frame.dataURL.indexOf(";")),
        data: { type: "data" as const, data: frame.dataURL.split(",")[1] },
      })),
    ],
  };
}
export function robotSnapshot(robot: Robot, cameras: Cameras, locale: Locale = getLocale()) {
  const s = robot.state;
  return {
    connected: s.connected,
    feedback_time: s.sampledAt,
    actual: s.actual && poseSummary(s.actual),
    joint_limits_deg: limits,
    joint_angle_tolerance_deg: JOINT_ANGLE_TOLERANCE_DEG,
    gripper_deg: s.gripper_deg,
    gripper_reference: { ...GRIPPER_REFERENCE, note: translate(GRIPPER_REFERENCE.note, locale) },
    servo_deg: s.monitors.map((m) => m.angle),
    monitors: s.monitors,
    cameras: cameras.available(),
    camera_bindings: cameras.bindings,
    mapping: robot.mapping,
  };
}
export function createRobotTools({
  robot,
  cameras,
  settings,
  signal,
  locale = getLocale(),
  record,
  changed,
}: {
  robot: Robot;
  cameras: Cameras;
  settings: AISettings;
  signal: AbortSignal;
  locale?: Locale;
  record: (kind: Entry["kind"], text: string, detail?: unknown) => Entry;
  changed: () => void;
}) {
  const t = (text: string, ...values: unknown[]) => translate(text, locale, ...values);
  const { jointsSchema, motionSchemas, motionSchema } = createMotionSchemas(locale);
  let tail = Promise.resolve();
  const runTool = async <T>(
    name: string,
    input: unknown,
    action: () => Promise<T> | T,
    ordered = true,
  ) => {
    // SDK may dispatch a batch concurrently. Hardware/camera calls retain
    // model order; pure previews can calculate while a motion is pending.
    let release = () => {};
    if (ordered) {
      const previous = tail;
      tail = new Promise<void>((r) => {
        release = r;
      });
      await previous;
    }
    const entry = record("tool", t("{0} · 执行中", name), input);
    try {
      signal.throwIfAborted();
      const value = await action();
      entry.text =
        value &&
        typeof value === "object" &&
        "success" in value &&
        value.success === false
          ? t("{0} · 未完成", name)
          : t("{0} · 已完成", name);
      // Camera pixels stay in the conversation, not in the rendered tool log.
      const log = splitFrames(value).info;
      entry.detail = JSON.stringify({ input, output: log }, null, 2);
      changed();
      return value;
    } catch (error) {
      entry.text = `${name} · ${signal.aborted ? t("已停止") : t("失败")}`;
      const failure = {
        error: error instanceof Error ? error.message : String(error),
        actual: robotSnapshot(robot, cameras, locale),
      };
      entry.detail = JSON.stringify({ input, ...failure }, null, 2);
      changed();
      if (signal.aborted) throw error;
      return failure;
    } finally {
      release();
    }
  };
  const observationFields = {
    observe: z.boolean().nullish().describe(
      t("默认 true：动作完成后自动附带外部与腕部两张新图。已有充分信息、无需动作后画面时可设 false；序列仅在整组结束后附图。"),
    ),
    observe_exclusive: z.boolean().nullish().describe(
      t("USB 带宽不足时 true，轮流开启两路分别取图；false 保留双路。未填写时沿用当前采集方式：双路已开启则保留，否则轮流取图。"),
    ),
  };
  const perform = (input: MotionInput) =>
    runMotion(robot, settings, input, signal);
  async function capture(role: Role, exclusive = false) {
    await cameras.activate(role, exclusive);
    signal.throwIfAborted();
    return cameras.capture(role);
  }
  async function afterMotion<T extends object>(
    motion: Promise<T>,
    observe?: boolean | null,
    exclusive?: boolean | null,
  ) {
    const result = await motion;
    if (observe === false) return result;
    try {
      signal.throwIfAborted();
      return { ...result, ...await cameras.capturePair(signal, exclusive ?? undefined) };
    } catch (error) {
      signal.throwIfAborted();
      // Observation errors retain the completed motion; never replay it.
      return { ...result, observation_errors: { cameras: error instanceof Error ? error.message : String(error) } };
    }
  }
  async function sequence(steps: MotionInput[]) {
    const results: {
      step: number;
      action: string;
      result: Awaited<ReturnType<typeof perform>>;
    }[] = [];
    for (const [index, step] of steps.entries()) {
      try {
        const result = await perform(step);
        if ("success" in result && result.success === false)
          return {
            success: false,
            completed_steps: results.length,
            results,
            failed_step: index + 1,
            failed_result: result,
          };
        results.push({ step: index + 1, action: step.action, result });
      } catch (error) {
        signal.throwIfAborted();
        return {
          success: false,
          completed_steps: results.length,
          results,
          failed_step: index + 1,
          error: error instanceof Error ? error.message : String(error),
          actual: robotSnapshot(robot, cameras, locale),
        };
      }
    }
    return { success: true, completed_steps: results.length, results };
  }
  return {
    get_state: tool({
      description:
        t("读取最新实际舵机反馈、模型关节角及已开启相机。TCP（毫米）、工具 XYZ 轴方向和仰角由实际角度经 URDF 正解计算；仰角相对基座 XY 平面，正数朝上、负数朝下。姿态来自电机反馈，不是相机测量；不运动。"),
      inputSchema: z.object({}),
      execute: (input) =>
        runTool("get_state", input, async () => {
          if (robot.state.connected) await robot.refresh(signal);
          return robotSnapshot(robot, cameras, locale);
        }),
    }),
    observe_camera: tool({
      description:
        t("一次完成绑定相机开启/切换和取图，返回原分辨率图像与当前姿态。external 外部全景；wrist 腕部近景。exclusive 默认 false；USB 带宽不足时 true 关闭另一路并轮流取图。"),
      inputSchema: z.object({
        role: z.enum(["external", "wrist"]),
        exclusive: z.boolean().nullish(),
      }),
      execute: (input) =>
        runTool("observe_camera", input, async () => ({
          ...(await capture(input.role, input.exclusive ?? false)),
          robot: robotSnapshot(robot, cameras, locale),
        })),
      toModelOutput,
    }),
    preview_joints: tool({
      description:
        t("一次批量比较多组六关节候选，返回各组的 TCP、工具轴方向及仰角、目标角或错误。仅计算，不运动、不检查碰撞。页面显示最后一组有效预览。已确定目标时直接用 move_joints，移动工具会自动校验并更新预览。"),
      inputSchema: z.object({ poses_deg: z.array(jointsSchema).min(1) }),
      execute: (input) =>
        runTool(
          "preview_joints",
          input,
          () => ({
            previews: input.poses_deg.map((values) => {
              try {
                return { valid: true, ...poseSummary(robot.preview(values)) };
              } catch (error) {
                return {
                  valid: false,
                  joints_deg: values,
                  error: error instanceof Error ? error.message : String(error),
                };
              }
            }),
          }),
          false,
        ),
    }),
    move_joints: tool({
      description:
        t("自动校验并预览目标，然后移动到 6 关节绝对模型角，保持夹爪。等待指定时长后读取实际反馈并返回误差。默认随结果附外部与腕部新图，observe=false 可关闭；取图失败时只重试观察，不重做动作。"),
      inputSchema: motionSchemas.move_joints
        .omit({ action: true })
        .extend(observationFields),
      execute: (input) =>
        runTool("move_joints", input, () =>
          afterMotion(
            perform({ ...input, action: "move_joints" }),
            input.observe,
            input.observe_exclusive,
          ),
        ),
      toModelOutput,
    }),
    move_tcp: tool({
      description:
        t("以毫米调整基座坐标中的 TCP 位置。relative=true 为增量；false 为绝对坐标。当前逆运动学是简化的位置逆解，从当前关节角局部迭代，不锁定朝向、不检查碰撞。求解失败不代表全局不可达，可改用关节预览和移动调整构型后再试。默认随结果附外部与腕部新图，observe=false 可关闭。"),
      inputSchema: motionSchemas.move_tcp
        .omit({ action: true })
        .extend(observationFields),
      execute: (input) =>
        runTool("move_tcp", input, () =>
          afterMotion(
            perform({ ...input, action: "move_tcp" }),
            input.observe,
            input.observe_exclusive,
          ),
        ),
      toModelOutput,
    }),
    gripper: tool({
      description:
        t("设置夹爪 ID6 开口角与功率上限。0°闭合；30°约71mm、60°约129mm，参考测量深度不同，按画面选择开口；90°为机械行程上限。power_mw 单位mW，0使用舵机默认，不是力度百分比。返回实际角度与功率，默认附外部和腕部新图；observe=false 可关闭。"),
      inputSchema: motionSchemas.gripper
        .omit({ action: true })
        .extend(observationFields),
      execute: (input) =>
        runTool("gripper", input, () =>
          afterMotion(
            perform({ ...input, action: "gripper" }),
            input.observe,
            input.observe_exclusive,
          ),
        ),
      toModelOutput,
    }),
    work_pose: tool({
      description:
        t("统一的前往/返回工作位工具：[0,0,-60,-60,0,0]°（模型坐标，J4 原始舵机 +60°），夹爪默认闭合。六轴和夹爪通过同一条同步指令执行，返回实际反馈；默认随结果附外部与腕部新图，observe=false 可关闭。"),
      inputSchema: motionSchemas.work_pose
        .omit({ action: true })
        .extend(observationFields),
      execute: (input) =>
        runTool("work_pose", input, () =>
          afterMotion(
            perform({ ...input, action: "work_pose" }),
            input.observe,
            input.observe_exclusive,
          ),
        ),
      toModelOutput,
    }),
    run_sequence: tool({
      description:
        t("一次执行已确定、无需中途看图再决策的动作序列，例如确认位置后夹紧→抬升，或释放→撤离→回工作位。需要重新看图检查位置和姿态的接近动作与夹取闭合分开。按顺序执行同一套运动方法，失败时返回已完成步骤，不重放前面的动作；默认只在整组结束后附外部与腕部新图，observe=false 可关闭。"),
      inputSchema: z.object({
        steps: z.array(motionSchema).min(1),
        ...observationFields,
      }),
      execute: (input) =>
        runTool("run_sequence", input, () =>
          afterMotion(
            sequence(input.steps),
            input.observe,
            input.observe_exclusive,
          ),
        ),
      toModelOutput,
    }),
  };
}
