<h1 align="center">🦾 Star Arm 102</h1>

<p align="center">
  <strong>Open-Source 6+1 DOF Robot Arm for LeRobot</strong><br>
  Teleoperate. Learn from demonstrations. Run your first AI task.
</p>

<p align="center">
  <a href="docs/specifications.md"><img src="https://img.shields.io/badge/DOF-6%2B1-16A085?style=flat-square" alt="6 arm joints plus 1 gripper"></a>
  <a href="lerobot/README.md"><img src="https://img.shields.io/badge/LeRobot-Integration-FFD21E?style=flat-square&amp;logo=huggingface&amp;logoColor=FFD21E" alt="LeRobot integration"></a>
  <a href="python-sdk/README.md"><img src="https://img.shields.io/badge/Python-SDK-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python SDK"></a>
  <a href="ros2-humble/README.md"><img src="https://img.shields.io/badge/ROS_2-Humble-22314E?style=flat-square&amp;logo=ros&amp;logoColor=white" alt="ROS 2 Humble"></a>
  <a href="lerobot/examples/act_pick/README.md"><img src="https://img.shields.io/badge/ACT-Pretrained_Model-8B5CF6?style=flat-square" alt="ACT pretrained model"></a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Language-English-8B5CF6?style=flat-square" alt="English"></a>
  <a href="README.zh.md"><img src="https://img.shields.io/badge/语言-简体中文-64748B?style=flat-square" alt="简体中文"></a>
</p>

<p align="center">
  <a href="https://fashionstar.com.hk/">🌐 Official Website</a> ·
  <a href="https://fashionstar.com.hk/robot-arm/star-arm-102">🔭 Series Overview</a> ·
  <a href="#where-to-buy">🛒 Where to Buy</a> ·
  <a href="https://fashionstar.com.hk/support/">💬 Support</a>
</p>

<p align="center">
  <a href="https://fashionstar.com.hk/store/collections/robot-arm/star-arm-102/">
    <img src="media/star-arm-102-hero.jpg" alt="Star Arm 102 robot arm" width="880">
  </a>
</p>

## 📑 Contents

