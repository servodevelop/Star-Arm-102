import { z } from "zod";
import { inverse } from "./model";
import type { Robot } from "./robot";
import type { AISettings } from "./types";

export const jointsSchema = z
  .array(z.number())
  .length(6)
  .describe("J1～J6 绝对模型角，单位度，不是原始舵机角");
const duration = z
  .number()
  .int()
  .positive()
  .nullish()
  .describe("运动时长毫秒，留空使用用户配置");
export const motionSchemas = {
  move_joints: z.object({
    action: z.literal("move_joints"),
    joints_deg: jointsSchema,
    duration_ms: duration,
  }),
  move_tcp: z.object({
    action: z.literal("move_tcp"),
    position_mm: z
      .array(z.number())
      .length(3)
      .describe("基座坐标系中的 XYZ，单位毫米"),
    relative: z
      .boolean()
      .describe("true 为相对当前 TCP 的增量，false 为绝对位置"),
    duration_ms: duration,
  }),
  gripper: z.object({
    action: z.literal("gripper"),
    angle_deg: z.number().min(0).max(90),
    power_mw: z.number().int().min(0).max(65535).nullish(),
    duration_ms: duration,
  }),
  work_pose: z.object({
    action: z.literal("work_pose"),
    duration_ms: duration,
  }),
};
export const motionSchema = z.discriminatedUnion("action", [
  motionSchemas.move_joints,
  motionSchemas.move_tcp,
  motionSchemas.gripper,
  motionSchemas.work_pose,
]);
export type MotionInput = z.infer<typeof motionSchema>;

// Single actions and sequences share these same execution methods. No second
// serial/IK implementation or recursive tool dispatch is needed.
export async function runMotion(
  robot: Robot,
  settings: AISettings,
  input: MotionInput,
  signal: AbortSignal,
) {
  signal.throwIfAborted();
  const duration = input.duration_ms ?? settings.durationMs;
  switch (input.action) {
    case "move_joints":
      return robot.move(input.joints_deg, duration, signal);
    case "gripper":
      return robot.gripper(
        input.angle_deg,
        duration,
        input.power_mw ?? settings.gripperPowerMw,
        signal,
      );
    case "work_pose":
      return robot.workPose(duration, settings.gripperPowerMw, signal);
    case "move_tcp": {
      await robot.refresh(signal);
      const current = robot.state.actual!;
      const target = input.relative
        ? input.position_mm.map((v, i) => v + current.tcp_mm[i])
        : input.position_mm;
      const solution = inverse(target, current.joints_deg);
      if (!solution.success || !solution.joints_deg)
        return { success: false, moved: false, solution, actual: current };
      return {
        solution,
        ...(await robot.move(solution.joints_deg, duration, signal)),
      };
    }
  }
}
