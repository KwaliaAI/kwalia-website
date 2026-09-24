#!/usr/bin/env python3
"""
Fix remaining Spanish orthography errors in index.html data-es attributes.
Second pass for missed corrections.
"""

import re
from pathlib import Path

# Additional corrections
CORRECTIONS = {
    # Accent errors (wrong accents)
    'escribír': 'escribir',
    'escenaríos': 'escenarios',

    # Missing accents on interrogatives "Cómo" (how)
    'Como suena': 'Cómo suena',
    'Como tener': 'Cómo tener',
    'Como leer': 'Cómo leer',
    'Como detectar': 'Cómo detectar',
    'Como pensar': 'Cómo pensar',
    'Como los algoritmos': 'Cómo los algoritmos',
    'como conservarla': 'cómo conservarla',

    # Missing accents on "Por qué" (why)
    'Por que los escritores': 'Por qué los escritores',
    'Por que todos': 'Por qué todos',
    'Por que antropomorfizamos': 'Por qué antropomorfizamos',
    'Por que desconectar': 'Por qué desconectar',
    'Por que no sentimos': 'Por qué no sentimos',

    # Missing accents on "Cuándo" (when)
    'Cuando confiar': 'Cuándo confiar',
    'cuando no': 'cuándo no',
    'Cuando los rios': 'Cuándo los ríos',

    # Missing accents on "Qué" (what) at start
    'Que pasa': 'Qué pasa',
    'Que significaria': 'Qué significaría',
    'Que decirles': 'Qué decirles',
    'Y que la': 'Y qué la',

    # Opening question marks (¿)
    'Cuál sería?': '¿Cuál sería?',
    'Y ahora qué?': '¿Y ahora qué?',

    # "sí" reflexivo
    'por si mismos': 'por sí mismos',

    # "Están" at start of sentence
    'Estan creciendo': 'Están creciendo',

    # "estratégica"
    'estrategica': 'estratégica',

    # "práctico"
    'practico': 'práctico',

    # Missing accents
    'Tu atencion': 'Tu atención',
    'tu atencion': 'tu atención',
    'ultima generacion': 'última generación',
    'tu': 'tú',  # Be careful with this one

    # Fix specific phrases
    'mejor que tu': 'mejor que tú',
    'de lo mas': 'de lo más',
}


def fix_data_es_attributes(content: str) -> str:
    """Apply corrections to data-es attributes only."""

    def fix_attribute(match):
        attr_value = match.group(1)

        for wrong, correct in CORRECTIONS.items():
            attr_value = attr_value.replace(wrong, correct)

        return f'data-es="{attr_value}"'

    # Fix data-es attributes
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
        print("Fixed additional spelling errors in essays/index.html")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
