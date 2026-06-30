# Hardware

本目录用于存放 Star Arm 102 的硬件相关资料，方便大家查阅零件清单、查看 CAD 图纸以及参考装配说明。



## 目录说明

- [parts/](./parts/): 各零件STEP 与 BOM
- [cad/](./cad/README.md): CAD工程图纸
- [assembly/](./assembly/README.md): 装配说明与装配参考资料

## 入口指引

### 1. 零件清单

如果你想了解这台机械臂需要哪些零件、每种零件需要多少数量，可以先查看 `Star Arm 102-LD_BOM.xlsx`。下面整理了两份便于在 GitHub 直接浏览的清单：主体物料表与配件清单表。

#### 主体物料表

| 序号 | 物料名称 | 备注 | 数量 |
|:---|:---|:---|:---|
| 1 | 3D打印件（star102底座下） | - | 1 |
| 2 | 3D打印件（star102底座上） | - | 1 |
| 3 | 3D打印件（star102_link1） | - | 1 |
| 4 | 3D打印件（star102_link2） | - | 1 |
| 5 | 3D打印件（star102_link3） | - | 1 |
| 6 | 3D打印件（star102_link4） | - | 1 |
| 7 | 3D打印件（star102_link5） | - | 1 |
| 8 | 3D打印件（star102_link6手柄） | - | 1 |
| 9 | 3D打印件（star102_手柄） | - | 1 |
| 10 | 3D打印件（star102_指环左） | - | 1 |
| 11 | 3D打印件（star102_指环右） | - | 1 |
| 12 | PCBD | UC-01 0.75平方5.5x2.1母头 | 1 |
| 13 | 线材 | L=120 mm 黑色编织线 | 5 |
| 14 | 线材 | L=200 mm 黑色编织线 | 2 |
| 15 | 螺丝 | HSCS M3*10 12.9级内六角圆柱头螺钉 | 1 |
| 16 | 螺丝 | M3*22 黑色内六角 | 4 |
| 17 | 螺丝 | M3*8加硬包黑十字槽螺杆 | 1 |
| 18 | 螺丝 | PB2.0*5 自攻十字槽加硬包黑沉头螺杆 | 39 |
| 19 | 螺丝 | M2*4.5 预点胶十字槽螺杆黑色沉头 | 35 |
| 20 | 螺丝 | M2*8 黑色内六角 | 16 |
| 21 | 螺丝 | M3*8自攻十字槽螺杆 | 2 |
| 22 | 螺母 | M3防松螺母 黑色 | 5 |
| 23 | 垫片 | M3不锈钢 | 1 |
| 24 | RA8-U01H-M | - | 4 |
| 25 | RA8-U02H-M | - | 1 |
| 26 | RA8-U03H-M | - | 2 |

#### 配件清单表

| 序号 | 物料名称 | 备注 | 数量 |
|:---|:---|:---|:---|
| 27 | 螺丝胶 | - | 1 |
| 28 | 木工夹 | - | 2 |
| 29 | 备用PCBD | UC-01 | 1 |
| 30 | 备用电源线 | XT30 电源转接线, 0.25米 | 1 |
| 31 | 数据线 | USB转type c数据线 | 1 |
| 32 | 线材 | PH-3Y 双头反向60芯 0.08 黑色硅胶排线 L=200 mm 黑色编织线 | 1 |
| 33 | 7号螺丝套装 | M2*8 黑色内六角 8pcs | 1 |
| 34 | 8号螺丝套装 | M2*4.5 预点胶十字槽螺杆黑色沉头 16pcs | 1 |
| 35 | 9号螺丝套装 | PB2.0*5 自攻十字槽加硬包黑沉头螺杆 16pcs | 1 |
| 36 | 鼠标垫 | - | 1 |

- [MakerWorld Models](https://makerworld.com.cn/zh/models/2366043-xing-bi-102-ld?from=search#profileId-2682765): 此处可以下载Star Arm 102-LD的3D打印文件，自行替换或者组装机械臂

### 2. 开放 STEP 文件

`parts/` 目录中提供了部分可编辑 STEP 文件，方便用户根据自己的安装场景、底座形状或手型进行二次修改。用户可以使用常见 CAD 软件打开这些文件，调整后再导出 STL 或其他格式进行 3D 打印。

| 文件 | 说明 | 适用场景 |
|:---|:---|:---|
| [First-Person_Camera_Mount_Base.STEP](./parts/First-Person_Camera_Mount_Base.STEP) | 第一视角相机固定底座 | 安装第一视角相机，可根据相机尺寸或安装位置调整 |
| [First-Person_Camera_Mount_Top_Cover.STEP](./parts/First-Person_Camera_Mount_Top_Cover.STEP) | 第一视角相机固定上盖 | 与相机固定底座配合使用，用于固定相机 |
| [StarArm102_Base_Bottom.STEP](./parts/StarArm102_Base_Bottom.STEP) | 机械臂底座下半部分 | 可根据实际安装方式修改底部结构 |
| [StarArm102_Base_Top.STEP](./parts/StarArm102_Base_Top.STEP) | 机械臂底座上半部分 | 可装配到修改后的StarArm102_Base_Bottom上检查是否有干涉 |
| [StarArm102_Base_Support.STEP](./parts/StarArm102_Base_Support.STEP) | 机械臂底托 | 用于归位时放置手柄，可自行打印 |
| [StarArm102_Handle.STEP](./parts/StarArm102_Handle.STEP) | 手柄 | 可根据用户手掌大小和握持习惯微调 |
| [StarArm102_Finger_Ring_Left.STEP](./parts/StarArm102_Finger_Ring_Left.STEP) | 左指环 | 可根据左手手指尺寸调整佩戴手感 |
| [StarArm102_Finger_Ring_Right.STEP](./parts/StarArm102_Finger_Ring_Right.STEP) | 右指环 | 可根据右手手指尺寸调整佩戴手感 |

> 建议在修改前保留原始文件备份；如果调整了相机固定件、底座或手柄结构，请在打印前检查装配间隙、螺丝孔位和运动空间，避免与机械臂运动范围发生干涉。


### 3. CAD 与工程图纸

如果你想查看整机结构、核对尺寸，可以进入 [cad/README.md](./cad/README.md)。


### 4. 装配说明

装配说明正在制作中，后续可以自购买散件套装，组装自己的机械臂。


