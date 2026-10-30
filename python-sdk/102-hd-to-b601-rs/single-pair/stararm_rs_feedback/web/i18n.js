// Original interface translations. Raw device logs remain verbatim.
export const messages = {
  "Star Arm 102 — 工作台": "Star Arm 102 — Workbench",
  "Star Arm 102 工作台": "Star Arm 102 workbench",
  "工作区导航": "Workspace navigation",
  "工作台": "Workbench",
  "反馈调校": "Feedback tuning",
  "运行日志": "Session logs",
  "连接中": "Connecting",
  "实时工作台": "Live workbench",
  "力反馈工作台": "Force feedback",
  "日志回放": "Replay logs",
  "仅监测": "Monitor only",
  "启动反馈": "Start feedback",
  "正常停止会话": "Stop session normally",
  "停止运行": "Stop session",
  "网页已打开，尚未连接机械臂。启动前请退出终端中已有的遥操作程序。": "Workbench ready  No robot connected  Exit any terminal teleoperation session before starting",
  "收起提示": "Dismiss notice",
  "会话概览": "Session overview",
  "会话状态": "Session",
  "未启动": "Idle",
  "本地设备": "Local devices",
  "Leader 阻尼": "Leader damping",
  " / 6 轴": " / 6 axes",
  "等待反馈数据": "Waiting for feedback",
  "峰值扭矩": "Peak torque",
  "RS 电机反馈值": "RS motor telemetry",
  "数据时效": "Data age",
  "参数尚未应用": "Settings not applied",
  "从臂姿态": "Follower pose",
  "等待数据": "Waiting for data",
  "受力显示数据": "Torque display source",
  "电机扭矩": "Motor torque",
  "剩余力矩": "Residual torque",
  "显示量程": "Display range",
  "受力颜色量程": "Torque color range",
  "6 自由度 + 夹爪": "6 axes + gripper",
  "正在加载模型": "Loading model",
  "恢复视角": "Reset view",
  "显示关节坐标轴": "Show joint axes",
  "显示或隐藏图上受力标注": "Show or hide torque annotations",
  "轴": "Axes",
  "标注": "Labels",
  "模型关节受力标注": "Joint torque annotations",
  "等待关节数据": "Waiting for joint data",
  "拖动旋转  滚轮缩放": "Drag to orbit  Scroll to zoom",
  "扭矩幅值": "Torque magnitude",
  "颜色仅表示量程占比": "Colors show a fraction of the display range",
  "电机扭矩含重力与运动影响  非末端接触力": "Motor torque includes gravity and motion  Not end effector contact force",
  "模型残差含摩擦与建模误差  模型无效时不显示数值": "Residual includes friction and model error  Invalid values are hidden",
  "关节状态": "Joint telemetry",
  "关节": "Joint",
  "角度": "Angle",
  "电流": "Current",
  "模式 / mW": "Mode / mW",
  "诊断详情": "Diagnostics",
  "温度": "Temperature",
  "当前死区": "Deadzone",
  "Leader 角度": "Leader angle",
  "等待实时数据": "Waiting for live data",
  "Iq 为滤波电流  功率为 Leader 请求值": "Iq is filtered current  Power is the requested Leader output",
  "扭矩趋势": "Torque history",
  "选择曲线": "Select a curve",
  "最近三十秒七轴扭矩曲线 单位牛米": "Seven joint torque curves over the last 30 seconds in newton meters",
  "过去 30 秒": "Last 30 seconds",
  "阻尼参数": "Damping settings",
  "保存后自动应用  重新初始化约 0.25 秒  HOLD 保持 1500 mW": "Saved settings apply automatically  Reinitialization takes about 0.25 s  HOLD remains at 1500 mW",
  "已保存": "Saved",
  "恢复默认值": "Restore defaults",
  "恢复默认": "Restore defaults",
  "保存并应用": "Save and apply",
  "普通阻尼总上限": "Overall damping cap",
  "400–1500；各轴还受下方上限限制": "400–1500  Per joint caps also apply",
  "只调整普通动态阻尼": "Ordinary dynamic damping only",
  "死区越小越容易触发；满输出标尺越小，同等负载下输出越强。每轴上限填 0 可关闭该轴普通阻尼；J6 保持关闭。": "Smaller deadzones trigger earlier  A smaller full output scale increases damping at the same load  Set a joint cap to 0 to disable ordinary damping  J6 stays disabled",
  "功率上限": "Power cap",
  "基础死区": "Base deadzone",
  "运动余量最大值": "Max motion margin",
  "最大运动余量": "Max motion margin",
  "满输出力矩标尺": "Full output scale",
  "Nm · 超过死区部分": "Nm above deadzone",
  "滤波与响应参数": "Filtering and response",
  "收起响应参数": "Collapse response settings",
  "臂部运动超范围清零已临时关闭，超过旧速度/加速度阈值时继续计算阻尼。J1 按自身回转残差判断；近限位按轴释放。J2/J3 同时处于近零模型无效区时，会暂停 J2–J5 普通阻尼，任一电机角达到 5° 后恢复。故障和通信保护仍生效。": "The former arm speed and acceleration cutoff is disabled  Damping continues above those thresholds  J1 uses its own rotation residual  Each axis releases near its limit  When J2 and J3 are both in the invalid near zero region J2–J5 damping pauses until either reaches 5°  Fault and communication guards remain active",
  "展开日志": "Show logs",
  "收起日志": "Hide logs",
  "会话记录": "Session records",
  "展开查看当前会话的原始输出": "Expand to view the original session output",
  "尚无运行日志": "No session logs yet",
  "日志保存在本机 data/ 目录": "Logs are stored in the local data/ directory",
  "关闭页面不会停止会话  停止运行可能回零或卸力": "Closing this page keeps the session running  Stopping may home or release the arms",
  "底座回转": "Base rotation",
  "肩部俯仰": "Shoulder pitch",
  "肘部俯仰": "Elbow pitch",
  "腕部俯仰": "Wrist pitch",
  "腕部偏转": "Wrist yaw",
  "腕部旋转": "Wrist roll",
  "夹爪": "Gripper",
  "RS iqf 滤波电流，约 2.86 Hz": "RS iqf filtered current at about 2.86 Hz",
  "突出": "Highlight",
  "曲线": "curve",
  "等待": "Waiting",
  "选择颜色量程": "Select color range",
  "未保存": "Unsaved",
  "普通阻尼关闭": "Ordinary damping disabled",
  "力矩滤波时间": "Torque filter time",
  "负载确认时间": "Load confirmation time",
  "输出平滑时间": "Output smoothing time",
  "功率上升速率": "Power rise rate",
  "功率下降速率": "Power fall rate",
  "请检查 ": "Check ",
  " 的范围": " range",
  "总功率上限须为 400–1500 mW": "Overall power cap must be 400–1500 mW",
  "参数已保存，等待控制循环确认生效。": "Settings saved  Waiting for the control loop to confirm",
  "参数已保存，下次启动时生效。": "Settings saved  Applies on the next start",
  "已填入默认值  保存并应用后生效": "Default values loaded  Save and apply to use them",
  "有未保存参数，请先保存或恢复已保存值。": "Unsaved settings  Save or restore the saved values first",
  "正在连接机械臂，请查看运行日志。": "Connecting to the arms  See session logs for progress",
  "已发送正常停止请求，等待回零/卸力清理。": "Normal stop requested  Waiting for homing and release",
  "按运动中剩余力矩更新": "Updating from moving residual torque",
  "按当前剩余力矩更新": "Updating from current residual torque",
  "按夹爪当前电机力矩更新": "Updating from gripper motor torque",
  "近零姿态模型无效": "Model invalid near zero pose",
  "本轴普通阻尼已释放": "Ordinary damping released on this axis",
  "接近本轴软件限位": "Near this axis software limit",
  "主臂缺帧": "Leader feedback gap",
  "普通阻尼已释放": "Ordinary damping released",
  "夹爪普通阻尼已释放": "Gripper damping released",
  "初始化": "Warming up",
  "无需停稳": "No stationary pose required",
  "日志回放 · 非实时": "Log replay · Historical data",
  "实时 CAN": "Live CAN",
  "数据已过期": "Data expired",
  "过期": "Expired",
  "历史请求值": "Historical requests",
  "HOLD · 独立堵转保持": "HOLD · Independent stall holding",
  "反馈输出已启用": "Feedback output enabled",
  "仅监测 · 未发送 Leader 阻尼": "Monitoring · No Leader damping sent",
  "运行中": "Running",
  "正在停止": "Stopping",
  "已结束": "Ended",
  "未知": "Unknown",
  "退出代码": "Exit code",
  "主臂短暂缺帧 · 跟随目标暂停，阻尼按 RS 更新": "Leader feedback gap · Follower targets paused · Damping follows RS telemetry",
  "实时数据已连接": "Live telemetry connected",
  "等待设备数据": "Waiting for devices",
  "本地网页已连接": "Local service connected",
  "已过期": "Expired",
  "已应用": "Applied",
  " · 等待应用": " · Pending",
  " · 启动后应用": " · Applies on start",
  "参数未应用：": "Settings not applied: ",
  "会话已结束（": "Session ended (",
  "），展开日志查看原因。": ")  Open logs for details",
  "网页服务连接中断": "Service disconnected",
  "网页服务暂不可达；此状态不能确认机械臂已停止。": "Local service unavailable  Robot stop cannot be confirmed",
  "等待新鲜设备数据": "Waiting for fresh device data",
  "已退出回放，尚未连接机械臂。": "Replay ended  No robot connected",
  "退出回放": "Exit replay",
  "正在回放 ": "Replaying ",
  "，所有数值为历史数据；旧日志缺少电流时显示“—”。": "  All values are historical  Missing current samples appear as —",
  "历史数据 · 非实时": "Historical data · Not live",
  "回放中": "Replaying",
  "历史日志参数": "Historical settings",
  "历史回放": "Replay",
  "历史采样": "Sample",
  " s 前": " s ago",
  "模型加载失败：": "Model failed to load: ",
  "历史回放 · 非实时受力": "Replay · Historical torque",
  "实时受力 · N·m": "Live torque · N·m",
  "数据过期 · 保留最后姿态": "Data expired · Last pose retained",
  "无效 / 缺失": "Invalid / missing",
  "历史回放，": "Historical replay · ",
  "模型剩余力矩": "Model residual torque",
  "数据过期": "Data expired",
  "暂无有效数据": "No valid data",
  "缺少数据": "Missing data",
  "非实时": "Not live",
  "低": "Low",
  "中": "Medium",
  "高": "High",
  "网页初始化失败：": "Workbench initialization failed: ",
  "界面预览 · 当前为模拟数据，仅用于检查布局与受力变色，未连接机械臂。": "UI preview · Simulated telemetry for layout and torque colors · No hardware connected",
  "界面预览 · 模拟数据，未连接硬件": "UI preview · Simulated data · No hardware connected",
  "界面预览 · 模拟数据": "UI preview · Simulated data",
  "模拟数据 · 非真实日志.csv": "simulated-data.csv",
  "参数字段不完整或包含未知字段": "Missing or unknown settings fields",
  "无效参数版本": "Invalid settings version",
  "总功率上限须为 400–1500 mW 的整数": "Overall power cap must be an integer from 400 to 1500 mW",
  "各轴上限须在 0 到总上限之间，J6 普通阻尼保持 0": "Joint caps must be between 0 and the overall cap  J6 must stay at 0",
  "需要七个值": "Seven values required",
  "J6 参数不可修改": "J6 settings cannot be changed",
  "数值须在 ": "Value must be between ",
  " 到 ": " and ",
  " 之间": " ",
  "参数已被其他页面修改，请刷新后重试": "Settings changed in another page  Refresh and try again",
  "请选择反馈运行或仅监测运行": "Choose feedback or monitor mode",
  "已有网页会话正在运行": "A workbench session is already running",
  "检测到终端遥操作会话 PID ": "Terminal teleoperation session found with PID ",
  "，请先退出旧程序": "  Exit the existing session first",
  "缺少 feedback.rs-dynamic.json": "Missing feedback.rs-dynamic.json",
  "请先停止实时会话，再回放日志": "Stop the live session before replaying logs",
  "data/ 中还没有可回放的动态日志": "No replayable dynamic logs in data/",
  "仅允许本机访问": "Local access only",
  "网页会话已失效，请刷新": "Workbench session expired  Refresh the page",
  "请求来源不匹配": "Request origin mismatch",
  "请求过大或为空": "Request is too large or empty",
  "需要 JSON": "JSON required",
  "无效停止请求": "Invalid stop request",
  "接口不存在": "Endpoint not found",
  "文件不存在": "File not found"
};
const escaped = Object.keys(messages).sort((a,b)=>b.length-a.length).map(s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));
const pattern = new RegExp(escaped.join('|'),'g');
let language = 'zh-CN';
try { if (localStorage.getItem('stararm102.language') === 'en') language = 'en'; } catch {}
export const currentLanguage = () => language;
export function translate(value, locale=language) {
  const text=String(value);
  return locale==='en' ? text.replace(pattern,match=>messages[match]) : text;
}
const texts=new WeakMap(), attributes=new WeakMap();
function excluded(node){return node.parentElement?.closest('script,style,pre,[data-no-i18n]');}
function renderText(node){
  if(excluded(node))return;
  let record=texts.get(node);
  if(!record||node.data!==record.rendered)record={source:node.data};
  const next=translate(record.source);record.rendered=next;texts.set(node,record);
  if(node.data!==next)node.data=next;
}
export function rememberText(element,source){
  if(element.firstChild?.nodeType===3)texts.set(element.firstChild,{source:String(source),rendered:element.firstChild.data});
}
function renderAttributes(element){
  if(element.closest('script,style,pre,[data-no-i18n]'))return;
  let records=attributes.get(element);if(!records){records={};attributes.set(element,records);}
  for(const name of ['aria-label','title','data-tooltip','placeholder']){
    const value=element.getAttribute(name);if(value===null)continue;
    let record=records[name];if(!record||record.rendered!==value)record={source:value};
    const next=translate(record.source);record.rendered=next;records[name]=record;
    if(value!==next)element.setAttribute(name,next);
  }
}
function render(root){
  if(root.nodeType===3){renderText(root);return;}
  if(root.nodeType===1)renderAttributes(root);
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT);
  while(walker.nextNode()){const node=walker.currentNode;if(node.nodeType===3)renderText(node);else renderAttributes(node);}
}
let callback=()=>{};
export function setLanguage(locale){
  language=locale==='en'?'en':'zh-CN';
  try{localStorage.setItem('stararm102.language',language);}catch{}
  document.documentElement.lang=language;render(document.documentElement);
  const button=document.getElementById('languageSwitch');
  if(button){button.setAttribute('aria-label',language==='en'?'切换到中文':'Switch to English');button.setAttribute('aria-pressed',String(language==='en'));}
  callback();
}
export function initLanguage(onChange=()=>{}){
  callback=onChange;
  const observer=new MutationObserver(changes=>{
    for(const change of changes){
      if(change.type==='characterData')renderText(change.target);
      else if(change.type==='attributes')renderAttributes(change.target);
      else change.addedNodes.forEach(render);
    }
  });
  observer.observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['aria-label','title','data-tooltip','placeholder']});
  document.getElementById('languageSwitch').onclick=()=>setLanguage(language==='en'?'zh-CN':'en');
  setLanguage(language);return observer;
}
