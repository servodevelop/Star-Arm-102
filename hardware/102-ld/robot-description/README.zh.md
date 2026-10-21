# Star Arm 102 LD/HD 机器人描述

[← 102-LD 硬件资源](../README.zh.md)　|　<sub>[English](README.md) / **简体中文**</sub>

主臂手柄与指环结构，供 LD/HD 使用。HD 舵机差异对应的质量与惯量尚未验证。

[下载完整 ZIP](downloads/star-arm-102-ld-hd-urdf-2026-10-21.zip?raw=true) · [浏览源码目录](stararm102-ld-hd-description/)

这是 **ROS 1 / catkin** 软件包。ZIP 与源码目录包含相同文件；请保留整个软件包目录，URDF 需要读取其中的网格。

目录名使用连字符；ROS 包名仍为 `stararm102_ld_hd_description`，启动命令和网格引用均使用此包名。

将 `stararm102-ld-hd-description/` 放入 catkin 工作空间的 `src/`，构建并加载工作空间环境后运行：

```bash
roslaunch stararm102_ld_hd_description display.launch
```

RViz 使用默认布局打开；将 Fixed Frame 设为 `base_link`，添加 RobotModel 显示项。关节限位、质量、惯量及 ROS/Gazebo 运行尚未验证。碰撞形状定义不代表查看器会自动阻止穿模。

**源模型中的 `joint5` 为固定关节**，因此不会转动；这里保留原始定义，待工程确认。

[ROS 2 使用指南](../../../ros2-humble/README.zh.md) · [许可范围](../../../LICENSE.md)
