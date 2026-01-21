#!/usr/bin/env python3
"""
Extract metadata from all essay HTML files and generate essays.json.
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def extract_essay_metadata(filepath: Path) -> dict:
    """Extract metadata from a single essay HTML file."""
    content = filepath.read_text(encoding='utf-8')

    # Determine language
    lang = 'es' if 'lang="es"' in content[:500] else 'en'

    # Extract title from <h1>
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
    title = title_match.group(1).strip() if title_match else filepath.stem

    # Extract subtitle from <p class="...text-xl...">
    subtitle_match = re.search(r'<p class="[^"]*text-xl[^"]*"[^>]*>([^<]+)</p>', content)
    subtitle = subtitle_match.group(1).strip() if subtitle_match else ""

    # Extract read time
    readtime_match = re.search(r'(\d+)\s*min', content[:2000])
    read_time = int(readtime_match.group(1)) if readtime_match else 5

    # Extract description from og:description or JSON-LD
    desc_match = re.search(r'og:description"[^>]*content="([^"]+)"', content)
    if not desc_match:
        desc_match = re.search(r'"description":\s*"([^"]+)"', content)
    excerpt = desc_match.group(1).strip() if desc_match else ""

    # Extract date
    date_match = re.search(r'"datePublished":\s*"([^"]+)"', content)
    date = date_match.group(1) if date_match else "2026-01-19"

    # Extract tags from tag-badge links
    tags = re.findall(r'filter=([^"]+)"[^>]*class="tag-badge"', content)

    # Determine primary book based on content/image references
    if '9781917717090' in content or 'mindkind' in content.lower():
        primary_book = 'mindkind'
    elif '9781917717137' in content or 'udair' in content.lower():
        primary_book = 'udair'
    else:
        primary_book = 'mindkind'  # default

    return {
        'filename': filepath.name,
        'slug': filepath.stem,
        'lang': lang,
        'title': title,
        'subtitle': subtitle,
        'excerpt': excerpt,
        'read_time': read_time,
        'date': date,
        'tags': tags,
        'primary_book': primary_book
    }


def find_essay_pairs(essays_dir: Path) -> list:
    """Find English-Spanish essay pairs."""
    # First, extract metadata from all essays
    all_metadata = {}
    for filepath in essays_dir.glob("*.html"):
        if filepath.name == "index.html":
            continue
        meta = extract_essay_metadata(filepath)
        all_metadata[filepath.stem] = meta

    # Known pairs mapping (English -> Spanish)
    # Some can be detected automatically, others need manual mapping
    known_pairs = {
        'youre-already-a-cyborg': 'ya-eres-un-cyborg',
        'why-corporations-are-people': 'por-que-las-empresas-son-personas',
        'your-thoughts-arent-yours': 'tus-pensamientos-no-son-tuyos',
        'the-case-for-ai-rights': 'el-caso-de-los-derechos-de-la-ia',
        'youre-training-ai-right-now': 'estas-entrenando-ia-ahora-mismo',
        'the-last-generation-that-remembers': 'la-ultima-generacion-que-recuerda',
        'why-just-unplug-is-no-longer-an-option': 'por-que-desconectar-ya-no-es-opcion',
        'the-algorithm-knows-you': 'el-algoritmo-te-conoce',
        'stop-asking-if-ai-is-conscious': 'deja-de-preguntar-si-la-ia-es-consciente',
        'the-myth-of-the-neutral-tool': 'el-mito-de-la-herramienta-neutral',
        '50-questions-well-be-asking-in-2035': '50-preguntas-que-nos-haremos-en-2035',
        'a-day-in-the-stratified-mindkind': 'un-dia-en-el-mindkind-estratificado',
        'the-case-for-being-offline-sometimes': 'a-favor-de-desconectarse-a-veces',
        'digital-anesthesia': 'anestesia-digital',
        'how-to-spot-manufactured-desire': 'como-detectar-deseo-manufacturado',
        'how-to-read-in-the-age-of-distraction': 'como-leer-en-la-era-de-la-distraccion',
        'how-algorithms-learned-to-want': 'como-los-algoritmos-aprendieron-a-desear',
        'ai-fiction-sounds-like': 'como-suena-la-ficcion-ia',
        'how-to-have-an-opinion-thats-actually-yours': 'como-tener-una-opinion-que-sea-realmente-tuya',
        'social-contract-never-signed': 'contrato-social-nunca-firmamos',
        'when-to-trust-ai': 'cuando-confiar-en-la-ia',
        'when-rivers-became-people': 'cuando-los-rios-se-convirtieron-en-personas',
        'should-ai-write-emails': 'deberia-ia-escribir-emails',
        'the-art-of-productive-misunderstanding': 'el-arte-del-malentendido-productivo',
        'the-strange-new-world-of-ai-art': 'el-extrano-nuevo-mundo-del-arte-ia',
        'pessoa-ghost-machine': 'el-fantasma-de-pessoa-en-la-maquina',
        'heteronym-returns': 'el-heteronimo-regresa',
        'the-problem-with-asking-if-ai-can-feel': 'el-problema-de-preguntar-si-la-ia-puede-sentir',
        'the-last-human-thought': 'el-ultimo-pensamiento-humano',
        'spectrum-of-ai': 'espectro-de-ia',
        'the-influencer-economy-is-a-preview': 'la-economia-de-influencers-es-un-adelanto',
        'the-attention-economy-ate-your-desires': 'la-economia-de-la-atencion-devoro-tus-deseos',
        'the-loneliness-epidemic-has-a-business-model': 'la-epidemia-de-soledad-tiene-un-modelo-de-negocio',
        'the-coming-cognitive-class-war': 'la-guerra-de-clases-cognitiva',
        'the-death-of-expertise': 'la-muerte-de-la-experiencia',
        'the-new-digital-divide': 'la-nueva-brecha-digital',
        'the-poetics-of-the-prompt': 'la-poetica-del-prompt',
        'real-reason-cant-focus': 'la-verdadera-razon-no-puedes-concentrarte',
        'what-cambridge-analytica-taught-us': 'lo-que-cambridge-analytica-nos-enseno',
        'the-three-futures': 'los-tres-futuros',
        'memory-becomes-external': 'memoria-externa',
        'on-writing-with-machines': 'sobre-escribir-con-maquinas',
        'think-clearly-age-of-ai': 'pensar-claridad-era-ia',
        'small-emergencies': 'pequenas-emergencias',
        'why-we-anthropomorphize-ai': 'por-que-antropomorfizamos-la-ia',
        'why-writers-are-angrier-than-visual-artists': 'por-que-los-escritores-estan-mas-enfadados',
        'why-everyones-worried-about-the-wrong-ai-risks': 'por-que-todos-se-preocupan-por-los-riesgos-equivocados-de-la-ia',
        'what-her-got-right-about-ai-love': 'que-acerto-her-sobre-el-amor-con-ia',
        'what-to-tell-your-kids-about-ai': 'que-decirles-a-tus-hijos-sobre-ia',
        'what-would-it-mean-for-ai-to-die': 'que-significaria-que-muriera-una-ia',
        'who-owns-a-thought': 'quien-es-dueno-de-un-pensamiento',
        'whos-responsible-when-ai-kills': 'quien-es-responsable-cuando-la-ia-mata',
        'administrative-realism': 'realismo-administrativo',
        'if-ai-could-vote': 'si-la-ia-pudiera-votar',
        'your-attention-is-being-strip-mined': 'tu-atencion-esta-siendo-saqueada',
    }

    # Build paired essay entries
    essays = []
    processed_slugs = set()

    for en_slug, es_slug in known_pairs.items():
        if en_slug in all_metadata and es_slug in all_metadata:
            en_meta = all_metadata[en_slug]
            es_meta = all_metadata[es_slug]

            essay = {
                "id": en_slug,
                "slug": {
                    "en": en_slug,
                    "es": es_slug
                },
                "title": {
                    "en": en_meta['title'],
                    "es": es_meta['title']
                },
                "subtitle": {
                    "en": en_meta['subtitle'],
                    "es": es_meta['subtitle']
                },
                "excerpt": {
                    "en": en_meta['excerpt'],
                    "es": es_meta['excerpt']
                },
                "date": en_meta['date'],
                "readTime": en_meta['read_time'],
                "primaryBook": en_meta['primary_book'],
                "tags": list(set(en_meta['tags'] + es_meta['tags'])),
                "status": "published"
            }
            essays.append(essay)
            processed_slugs.add(en_slug)
            processed_slugs.add(es_slug)

    # Handle any remaining essays that weren't paired
    for slug, meta in all_metadata.items():
        if slug not in processed_slugs:
            print(f"Warning: Unpaired essay: {slug} ({meta['lang']})")

    return essays


def main():
    essays_dir = Path("essays")

    if not essays_dir.exists():
        print("Error: essays directory not found")
        return

    essays = find_essay_pairs(essays_dir)

    # Sort by date, then by id
    essays.sort(key=lambda x: (x['date'], x['id']), reverse=True)

    # Write to JSON
    output_path = Path("data/essays.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(essays, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(essays)} essay entries")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
