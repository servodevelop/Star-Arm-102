# SDK 来源与许可信息

- 上游仓库：<https://github.com/motorbridge/motorbridge-smart-servo>
- 来源：PyPI `motorbridge-smart-servo` 0.0.4 源码包，对应上游 v0.0.4。
- 上游提交：`319649f0b89d0aa247d8862ca4c4c72c198e6d90`。
- 作者：tianrking。
- 上游声明的许可：MIT。
- 项目自带 SDK 的 Python 包版本：`0.0.4+rsfix1.damping1`。

原始 PyPI 源码包提供以下元数据：

```text
Name: motorbridge-smart-servo
Version: 0.0.4
Author: tianrking
License-Expression: MIT
```

其 `Cargo.toml` 也声明 `authors = ["tianrking"]` 和 `license = "MIT"`。这些作者与许可声明保留在本目录的 `pyproject.toml` 和 `Cargo.toml` 中。MIT 许可文本可见 <https://spdx.org/licenses/MIT.html>。

原始 0.0.4 源码归档及上述提交的 Git 文件树均未提供独立的 LICENSE、COPYING 或 NOTICE 文件，也未提供版权年份或版权持有人声明。本文记录其实际提供的元数据，不补造或替代上游版权声明。

本目录包含零角可靠性处理、`set_zero_confirm_samples()` 接口及相应测试，并提供通过现有控制器互斥锁发送 `0x09` 指令的 `set_damping()` 接口。版本标识中的 `rsfix1` 对应零角处理和确认帧数接口，`damping1` 对应固定阻尼接口；该包未发布到 PyPI。

构建和使用说明见 [项目自带 SDK](../README.md)。
