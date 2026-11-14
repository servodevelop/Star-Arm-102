// Chinese source strings are stable message keys; parameters keep values out of translations.
export const messages: Record<string, string> = {
  外部相机: "External camera",
  腕部相机: "Wrist camera",
  实际回读: "Actual feedback",
  目标预览: "Target preview",
  姿态预览视角: "Pose preview view",
  空间: "Spatial",
  侧视: "Side",
  俯视: "Top",
  实际机械臂与目标的运动学预览: "Kinematic preview of actual and target poses",
  连接从臂后显示实际姿态: "Connect the follower to see its actual pose",
  未开启: "Off",
  "请使用 HTTPS 或 localhost 连接相机与机械臂。":
    "Use HTTPS or localhost to connect cameras and the arm.",
  "当前浏览器不支持串口连接，请使用 Chrome 或 Edge。":
    "This browser does not support serial connections. Use Chrome or Edge.",
  "会话保存失败：{0}": "Could not save the conversation: {0}",
  "本地数据读取失败：{0}": "Could not read local data: {0}",
  "相机列表读取失败：{0}": "Could not read camera list: {0}",
  请求已停止: "Request stopped",
  "相机需要 HTTPS 或 localhost 安全上下文":
    "Cameras require HTTPS or a localhost secure context",
  配置已保存: "Configuration saved",
  "看见，判断，行动": "See, decide, act",
  "连接相机与机械臂，用自然语言完成任务。":
    "Connect cameras and a robot arm. Give tasks in natural language.",
  从臂已连接: "Follower connected",
  从臂未连接: "Follower disconnected",
  "停止 AI 与运动": "Stop AI and motion",
  连接与观察: "Connect and observe",
  "连接机械臂，绑定外部与腕部相机。":
    "Connect the arm and bind external and wrist cameras.",
  保存配置: "Save configuration",
  从臂连接: "Follower connection",
  串口波特率: "Serial baud rate",
  "默认动作时长 / ms": "Motion duration / ms",
  默认动作时长: "Default motion duration",
  "正在连接…": "Connecting…",
  断开从臂: "Disconnect follower",
  选择串口并连接: "Select serial port and connect",
  "回读中…": "Reading…",
  回读姿态: "Read actual pose",
  "连接后读取当前姿态。": "Read the current pose after connecting.",
  执行状态: "Execution state",
  执行中: "Running",
  回读中: "Reading",
  就绪: "Ready",
  未连接: "Disconnected",
  夹爪实际开口角: "Actual gripper opening",
  夹爪功率回读: "Gripper power feedback",
  关节映射与零点: "Joint mapping and offsets",
  "方向与零点用于校准关节角度，修改后会更新姿态与预览。":
    "Direction and offsets calibrate joint angles. Changes update the pose and preview.",
  关节: "Joint",
  方向: "Direction",
  "零点 / °": "Offset / °",
  "J{0} 方向": "J{0} direction",
  同向: "Forward",
  反向: "Reverse",
  "J{0} 零点": "J{0} offset",
  "{0}实时画面": "{0} live view",
  选择设备并开启预览: "Select a device and start preview",
  绑定设备: "Bound device",
  "{0}设备": "{0} device",
  未绑定: "Not bound",
  已绑定设备: "Bound device",
  "（当前不可用）": " (currently unavailable)",
  "摄像头 {0}": "Camera {0}",
  采集分辨率: "Capture resolution",
  "{0}分辨率": "{0} resolution",
  期望帧率: "Requested frame rate",
  "{0}帧率": "{0} frame rate",
  "开启中…": "Starting…",
  开启预览: "Start preview",
  关闭: "Close",
  授权并刷新摄像头: "Authorize and refresh cameras",
  "授权 / 刷新": "Authorize / refresh",
  "正在请求摄像头权限…": "Requesting camera access…",
  "授权后显示当前电脑的摄像头，无需连接从臂。":
    "Authorize to list cameras on this computer. No arm connection is required.",
  "画面卡顿时，可关闭暂不使用的一路相机。":
    "If video stutters, close the camera you are not using.",
  "AI 与任务": "AI and tasks",
  "保留上下文，运行中可继续发送提醒和补充。":
    "Keep context and send reminders while a task runs.",
  正在处理: "Processing",
  等待任务: "Waiting for a task",
  模型与动作配置: "Model and motion settings",
  "OpenAI 兼容 API 地址": "OpenAI-compatible API URL",
  "AI API 地址": "AI API URL",
  "保存 AI 配置后将自动记住": "Remembered after saving AI settings",
  模型: "Model",
  "AI 模型": "AI model",
  思考强度: "Reasoning effort",
  "AI 思考强度": "AI reasoning effort",
  模型默认: "Model default",
  "原生上下文压缩阈值 / token": "Native context compaction threshold / tokens",
  原生上下文压缩阈值: "Native context compaction threshold",
  "达到后由模型原生压缩，0 关闭；思考强度保持不变。":
    "Native compaction starts at this threshold; 0 turns it off. Reasoning effort stays unchanged.",
  "夹爪默认功率上限 / mW": "Default gripper power limit / mW",
  夹爪功率上限: "Gripper power limit",
  "模型需支持看图和工具调用。配置修改从下次任务生效。夹爪功率填 0 使用默认值。":
    "The model needs image understanding and tool calling. Changes apply to the next task. Gripper power 0 uses its default.",
  "AI 请求性能": "AI request performance",
  最近模型响应: "Latest model response",
  未回报: "Not reported",
  "{0} 秒": "{0} s",
  输入: "Input",
  缓存命中: "Cache hit rate",
  "保存 AI 配置": "Save AI settings",
  模型列表已更新: "Model list updated",
  刷新模型列表: "Refresh model list",
  "正在验证…": "Verifying…",
  验证连接与能力: "Verify connection and capabilities",
  用一句话定义任务: "Describe a task",
  "例如：观察两路画面，把紫色海绵放到中心标记，然后回到工作位。":
    "Example: inspect both views, move the purple sponge to the center mark, then return to the work pose.",
  追加对话: "Continue conversation",
  "AI 任务": "AI task",
  "新任务建议先开启新会话。": "Start a new conversation for a new task.",
  "开启外部相机预览后，任务会附带其当前画面。":
    "With the external preview active, its current image is attached to the task.",
  "描述目标；仅观察时请说明。Ctrl / ⌘ + Enter 发送。":
    "Describe the goal; specify observation-only if needed. Ctrl / ⌘ + Enter to send.",
  开始会话: "Start conversation",
  新会话: "New conversation",
  "AI 流程": "AI activity",
  你: "You",
  状态: "Status",
  姿态与手动控制: "Pose and manual control",
  "实际 TCP / mm": "Actual TCP / mm",
  关节目标与夹爪: "Joint targets and gripper",
  "J{0} 目标角度": "J{0} target angle",
  预览目标: "Preview target",
  使用实际角度: "Use actual angles",
  执行关节目标: "Execute joint target",
  回工作位: "Return to work pose",
  "夹爪开口角 / °": "Gripper opening / °",
  夹爪目标开口角: "Target gripper opening",
  执行夹爪: "Execute gripper",
  "工作位会闭合夹爪。开口参考：30°约 71 mm，60°约 129 mm（测量深度不同）。":
    "The work pose closes the gripper. Opening references: about 71 mm at 30° and 129 mm at 60° (measured at different depths).",
  "TCP 位置逆解": "TCP position IK",
  "输入目标位置，先预览，再执行。未找到解时，可先调整关节角度。":
    "Enter a target position, preview it, then execute. If IK fails, adjust the joint configuration first.",
  "相对当前 TCP 的增量": "Offset from current TCP",
  "IK 未找到解：{0}，位置误差 {1} mm":
    "IK found no solution: {0}; position error {1} mm",
  "位置逆解已预览，误差 {0} mm；在关节控制中点击执行":
    "IK preview ready, error {0} mm; execute from the joint controls",
  求解并预览: "Solve and preview",
  实际舵机反馈: "Actual servo feedback",
  原始角度: "Raw angle",
  电压: "Voltage",
  电流: "Current",
  功率: "Power",
  "追加到当前会话？": "Continue this conversation?",
  "会继续使用当前聊天记录。新任务建议先开启新会话。":
    "This uses the existing chat history. Start a new conversation for a new task.",
  取消: "Cancel",
  确认追加: "Confirm and continue",
  "J1～J6 绝对模型角，单位度，不是原始舵机角":
    "Absolute J1–J6 model angles in degrees, not raw servo angles",
  "运动时长毫秒，留空使用用户配置":
    "Motion duration in milliseconds; omit to use the user setting",
  "基座坐标系中的 XYZ，单位毫米": "XYZ in the base frame, in millimeters",
  "true 为相对当前 TCP 的增量，false 为绝对位置":
    "true: offset from current TCP; false: absolute position",
  "请填写模型地址、模型 ID 和 API Key":
    "Enter the model endpoint, model ID, and API key",
  "任务开始时的实际状态数据（后续以工具反馈为准）：{0}":
    "Actual state at task start (use subsequent tool feedback for updates): {0}",
  "初始画面未就绪，可用相机工具取图：{0}":
    "Initial image not ready; use the camera tool: {0}",
  "{0}\n已采集的本轮初始画面：{1}":
    "{0}\nInitial image captured for this task: {1}",
  "网络重试 {0}/{1}，10 秒后继续：{2}":
    "Network retry {0}/{1}, continuing in 10 seconds: {2}",
  "调用已开始处理，但未收到完整结果；先核对实际状态，不要自动重放动作。":
    "The call started but no complete result was received. Check actual state before repeating any action.",
  "模型响应结束原因为 {0}；SDK 未执行此调用。":
    "Model response ended with {0}; the SDK did not execute this call.",
  "模型输出达到长度限制，保留当前结果并继续":
    "Model output reached its length limit; retaining results and continuing",
  "上一段模型输出因长度限制截断。依据已经返回的工具结果继续当前任务，已执行的动作不重复执行。":
    "The previous model output was truncated by its length limit. Continue from returned tool results without repeating executed actions.",
  "模型响应未正常完成：{0}": "Model response did not complete normally: {0}",
  "本轮已结束；请以相机画面和实际反馈核对物体结果":
    "Turn finished; check camera images and actual feedback to verify the object result",
  "已停止，未完成目标保留在当前会话":
    "Stopped; the unfinished goal remains in this conversation",
  "运行失败：{0}": "Execution failed: {0}",
  "上一轮{0}。先检查当前实际状态，再继续；不要自动重放已经执行的动作。":
    "Previous turn {0}. Check actual state before continuing; do not replay executed actions.",
  已停止: "Stopped",
  "中断：{0}": "interrupted: {0}",
  正在原生压缩上下文: "Compacting context natively",
  "模型入口未返回原生 compaction 项；原会话已保留，未使用手工摘要替代":
    "The endpoint returned no native compaction item; original history is retained without a manual summary",
  "原生上下文压缩完成，继续当前任务":
    "Native context compaction complete; continuing the task",
  请先停止当前任务: "Stop the current task first",
  " · 已中断，待核对": " · Interrupted; check state",
  " · 执行中": " · Running",
  "页面已重新打开，上轮任务已中断。先检查当前实际状态，再继续；不要自动重放已经执行的动作。":
    "The page was reopened and the previous task was interrupted. Check actual state before continuing; do not replay executed actions.",
  "上轮任务已中断；重新连接设备后可在当前会话继续":
    "The previous task was interrupted; reconnect devices to continue this conversation",
  "模型列表 HTTP {0}": "Model list HTTP {0}",
  "调用 describe_input 描述当前输入，再根据工具结果简短回复。不会操作机械臂。":
    "Call describe_input to describe the current input, then briefly reply using its result. No arm movement.",
  "返回输入；不操作设备": "Return the input without operating devices",
  "未完成工具调用与回复，不能确认兼容":
    "Tool calling and reply were incomplete; compatibility is unconfirmed",
  "{0}：文本、流式、工具回传通过{1}。{2}":
    "{0}: text, streaming, and tool round trip passed{1}. {2}",
  "；已发送相机图片，请核对描述": "; camera image sent, check its description",
  "；识图未测（未开启相机）": "; image understanding not tested (camera off)",
  请先选择摄像头: "Select a camera first",
  信号已断开: "Signal disconnected",
  此角色没有相机绑定: "No camera is bound to this role",
  尚未绑定摄像头: "No camera bound yet",
  "{0}摄像头没有有效画面": "{0} camera has no valid image",
  腕部: "Wrist",
  外部: "External",
  "{0} 摄像头画面来源与当前绑定不一致":
    "{0} camera source does not match its current binding",
  浏览器无法创建取图画布:
    "The browser could not create an image capture canvas",
  "{0} 摄像头当前为全黑图，请检查画面或照明":
    "{0} camera image is all black; check the view or lighting",
  "源于经审核的 GraspGenX 有效夹持空间；测量深度不同，不是所有深度的指尖间距，也不是连续角度—宽度标定曲线。90°为机械行程上限，不是默认张开目标。":
    "From the reviewed GraspGenX effective gripping space. Measurements use different depths: these are neither tip gaps at all depths nor a continuous angle-to-width calibration. 90° is the mechanical travel limit, not the default opening.",
  "需要 6 个有限的模型关节角（度）":
    "Six finite model joint angles in degrees are required",
  "J{0} 超出原模型范围 {1}°": "J{0} is outside the original model range {1}°",
  操作已取消: "Operation cancelled",
  从臂串口未连接: "Follower serial port is not connected",
  "舵机回读不完整，未响应 ID：{0}；不将目标角度当成反馈":
    "Incomplete servo feedback; missing IDs: {0}. Target angles are not used as feedback",
  "夹爪驱动角范围为 0～90°，0°闭合、90°最大张开":
    "Gripper angle must be 0–90°: 0° closed, 90° fully open",
  运动时长需为有效的正整数毫秒:
    "Motion duration must be a positive integer in milliseconds",
  "协议功率需为 0～65535 mW 的整数，0 使用舵机默认":
    "Protocol power must be an integer from 0 to 65535 mW; 0 uses the servo default",
  "{0} · 执行中": "{0} · Running",
  "{0} · 未完成": "{0} · Incomplete",
  "{0} · 已完成": "{0} · Completed",
  失败: "Failed",
  "默认 true：动作完成后自动附带外部与腕部两张新图。已有充分信息、无需动作后画面时可设 false；序列仅在整组结束后附图。":
    "Default true: attach fresh external and wrist images after motion. Set false when no new images are needed. Sequences attach images only after the whole sequence ends.",
  "USB 带宽不足时 true，轮流开启两路分别取图；false 保留双路。未填写时沿用当前采集方式：双路已开启则保留，否则轮流取图。":
    "Use true for limited USB bandwidth to capture cameras in turn; false keeps both running. If omitted, preserve dual capture when both are active; otherwise alternate.",
  "读取最新实际舵机反馈、模型关节角及已开启相机。TCP（毫米）、工具 XYZ 轴方向和仰角由实际角度经 URDF 正解计算；仰角相对基座 XY 平面，正数朝上、负数朝下。姿态来自电机反馈，不是相机测量；不运动。":
    "Read actual servo feedback, model joint angles, and active cameras. TCP in millimeters, tool XYZ axes, and elevations come from URDF FK of actual motor angles. Elevation is relative to base XY: positive up, negative down. Pose comes from motor feedback, not cameras. No motion.",
  "一次完成绑定相机开启/切换和取图，返回原分辨率图像与当前姿态。external 外部全景；wrist 腕部近景。exclusive 默认 false；USB 带宽不足时 true 关闭另一路并轮流取图。":
    "Start or switch a bound camera and capture in one call. Returns original-resolution image and current pose. external is the workspace view; wrist is the close view. exclusive defaults to false; true closes the other camera for limited USB bandwidth.",
  "一次批量比较多组六关节候选，返回各组的 TCP、工具轴方向及仰角、目标角或错误。仅计算，不运动、不检查碰撞。页面显示最后一组有效预览。已确定目标时直接用 move_joints，移动工具会自动校验并更新预览。":
    "Compare multiple six-joint candidates in one call. Returns TCP, tool axes, elevations, target angles, or errors. Calculation only: no motion or collision check. The page shows the last valid preview. Use move_joints directly for a determined target; it validates and previews automatically.",
  "自动校验并预览目标，然后移动到 6 关节绝对模型角，保持夹爪。等待指定时长后读取实际反馈并返回误差。默认随结果附外部与腕部新图，observe=false 可关闭；取图失败时只重试观察，不重做动作。":
    "Validate and preview the target, then move to six absolute model joint angles while holding the gripper. Wait for the chosen duration, read actual feedback, and return error. Fresh external and wrist images are attached by default; observe=false disables them. If capture fails, retry observation rather than the movement.",
  "以毫米调整基座坐标中的 TCP 位置。relative=true 为增量；false 为绝对坐标。当前逆运动学是简化的位置逆解，从当前关节角局部迭代，不锁定朝向、不检查碰撞。求解失败不代表全局不可达，可改用关节预览和移动调整构型后再试。默认随结果附外部与腕部新图，observe=false 可关闭。":
    "Move TCP in the base frame in millimeters. relative=true means an offset; false means absolute coordinates. This is a simplified local position IK from current angles: no orientation lock or collision check. Failure does not prove global unreachability; preview and move joints to adjust configuration before retrying. Fresh external and wrist images are attached by default; observe=false disables them.",
  "设置夹爪 ID6 开口角与功率上限。0°闭合；30°约71mm、60°约129mm，参考测量深度不同，按画面选择开口；90°为机械行程上限。power_mw 单位mW，0使用舵机默认，不是力度百分比。返回实际角度与功率，默认附外部和腕部新图；observe=false 可关闭。":
    "Set gripper ID6 opening angle and power limit. 0° closed; approximately 71 mm at 30° and 129 mm at 60°, measured at different depths. Choose opening from images; 90° is the mechanical limit. power_mw uses mW, with 0 for servo default; it is not force percent. Returns actual angle and power. Attaches fresh external and wrist images by default; observe=false disables them.",
  "统一的前往/返回工作位工具：[0,0,-60,-60,0,0]°（模型坐标，J4 原始舵机 +60°），夹爪默认闭合。六轴和夹爪通过同一条同步指令执行，返回实际反馈；默认随结果附外部与腕部新图，observe=false 可关闭。":
    "Go or return to work pose: [0,0,-60,-60,0,0]° in model coordinates (raw servo J4 +60°), with gripper closed by default. Six axes and gripper use one synchronous command. Returns actual feedback, with fresh external and wrist images by default; observe=false disables them.",
  "一次执行已确定、无需中途看图再决策的动作序列，例如确认位置后夹紧→抬升，或释放→撤离→回工作位。需要重新看图检查位置和姿态的接近动作与夹取闭合分开。按顺序执行同一套运动方法，失败时返回已完成步骤，不重放前面的动作；默认只在整组结束后附外部与腕部新图，observe=false 可关闭。":
    "Execute a determined action sequence without intermediate visual decisions: for example close then lift, or release then retreat then return to work pose. Separate approaches requiring a new visual check from gripper closure. Executes shared motion methods in order; failure returns completed steps without replaying earlier actions. Fresh external and wrist images are attached once at the end by default; observe=false disables them.",
  "正解需要 6 个有限弧度值": "FK requires six finite angles in radians",
  协议参数长度超过一字节范围:
    "Protocol parameters exceed the one-byte length limit",
  "同步指令的角度、ID 与功率条目数量不一致":
    "Synchronous command angle, ID, and power counts differ",
  "舵机角度超出协议 32 位有符号数范围":
    "Servo angle exceeds the signed 32-bit protocol range",
  串口已经打开: "Serial port is already open",
  "Web Serial 不可用，请使用 HTTPS / localhost 下的 Chrome 或 Edge":
    "Web Serial is unavailable. Use Chrome or Edge over HTTPS / localhost",
  "{0} 串口已断开": "{0} serial port disconnected",
  "{0} · 已中断，待核对": "{0} · Interrupted; check state",
  "{0} · 已停止": "{0} · Stopped",
  "{0} · 失败": "{0} · Failed",
};
