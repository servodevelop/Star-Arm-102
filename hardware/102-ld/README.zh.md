# Star Arm 102-LD 硬件

[← 硬件资源](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

<p align="center">
  <a href="images/102-ld-diy-kit-main-image-01-2.webp"><img src="images/102-ld-diy-kit-main-image-01-2.webp" alt="Star Arm 102-LD DIY 套件" width="15%"></a>
  <a href="images/102-ld-main-image-02.webp"><img src="images/102-ld-main-image-02.webp" alt="Star Arm 102-LD 产品图片 2" width="15%"></a>
  <a href="images/102-ld-main-image-03.webp"><img src="images/102-ld-main-image-03.webp" alt="Star Arm 102-LD 产品图片 3" width="15%"></a>
  <a href="images/102-ld-main-image-04.webp"><img src="images/102-ld-main-image-04.webp" alt="Star Arm 102-LD 产品图片 4" width="15%"></a>
  <a href="images/102-ld-main-image-05.webp"><img src="images/102-ld-main-image-05.webp" alt="Star Arm 102-LD 产品图片 5" width="15%"></a>
  <a href="images/102-ld-main-image-06.webp"><img src="images/102-ld-main-image-06.webp" alt="Star Arm 102-LD 产品图片 6" width="15%"></a>
</p>

**目录：**

- [📂 资源目录](#resources)
- [📋 物料清单](#bill-of-materials)

<a id="resources"></a>

## 资源目录

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| [DIY 装配](../../docs/diy-assembly/README.zh.md#102-ld) | 主体机械臂装配视频 | ✅ 已完成 |
| [step/](step/) | parts/ 零件模型；assembly/ 共用装配模型 | ✅ 已完成 |
| [printing/](printing/) | 3MF 打印项目；STL：[查看零件](printing/stl/) · [下载整套 ZIP](printing/star-arm-102-ld-stl.zip) | ✅ 已完成 |
| [drawings/](drawings/) | PDF／DWG 图纸 | ✅ 已完成 |
| [robot-description/](robot-description/) | URDF 模型：[浏览源码](robot-description/) · [下载 ZIP](robot-description/star-arm-102-ld-hd-urdf.zip) | ✅ 已完成 |

<a id="bill-of-materials"></a>

## 物料清单

下表列出 102-LD 的 **28 项装机物料**；无图片的条目标为待补。

打印件名称与 STEP、STL 及独立 3MF 文件名一致。BOM 中的打印参数仅供参考，尚未完成实物打印验证。

| 序号 | SKU | 名称／型号 | 图片 | 描述 | 数量 |
| :---: | --- | --- | :---: | --- | :---: |
| 1 | 02.06.00000394 | RA8-U01H-M | <img src="images/ra8-u01h-m.webp" alt="RA8-U01H-M" width="90"> | UART 总线舵机/12V/双轴/无电机（无扭矩输出）/12 位磁性绝对值编码器/25T | 4 |
| 2 | 02.06.00000396 | RA8-U02H-M | <img src="images/ra8-u02h-m.webp" alt="RA8-U02H-M" width="90"> | UART 总线舵机/12V/双轴款壳体（平面下盖，无后输出轴）/无电机（无扭矩输出）/12 位磁性绝对值编码器/D 型轴 | 1 |
| 3 | 02.06.00000395 | RA8-U03H-M | <img src="images/ra8-u03h-m.webp" alt="RA8-U03H-M" width="90"> | UART 总线舵机/12V/双轴款壳体（平面下盖，无后输出轴）/无电机（无扭矩输出）/12 位磁性绝对值编码器/25T | 2 |
| 4 | 01.03.03000131 | star-arm-102-base-bottom | <img src="images/star-arm-102-base-bottom.png" alt="star-arm-102-base-bottom" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：15% | 1 |
| 5 |  | star-arm-102-base-top | <img src="images/star-arm-102-base-top.png" alt="star-arm-102-base-top" width="90"> | PLA 3D 打印件（象牙白）；分区域参数，详见 3MF | 1 |
| 6 | 01.03.03000133 | star-arm-102-link1 | <img src="images/star-arm-102-link1.png" alt="star-arm-102-link1" width="90"> | PLA 3D 打印件（象牙白）；壁数：5；填充密度：50% | 1 |
| 7 | 01.03.03000134 | star-arm-102-link2 | <img src="images/star-arm-102-link2.png" alt="star-arm-102-link2" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：10% | 1 |
| 8 | 01.03.03000135 | star-arm-102-link3 | <img src="images/star-arm-102-link3.png" alt="star-arm-102-link3" width="90"> | PLA 3D 打印件（象牙白＋黑色）；分区域参数，详见 3MF | 1 |
| 9 | 01.03.03000136 | star-arm-102-link4 | <img src="images/star-arm-102-link4.png" alt="star-arm-102-link4" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：15% | 1 |
| 10 | 01.03.03000137 | star-arm-102-link5 | <img src="images/star-arm-102-link5.png" alt="star-arm-102-link5" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：15% | 1 |
| 11 | 01.03.03000138 | star-arm-102-link6-handle | <img src="images/star-arm-102-link6-handle.png" alt="star-arm-102-link6-handle" width="90"> | PLA 3D 打印件（象牙白）；壁数：5；填充密度：15% | 1 |
| 12 | 01.03.03000139 | star-arm-102-handle | <img src="images/star-arm-102-handle.png" alt="star-arm-102-handle" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：15% | 1 |
| 13 | 01.03.03000140 | star-arm-102-finger-ring-left | <img src="images/star-arm-102-finger-ring-left.png" alt="star-arm-102-finger-ring-left" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：15% | 1 |
| 14 | 01.03.03000141 | star-arm-102-finger-ring-right | <img src="images/star-arm-102-finger-ring-right.png" alt="star-arm-102-finger-ring-right" width="90"> | PLA 3D 打印件（象牙白）；壁数：2；填充密度：15% | 1 |
| 15 | 01.08.05000012 | 滚针轴承 | <img src="../../media/axk2035-2as-bearing.png" alt="AXK2035+2AS 滚针轴承" width="90"> | AXK2035+2AS；内径 20 mm，外径 35 mm，厚度 4 mm | 1 |
| 16 | 03.01.00000107 | PCBA | <img src="../../media/uc-01-primary.webp" alt="UC-01" width="90"> | UC-01，接DC圆头电源线，0.75平方5.5x2.1母头,0.15米 | 1 |
| 17 | 01.01.17000102 | 线材 | <a href="../../media/ph-3y-servo-cable-120mm.png"><img src="../../media/ph-3y-servo-cable-120mm.png" alt="PH-3Y 120 mm 舵机连接线" width="90"></a> | PH-3Y 接头，两端线序反向；黑色硅胶绝缘排线，外覆黑色编织护套；每根导体 60 × Ø0.08 mm（约 22 AWG）；长度 120 mm | 5 |
| 18 | 01.01.17000101 | 线材 | <a href="../../media/ph-3y-servo-cable-200mm.png"><img src="../../media/ph-3y-servo-cable-200mm.png" alt="PH-3Y 200 mm 舵机连接线" width="90"></a> | PH-3Y 接头，两端线序反向；黑色硅胶绝缘排线，外覆黑色编织护套；每根导体 60 × Ø0.08 mm（约 22 AWG）；长度 200 mm | 2 |
| 19 | 01.06.01000167 | M3 × 10 内六角圆柱头螺钉 | 待补 | 强度等级 12.9，黑色表面 | 1 |
| 20 | 01.06.01000183 | M3 × 22 内六角圆柱头螺钉 | 待补 | 黑色表面 | 4 |
| 21 |  | 螺丝 | 待补 | M3*10加硬包黑十字槽螺杆 | 1 |
| 22 | 01.06.01000060 | PB2.0 × 5 十字槽自攻螺钉 | 待补 | 加硬，黑色表面 | 39 |
| 23 | 01.06.01000079 | M2 × 4.5 十字槽盘头螺钉 | 待补 | 黑色表面，螺纹预涂锁固胶 | 35 |
| 24 | 01.06.01000184 | M2 × 8 内六角圆柱头螺钉 | 待补 | 黑色表面 | 16 |
| 25 |  | M2 × 10 内六角螺钉 | 待补 | 黑色表面 | 8 |
| 26 |  | 3 × 12 mm 十字槽沉头自攻螺钉 | 待补 | 银色表面 | 2 |
| 27 | 01.06.01000086 | M3 防松螺母 | 待补 | 黑色表面 | 5 |
| 28 |  | 垫片 | 待补 | M3不锈钢 | 1 |

发现资料错误或需要帮助？请通过 [Support 支持中心](https://fashionstar.com.hk/support/) 联系我们，并注明型号及对应文件或条目。
