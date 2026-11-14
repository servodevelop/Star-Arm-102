# Bundled SDK

[← User guide](../README.md) | <sub>**English** / [简体中文](README.zh.md)</sub>

**Contents**

- ▸ [Build](#build)
- ▸ [Extract to the runtime directory](#runtime)
- ▸ [Transport tests](#tests)

`motorbridge-smart-servo/` provides the Python interface and native Rust extension for communication with the StarArm 102-HD leader. Teleoperation loads this SDK from `vendor/runtime` and reuses the leader's existing serial connection. See [LICENSE-NOTICE.md](motorbridge-smart-servo/LICENSE-NOTICE.md) for source, author, and license information, and the [SDK README](motorbridge-smart-servo/README.md) for its interfaces.

The repository includes source code, but no prebuilt wheel or `vendor/runtime`. Complete the following build and extraction steps on the Linux computer that controls the arms before starting teleoperation for the first time.

<a id="build"></a>

## Build

You need a Rust toolchain (`rustc` and `cargo`), a C linker, and a Python 3.10 or later environment with LeRobot and the arm plugins installed. Run all commands below from `python-sdk/102-hd-b601-rs-damping/`. `STARARM_PYTHON` must be the absolute path to that environment's interpreter; use the same interpreter to start the dashboard.

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

Build outputs are placed in `vendor/wheels/`. They contain the native extension for the current platform and cannot be used directly on a different operating system or architecture.

<a id="runtime"></a>

## Extract to the runtime directory

Continue in `python-sdk/102-hd-b601-rs-damping/`. The script selects only a wheel for the current SDK version. If multiple matching files are present, set `STARARM_WHEEL` to the path of the wheel produced by this build before running the script.

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

Verify the import path and required interfaces. This command does not connect to hardware:

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

Return to the [user guide](../README.md) to start the dashboard. The launcher sets the SDK import path for the teleoperation process; you do not need to install the wheel into the Python environment.

<a id="tests"></a>

## Transport tests

Run from `python-sdk/102-hd-b601-rs-damping/`:

```bash
PYTHONPATH="$PWD/vendor/runtime" "$STARARM_PYTHON" -m unittest discover \
  -s vendor/motorbridge-smart-servo/tests -v
```

The tests use Linux pseudo-terminals to check damping command encoding, writes to all seven axes, HOLD / unlock commands, and mutual exclusion of serial transactions. They do not access physical arms.
