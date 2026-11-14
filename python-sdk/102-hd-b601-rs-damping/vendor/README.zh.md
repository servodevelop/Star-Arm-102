# 项目自带 SDK

[← 使用教程](../README.zh.md) | <sub>[English](README.md) / **简体中文**</sub>

**目录**

- ▸ [构建](#build)
- ▸ [解压到运行目录](#runtime)
- ▸ [通信测试](#tests)

`motorbridge-smart-servo/` 提供 StarArm 102-HD 主臂通信所需的 Python 接口和 Rust 原生扩展。遥操作通过 `vendor/runtime` 加载该 SDK，并复用主臂已有的串口连接。源码来源、作者和许可信息见 [LICENSE-NOTICE.md](motorbridge-smart-servo/LICENSE-NOTICE.md)，接口说明见 [SDK README](motorbridge-smart-servo/README.zh.md)。

仓库包含源码，不包含预编译 wheel 或 `vendor/runtime`。首次启动遥操作前，请在运行机械臂的 Linux 主机上完成以下构建和解压步骤。

<a id="build"></a>

## 构建

需要 Rust 工具链（`rustc`、`cargo`）、C 链接器，以及已安装 LeRobot 和机械臂插件的 Python 3.10 或以上环境。以下命令均从 `python-sdk/102-hd-b601-rs-damping/` 目录执行；`STARARM_PYTHON` 必须是该环境解释器的绝对路径，启动网页时使用同一解释器。

```bash
# Activate the LeRobot environment, or set STARARM_PYTHON to its absolute interpreter path.
export STARARM_PYTHON="${STARARM_PYTHON:-$(command -v python)}"
"$STARARM_PYTHON" -m pip install 'maturin>=1.7,<2'

(
  set -e
  cd vendor/motorbridge-smart-servo
  cargo test --locked -p smart_servo_core -p smart_servo_vendor_fashionstar
  "$STARARM_PYTHON" -m maturin build --locked --release \
    --interpreter "$STARARM_PYTHON" --out ../wheels
)
```

构建产物位于 `vendor/wheels/`，包含当前平台的原生扩展，不可直接跨操作系统或架构使用。

<a id="runtime"></a>

## 解压到运行目录

继续在 `python-sdk/102-hd-b601-rs-damping/` 目录运行。脚本只选择当前 SDK 版本的 wheel；若目录中有多个匹配文件，先将 `STARARM_WHEEL` 设置为本次构建产物的路径，再执行脚本。

```bash
# If multiple wheels are present, select the file reported by maturin:
# export STARARM_WHEEL="vendor/wheels/your-built-wheel.whl"

"$STARARM_PYTHON" - <<'PY'
import os
from pathlib import Path
from zipfile import ZipFile

pattern = "motorbridge_smart_servo-0.0.4+rsfix1.damping1-*.whl"
chosen = os.environ.get("STARARM_WHEEL")
wheels = [Path(chosen)] if chosen else sorted(Path("vendor/wheels").glob(pattern))
if len(wheels) != 1 or not wheels[0].is_file() or not wheels[0].match(pattern):
    raise SystemExit("Set STARARM_WHEEL to the SDK wheel produced by this build.")

wheel = wheels[0]
runtime = Path("vendor/runtime")
runtime.mkdir(parents=True, exist_ok=True)
with ZipFile(wheel) as archive:
    members = [name for name in archive.namelist()
               if name.startswith(("motorbridge_smart_servo/",
                                   "motorbridge_smart_servo-0.0.4+rsfix1.damping1.dist-info/"))]
    if not any(name.startswith("motorbridge_smart_servo/_native") for name in members):
        raise SystemExit("The wheel does not contain the SDK native extension.")
    archive.extractall(runtime, members=members)
print(f"Extracted {wheel} to {runtime.resolve()}")
PY
```

验证导入路径和所需接口；此命令不会连接设备：

```bash
PYTHONPATH="$PWD/vendor/runtime" "$STARARM_PYTHON" - <<'PY'
from pathlib import Path
import motorbridge_smart_servo as sdk

assert Path(sdk.__file__).resolve().is_relative_to(Path("vendor/runtime").resolve())
assert callable(getattr(sdk.FashionStarServo, "set_damping", None))
assert callable(getattr(sdk.FashionStarServo, "set_zero_confirm_samples", None))
print("SDK ready:", sdk.__file__)
PY
```

完成后返回[使用教程](../README.zh.md)启动网页。启动器会为遥操作进程设置 SDK 导入路径，无需将 wheel 安装到 Python 环境中。

<a id="tests"></a>

## 通信测试

在 `python-sdk/102-hd-b601-rs-damping/` 目录执行：

```bash
PYTHONPATH="$PWD/vendor/runtime" "$STARARM_PYTHON" -m unittest discover \
  -s vendor/motorbridge-smart-servo/tests -v
```

测试使用 Linux 伪终端，验证阻尼指令编码、七轴写入、HOLD / 解锁及串口事务互斥，不访问实际机械臂。
