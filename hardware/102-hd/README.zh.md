# Star Arm 102-HD 硬件

[← 硬件资源](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

<p align="center">
  <a href="images/102-hd-diy-kit-main-image-01.webp"><img src="images/102-hd-diy-kit-main-image-01.webp" alt="Star Arm 102-HD DIY 套件" width="15%"></a>
  <a href="images/102-hd-main-image-02-1.webp"><img src="images/102-hd-main-image-02-1.webp" alt="Star Arm 102-HD 产品图片 2" width="15%"></a>
  <a href="images/102-hd-main-image-04-1.webp"><img src="images/102-hd-main-image-04-1.webp" alt="Star Arm 102-HD 产品图片 3" width="15%"></a>
  <a href="images/102-hd-main-image-05-1.webp"><img src="images/102-hd-main-image-05-1.webp" alt="Star Arm 102-HD 产品图片 4" width="15%"></a>
  <a href="images/102-hd-main-image-06.webp"><img src="images/102-hd-main-image-06.webp" alt="Star Arm 102-HD 产品图片 5" width="15%"></a>
  <a href="images/102-hd-main-image-07.webp"><img src="images/102-hd-main-image-07.webp" alt="Star Arm 102-HD 产品图片 6" width="15%"></a>
</p>

**目录：**

- [📂 资源目录](#resources)
- [📋 物料清单](#bill-of-materials)
- [🔢 关节与舵机 ID 对照](../../docs/specifications.zh.md#joint-ids-and-names)

<a id="resources"></a>

## 资源目录

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| [DIY 装配](../../docs/diy-assembly/README.zh.md#102-hd) | 主体装配视频（按说明替换 HD 舵机）及按钮接线照片 | ✅ 已完成 |
| [step/](step/) | parts/ 零件模型；assembly/ 共用装配模型 | ✅ 已完成 |
| [stl/](stl/) | [下载整套 STL（14 个打印件）](stl/downloads/star-arm-102-hd-stl-2026-10-22.zip?raw=true) · [浏览单个 STL](stl/) | ✅ 已完成 |
| [drawings/](../102-ld/drawings/) | LD/HD 共用主体图纸（PDF／DWG） | ✅ 已完成 |
| [URDF 模型](urdf/) | [下载完整 URDF 包](urdf/downloads/star-arm-102-ld-hd-urdf-2026-10-23.zip?raw=true) · [浏览源码](urdf/stararm102-ld-hd-description/) | ✅ 已完成 |

<a id="bill-of-materials"></a>

## 物料清单

下表列出 102-HD 的 **32 项装机物料**；无图片的条目标为待补。

打印件的“型号／规格”栏填写零件标识，与所提供的 STEP、STL 文件名主体一致（不含扩展名）。全部 14 个打印件（含手柄托）均提供 STEP 和 STL 文件；STL 下载 ZIP 与 stl/ 目录包含相同的 14 个文件。本表不再记录打印参数：请从 [stl/](stl/) 取 STL，按自己的机型与耗材切片，层高、壁数、填充率随机型与材料而定。

打印件图片由对应的 STEP 模型渲染生成。紧固件图片为 AI 生成的外观示意图，规格以表格文字为准；点击图片可放大查看。

| 序号 | 品名 | 型号／规格 | 图片 | 描述 | 数量 |
| :---: | --- | --- | :---: | --- | :---: |
| 1 | UART 总线舵机 | RP8-U45H-M | <img src="images/rp8-u45h-m.webp" alt="RP8-U45H-M" width="90"> | 12V；45kg-cm；118rpm；双轴；空心杯电机；12 位磁性绝对值编码器；25T | 4 |
| 2 | UART 总线舵机 | RP8-U45H-M-C028 | <img src="images/rp8-u45h-m-c028.webp" alt="RP8-U45H-M-C028" width="90"> | 12V；45kg-cm；118rpm；双轴款壳体（平面下盖，无后输出轴）；空心杯电机；12 位磁性绝对值编码器；25T | 2 |
| 3 | UART 总线舵机 | RP8-U45H-M-C029 | <img src="images/rp8-u45h-m-c029.webp" alt="RP8-U45H-M-C029" width="90"> | 12V；45kg-cm；118rpm；双轴款壳体（平面下盖，无后输出轴）；空心杯电机；12 位磁性绝对值编码器；D 型轴 | 1 |
| 4 | 基座底板 | star-arm-102-base-bottom | <a href="images/star-arm-102-base-bottom.png"><img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 5 | 基座顶板 | star-arm-102-base-top | <a href="images/star-arm-102-base-top.png"><img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 6 | 连杆 1 | star-arm-102-link1 | <a href="images/star-arm-102-link1.png"><img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 7 | 连杆 2 | star-arm-102-link2 | <a href="images/star-arm-102-link2.png"><img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 8 | 连杆 3 | star-arm-102-link3 | <a href="images/star-arm-102-link3.png"><img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"></a> | 象牙白＋黑色，PLA 3D 打印件 | 1 |
| 9 | 连杆 4 | star-arm-102-link4 | <a href="images/star-arm-102-link4.png"><img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 10 | 连杆 5 | star-arm-102-link5 | <a href="images/star-arm-102-link5.png"><img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 11 | 连杆 6 | star-arm-102-link6 | <a href="images/star-arm-102-link6.png"><img src="images/star-arm-102-link6.png" alt="star-arm-102-link6" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 12 | 手柄 | star-arm-102-handle | <a href="images/star-arm-102-handle.png"><img src="images/star-arm-102-handle.png" alt="star-arm-102-handle" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 13 | 手柄托 | star-arm-102-handle-rest | <a href="images/star-arm-102-handle-rest.png"><img src="images/star-arm-102-handle-rest.png" alt="手柄托" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 14 | 左指环 | star-arm-102-finger-ring-left | <a href="images/star-arm-102-finger-ring-left.png"><img src="images/star-arm-102-finger-ring-left.png" alt="star-arm-102-finger-ring-left" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 15 | 右指环 | star-arm-102-finger-ring-right | <a href="images/star-arm-102-finger-ring-right.png"><img src="images/star-arm-102-finger-ring-right.png" alt="star-arm-102-finger-ring-right" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 16 | HD 按钮上盖 | hd-button-cover | <a href="images/hd-button-cover.png"><img src="images/hd-button-cover.png" alt="hd-button-cover" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 17 | HD 按钮底座 | hd-button-base | <a href="images/hd-button-base.png"><img src="images/hd-button-base.png" alt="hd-button-base" width="90"></a> | 象牙白，PLA 3D 打印件 | 1 |
| 18 | TTL/USB 舵机转接板 | UC-01 | <img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"> | USB Type-C；半双工／全双工转换；3.3 V／5 V TTL 电平可切换；输入电压 6–15 V；2 个 PH2.0 舵机接口；反接保护<br>XT30 接口 | 1 |
| 19 | 按钮板 | UK-01 | <a href="images/uk-01-board.webp"><img src="images/uk-01-board.webp" alt="UK-01 电路板" width="90"></a> | 带座子 | 1 |
| 20 | 推力滚针轴承 | AXK2035+2AS | <img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS 滚针轴承" width="90"> | 内径 20 mm，外径 35 mm，厚度 4 mm | 1 |
| 21 | 舵机连接线 | PH2.0 (PH-3Y)<br>120 mm | <a href="../../media/ph-3y-servo-cable-120mm.png"><img src="../../media/ph-3y-servo-cable-120mm-thumbnail.png" alt="PH2.0 120 mm 舵机连接线" width="90"></a> | 黑色硅胶绝缘排线，外覆黑色编织护套；两端线序反向；每根导体 60 × Ø0.08 mm（约 22 AWG） | 6 |
| 22 | 舵机连接线 | PH2.0 (PH-3Y)<br>200 mm | <a href="../../media/ph-3y-servo-cable-200mm.png"><img src="../../media/ph-3y-servo-cable-200mm-thumbnail.png" alt="PH2.0 200 mm 舵机连接线" width="90"></a> | 黑色硅胶绝缘排线，外覆黑色编织护套；两端线序反向；每根导体 60 × Ø0.08 mm（约 22 AWG） | 2 |
| 23 | 内六角圆柱头螺钉 | M3 × 22 | <a href="../../media/fasteners/m3-22-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-22-socket-head-cap-screw.png" alt="M3 × 22 内六角圆柱头螺钉示意图" width="90"></a> | 黑色表面 | 4 |
| 24 | 内六角圆柱头螺钉 | M3 × 10 | <a href="../../media/fasteners/m3-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m3-10-socket-head-cap-screw.png" alt="M3 × 10 内六角圆柱头螺钉示意图" width="90"></a> | 黑色表面，强度等级 12.9 | 1 |
| 25 | 内六角圆柱头螺钉 | M2 × 10 | <a href="../../media/fasteners/m2-10-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-10-socket-head-cap-screw.png" alt="M2 × 10 内六角圆柱头螺钉示意图" width="90"></a> | 黑色表面 | 8 |
| 26 | 内六角圆柱头螺钉 | M2 × 8 | <a href="../../media/fasteners/m2-8-socket-head-cap-screw.png"><img src="../../media/fasteners/m2-8-socket-head-cap-screw.png" alt="M2 × 8 内六角圆柱头螺钉示意图" width="90"></a> | 黑色表面 | 8 |
| 27 | 十字槽沉头自攻螺钉 | 3 × 12 mm | <a href="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png"><img src="../../media/fasteners/3-12-phillips-flat-head-self-tapping-screw.png" alt="3 × 12 mm 十字槽沉头自攻螺钉示意图" width="90"></a> | 银色表面，尖尾 | 2 |
| 28 | 十字槽盘头机牙螺钉 | M3 × 10 | <a href="../../media/fasteners/m3-10-phillips-pan-head-screw.png"><img src="../../media/fasteners/m3-10-phillips-pan-head-screw.png" alt="M3 × 10 十字槽盘头机牙螺钉示意图" width="90"></a> | 黑色表面，加硬 | 1 |
| 29 | 十字槽盘头自攻螺钉 | 2 × 5 mm | <a href="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png"><img src="../../media/fasteners/2-5-phillips-pan-head-blunt-point-self-tapping-screw.png" alt="2 × 5 mm 十字槽盘头自攻螺钉示意图" width="90"></a> | 黑色表面，加硬，平尾 | 46 |
| 30 | 十字槽盘头机牙螺钉 | M2 × 4.5 | <a href="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png"><img src="../../media/fasteners/m2-4-5-phillips-pan-head-screw.png" alt="M2 × 4.5 十字槽盘头机牙螺钉示意图" width="90"></a> | 黑色表面；靠近末端的约 2/3 螺纹段预涂蓝色锁固胶 | 35 |
| 31 | 螺母 | M3 | <a href="../../media/fasteners/m3-nut.png"><img src="../../media/fasteners/m3-nut.png" alt="M3 螺母示意图" width="90"></a> | 黑色表面 | 5 |
| 32 | 垫片 | M3（3 × 6 × 0.5 mm） | <a href="../../media/fasteners/m3-6-0-5-stainless-washer.png"><img src="../../media/fasteners/m3-6-0-5-stainless-washer.png" alt="M3（3 × 6 × 0.5 mm） 垫片示意图" width="90"></a> | 不锈钢 | 1 |

发现资料错误或需要帮助？请通过 [Support 支持中心](https://fashionstar.com.hk/support/) 联系我们，并注明型号及对应文件或条目。
