import { createOpenAI } from "@ai-sdk/openai";
import { generateText, isStepCount, streamText, tool } from "ai";
import { z } from "zod";
import { Cameras, type CameraFrame } from "./cameras";
import { Robot } from "./robot";
import { networkErrorMessage, networkRecovery, networkRetries, resilientModel } from "./network";
import { instructions } from "./prompts";
import { createRobotTools, robotSnapshot } from "./tools";
import { activeContext, hasCompaction, withoutCompactions } from "./context";
import {
  type Entry,
  type Session,
  type AISettings,
  emptySession,
  DEFAULT_AI,
} from "./types";
export { type Entry, type Session, type AISettings, DEFAULT_AI } from "./types";

export class Agent {
  session: Session = emptySession();
  get running() { return this.session.active; }
  private controller?: AbortController;
  constructor(
    private robot: Robot,
    private cameras: Cameras,
    private changed: (session: Session, running: boolean) => void,
  ) { }
  private emit() {
    this.changed(
      {
        ...this.session,
        messages: [...this.session.messages],
        entries: [...this.session.entries],
        pending: [...this.session.pending],
      },
      this.running,
    );
  }
  private entry(kind: Entry["kind"], text: string, detail?: unknown) {
    const e: Entry = {
      id: `${Date.now()}-${this.session.entries.length}`,
      kind,
      text,
      at: Date.now(),
      ...(detail === undefined
        ? {}
        : { detail: JSON.stringify(detail, null, 2) }),
    };
    this.session.entries.push(e);
    this.emit();
    return e;
  }
  supplement(text: string) {
    this.session.pending.push(text);
    this.entry("user", text);
  }
  private flushPending() {
    this.session.messages.push(
      ...this.session.pending
        .splice(0)
        .map((content) => ({ role: "user" as const, content })),
    );
  }
  async run(text: string, settings: AISettings, apiKey: string) {
    if (this.running) {
      this.supplement(text);
      return;
    }
    if (!settings.baseURL.trim() || !settings.model.trim() || !apiKey.trim())
      throw Error("请填写模型地址、模型 ID 和 API Key");
    this.controller = new AbortController();
    const signal = this.controller.signal;
    this.session.active = true;
    try {
      const scope = JSON.stringify([settings.baseURL.replace(/\/+$/, ""), settings.model]);
      if (this.session.contextScope && this.session.contextScope !== scope) {
        this.session.messages = withoutCompactions(this.session.messages);
        delete this.session.cacheKey;
        delete this.session.usage;
      }
      this.session.contextScope = scope;
      this.session.cacheKey ??= crypto.randomUUID();
      this.entry("user", text);
      this.session.messages.push({ role: "user", content: text });
      const state = `任务开始时的实际状态数据（后续以工具反馈为准）：${JSON.stringify(robotSnapshot(this.robot, this.cameras))}`;
      const available = this.cameras.available();
      const role = available.includes("external") ? "external" : undefined;
      let frame: CameraFrame | undefined;
      if (role) {
        try { frame = this.cameras.capture(role); }
        catch (error) { this.entry("status", `初始画面未就绪，可用相机工具取图：${String(error)}`); }
      }
      this.session.messages.push({ role: "user", content: frame ? [
        { type: "text", text: `${state}\n已采集的本轮初始画面：${JSON.stringify({ role: frame.role, captured_at: frame.captured_at, width: frame.width, height: frame.height })}` },
        { type: "file", data: frame.dataURL, mediaType: frame.dataURL.slice(5, frame.dataURL.indexOf(";")) },
      ] : state });
      this.emit();
      const provider = createOpenAI({
        baseURL: settings.baseURL.replace(/\/+$/, ""),
        apiKey,
      });
      let reply: Entry | undefined;
      const tools = createRobotTools({
        robot: this.robot,
        cameras: this.cameras,
        settings,
        signal,
        record: (kind, text, detail) => this.entry(kind, text, detail),
        changed: () => this.emit(),
      });
      for (;;) {
        signal.throwIfAborted();
        this.flushPending();
        const threshold = settings.compactTokens ?? DEFAULT_AI.compactTokens!;
        if (threshold > 0 && (this.session.usage?.inputTokens ?? 0) >= threshold) {
          await this.compact(settings, apiKey, signal);
          this.flushPending();
        }
        const startedTools = new Set<string>();
        const result = streamText({
          model: provider.responses(settings.model),
          // Static instructions preserve a reusable system prefix. Dynamic
          // posture, timestamps and reminders belong in conversation data.
          system: instructions,
          messages: activeContext(this.session.messages),
          tools,
          providerOptions: {
            openai: {
              store: false,
              promptCacheKey: this.session.cacheKey,
              parallelToolCalls: true,
              ...(settings.effort ? { reasoningEffort: settings.effort } : {}),
            },
          },
          maxRetries: 0,
          streamRetries: networkRetries,
          abortSignal: signal,
          stopWhen: isStepCount(1),
          prepareStep: () => ({
            model: resilientModel(
              provider.responses(settings.model),
              signal,
              async (status) => {
                reply = undefined;
                this.entry(
                  "status",
                  `网络重试 ${status.attempt}/${networkRetries}，10 秒后继续：${status.error}`,
                );
              },
            ),
          }),
          onToolExecutionStart: ({ toolCall }) => { startedTools.add(toolCall.toolCallId); },
          onStepEnd: async (step) => {
            reply = undefined;
            this.session.messages.push(...step.response.messages);
            // Close unanswered local calls without inventing motion feedback.
            // SDK may skip a call on truncation, or lose its result on failure.
            const returned = new Set(step.response.messages.flatMap((m) =>
              m.role === "tool" ? m.content.filter((p) => p.type === "tool-result").map((p) => p.toolCallId) : []));
            const unanswered = step.toolCalls.filter((call) => !call.providerExecuted && !returned.has(call.toolCallId));
            if (unanswered.length) this.session.messages.push({ role: "tool", content: unanswered.map((call) => ({
              type: "tool-result", toolCallId: call.toolCallId, toolName: call.toolName,
              output: { type: "error-text", value: startedTools.has(call.toolCallId)
                ? "调用已开始处理，但未收到完整结果；先核对实际状态，不要自动重放动作。"
                : `模型响应结束原因为 ${step.finishReason}；SDK 未执行此调用。` },
            })) });
            if (hasCompaction(step.response.messages)) delete this.session.usage;
            else this.session.usage = {
              inputTokens: step.usage.inputTokens,
              cachedTokens: step.usage.inputTokenDetails.cacheReadTokens,
              responseMs: step.performance.responseTimeMs,
            };
            this.emit();
          },
        });
        for await (const part of result.fullStream) {
          if (part.type === "error") throw part.error;
          if (part.type === "text-delta") {
            reply ??= this.entry("assistant", "");
            reply.text += part.text;
            this.emit();
          }
        }
        const reason = await result.finishReason;
        if (reason === "length") {
          this.entry("status", "模型输出达到长度限制，保留当前结果并继续");
          this.session.messages.push({
            role: "user",
            content: "上一段模型输出因长度限制截断。依据已经返回的工具结果继续当前任务，已执行的动作不重复执行。",
          });
          continue;
        }
        if (reason !== "stop" && reason !== "tool-calls")
          throw Error(`模型响应未正常完成：${reason}`);
        if (reason !== "tool-calls" && !this.session.pending.length) break;
      }
      this.entry("status", "本轮已结束；请以相机画面和实际反馈核对物体结果");
    } catch (error) {
      const message = networkErrorMessage(error);
      this.entry(
        "status",
        signal.aborted
          ? "已停止，未完成目标保留在当前会话"
          : `运行失败：${message}`,
      );
      this.flushPending();
      // Persist an explicit boundary so a resumed conversation does not assume success.
      this.session.messages.push({
        role: "user",
        content: `上一轮${signal.aborted ? "已停止" : `中断：${message}`}。先检查当前实际状态，再继续；不要自动重放已经执行的动作。`,
      });
    } finally {
      this.session.active = false;
      this.controller = undefined;
      this.emit();
    }
  }
  private async compact(settings: AISettings, apiKey: string, signal: AbortSignal) {
    this.entry("status", "正在原生压缩上下文");
    const started = performance.now();
    const recovery = networkRecovery(signal, async (status) => {
      this.entry("status", `网络重试 ${status.attempt}/${networkRetries}，10 秒后继续：${status.error}`);
    });
    const result = await recovery.run(() => generateText({
      model: createOpenAI({ baseURL: settings.baseURL.replace(/\/+$/, ""), apiKey }).responses(settings.model),
      system: instructions,
      messages: activeContext(this.session.messages),
      providerOptions: { openai: {
        store: false, compactionTrigger: true, promptCacheKey: this.session.cacheKey,
        ...(settings.effort ? { reasoningEffort: settings.effort } : {}),
      } },
      toolChoice: "none",
      maxRetries: 0,
      abortSignal: signal,
    }));
    signal.throwIfAborted();
    if (!hasCompaction(result.response.messages))
      throw Error("模型入口未返回原生 compaction 项；原会话已保留，未使用手工摘要替代");
    this.session.messages.push(...result.response.messages);
    delete this.session.usage;
    this.entry("status", "原生上下文压缩完成，继续当前任务", {
      duration_ms: performance.now() - started,
      input_tokens: result.usage.inputTokens, output_tokens: result.usage.outputTokens,
    });
  }
  async stop() {
    this.cancel();
    await this.robot.stop();
  }
  cancel() {
    this.controller?.abort();
  }
  reset() {
    if (this.running) throw Error("请先停止当前任务");
    this.session = emptySession();
    this.emit();
  }
  restore(session: Session) {
    if (this.running) throw Error("请先停止当前任务");
    this.session = {
      ...emptySession(), ...session,
      active: false,
      messages: [...session.messages],
      pending: [...(session.pending ?? [])],
      entries: session.entries.map((entry) => ({
        ...entry,
        text: entry.kind === "tool"
          ? entry.text.replace(/ · 执行中$/, " · 已中断，待核对")
          : entry.text,
      })),
    };
    this.flushPending();
    if (session.active || session.entries.some((e) => e.kind === "tool" && e.text.endsWith(" · 执行中"))) {
      this.session.messages.push({
        role: "user",
        content: "页面已重新打开，上轮任务已中断。先检查当前实际状态，再继续；不要自动重放已经执行的动作。",
      });
      this.entry("status", "上轮任务已中断；重新连接设备后可在当前会话继续");
    }
    this.emit();
  }
}

