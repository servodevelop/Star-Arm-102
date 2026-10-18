"""Check bilingual documentation structure; translation meaning needs review."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
PARSER = MarkdownIt('commonmark')

class HTMLAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and attrs.get('src'):
            self.images.append(attrs['src'])
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])

def canonical(target, source=None):
    # Language-specific targets may differ while referring to the same guide.
    target = unquote(target).split('#')[0]
    # Directory browsing and README reading are distinct destinations.
    target = target.replace('README.zh-CN.md', 'README.md').replace('README.zh.md', 'README.md')
    target = target.replace('.zh.md', '.md')
    # The older LeRobot guide predates the *.zh.md convention.
    return re.sub(r'(^|/)stararm102\.md$', r'\1stararm102_en.md', target)

def document_pairs(root):
    pairs = set()
    for zh in list(root.rglob('*.zh.md')) + list(root.rglob('README.zh-CN.md')):
        if any(p.startswith('.') for p in zh.relative_to(root).parts):
            continue
        en = zh.with_name(zh.name.replace('.zh-CN.md', '.md').replace('.zh.md', '.md'))
        # Explicitly labeled Chinese-only historical resources are not translations.
        if en.exists() or zh.name in ('README.zh.md', 'README.zh-CN.md'):
            pairs.add((en, zh))
    legacy_en = root / 'lerobot/stararm102_en.md'
    legacy_zh = root / 'lerobot/stararm102.md'
    if legacy_en.exists() or legacy_zh.exists():
        pairs.add((legacy_en, legacy_zh))
    return sorted(pairs)

def signature(path):
    text = path.read_text()
    tokens = PARSER.parse(text)
    headings, code, images, links = [], [], [], []
    def visit(items):
        for token in items:
            if token.type == 'heading_open':
                headings.append(token.tag)
            elif token.type in ('fence', 'code_block'):
                content = token.content
                # Directory-tree annotations are prose and may be translated.
                if token.type == 'fence' and token.info.strip() == 'text':
                    content = re.sub(r'(?m)^([ │]*[├└]─+[ ]+\S+)[ ]{2,}[^\n]+$', r'\1', content)
                code.append(content)
            elif token.type == 'image':
                images.append(token.attrGet('src'))
            elif token.type == 'link_open':
                links.append(token.attrGet('href'))
            elif token.type in ('html_inline', 'html_block'):
                html = HTMLAssets()
                html.feed(token.content)
                images.extend(html.images)
                links.extend(html.links)
            if token.children:
                visit(token.children)
    visit(tokens)
    tables = []
    rows = []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            rows.append(len(re.split(r'(?<!\\)\|', line)))
        elif rows:
            tables.append(rows)
            rows = []
    return {'headings': headings, 'code': code, 'images': Counter(images),
            'tables': tables, 'links': {canonical(x, path) for x in links if canonical(x, path)}}

def main():
    pairs = document_pairs(ROOT)
    errors = []
    for en, zh in pairs:
        if not en.exists() or not zh.exists():
            errors.append(f'{zh.relative_to(ROOT)}: missing bilingual counterpart')
            continue
        a, b = signature(en), signature(zh)
        for field in a:
            if a[field] != b[field]:
                detail = ''
                if field == 'links':
                    detail = f'; EN only: {a[field] - b[field]}; ZH only: {b[field] - a[field]}'
                errors.append(f'{zh.relative_to(ROOT)}: mismatched {field}{detail}')
    print('\n'.join(errors)) if errors else None
    print(f'Checked {len(pairs)} bilingual documentation pairs; {len(errors)} structural errors.')
    print('Manual review is required for translation meaning and synchronized factual changes.')
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
