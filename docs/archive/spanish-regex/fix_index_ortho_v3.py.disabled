#!/usr/bin/env python3
"""
Fix incorrectly added accents and remaining issues in index.html.
"""

import re
from pathlib import Path

# Corrections for errors introduced
CORRECTIONS = {
    # Remove incorrect accents
    'túya': 'tuya',
    'túyo': 'tuyo',
    'túyos': 'tuyos',
    'túyas': 'tuyas',
    'tús': 'tus',
    'manufactúrado': 'manufacturado',

    # Fix "Por qué" patterns
    'Por que los escritores': 'Por qué los escritores',
    'Por que todos': 'Por qué todos',
    'Por que antropomorfizamos': 'Por qué antropomorfizamos',
    'Por que desconectar': 'Por qué desconectar',
    'Por que no sentimos': 'Por qué no sentimos',
    'Por que las empresas': 'Por qué las empresas',

    # Cuándo/Cuando patterns
    'Cuando los rios': 'Cuando los ríos',

    # "Están" at start
    'Estan creciendo': 'Están creciendo',

    # Práctico
    'De lo practico': 'De lo práctico',

    # estratégica
    'estrategica': 'estratégica',

    # última
    'La ultima generacion': 'La última generación',

    # missing accents in specific phrases
    'que escribi': 'que escribí',
    'y como conservarla': 'y cómo conservarla',
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
        print("Fixed accent errors in essays/index.html")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
