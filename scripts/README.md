# Repository Maintenance Scripts

[← Home](../README.md)　|　<sub>**English**</sub>

These scripts are for repository contributors. For customer-facing robot and servo tools, see the [tool directory](../tools/README.md).

- `check_docs.py`: check local file and image links in Markdown. Remote URLs and heading fragments are not checked.
- `check_readme_sync.py`: check section structure, table dimensions, images, code blocks, and link targets across existing English/Chinese document pairs, including READMEs, Getting Started, the Python reference, and the older LeRobot guide. Chinese-only historical resources are not treated as translations. Translation meaning still requires human review.
- `requirements-docs.txt`: Python dependencies for the documentation check.

Run from the repository root with Python 3.10 or newer:

```bash
python -m pip install -r scripts/requirements-docs.txt
python scripts/check_docs.py
python scripts/check_readme_sync.py
```

The GitHub documentation workflow runs this check automatically. See [Contributing](../CONTRIBUTING.md) for the complete checks.

- `package_urdf.py`: regenerate the LD/HD and FL URDF download ZIPs from their source directories. Run after editing either package.
