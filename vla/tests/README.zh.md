# 测试

← [vla-arms-agent](../README.zh.md) · <sub>[English](README.md) / **简体中文**</sub>

- `i18n.test.ts`：检查翻译参数和未知错误、语言变化时运动数值一致、英文工具状态恢复，以及运行中固定提示词和工具语言；使用本地 SDK 数据，不访问网络或机械臂。
- `core.test.ts`：从厂商工作台提取的固定正解结果和协议报文作为对照；虚拟串口验证分片、后台回读保持就绪、动作执行状态、串口队列、取消、连接失败和重新连接，不发送真机动作。
- `context.test.ts`：检查原生密文检查点承接、完整历史保留和无效检查点不裁剪上下文。
- `agent.test.ts`：检查任务初始化失败、请求停止、未结束会话恢复、补充消息保留及真实 SDK 请求的前缀、会话缓存键、原生压缩承接、输出截断续写、失败及动作中停止后的恢复，保留真实执行状态和历史；不访问网络或机械臂。
- `cameras.test.ts`：模拟开启期间关闭和播放失败，检查状态与设备释放、轮流和双路取图、全黑帧与错误来源校验、未绑定角色取图不关闭已有预览、启动等待和等待期间断线的就绪状态。
- `network.test.ts`：使用虚拟时钟检查 15 次重试、10 秒间隔、取消等待及流中断后不重复执行工具。
- `tools.test.ts`：检查批量预览、并发预览与设备操作顺序、动作后默认双图、关闭附图和取图失败不重复运动；验证序列在 IK 失败后不会进入后续闭爪，已完成步骤会返回给模型。
- `page.spec.ts`：Playwright 检查部署页 AI 全部配置的编辑、保存、刷新恢复和密钥清除、目标预览、未结束会话恢复、停止模型验证、正序对话、滚动衔接与展开后的响应式布局。使用 `pnpm test:e2e`，默认访问本机 8780 端口。
- `live-control.mjs`：本项目真实网页验收入口，通过正常表单和按钮操作；需要实际相机、机械臂和支持视觉、工具调用的 Responses API。会执行真实动作。JSON 行命令从标准输入传入，页面与状态输出在 `temp/live/`，浏览器测试配置在 `temp/live-profile/`，均可删除重建。
- `task-report.mjs`：在网页发送任务后运行 `node tests/task-report.mjs 1`（参数为轮次）。只读记录整轮耗时、工具结果、模型请求耗时和过程图像到 `temp/five-rounds/round-1/`。最终成功需查看图像和实际反馈核对，脚本不会将 AI 自述自动当成物理成功。审核后在 `report.json` 填入各次放置确认时间（含追加纠偏）、各自耗时、回工作位时间、`physical_success` 与 `grasp_retries`，运行 `node tests/task-report.mjs summary` 生成最终报告；脚本检查分段时间之和等于整轮时间。来源：本工程真实网页重复验收。
- `profile-task.mjs`：发送任务前运行 `node tests/profile-task.mjs astra-batched-center-1`，随后在同一网页正常发送任务。只读记录下一次任务的请求耗时、首包、工具参数就绪、响应结束、token 用量、实际工具记录和过程画面，输出到 `temp/latency-comparison/<名称>/`。不发送模型或设备命令，不保存 API Key 或完整请求正文；结束后保存本轮实际提交的相机图片并检查解码、尺寸和全黑帧。`physical_success` 留空，需结合过程画面人工核对。来源：本工程真实网页性能对照测试。
- `compare-image-codecs.mjs`：开启相机预览后运行 `CHROMIUM_PATH=/path/to/chrome node tests/compare-image-codecs.mjs external`，腕部使用 `wrist`。从现有预览读取一帧，使用独立浏览器比较原生 JPEG90、MozJPEG90、WebP90 和无损 PNG，记录原分辨率、文件大小、编码时间与像素误差到 `temp/latency-comparison/codecs/<角色>/`。不发送模型请求或机械臂命令。来源：本工程相机实测，压缩库为 `@jsquash/jpeg`（MozJPEG / Squoosh）。
- `summarize-latency.mjs`：完成 `benchmark-cache.mjs` 的 `baseline-{medium,low}`、`final-{medium,low}` 六轮对照及 `native-ui` 原生压缩验证，并采集 `profile-task.mjs` 的 `sol-final-medium-center-1`、`native-grasp-center-1` 完整抓放，并采集 Astra 默认双图的 `astra-dual-observation-red-1` 及审核候选 `final-review-astra-red-1` 后，核对过程图像、填写 `physical_success` 和 `review`，运行 `node tests/summarize-latency.mjs` 生成 `docs/PERFORMANCE.zh.md`。脚本检查模型、等级、任务文本、客户端版本、缓存键和原生检查点验证结果；只读等待与完整抓放分别计时，保留较慢实验。原始数据保存在 `temp/`，清理后需重新采集。来源：本工程真实网页缓存与抓放对照测试。
- `select-serial.py`：仅供 X11 上的真机浏览器测试，使用键盘选择 Chromium 串口弹窗中的唯一 USB 转串口设备；不直接读写串口。先从弹窗确认设备枚举完成、恰好连接一个 USB 串口且该设备排在列表末尾，再调用脚本。脚本不自动判断弹窗是否就绪，默认使用人工选择。

```sh
CHROMIUM_PATH=/path/to/chrome HEADED=1 node tests/live-control.mjs
```

先输入 `{"action":"connect"}` 并在浏览器选择从臂串口。`configure` 使用命令参数或当前页面地址/模型；如存在现有工程 `.env`，可从中读取已授权配置。密钥可由 `AI_API_KEY` 环境变量、`AI_CONFIG_FILE` 指向的 CLIProxyAPI 配置或已有 `.env` 提供，通过网页配置保存到测试浏览器，不写入日志。独立运行不要求存在父级工程。

常用命令：

```json
{"action":"configure","baseURL":"http://127.0.0.1:8317/v1","model":"gpt-6-astra","effort":"medium"}
{"action":"cameras","resolution":"1280x720","indices":[1,2],"only":0}
{"action":"task","text":"把海绵移动到中心框并放置到红色框，如果已经在中心框则只需要放到红色框。"}
{"action":"status"}
{"action":"close"}
```

`indices` 是网页设备列表索引，必须先核对设备名称；两路绑定都会保存，`only` 为 0（仅开启外部）或 1（仅开启腕部），省略时分别开启两路。带宽不足时可由网页或 AI 切换采集。`task` 使用“开始会话”或“追加对话”按钮；已有会话时会点击弹框中的“确认追加”。AI 流程在输入框下方按时间正序展示，测试采集时按原始顺序记录。`temp/live/network.json` 记录模型请求耗时、状态码与系统提示词哈希；密钥随配置保存在测试浏览器，图片通过相机工具发送。验收结合最终画面、电机反馈和物体实际落点，共同核对完整抓放结果。

来源：厂商对照提交及移植范围见 [vendor 说明](../src/vendor/star-arm/README.zh.md)；页面测试、真机操作封装和 X11 弹窗辅助由本工程编写。

- `benchmark-cache.mjs`：在已连接的真实测试网页执行同一文本的六轮只读观察，命令为 `node tests/benchmark-cache.mjs <名称> medium 262144`，low 单独运行同等级对照。使用正常表单、保存、开始/追加对话和确认按钮，不注入状态；仅允许只读工具结果。记录每轮总耗时、全部模型请求、原生压缩时间、客户端指纹、缓存键哈希及真实 token 用量到 `temp/native-compaction/<名称>/`。不保存密钥、原始请求正文或原生密文。来源：本工程真实网页缓存与速度对照。
