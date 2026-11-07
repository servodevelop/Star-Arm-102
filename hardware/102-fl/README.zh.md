# Star Arm 102-FL 硬件

[← 硬件资源](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

<p align="center">
  <a href="images/102-fl-diy-kit-main-image-01.webp"><img src="images/102-fl-diy-kit-main-image-01.webp" alt="Star Arm 102-FL DIY 套件" width="15%"></a>
  <a href="images/102-fl-main-image-02.webp"><img src="images/102-fl-main-image-02.webp" alt="Star Arm 102-FL 产品图片 2" width="15%"></a>
  <a href="images/102-fl-main-image-03.webp"><img src="images/102-fl-main-image-03.webp" alt="Star Arm 102-FL 产品图片 3" width="15%"></a>
  <a href="images/102-fl-main-image-04.webp"><img src="images/102-fl-main-image-04.webp" alt="Star Arm 102-FL 产品图片 4" width="15%"></a>
  <a href="images/102-fl-main-image-05.webp"><img src="images/102-fl-main-image-05.webp" alt="Star Arm 102-FL 产品图片 5" width="15%"></a>
  <a href="images/102-fl-main-image-06.webp"><img src="images/102-fl-main-image-06.webp" alt="Star Arm 102-FL 产品图片 6" width="15%"></a>
</p>

**目录：**

- [📂 资源目录](#resources)
- [📋 标准夹爪版物料清单](#bill-of-materials)
- [🖐️ 柔性夹爪零件清单](#flexible-gripper-bom)
- [📷 摄像头模组（选配）](#camera-module-bom)
- [🔢 关节与舵机 ID 对照](../../docs/specifications.zh.md#joint-ids-and-names)

<a id="resources"></a>

## 资源目录

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| [DIY 装配](../../docs/diy-assembly/README.zh.md#102-fl) | 主体机械臂装配视频 | ✅ 已完成 |
| [step/](step/) | 整机 STEP 模型：[标准夹爪版](step/star-arm-102-fl-assembly-export-2026-11-01.step) · [柔性夹爪版](step/star-arm-102-fl-flexible-gripper-assembly-export-2026-11-01.step) | ✅ 已完成 |
| [3mf/](3mf/) | [下载 3MF 打印文件（2026-08-07）](3mf/star-arm-102-fl-2026-08-07.3mf?raw=true) | ✅ 已提供 |
| [drawings/](drawings/) | PDF／DWG 图纸 | ✅ 已完成 |
| [URDF 模型](urdf/) | [下载完整 URDF 包](urdf/downloads/star-arm-102-fl-urdf-2026-10-23.zip?raw=true) · [浏览源码](urdf/stararm102-fl-description/) | ✅ 已完成 |

<a id="bill-of-materials"></a>

## 标准夹爪版物料清单

下表列出 102-FL **标准夹爪版的 29 项装机物料**；无图片的条目标为待补。

打印件按品名识别。装配树中的英文名称（如 `Link 1`）与英文版 BOM 的品名对应，中文版对应“连杆 1”。

打印件的“型号／规格／零件标识”栏填写零件标识。例如，“连杆 1”的零件标识为 `star-arm-102-link1`；`star-arm-102-` 前缀用于识别所属产品系列。

[3MF 打印文件（2026-08-07）](3mf/star-arm-102-fl-2026-08-07.3mf?raw=true)已放在 [3mf/](3mf/)。本表不记录打印参数；层高、壁数和填充率应根据打印机与耗材选择。

打印件图片由对应的 STEP 模型渲染生成。紧固件图片为 AI 生成的外观示意图，规格以表格文字为准；点击图片可放大查看。

<table width="100%">
<thead>
<tr>
  <th width="5%">序号</th>
  <th width="17%">品名</th>
  <th width="24%">型号／规格／零件标识</th>
  <th width="11%">图片</th>
  <th width="37%">描述</th>
  <th width="6%">数量</th>
</tr>
</thead>
<tbody>
<tr>
  <td align="center">1</td>
  <td>UART 总线舵机</td>
  <td>RX8-U48H-M</td>
  <td align="center"><a href="images/rx8-u48h-m.webp"><img src="images/rx8-u48h-m.webp" alt="RX8-U48H-M" width="90"></a></td>
  <td>12V；48kg-cm；70rpm；双轴；无刷电机；12 位磁性绝对值编码器；25T</td>
  <td align="center">2</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>UART 总线舵机</td>
  <td>RA8-U35H-M</td>
  <td align="center"><a href="images/ra8-u35h-m.png"><img src="images/ra8-u35h-m.png" alt="RA8-U35H-M" width="90"></a></td>
  <td>12V；35kg-cm；55rpm；双轴；有刷铁芯电机；12 位磁性绝对值编码器；25T</td>
  <td align="center">3</td>
</tr>
<tr>
  <td align="center">3</td>
  <td>UART 总线舵机</td>
  <td>RA8-U35H-M-C047</td>
  <td align="center"><a href="images/ra8-u35h-m-c047.webp"><img src="images/ra8-u35h-m-c047.webp" alt="RA8-U35H-M-C047" width="90"></a></td>
  <td>12V；35kg-cm；55rpm；双轴款壳体（平面下盖，无后输出轴）；有刷铁芯电机；12 位磁性绝对值编码器；25T</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">4</td>
  <td>UART 总线舵机</td>
  <td>RA8-U27H-M-C005</td>
  <td align="center"><a href="images/ra8-u27h-m-c005.webp"><img src="images/ra8-u27h-m-c005.webp" alt="RA8-U27H-M-C005" width="90"></a></td>
  <td>12V；25kg-cm；72rpm；双轴款壳体（平面下盖，无后输出轴）；有刷铁芯电机；12 位磁性绝对值编码器；D 型轴</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">5</td>
  <td>基座底板</td>
  <td>star-arm-102-base-bottom</td>
  <td align="center"><a href="images/star-arm-102-base-bottom.png"><img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">6</td>
  <td>基座顶板</td>
  <td>star-arm-102-base-top</td>
  <td align="center"><a href="images/star-arm-102-base-top.png"><img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">7</td>
  <td>连杆 1</td>
  <td>star-arm-102-link1</td>
  <td align="center"><a href="images/star-arm-102-link1.png"><img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">8</td>
  <td>连杆 2</td>
  <td>star-arm-102-link2</td>
  <td align="center"><a href="images/star-arm-102-link2.png"><img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">9</td>
  <td>连杆 3</td>
  <td>star-arm-102-link3</td>
  <td align="center"><a href="images/star-arm-102-link3.png"><img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"></a></td>
  <td>象牙白＋黑色，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">10</td>
  <td>连杆 4</td>
  <td>star-arm-102-link4</td>
  <td align="center"><a href="images/star-arm-102-link4.png"><img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">11</td>
  <td>连杆 5</td>
  <td>star-arm-102-link5</td>
  <td align="center"><a href="images/star-arm-102-link5.png"><img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">12</td>
  <td>连杆 6</td>
  <td>star-arm-102-link6</td>
  <td align="center"><a href="images/star-arm-102-link6.png"><img src="images/star-arm-102-link6.png" alt="star-arm-102-link6" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">13</td>
  <td>夹爪主体</td>
  <td>star-arm-102-gripper-body</td>
  <td align="center"><a href="images/star-arm-102-gripper-body.png"><img src="images/star-arm-102-gripper-body.png" alt="star-arm-102-gripper-body" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">14</td>
  <td>左指尖</td>
  <td>star-arm-102-fingertip-left</td>
  <td align="center"><a href="images/star-arm-102-fingertip-left.png"><img src="images/star-arm-102-fingertip-left.png" alt="star-arm-102-fingertip-left" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">15</td>
  <td>右指尖</td>
  <td>star-arm-102-fingertip-right</td>
  <td align="center"><a href="images/star-arm-102-fingertip-right.png"><img src="images/star-arm-102-fingertip-right.png" alt="star-arm-102-fingertip-right" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">16</td>
  <td>推力滚针轴承</td>
  <td>AXK2035+2AS</td>
  <td align="center"><a href="../../media/axk2035-2as-bearing.png"><img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS 滚针轴承" width="90"></a></td>
  <td>内径 20 mm，外径 35 mm，厚度 4 mm</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">17</td>
  <td>TTL/USB 舵机转接板</td>
  <td>UC-01</td>
  <td align="center"><a href="../../media/uc-01-primary.webp"><img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"></a></td>
  <td>USB Type-C；半双工／全双工转换；3.3 V／5 V TTL 电平可切换；输入电压 6–15 V；2 个 PH2.0 舵机接口；反接保护<br>XT30 接口</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">18</td>
  <td>舵机连接线</td>
  <td>PH2.0 (PH-3Y)<br>120 mm</td>
  <td align="center"><a href="../../media/ph-3y-servo-cable-120mm-thumbnail.png"><img src="../../media/ph-3y-servo-cable-120mm-thumbnail.png" alt="PH2.0 120 mm 舵机连接线" width="90"></a></td>
  <td>黑色硅胶绝缘排线，外覆黑色编织护套；两端线序反向；每根导体 60 × Ø0.08 mm（约 22 AWG）</td>
  <td align="center">4</td>
</tr>
<tr>
  <td align="center">19</td>
  <td>舵机连接线</td>
  <td>PH2.0 (PH-3Y)<br>200 mm</td>
  <td align="center"><a href="../../media/ph-3y-servo-cable-200mm-thumbnail.png"><img src="../../media/ph-3y-servo-cable-200mm-thumbnail.png" alt="PH2.0 200 mm 舵机连接线" width="90"></a></td>
  <td>黑色硅胶绝缘排线，外覆黑色编织护套；两端线序反向；每根导体 60 × Ø0.08 mm（约 22 AWG）</td>
  <td align="center">3</td>
</tr>
<tr>
  <td align="center">20</td>
  <td>内六角圆柱头螺钉</td>
  <td>M3 × 22</td>
  <td align="center"><a href="../../media/fasteners/m3-22-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-22-socket-head-cap-screw.png" alt="M3 × 22 内六角圆柱头螺钉示意图" width="90"></a></td>
  <td>黑色表面</td>
  <td align="center">4</td>
</tr>
<tr>
  <td align="center">21</td>
  <td>内六角圆柱头螺钉</td>
  <td>M3 × 10</td>
  <td align="center"><a href="../../media/fasteners/m3-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-10-socket-head-cap-screw.png" alt="M3 × 10 内六角圆柱头螺钉示意图" width="90"></a></td>
  <td>黑色表面，强度等级 12.9</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">22</td>
  <td>内六角圆柱头螺钉</td>
  <td>M2 × 10</td>
  <td align="center"><a href="../../media/fasteners/m2-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-10-socket-head-cap-screw.png" alt="M2 × 10 内六角圆柱头螺钉示意图" width="90"></a></td>
  <td>黑色表面</td>
  <td align="center">8</td>
</tr>
<tr>
  <td align="center">23</td>
  <td>内六角圆柱头螺钉</td>
  <td>M2 × 8</td>
  <td align="center"><a href="../../media/fasteners/m2-8-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-8-socket-head-cap-screw.png" alt="M2 × 8 内六角圆柱头螺钉示意图" width="90"></a></td>
  <td>黑色表面</td>
  <td align="center">16</td>
</tr>
<tr>
  <td align="center">24</td>
  <td>十字槽沉头自攻螺钉</td>
  <td>3 × 12 mm</td>
  <td align="center"><a href="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png"><img src="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png" alt="3 × 12 mm 十字槽沉头自攻螺钉示意图" width="90"></a></td>
  <td>银色表面，尖尾</td>
  <td align="center">2</td>
</tr>
<tr>
  <td align="center">25</td>
  <td>十字槽盘头机牙螺钉</td>
  <td>M3 × 10</td>
  <td align="center"><a href="../../media/fasteners/m3-10-phillips-pan-head-screw.png"><img src="../../media/fasteners/m3-10-phillips-pan-head-screw.png" alt="M3 × 10 十字槽盘头机牙螺钉示意图" width="90"></a></td>
  <td>黑色表面，加硬</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">26</td>
  <td>十字槽盘头自攻螺钉</td>
  <td>2 × 5 mm</td>
  <td align="center"><a href="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png"><img src="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png" alt="2 × 5 mm 十字槽盘头自攻螺钉示意图" width="90"></a></td>
  <td>黑色表面，加硬，平尾</td>
  <td align="center">30</td>
</tr>
<tr>
  <td align="center">27</td>
  <td>十字槽盘头机牙螺钉</td>
  <td>M2 × 4.5</td>
  <td align="center"><a href="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png"><img src="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png" alt="M2 × 4.5 十字槽盘头机牙螺钉示意图" width="90"></a></td>
  <td>黑色表面；靠近末端的约 2/3 螺纹段预涂蓝色锁固胶</td>
  <td align="center">47</td>
</tr>
<tr>
  <td align="center">28</td>
  <td>螺母</td>
  <td>M3</td>
  <td align="center"><a href="../../media/fasteners/m3-nut.png"><img src="../../media/fasteners/m3-nut.png" alt="M3 螺母示意图" width="90"></a></td>
  <td>黑色表面</td>
  <td align="center">6</td>
</tr>
<tr>
  <td align="center">29</td>
  <td>垫片</td>
  <td>M3（3 × 6 × 0.5 mm）</td>
  <td align="center"><a href="../../media/fasteners/m3-6-0-5-stainless-washer.png"><img src="../../media/fasteners/m3-6-0-5-stainless-washer.png" alt="M3（3 × 6 × 0.5 mm） 垫片示意图" width="90"></a></td>
  <td>不锈钢</td>
  <td align="center">2</td>
</tr>
</tbody>
</table>
<a id="flexible-gripper-bom"></a>

## 柔性夹爪零件清单

以下为柔性夹爪的 **7 件机械零件**，用于替换标准夹爪的主体及左右指尖（上表第 13–15 项）。共用舵机不重复计入；安装紧固件的规格与用量待核对，因此本表不是完整改装采购清单。每项数量按一套柔性夹爪计算。

图片取自[柔性夹爪版整机 STEP](step/star-arm-102-fl-flexible-gripper-assembly-export-2026-11-01.step)。“型号／规格／零件标识”栏采用 STEP 中的英文零件名称，便于在装配树中定位。主体、连杆和齿轮为象牙白 PLA 3D 打印件，左右指尖为白色 TPU 90A 3D 打印件。左右连杆几何相同，按安装位置区分，各需 1 件。

零件模型与图纸见[柔性夹爪目录](../flexible-gripper/)；3MF 打印文件待提供。

<table width="100%">
<thead>
<tr>
  <th width="5%">序号</th>
  <th width="17%">品名</th>
  <th width="24%">型号／规格／零件标识</th>
  <th width="11%">图片</th>
  <th width="37%">描述</th>
  <th width="6%">数量</th>
</tr>
</thead>
<tbody>
<tr>
  <td align="center">1</td>
  <td>柔性夹爪主体</td>
  <td>Flexible Gripper Body</td>
  <td align="center"><a href="images/flexible-gripper-body.png"><img src="images/flexible-gripper-body.png" alt="柔性夹爪主体" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>柔性夹爪左连杆</td>
  <td>Flexible Gripper Link Left</td>
  <td align="center"><a href="images/flexible-gripper-link-left.png"><img src="images/flexible-gripper-link-left.png" alt="柔性夹爪左连杆" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">3</td>
  <td>柔性夹爪右连杆</td>
  <td>Flexible Gripper Link Right</td>
  <td align="center"><a href="images/flexible-gripper-link-right.png"><img src="images/flexible-gripper-link-right.png" alt="柔性夹爪右连杆" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">4</td>
  <td>柔性夹爪左齿轮</td>
  <td>Flexible Gripper Gear Left</td>
  <td align="center"><a href="images/flexible-gripper-gear-left.png"><img src="images/flexible-gripper-gear-left.png" alt="柔性夹爪左齿轮" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">5</td>
  <td>柔性夹爪右齿轮</td>
  <td>Flexible Gripper Gear Right</td>
  <td align="center"><a href="images/flexible-gripper-gear-right.png"><img src="images/flexible-gripper-gear-right.png" alt="柔性夹爪右齿轮" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">6</td>
  <td>柔性夹爪左指尖</td>
  <td>Flexible Gripper Fingertip Left</td>
  <td align="center"><a href="images/flexible-gripper-fingertip-left.png"><img src="images/flexible-gripper-fingertip-left.png" alt="柔性夹爪左指尖" width="90"></a></td>
  <td>白色，TPU 90A 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">7</td>
  <td>柔性夹爪右指尖</td>
  <td>Flexible Gripper Fingertip Right</td>
  <td align="center"><a href="images/flexible-gripper-fingertip-right.png"><img src="images/flexible-gripper-fingertip-right.png" alt="柔性夹爪右指尖" width="90"></a></td>
  <td>白色，TPU 90A 3D 打印件</td>
  <td align="center">1</td>
</tr>
</tbody>
</table>
<a id="camera-module-bom"></a>

## 摄像头模组（选配）

**选配，不计入标准夹爪版的 29 项装机物料。** 以下为安装在夹爪上方的一套第一视角摄像头模组，每项各需 1 件。摄像头参数依据 HQ-1080KDT-01 规格书 V01；图片为 STEP 外形参考，实际外观以实物为准。安装线材及紧固件待核对。

1080p／60fps 为 MJPG 输出模式；YUV 在 1920 × 1080 下为 5fps。规格书标注物距为 70cm 至无穷远，夹爪近距离拍摄需确认成像效果；100° 视场角未注明水平、垂直或对角线方向。

第三视角桌面摄像头底座属于另一种安装方式，不计入本表；相关资源见[摄像头模组目录](../camera-module/)。

<table width="100%">
<thead>
<tr>
  <th width="5%">序号</th>
  <th width="17%">品名</th>
  <th width="24%">型号／规格／零件标识</th>
  <th width="11%">图片</th>
  <th width="37%">描述</th>
  <th width="6%">数量</th>
</tr>
</thead>
<tbody>
<tr>
  <td align="center">1</td>
  <td>第一视角摄像头底座（卡扣式）</td>
  <td>first-person-camera-base-snap-fit</td>
  <td align="center"><a href="images/first-person-camera-base.png"><img src="images/first-person-camera-base.png" alt="第一视角摄像头底座（卡扣式）" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">2</td>
  <td>第一视角摄像头盖（卡扣式）</td>
  <td>first-person-camera-cover-snap-fit</td>
  <td align="center"><a href="images/first-person-camera-cover.png"><img src="images/first-person-camera-cover.png" alt="第一视角摄像头盖（卡扣式）" width="90"></a></td>
  <td>象牙白，PLA 3D 打印件</td>
  <td align="center">1</td>
</tr>
<tr>
  <td align="center">3</td>
  <td>USB 摄像头模组</td>
  <td>HQ-1080KDT-01</td>
  <td align="center"><a href="images/first-person-camera-module.png"><img src="images/first-person-camera-module.png" alt="HQ-1080KDT-01 USB 摄像头模组（STEP 外形参考）" width="90"></a></td>
  <td>200 万像素彩色 CMOS；1920 × 1080 @ 60fps（MJPG）；USB 2.0；5V USB 供电；视场角 100°；模组尺寸 32 × 32 × 18 mm</td>
  <td align="center">1</td>
</tr>
</tbody>
</table>
发现资料错误或需要帮助？请通过 [Support 支持中心](https://fashionstar.com.hk/support/) 联系我们，并注明型号及对应文件或条目。
