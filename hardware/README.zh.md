# Star Arm 102 规格与硬件资源

[← 首页](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

**目录：**

- [🔧 产品规格](#product-specifications)
- [🔢 关节与舵机 ID 对照](../docs/specifications.zh.md#joint-ids-and-names)
- [🛠️ DIY 装配](../docs/diy-assembly/)
- [📂 目录结构](#directory-structure)

按型号查看详情：**[102-LD](102-ld/)** · **[102-HD](102-hd/)** · **[102-FL](102-fl/)**。

配件：**[摄像头模组](camera-module/)** · **[柔性夹爪](flexible-gripper/)**。

<a id="product-specifications"></a>

## 产品规格

| 规格 | Star Arm 102-LD | Star Arm 102-HD | Star Arm 102-FL |
| --- | --- | --- | --- |
| 产品类型 | 示教主臂（Leader Arm） | 姿态保持主臂（Leader Arm） | 执行从臂（Follower Arm） |
| 电源规格 | 12 V / 3 A | 12 V / 5 A | 12 V / 10 A |
| 臂展 | 420mm | 420mm | 420mm |
| 自由度 | 6+1 | 6+1 | 6+1 |
| 负载 | — | — | 500g（建议在 70% 臂展处使用） |
| 重复定位精度／编码器 | 12-bit 磁编码器 | 12-bit 磁编码器 | 2mm |
| 关节运动范围 | 关节 1: ±110°<br>关节 2: 0°–180°<br>关节 3: 0°–270°<br>关节 4: ±90°<br>关节 5: ±65°<br>关节 6: ±150°<br>手柄: 0°–90° | 关节 1: ±110°<br>关节 2: 0°–180°<br>关节 3: 0°–270°<br>关节 4: ±90°<br>关节 5: ±65°<br>关节 6: ±150°<br>手柄: 0°–90° | 关节 1: ±110°<br>关节 2: 0°–180°<br>关节 3: 0°–270°<br>关节 4: ±90°<br>关节 5: ±65°<br>关节 6: ±150°<br>夹爪: 0°–90° |
| 舵机配置 | RA8-U01H-M × 4<br>RA8-U02H-M × 1<br>RA8-U03H-M × 2 | RP8-U45H-M × 4<br>RP8-U45H-M-C029 × 1<br>RP8-U45H-M-C028 × 2 | RA8-U35H-M × 3<br>RX8-U50H-M × 2<br>RA8-U27H-M-C005 × 1<br>RA8-U35H-M-C047 × 1 |
| 本机重量 | 764g | 934g | 865g |
| 通信方式 | UART / UC-01 | UART / UC-01 | UART / UC-01 |
| 工作温度 | 0–40°C | 0–40°C | 0–40°C |

表中的关节 1–6（J1–J6）对应舵机 ID 0–5，手柄／夹爪对应 ID 6；HD 按钮板使用 ID 7。 [关节与舵机 ID 对照](../docs/specifications.zh.md#joint-ids-and-names)。

<a id="directory-structure"></a>

## 目录结构

下方展开 LD 的目录。HD 和 FL 使用相同资源分类，各自提供型号对应文件和页内 BOM。省略具体文件。

```text
hardware/
├── README.md
├── README.zh.md
├── 102-ld/
│   ├── README.md
│   ├── README.zh.md
│   ├── step/
│   │   ├── assembly/
│   │   └── parts/
│   ├── printing/
│   │   ├── star-arm-102-ld-complete-print-project.3mf
│   │   ├── star-arm-102-ld-stl.zip
│   │   ├── stl/
│   │   └── 3mf/
│   ├── drawings/
│   └── robot-description/
│       ├── stararm102_ld_hd_description/
│       └── star-arm-102-ld-hd-urdf.zip
├── 102-hd/
├── 102-fl/
├── camera-module/
└── flexible-gripper/
```

`step/assembly/` 存放 CAD 装配模型；装配、PID 设置与零位校准集中在 [DIY 装配指南](../docs/diy-assembly/README.zh.md)。每个型号均在自身的 robot-description 目录提供 ROS 1 源码与完整 ZIP：[LD](102-ld/robot-description/)、[HD](102-hd/robot-description/)、[FL](102-fl/robot-description/)。LD 与 HD 包含相同模型。

## 许可

硬件许可仍待明确，见 [许可范围](../LICENSE.md)。复制或重命名文件不授予新的许可。
