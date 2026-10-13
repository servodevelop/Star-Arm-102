# Repository documentation rules

- English is the default customer entry. If a README has a Chinese counterpart, keep both complete and synchronized in the same change, including section order, images, tables, links, commands, compatibility, and validation status.
- Read both versions before changing either. Check translation meaning manually; structural checks are not proof of semantic equivalence.
- Use README.md and README.zh.md for new pairs. Preserve the existing Butterfly README.zh-CN.md filename for link compatibility. Do not create README_zh.md aliases.
- Organize documentation around customer tasks: useful resources must be easy to find, without duplicated content or internal handoff/cost records in customer pages.
- Keep older resources only when useful for a supported hardware/software version; label their applicable version clearly. Do not publish historical files merely for archival purposes. Git history preserves removed content. Do not substitute an old guide for a current translation.
- Run `python scripts/check_docs.py` and `python scripts/check_readme_sync.py` after documentation changes.
- Use lowercase and hyphens for resource directory names; preserve language and framework identifiers.
- Browser operations default to the Codex in-app browser. Use Chrome only when explicitly requested by the user.

- For directory README navigation, keep the title first, then put the direct-parent link first in a navigation row below the title (`← Parent`), followed by a separator and compact text language switch wrapped in `<sub>` (`<sub>**English** / [简体中文](README.zh.md)</sub>` or its Chinese counterpart). Show the current language in bold without a self-link. For English-only pages, show only English. Do not use globe icons or badges for directory language navigation. For longer pages, add a localized “Contents” / “目录” label below the parent/language navigation, followed by a vertical unordered list with one icon-prefixed link per line, linking either to an explicit section anchor or directly to the relevant page/directory; do not add a redundant body section solely to repeat a navigation link; omit this navigation on short pages. Do not create README files solely for navigation in data-only directories.

- Keep product- or guide-specific images in an `images/` directory alongside the relevant documentation. Store homepage and shared images under root `media/`. Do not list image storage directories in customer resource tables or create empty image placeholders. Keep runtime assets such as URDF meshes inside their packages.

- Keep corresponding English and Chinese navigation targets consistent in kind: when English links to a directory, Chinese must link to the same directory rather than its README. When English links directly to a document, Chinese must use its Chinese counterpart when available (including README.zh-CN.md where applicable), otherwise English. Preserve explicit English language switches. GitHub directory pages do not retain the previously selected language.
