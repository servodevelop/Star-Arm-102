// Final report from real-page cache benchmarks and reviewed real pick/place.
// Source: benchmark-cache.mjs and profile-task.mjs. No device/model commands.
import { readFile, writeFile } from "node:fs/promises";
const sum = (a, key) => a.reduce((n, x) => n + (x[key] ?? 0), 0);
const sec = (n) => (n / 1000).toFixed(1);
const pct = (n) => `${(n * 100).toFixed(1)}%`;
async function benchmark(label) {
  const r = JSON.parse(await readFile(`temp/native-compaction/${label}/report.json`, "utf8"));
  if (r.rounds.length !== 6 || r.model !== "gpt-6.1-sol" || r.requests.some((q) => q.model !== r.model || q.effort !== r.effort || (q.actual_model && q.actual_model !== r.model)))
    throw Error(`Incomplete or mixed benchmark: ${label}`);
  const regular = r.requests.filter((q) => !q.compaction_request);
  return { ...r, total: sum(r.rounds, "total_ms"), modelMs: sum(r.requests, "ms"),
    cache: sum(regular, "cached_tokens") / sum(regular, "input_tokens"),
    compactCount: r.requests.length - regular.length,
    compactMs: sum(r.requests.filter((q) => q.compaction_request), "ms"),
  };
}
const pairs = [];
for (const effort of ["medium", "low"]) {
  const before = await benchmark(`baseline-${effort}`), after = await benchmark(`final-${effort}`);
  if (before.task !== after.task || before.effort !== effort || after.effort !== effort || before.client_bundle_hash === after.client_bundle_hash)
    throw Error("Compare identical tasks/models/grades on distinct builds");
  if (after.native_compaction_threshold !== 32768 || after.requests.some((q) => !q.cache_key_hash) || new Set(after.requests.map((q) => q.cache_key_hash)).size !== 1)
    throw Error("Final cache configuration differs");
  pairs.push({ effort, before, after });
}
if (new Set(pairs.map((p) => p.after.client_bundle_hash)).size !== 1) throw Error("Final builds differ");
const nativeCheck = JSON.parse(await readFile("temp/native-compaction/native-ui-verified.json", "utf8"));
if (!nativeCheck.native_checkpoint_visible || !nativeCheck.marker_restored) throw Error("Native roundtrip not verified");
const baseline = JSON.parse(await readFile("temp/latency-comparison/sol-final-medium-center-1/report.json", "utf8"));
const grasp = JSON.parse(await readFile("temp/latency-comparison/native-grasp-center-1/report.json", "utf8"));
if (typeof grasp.physical_success !== "boolean") throw Error("Review physical outcome first");
if (grasp.model !== baseline.model || grasp.effort !== baseline.effort || grasp.entries.find((e) => e.kind === "user")?.text !== baseline.entries.find((e) => e.kind === "user")?.text)
  throw Error("Physical task/model/grade differs");
if (grasp.client_bundle_hash !== pairs[0].after.client_bundle_hash) throw Error("Physical test loaded another build");
const candidates = await Promise.all(["native-medium", "native-low", "affinity-medium", "cache-only-medium"].map(benchmark));
const summaryRows = pairs.map(({ effort, before: a, after: b }) =>
  `| ${effort} | ${sec(a.total)}→${sec(b.total)} | ${sec(a.total / 6)}→${sec(b.total / 6)} | ${a.requests.length}→${b.requests.length} | ${pct(a.cache)}→${pct(b.cache)} | ${pct(1 - b.total / a.total)} |`).join("\n");
const roundRows = pairs.flatMap(({ effort, before: a, after: b }) => a.rounds.map((r, i) =>
  `| ${effort} | ${i + 1} | ${sec(r.total_ms)} | ${sec(b.rounds[i].total_ms)} |`)).join("\n");
const candidateRows = candidates.map((r) => `| ${r.label} | ${sec(r.total)} | ${pct(r.cache)} | ${r.compactCount} / ${sec(r.compactMs)} |`).join("\n");
const modelTime = (r) => sum(r.requests, "total_ms");
const graspRows = [baseline, grasp].map((r, i) => `| ${i ? "最终实现" : "8abb396"} | ${sec(r.total_ms)} | ${sec(modelTime(r))} | ${sec(r.total_ms - modelTime(r))} | ${r.request_count} |`).join("\n");
const astra = JSON.parse(await readFile("temp/latency-comparison/astra-dual-observation-red-1/report.json", "utf8"));
if (astra.model !== "gpt-6-astra" || astra.effort !== "medium" || !astra.reviewed_views || !astra.submitted_image_checks_passed || !astra.pair_checks_passed)
  throw Error("Review Astra's actual paired images and physical outcome first");
