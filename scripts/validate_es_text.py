#!/usr/bin/env python3
"""Read-only Spanish audit. Findings require review; this never rewrites prose."""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent

class PageText(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.parts, self.body, self.titles, self.labels = [], [], [], []
        self.stack = []
        self.lang = ''
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html': self.lang = attrs.get('lang', '')
        if attrs.get('data-es'): self.labels.append(attrs['data-es'])
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append((tag, attrs.get('class', '')))

    def handle_endtag(self, tag):
        if tag in {'p','h1','h2','h3','h4','li','div','section','header','footer','nav','title'}:
            self.handle_data('\n')
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, value):
        if any(tag in {'script','style','noscript'} for tag, _ in self.stack): return
        self.parts.append(value)
        if any('essay-body' in classes.split() for _, classes in self.stack): self.body.append(value)
        if any(tag == 'h1' for tag, _ in self.stack): self.titles.append(value)


def text_findings(text, source, title=False, allow_dialogue=False):
    found = []
    def add(rule, excerpt): found.append(dict(source=source, rule=rule, excerpt=excerpt.strip()[:240]))
    # These cited English paper titles retain their original punctuation.
    question_text = text
    for citation in ('What Is It Like to Be a Bat?', 'What is consciousness, and could machines have it?'):
        question_text = question_text.replace('«' + citation + '»', '«' + citation[:-1] + '»')
    for sentence in re.split(r'[.!\n]+', question_text):
        openings = 0
        for i, char in enumerate(sentence):
            if char == '¿': openings += 1
            elif char == '?':
                if openings: openings -= 1
                else: add('missing_open_question', sentence[max(0,i-180):i+1])
    for m in re.finditer('—', text):
        line = text[text.rfind('\n', 0, m.start())+1:]
        if allow_dialogue and line.lstrip().startswith('—'):
            continue  # GM explicitly preserved Spanish fiction dialogue and attribution rayas.
        add('em_dash', text[max(0,m.start()-70):m.end()+70])
    for m in re.finditer(r'\bno solo\b[^.!?\n]{0,500}\bsino\b', text, re.I): add('no_solo_sino', m[0])
    for m in re.finditer(r'\bno sólo\b', text, re.I): add('no_solo_accent', m[0])
    words = re.findall(r'\b[^\W\d_]+\b', text, re.UNICODE)
    if title and sum(w[0].isupper() and not w.isupper() for w in words[1:]) >= 3:
        add('title_case_review', text)
    return found


def spanish_values(value, location='', selected=False):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from spanish_values(item, location+'.'+key, selected or key == 'es')
    elif isinstance(value, list):
        for i, item in enumerate(value): yield from spanish_values(item, f'{location}[{i}]', selected)
    elif selected and isinstance(value, str): yield location, value


def scan(root=ROOT):
    findings, pages = [], {}
    for path in sorted((root/'essays').glob('*.html')):
        page = PageText(path.read_text())
        pages[path.stem] = page
        if page.lang == 'es':
            findings += text_findings(''.join(page.parts), str(path.relative_to(root)),
                                      allow_dialogue=path.stem=='un-dia-en-el-mindkind-estratificado')
            findings += [f for f in text_findings(''.join(page.titles), str(path.relative_to(root)), True) if f['rule']=='title_case_review']
        if path.name == 'index.html':
            for i, value in enumerate(page.labels): findings += text_findings(value, f'essays/index.html:data-es[{i}]')
    for name in ('essays','books','fiction','heteronyms','i18n/es'):
        path=root/'data'/f'{name}.json'
        for key,value in spanish_values(json.loads(path.read_text()), selected=name=='i18n/es'):
            findings += text_findings(value, f'data/{name}.json{key}', '.title.' in key)
    for entry in json.loads((root/'data/essays.json').read_text()):
        if entry.get('status') != 'published': continue
        slugs = entry.get('slug', {})
        en, es = pages.get(slugs.get('en')), pages.get(slugs.get('es'))
        if not en or not es: continue
        words = lambda p: len(re.findall(r'\b\w+\b', ''.join(p.body)))
        a,b = words(en),words(es)
        if a and b/a < 1:
            findings.append(dict(source='essays/'+slugs['es']+'.html', rule='translation_ratio',
                                 excerpt=f'ES={b}, EN={a}, ratio={b/a:.3f}', es_words=b,en_words=a,ratio=round(b/a,3)))
    return findings


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path, help='write full findings for human review')
    parser.add_argument('--pages', nargs='+', help='gate only these approved essay slugs; full audit remains the default')
    args=parser.parse_args()
    findings=scan()
    if args.pages:
        sources = {'essays/' + slug + '.html' for slug in args.pages}
        missing = [slug for slug in args.pages if not (ROOT/'essays'/f'{slug}.html').exists()]
        if missing: parser.error('missing release pages: ' + ', '.join(missing))
        entries = json.loads((ROOT/'data/essays.json').read_text())
        metadata_prefixes = tuple(f'data/essays.json[{i}].' for i, entry in enumerate(entries)
                                  if entry.get('slug', {}).get('es') in args.pages)
        findings = [f for f in findings if f['source'] in sources
                    or f['source'].startswith(metadata_prefixes)]
        print('Release scope: ' + ', '.join(args.pages))
    counts=Counter(f['rule'] for f in findings)
    for rule in ('missing_open_question','em_dash','no_solo_sino','no_solo_accent','title_case_review','translation_ratio'):
        print(f'{rule}: {counts[rule]}')
    print(f'total findings: {len(findings)}; sources: {len(set(f["source"] for f in findings))}')
    if args.json: args.json.write_text(json.dumps(dict(counts=dict(counts),findings=findings),ensure_ascii=False,indent=2)+'\n')
    return int(bool(findings))

if __name__ == '__main__': raise SystemExit(main())
