#!/usr/bin/env python3
"""
Final corrections for remaining orthography errors in index.html.
"""

import re
from pathlib import Path

CORRECTIONS = {
    # Wrong accent in "Octubre"
    'Octúbre': 'Octubre',

    # "tu" as possessive (not pronoun)
    'tú chatbot': 'tu chatbot',
    'tú movil': 'tu móvil',

    # "poética"
    'poetica': 'poética',

    # Other potential issues
    'Agostó': 'Agosto',
    'Juniò': 'Junio',
    'Mayó': 'Mayo',
}


def fix_data_es_attributes(content: str) -> str:
    """Apply corrections to data-es attributes only."""

    def fix_attribute(match):
        attr_value = match.group(1)

        for wrong, correct in CORRECTIONS.items():
            attr_value = attr_value.replace(wrong, correct)

        return f'data-es="{attr_value}"'

    content = re.sub(r'data-es="([^"]*)"', fix_attribute, content)

    return content


def main():
    index_path = Path("essays/index.html")

    if not index_path.exists():
        print("Error: essays/index.html not found")
        return

    content = index_path.read_text(encoding='utf-8')
    original = content

    content = fix_data_es_attributes(content)

    if content != original:
        index_path.write_text(content, encoding='utf-8')
        print("Fixed remaining spelling errors in essays/index.html")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