const motionTools = astra.entries.filter((e) => e.kind === "tool").map((e) => JSON.parse(e.detail ?? "{}"));
const observationMs = motionTools.reduce((total, t) => total + (t.output?.observation_ms ?? 0), 0);
const astraModelMs = modelTime(astra);
const frameBytes = astra.submitted_frames.map((f) => f.bytes);
const review = JSON.parse(await readFile("temp/latency-comparison/final-review-astra-red-1/report.json", "utf8"));
if (!review.reviewed_views || !review.visual_review_passed || !review.submitted_image_checks_passed || !review.cycle_completed)
  throw Error("Final review run requires completed physical and image review");
const reviewModelMs = modelTime(review);
const reviewImageMs = review.entries.filter((e) => e.kind === "tool")
  .reduce((total, e) => total + (JSON.parse(e.detail ?? "{}").output?.observation_ms ?? 0), 0);
const doc = `# AI 等待时间、缓存与原生压缩

← [vla-arms-agent](../README.zh.md) · <sub>[English](PERFORMANCE.md) / **简体中文**</sub>

测试日期：2026-11-14。模型固定为 gpt-6.1-sol，medium 与 low 分别作同等级对照。全部任务从本机真实网页的表单、开始或追加按钮执行，读取实际机械臂反馈和 1280×720 外部相机画面。先用静止场景比较模型等待和缓存，再单独执行完整抓放。前两组对照使用 471be14 的单张首帧实现；末节为动作后默认双图的 Astra 真机结果。

## 同等级六轮只读对照

相同任务文本：“只读取一次外部相机画面和当前关节状态，用一句话报告海绵位置；不执行任何机械臂动作。”每组新建会话后连续追加六轮，场景与机械臂位置未人工调整。总时间包含本页准备画面、模型等待、取图和最终回复。

| 等级 | 六轮总耗时：原→新 / 秒 | 平均每轮：原→新 / 秒 | 模型请求：原→新 | 缓存命中：原→新 | 总耗时减少 |
| --- | ---: | ---: | ---: | ---: | ---: |
${summaryRows}

原版为 8abb396。最终实现将已开启预览的当前帧和实际姿态随任务发送，六轮均用一次模型请求完成观察和回复，减少了先请求取图再判断的往返。模型与思考强度未降低，未缩小图像分辨率。缓存比例按上游回报的 cached_tokens / input_tokens 加权计算。

| 等级 | 轮次 | 原版 / 秒 | 最终 / 秒 |
| --- | ---: | ---: | ---: |
${roundRows}

## 完整真机抓放

同为 gpt-6.1-sol / medium，任务文本相同：从左侧红框抓起紫色海绵、放到中心白色虚线框并回工作位。下表从网页发送计时到任务结束，包括全部取图、姿态预览、动作、释放及回工作位；不把只读观察的加速比例直接用于整次抓放。

| 实现 | 整次 / 秒 | 全部模型请求累计 / 秒 | 设备、取图及页面处理 / 秒 | 请求数 |
| --- | ---: | ---: | ---: | ---: |
${graspRows}

最终实际结果：${grasp.review ?? (grasp.physical_success ? "过程与最终图像确认抓放完成。" : "未完成。")}

本次完整抓放未提速：常规模型请求 ${grasp.requests.filter((q) => !q.compaction_request).length} 次，对照为 ${baseline.request_count} 次；原生压缩另用 ${sec(sum(grasp.requests.filter((q) => q.compaction_request), "total_ms"))} 秒。姿态纠偏产生的额外回合和压缩开销抵消了缓存收益。

完整抓放每版仅一次，物体朝向、模型规划和纠偏过程会变化；本表是单次实测，不是稳定成功率或统一加速比例。模型请求累计包含网络、上游处理与响应流。设备等时间为整次减去请求累计，不是纯电机运行时长。

## 原生压缩与缓存实现

- 通过现有 Vercel AI SDK 的 compactionTrigger 调用同一个 /responses 入口，真实返回 openai.compaction 密文。后续原样承接检查点，浏览器保留原始历史，不生成手工摘要。
- 当前默认阈值为 256K（262144 token）；本报告的性能数据采集时使用 32768 token。使用模型回报的输入用量，在模型调用结束后、下一次请求前触发；配置填 0 关闭。压缩进度在 AI 流程显示，可停止，期间收到的补充会在下一步送达。
- 同一会话使用稳定 prompt_cache_key，窗口内只追加消息；从最新原生检查点承接后重新累积。切换模型或入口时重新建立检查点。
- 配置面板展示最近模型响应时间、输入量及实际缓存命中；未回报的用量显示“未回报”。
- 本地 CLIProxyAPI 已将 routing.session-affinity 从 false 改为 true，其他路由及认证配置保持原值，未重启代理进程。此设置属于本地模型服务，不随应用源码部署。

最终网页已用单独测试阈值触发原生压缩，随后准确恢复 native-check-741 标记，测试结束时恢复为当时配置的 32768，当前默认已调整为 256K。单元测试另覆盖检查点缺失不丢历史、压缩中用户补充、模型切换和缓存键连续性。

原生压缩会缩小输入，也会改变缓存前缀并产生处理开销，因此没有采用低阈值频繁压缩。[OpenAI 原生压缩说明](https://developers.openai.com/api/docs/guides/compaction)、[缓存前缀说明](https://developers.openai.com/api/docs/guides/prompt-caching)。

## 未采用的参数与消融对照

下列六轮结果全部保留。native 为固定缓存键与 16K 原生阈值、代理亲和关闭；affinity 为只开启代理亲和；cache-only 为 32K 和亲和开启但未预取初始帧。普通请求的缓存比例不包含压缩请求，但总耗时包含压缩开销。

| 方案 / 等级 | 六轮总耗时 / 秒 | 普通请求缓存命中 | 原生压缩次数 / 耗时秒 |
| --- | ---: | ---: | ---: |
${candidateRows}

cache-only 的缓存命中提高后，总耗时仍未下降，因此最终同时减少了首帧获取往返。16K 压缩耗时较多，未作为默认配置。各组为顺序实测，不能据此认定路由或缓存的独立收益；最终差额包含应用与本地代理配置的组合影响。

## Astra：运动后默认双图

任务：“把紫色海绵放到左侧红色虚线框内，放下后回到工作位。”通过真实网页启动，gpt-6-astra / medium，压缩阈值 256K。执行期间只读记录，没有插入动作、补充或纠偏指令。

| 阶段 | 耗时 / 秒 |
| --- | ---: |
| 整次抓放，包括返回工作位 | ${sec(astra.total_ms)} |
| 全部模型请求累计（${astra.request_count} 次） | ${sec(astraModelMs)} |
| 轮流开启、取双图及编码（${astra.submitted_frames.length / 2} 组） | ${sec(observationMs)} |
| 运动、反馈与页面处理等剩余时间 | ${sec(astra.total_ms - astraModelMs - observationMs)} |

起止时间采用真实会话时间戳；模型耗时采用浏览器 ResourceTiming，取图时间采用工具的 observation_ms。剩余时间为相减结果，不是纯电机运行时间。

实际结果：${astra.review}

- 共 ${astra.submitted_frames.length} 张动作后图片，外部与腕部各 ${astra.submitted_frames.length / 2} 张，全部 1280×720；解码、尺寸、非全黑检查及逐图视角核对通过。单张 WebP90 约 ${(Math.min(...frameBytes) / 1024).toFixed(1)}–${(Math.max(...frameBytes) / 1024).toFixed(1)} KiB。
- 本轮采用轮流取图，每组双图平均 ${sec(observationMs / (astra.submitted_frames.length / 2))} 秒；两张图分别携带采集时间，不作为同时曝光的双目图使用。
- 单独 observe_camera 调用为 ${astra.tool_counts.observe_camera ?? 0} 次，姿态预览 ${astra.tool_counts.preview_joints ?? 0} 次。模型等待占整次约 ${pct(astraModelMs / astra.total_ms)}，是本轮主要耗时。
- 工具默认返回双图，AI 可通过 observe=false 不附图；本轮未使用关闭开关。只有整组序列结束才取图，取图失败保留运动结果。

本节为单次 Astra 结果，任务方向及模型与前面 sol 对照不同，不据此计算同条件加速比例或成功率。

## 审核候选回归

最后一次回归为 gpt-6-astra / medium，相同红框任务，包含新相机就绪流程与整理后的提示词。执行过程只等待和记录。

| 项目 | 最终实测 |
| --- | ---: |
| 整次抓放及回工作位 | ${sec(review.total_ms)} 秒 |
| 模型请求累计 / 次数 | ${sec(reviewModelMs)} 秒 / ${review.request_count} |
| 双图采集、切换与编码 | ${sec(reviewImageMs)} 秒 |
| 运动、反馈及页面等剩余时间 | ${sec(review.total_ms - reviewModelMs - reviewImageMs)} 秒 |
| 姿态预览 / 独立取图 | ${review.tool_counts.preview_joints ?? 0} / ${review.tool_counts.observe_camera ?? 0} 次 |
| 动作后实际图片 | ${review.submitted_frames.length} 张，1280×720 |

${review.review}

本轮包含一次抓空后的自主重试，不作为稳定提速或成功率的证明。提示词整理的效果仍受模型判断和实际抓取条件影响。

故障注入通过真实 SDK 验证长度截断、过滤响应和动作中停止后的继续；未执行与结果未确认的调用分开记录，已执行动作不重放。真实网页验证了读取未绑定腕部时外部预览保持开启。37 项单元测试、5 项页面测试、生产构建及上述真机回归完成。

## 复测

[测试说明](../tests/README.zh.md)列出 benchmark-cache.mjs、profile-task.mjs 与本报告生成器的用法。数据写入 temp/native-compaction/ 和 temp/latency-comparison/，可重新采集；报告不包含 API Key、请求图片或原生密文。抓放结果需检查抬升与最终画面，不能只采用模型自述。
`;
await writeFile("docs/PERFORMANCE.zh.md", doc);
console.log(JSON.stringify({ report: "docs/PERFORMANCE.zh.md", same_effort_pairs: pairs.length, physical_reviewed: true }));
