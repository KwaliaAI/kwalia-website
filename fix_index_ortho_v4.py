#!/usr/bin/env python3
"""
Final fix for remaining orthography errors in index.html.
"""

import re
from pathlib import Path

CORRECTIONS = {
    # Remove incorrect accent from "Futuro"
    'Futúro': 'Futuro',

    # Fix "devoró" (past tense)
    'devoro tus': 'devoró tus',

    # Fix "Tú" as subject pronoun
    'Tu no lo decidiste': 'Tú no lo decidiste',

    # Missing opening question marks
    'Eso que querías comprar?': '¿Eso que querías comprar?',
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
        print("Fixed final spelling errors in essays/index.html")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