export async function models(settings: AISettings, apiKey: string, signal?: AbortSignal) {
  const response = await fetch(
    `${settings.baseURL.replace(/\/+$/, "")}/models`,
    { headers: { Authorization: `Bearer ${apiKey}` }, signal },
  );
  const value = await response.json();
  if (!response.ok)
    throw Error(value.error?.message ?? `模型列表 HTTP ${response.status}`);
  return (value.data as { id: string }[]).map((v) => v.id);
}
export async function checkAI(
  settings: AISettings,
  apiKey: string,
  frame?: CameraFrame,
  signal?: AbortSignal,
) {
  let called = false;
  const result = streamText({
    model: createOpenAI({
      baseURL: settings.baseURL.replace(/\/+$/, ""),
      apiKey,
    }).responses(settings.model),
    providerOptions: {
      openai: {
        store: false,
        ...(settings.effort ? { reasoningEffort: settings.effort } : {}),
      },
    },
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: "调用 describe_input 描述当前输入，再根据工具结果简短回复。不会操作机械臂。",
          },
          ...(frame ? [{ type: "image" as const, image: frame.dataURL }] : []),
        ],
      },
    ],
    tools: {
      describe_input: tool({
        description: "返回输入；不操作设备",
        inputSchema: z.object({ description: z.string() }),
        execute: (input) => {
          called = true;
          return input;
        },
      }),
    },
    stopWhen: isStepCount(2),
    maxRetries: 0,
    abortSignal: signal,
  });
  const text = await result.text;
  if (!called || !text) throw Error("未完成工具调用与回复，不能确认兼容");
  return `${settings.model}：文本、流式、工具回传通过${frame ? "；已发送相机图片，请核对描述" : "；识图未测（未开启相机）"}。${text}`;
}
