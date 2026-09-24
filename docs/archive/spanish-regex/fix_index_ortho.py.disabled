#!/usr/bin/env python3
"""
Fix Spanish orthography in index.html data-es attributes.
"""

import re
from pathlib import Path

# Corrections for data-es attributes
CORRECTIONS = {
    # Tildes faltantes en palabras comunes
    'Atencion': 'Atención',
    'atencion': 'atención',
    'maquina': 'máquina',
    'heteronimo': 'heterónimo',
    'extrano': 'extraño',
    'autoria': 'autoría',
    'ficcion': 'ficción',
    'Ficcion': 'Ficción',
    'ultimo': 'último',
    'Pequenas': 'Pequeñas',
    'reflexion': 'reflexión',
    'Desconexion': 'Desconexión',
    'desconexion': 'desconexión',
    'terminos': 'términos',
    'diseno': 'diseño',
    'razon': 'razón',
    'economia': 'economía',
    'pelicula': 'película',
    'tecnologia': 'tecnología',
    'politica': 'política',
    'opinion': 'opinión',
    'distraccion': 'distracción',
    'practica': 'práctica',
    'guia': 'guía',
    'Deberia': 'Debería',
    'rios': 'ríos',
    'sabran': 'sabrán',
    'metafora': 'metáfora',
    'fantasia': 'fantasía',
    'conversacion': 'conversación',
    'escribi': 'escribí',
    'regalias': 'regalías',
    'capitulo': 'capítulo',
    'manana': 'mañana',
    'opcion': 'opción',
    'seudonimos': 'seudónimos',
    'querias': 'querías',
    'ultima': 'última',

    # Acentos en interrogativos
    'Que pasa': 'Qué pasa',
    'Que significaria': 'Qué significaría',
    'Que acerto': 'Qué acertó',
    'Que decirles': 'Qué decirles',
    'Y que la': 'Y qué la',
    'Y ahora que': 'Y ahora qué',
    'Cual seria': 'Cuál sería',
    'Quien es': 'Quién es',

    # "esta/estan" como verbos
    'esta siendo': 'está siendo',
    'esta convirtiendo': 'está convirtiendo',
    'estan creciendo': 'están creciendo',
    'estan mas': 'están más',
    'estan rotas': 'están rotas',
    'esta escribiendo': 'está escribiendo',

    # "mas" como adverbio
    ' mas ': ' más ',
    ' mas.': ' más.',
    ' mas,': ' más,',
    'algo mas grande': 'algo más grande',
    'mas rara': 'más rara',
    'mas difícil': 'más difícil',
    'mas complicada': 'más complicada',

    # "dia" como sustantivo
    'Un dia': 'Un día',
}


def fix_data_es_attributes(content: str) -> str:
    """Apply corrections to data-es attributes only."""

    def fix_attribute(match):
        attr_value = match.group(1)
        original = attr_value

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
        print("Fixed spelling errors in essays/index.html")
    else:
        print("No changes needed")


if __name__ == "__main__":
    main()