- [📖 Introduction](#introduction)
- [🛒 Where to Buy](#where-to-buy)
- [🚀 Get Started](docs/getting-started.md)
- [🔧 DIY Assembly](docs/diy-assembly/README.md)
- [🌐 Cross-Brand Follower Arm Compatibility](#cross-brand-pairings)
- [🎮 Connect Your Leader to a Virtual Follower](#web-controller)
- [🤖 Run Your First AI Task](#run-your-first-ai-task)
- [⚙️ Hardware Resources](hardware/)
- [🤗 LeRobot Teleoperation & Training](lerobot/README.md)
- [💬 Natural Language Control](integrations/butterfly/README.md)
- [🦾 ROS 2 Humble Applications](ros2-humble/README.md)
- [🐍 Python SDK](python-sdk/README.md)
- [🧰 Control & Configuration Tools](tools/README.md)

[🛠️ Repository structure](#repository-structure) · [🔗 Related Projects](#related-projects)

---

<a id="introduction"></a>

## 📖 Introduction

Star Arm 102 is an open-source robot arm platform developed by **[Fashion Star](https://fashionstar.com.hk/)** for teleoperation, demonstration collection, and LeRobot learning workflows.

- **6+1 DoF, more wrist flexibility** — Six arm joints plus gripper control give you flexible wrist movement and versatile end-effector orientations.
- **Pieper-compliant kinematics** — Three consecutive parallel joint axes enable analytical inverse kinematics.
- **420 mm reach** — Across the LD, HD, and FL models for tabletop manipulation setups.
- **500g working payload** — The 102-FL follower features two high-torque brushless bus servo joints for task execution.
- **Two leader options** — Choose the lightweight 102-LD for free hand-guided teaching, or the pose-holding 102-HD with high-torque coreless bus servos for stable demonstrations.
- **Open-source resources** — STEP models, 3D-printing projects, BOMs, URDF robot descriptions, and control code for learning, building, and customization.
- **Teach by hand. Feel the load.** — Use ROS 2 for hand-guided teaching and feel changes in a supported follower's load through the 102-HD leader.
- **Pretrained ACT task** — Run the supplied block-placement policy on 102-FL without retraining, after completing the specified environment, calibration, and two-camera setup.

<a id="arm-specifications"></a>

## 🔧 Specifications

| Specification | Star Arm 102-LD | Star Arm 102-HD | Star Arm 102-FL |
| --- | --- | --- | --- |
| Arm type | Leader Arm | Pose-holding Leader Arm | Follower Arm |
| Power | 12 V / 3 A | 12 V / 5 A | 12 V / 10 A |
| Reach | 420mm | 420mm | 420mm |
| DoF | 6+1 | 6+1 | 6+1 |
| Payload | — | — | 500g (70% reach recommended) |
| Repeatability / Encoder | 12-bit magnetic encoder | 12-bit magnetic encoder | 2mm |
| Joint Motion Range | Joint 1: ±110°<br>Joint 2: 0°–180°<br>Joint 3: 0°–270°<br>Joint 4: ±90°<br>Joint 5: ±65°<br>Joint 6: ±150°<br>Handle: 0°–90° | Joint 1: ±110°<br>Joint 2: 0°–180°<br>Joint 3: 0°–270°<br>Joint 4: ±90°<br>Joint 5: ±65°<br>Joint 6: ±150°<br>Handle: 0°–90° | Joint 1: ±110°<br>Joint 2: 0°–180°<br>Joint 3: 0°–270°<br>Joint 4: ±90°<br>Joint 5: ±65°<br>Joint 6: ±150°<br>Gripper: 0°–90° |
| Servos | RA8-U01H-M × 4<br>RA8-U02H-M × 1<br>RA8-U03H-M × 2 | RP8-U45H-M × 4<br>RP8-U45H-M-C029 × 1<br>RP8-U45H-M-C028 × 2 | RA8-U35H-M × 3<br>RX8-U50H-M × 2<br>RA8-U27H-M-C005 × 1<br>RA8-U35H-M-C047 × 1 |
| Arm weight | 764g | 934g | 865g |
| Communication | UART / UC-01 | UART / UC-01 | UART / UC-01 |
| Operating Temperature | 0–40°C | 0–40°C | 0–40°C |

<a id="where-to-buy"></a>

## 🛒 Where to Buy

Choose your [Star Arm 102](https://fashionstar.com.hk/store/collections/robot-arm/star-arm-102/) as a **fully assembled arm** to get started sooner, or a **DIY kit** to build it yourself. **In-stock options, ready to ship.** Select your model and configuration on the product page for current availability.

**International store:**

| Product | Shop | Product overview |
| :---: | --- | --- |
| <a href="https://fashionstar.com.hk/store/product/star-arm-102-ld/"><img src="media/102-ld-main-image-01-430x430.webp" alt="Star Arm 102-LD" width="120"></a> | **[Shop&nbsp;102&#8209;LD&nbsp;→](https://fashionstar.com.hk/store/product/star-arm-102-ld/)** | **Lightweight leader arm** for hand-guided teaching, teleoperation, and demonstration collection; torque-disabled joints move freely |
| <a href="https://fashionstar.com.hk/store/product/star-arm-102-hd/"><img src="media/102-hd-main-image-01-2-430x430.webp" alt="Star Arm 102-HD" width="120"></a> | **[Shop&nbsp;102&#8209;HD&nbsp;→](https://fashionstar.com.hk/store/product/star-arm-102-hd/)** | **Pose-holding leader arm** with high-torque coreless bus servos, for stable demonstrations and extended data collection |
| <a href="https://fashionstar.com.hk/store/product/star-arm-102-fl/"><img src="media/102-fl-main-image-01-430x430.webp" alt="Star Arm 102-FL" width="120"></a> | **[Shop&nbsp;102&#8209;FL&nbsp;→](https://fashionstar.com.hk/store/product/star-arm-102-fl/)** | **Follower arm** for teleoperation and policy execution; two high-torque brushless bus servo joints, with a specified 500g working payload |

**Chinese purchase channel:** [Taobao](https://item.taobao.com/item.htm?id=1045277992605&skuId=6239416958433). Select the required model and kit option on the listing.

<a id="cross-brand-pairings"></a>

## 🌐 One Leader, Multiple Robot Platforms

Have a third-party follower? Explore Star Arm 102-LD / HD pairing resources by follower model, then choose the matching Python or LeRobot path.

<!-- reBot image: transparent image extracted with empty alpha margins trimmed from page 1 of Seeed Studio’s product sheet, hosted at https://akizukidenshi.com/goodsaffix/reBot_Arm_B601_DM_Physical_AI_Robotics_Arm.pdf -->
<table>
  <tr>
    <td align="center" width="25%"><a href="integrations/seeed-rebot/README.md"><img src="media/rebot-b601-dm.png" width="273" alt="Seeed reBot B601-DM" height="180"></a></td>
    <td align="center" width="25%"><a href="integrations/yam/README.md"><img src="media/i2rt-yam.png" width="180" alt="I2RT YAM" height="180"></a></td>
    <td align="center" width="25%"><a href="integrations/galaxea-a1/README.md"><img src="media/galaxea-a1.png" width="180" alt="Galaxea A1" height="180"></a></td>
    <td align="center" width="25%"><a href="integrations/lumos-touch/README.md"><img src="media/lumos-touch-front.webp" width="111" alt="Lumos Touch R1" height="180"></a></td>
  </tr>
  <tr>
    <td align="center"><a href="integrations/seeed-rebot/README.md"><strong>Seeed reBot<br>B601-DM &amp; B601-RS →</strong></a></td>
    <td align="center"><a href="integrations/yam/README.md"><strong>YAM →</strong></a></td>
    <td align="center"><a href="integrations/galaxea-a1/README.md"><strong>Galaxea A1 →</strong></a></td>
    <td align="center"><a href="integrations/lumos-touch/README.md"><strong>Lumos Touch →</strong></a></td>
  </tr>
</table>

**[Cross-Brand Compatibility and Evidence →](integrations/compatibility.md)**

<a id="control-and-configuration-tools"></a>
<a id="web-controller"></a>

## 🎮 Connect Your Leader to a Virtual Follower

Start with your Star Arm 102 leader and a virtual follower in the web controller—no physical follower needed for this first experience.

- Get familiar with teleoperation and prepare your setup before connecting a physical follower.
- Follow the Wiki guide for supported leader models, connection steps, and calibration instructions.

[![Star Arm 102 web control interface preview](media/web-control-preview.jpg)](https://fashionstar.com.hk/wiki/software/robot-arm/web-config-tool/)

**[Connect Your Leader →](https://fashionstar.com.hk/wiki/software/robot-arm/web-config-tool/)**

*Interface preview with no hardware connected. Tool versions, downloads, and detailed instructions are maintained in the Wiki.*

<a id="try-your-first-ai-task"></a>
<a id="run-your-first-ai-task"></a>

## 🤖 Run Your First AI Task

Watch Star Arm 102-FL pick up and place a block using our pretrained ACT model. Then try the same task on your own 102-FL—**no retraining required**.

<p align="center">
  <a href="https://github.com/user-attachments/assets/6774384d-f437-4aa9-a364-cd66eba965f7">
    <img src="lerobot/examples/act_pick/docs/images/setup-side.jpg" alt="Side view of the Star Arm 102 ACT workspace — watch the block-placement demo" width="640">
  </a><br>
  <a href="https://github.com/user-attachments/assets/6774384d-f437-4aa9-a364-cd66eba965f7"><strong>▶ Watch the ACT block-placement demo</strong></a>
</p>

**[Try the Pretrained ACT Model →](lerobot/examples/act_pick/README.md)** · **[Collect Data and Train Your Own Task →](lerobot/README.md)**

The guide walks you through the required hardware, two-camera setup, calibration, and workspace preparation.

<a id="teaching-and-force-feedback"></a>

## 🎮 Teach by Hand. Feel the Load.

Explore two ways to interact with your arm through ROS 2:

- **Hand-Guided Teaching** — Guide the arm by hand to demonstrate motion through ROS 2.
- **Force Feedback on 102-HD** — Feel changes in a supported follower's load as changes in resistance at the HD leader, bringing a sense of the remote arm's effort to your hand.

**[Explore ROS 2 Capabilities →](ros2-humble/README.md)**

*Feature-specific setup guides, supported arm combinations, and validation records are being prepared.*

<a id="development-paths"></a>
<a id="documentation-and-support"></a>
<a id="documentation-index"></a>
<a id="choose-your-setup"></a>
<a id="before-connecting"></a>

<a id="repository-structure"></a>

## 🛠️ Repository structure

```text
Star-Arm-102/
├── README.md
├── README.zh.md
├── hardware/
│   ├── 102-ld/                               BOM in each model README; LD layout expanded below
│   │   ├── step/
│   │   │   ├── assembly/
│   │   │   └── parts/
│   │   ├── stl/
│   │   │   ├── downloads/
│   │   │   │   └── star-arm-102-ld-stl.zip
│   │   │   └── *.stl
│   │   ├── drawings/
│   │   └── robot-description/
│   ├── 102-hd/
│   ├── 102-fl/
│   ├── camera-module/
│   └── flexible-gripper/
├── integrations/
│   ├── seeed-rebot/
│   ├── yam/
│   ├── galaxea-a1/
│   ├── lumos-touch/
│   └── butterfly/                            Natural-language control application
├── lerobot/
│   ├── README.md
│   ├── README.zh.md
│   ├── examples/act_pick/
│   ├── lerobot-robot-stararm102/
│   ├── lerobot-teleoperator-stararm102/
│   └── lerobot-stararm102/
├── python-sdk/
├── ros2-humble/
│   └── src/
├── tools/                                    Web control and servo configuration tools
├── docs/                                     Getting started, assembly, and troubleshooting
│   ├── getting-started.md
│   ├── getting-started.zh.md
│   └── diy-assembly/
│       ├── README.md
│       └── README.zh.md
├── media/
├── scripts/
├── tests/
├── .github/
├── AGENTS.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE.md
```

<a id="related-projects"></a>

## 🌐 Related projects

- [Fashion Star UART/RS-485 Bus Servo SDK](https://github.com/servodevelop/servo-uart-rs485-sdk)
- [Fashion Star CAN Bus Servo SDK](https://github.com/servodevelop/servo-canbus-sdk)
- [PiPER-Mate](https://github.com/servodevelop/piper-mate) — A compact leader arm with the AgileX PiPER joint layout, for teleoperating PiPER followers and collecting training data.
- [StarAI Arm](https://github.com/servodevelop/lerobot-starai) — An ALOHA-style arm series pairing a Violin leader with Viola or Cello followers for LeRobot imitation learning and data collection.

Software directories and model release URLs remain available. English is the default entry; existing English and Chinese READMEs maintain matching sections, images, commands, and status. English-only detailed documents remain accessible through their links. The [historical Chinese homepage](README.legacy.zh.md) is retained for reference, not as the current operating guide.

[Changes](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [License scope](LICENSE.md)
