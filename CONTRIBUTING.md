# Contributing

Use [GitHub Issues](https://github.com/servodevelop/Star-Arm-102/issues/new/choose) for a reproducible problem or documentation correction. Include your arm models, software versions, selected plugin generation, command, and full error text. Remove tokens and personal information from logs.

## Documentation

English remains the default entry. Where a Chinese README exists, both languages are full, synchronized versions: preserve section order, images, tables, navigation, commands, compatibility limits, and validation status. Update both in the same change whenever fixing or extending either language. Use `README.md` and `README.zh.md`; keep the existing Butterfly `README.zh-CN.md` path for link compatibility. Do not add duplicate underscore-named entry pages.

Current README pairs must not become short summaries of one another. Organize resources around customer tasks and avoid duplicate content or internal handoff/cost records. Retain older resources only when useful for a supported version, with the applicable version clearly labeled; do not publish files solely for archival purposes. Git history preserves removed content. Detailed documents without a translation may remain English-only. Check translation meaning manually; automated structural checks cannot establish semantic equivalence.

Preserve existing package names, source directory paths, and model release links unless a migration is explicitly documented. Do not put model weights, local datasets, calibration files, or virtual environments into Git.

## Cross-brand pairing documentation

Keep customer pairing guides in `integrations/`, Python implementations in `python-sdk/`, and LeRobot plugins in `lerobot/` or their upstream repositories. Link to one authoritative command sequence. Use exact brand/model names and record LD, HD button, teleoperation, recording, and inference evidence separately. Do not label a virtual-model preview as real-follower support. See the [evidence requirements](integrations/compatibility.md).

## Naming

Use lowercase words separated by hyphens (`kebab-case`) for new repository names, resource directories, descriptive filenames, and branch names. Examples: `hardware/`, `102-ld/`, `camera-mount.step`, and `codex/phase-one-english`. Use lowercase file extensions for exported assets.

Keep conventional filenames such as `README.md`, `README.zh.md`, `LICENSE`, and `CHANGELOG.md`. Follow language and tool requirements for Python modules, ROS packages, and other integration identifiers. Migrate existing paths deliberately and update their references; check exact letter case for Linux and GitHub compatibility. Do not rename the GitHub repository or existing branches as part of a resource-file cleanup.

## Check a change

From the repository root in a Python environment:

```bash
python -m pip install -r scripts/requirements-docs.txt -r python-sdk/102-ld-hd-to-102-fl/single-pair/requirements.txt
python scripts/check_docs.py
python scripts/check_readme_sync.py
python -m unittest discover -s tests -v
```

For hardware-affecting changes, record the actual arm, firmware, environment, calibration, and observed behavior. Software checks do not establish physical correctness. See the [validation checklist](docs/validation.md).

Follow the existing [license scope](LICENSE.md); do not replace component licenses during a documentation edit.
