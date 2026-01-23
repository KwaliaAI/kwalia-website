#!/usr/bin/env python3
"""
Sincroniza los metadatos de los ensayos HTML con data/essays.json

Uso:
    python3 sync_essays_json.py                    # Sincroniza todos los ensayos
    python3 sync_essays_json.py ensayo1.html ...   # Sincroniza ensayos específicos

El script extrae de cada HTML:
- title (de <title> o <h1>)
- subtitle (de la etiqueta p.text-xl después del h1)
- og:description (para excerpt)
"""

import json
import os
import re
import sys
from pathlib import Path
from html.parser import HTMLParser

ESSAYS_DIR = Path(__file__).parent / "essays"
JSON_PATH = Path(__file__).parent / "data" / "essays.json"


class EssayMetadataExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.subtitle = None
        self.og_description = None
        self.lang = None

        self._in_title = False
        self._in_h1 = False
        self._in_subtitle = False
        self._found_h1 = False
        self._current_tag = None
        self._current_attrs = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._current_tag = tag
        self._current_attrs = attrs_dict

        if tag == "html":
            self.lang = attrs_dict.get("lang", "en")

        if tag == "title":
            self._in_title = True

        if tag == "h1":
            self._in_h1 = True

        if tag == "meta":
            prop = attrs_dict.get("property", "")
            name = attrs_dict.get("name", "")
            content = attrs_dict.get("content", "")

            if prop == "og:description" or name == "description":
                self.og_description = content

        # Subtitle: primer <p> con class que contiene "text-xl" después de h1
        if tag == "p" and self._found_h1 and not self.subtitle:
            classes = attrs_dict.get("class", "")
            if "text-xl" in classes or "text-c2/70" in classes:
                self._in_subtitle = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "h1":
            self._in_h1 = False
            self._found_h1 = True
        if tag == "p":
            self._in_subtitle = False

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self._in_title and not self.title:
            # Quitar " | Kwalia" del título
            self.title = re.sub(r'\s*\|\s*Kwalia\s*$', '', data).strip()

        if self._in_h1 and not self.title:
            self.title = data

        if self._in_subtitle and not self.subtitle:
            self.subtitle = data


def extract_metadata_from_html(html_path: Path) -> dict:
    """Extrae metadatos de un archivo HTML de ensayo."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = EssayMetadataExtractor()
    parser.feed(content)

    return {
        'lang': parser.lang or 'en',
        'title': parser.title,
        'subtitle': parser.subtitle,
        'excerpt': parser.og_description or parser.subtitle,
    }


def get_slug_from_filename(filename: str) -> str:
    """Extrae el slug del nombre de archivo."""
    return filename.replace('.html', '')


def find_essay_entry(essays: list, slug: str, lang: str) -> tuple:
    """Encuentra la entrada del ensayo en el JSON y devuelve (índice, entrada)."""
    for i, essay in enumerate(essays):
        essay_slug = essay.get('slug', {})
        if isinstance(essay_slug, dict):
            if essay_slug.get(lang) == slug or essay_slug.get('en') == slug or essay_slug.get('es') == slug:
                return i, essay
        elif essay_slug == slug:
            return i, essay
    return -1, None


def sync_essay(html_path: Path, essays: list) -> bool:
    """
    Sincroniza un ensayo HTML con su entrada en el JSON.
    Retorna True si hubo cambios.
    """
    filename = html_path.name
    slug = get_slug_from_filename(filename)

    metadata = extract_metadata_from_html(html_path)
    lang = metadata['lang']

    idx, entry = find_essay_entry(essays, slug, lang)

    if idx == -1:
        print(f"  [SKIP] {filename}: No encontrado en essays.json")
        return False

    changed = False

    # Actualizar título
    if metadata['title']:
        current_title = entry.get('title', {})
        if isinstance(current_title, dict):
            if current_title.get(lang) != metadata['title']:
                current_title[lang] = metadata['title']
                entry['title'] = current_title
                changed = True
                print(f"  [UPDATE] {filename}: title.{lang} = {metadata['title'][:50]}...")

    # Actualizar subtítulo
    if metadata['subtitle']:
        current_subtitle = entry.get('subtitle', {})
        if isinstance(current_subtitle, dict):
            if current_subtitle.get(lang) != metadata['subtitle']:
                current_subtitle[lang] = metadata['subtitle']
                entry['subtitle'] = current_subtitle
                changed = True
                print(f"  [UPDATE] {filename}: subtitle.{lang} = {metadata['subtitle'][:50]}...")

    # Actualizar excerpt
    if metadata['excerpt']:
        current_excerpt = entry.get('excerpt', {})
        if isinstance(current_excerpt, dict):
            if current_excerpt.get(lang) != metadata['excerpt']:
                current_excerpt[lang] = metadata['excerpt']
                entry['excerpt'] = current_excerpt
                changed = True
                print(f"  [UPDATE] {filename}: excerpt.{lang} = {metadata['excerpt'][:50]}...")

    if changed:
        essays[idx] = entry

    return changed


def main():
    if not JSON_PATH.exists():
        print(f"Error: No se encuentra {JSON_PATH}")
        sys.exit(1)

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        essays = json.load(f)

    # Determinar qué archivos sincronizar
    if len(sys.argv) > 1:
        # Archivos específicos
        html_files = []
        for arg in sys.argv[1:]:
            path = Path(arg)
            if not path.exists():
                path = ESSAYS_DIR / arg
            if path.exists() and path.suffix == '.html':
                html_files.append(path)
            else:
                print(f"Warning: {arg} no encontrado o no es HTML")
    else:
        # Todos los archivos HTML en essays/
        html_files = list(ESSAYS_DIR.glob("*.html"))
        # Excluir index.html
        html_files = [f for f in html_files if f.name != "index.html"]

    print(f"Sincronizando {len(html_files)} ensayos con essays.json...")
    print()

    total_changed = 0
    for html_path in sorted(html_files):
        if sync_essay(html_path, essays):
            total_changed += 1

    if total_changed > 0:
        # Guardar JSON actualizado
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(essays, f, ensure_ascii=False, indent=2)
        print()
        print(f"Actualizado essays.json ({total_changed} ensayos modificados)")
    else:
        print()
        print("No se encontraron cambios.")


if __name__ == "__main__":
    main()
