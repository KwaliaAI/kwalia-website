#!/usr/bin/env python3
"""
Comprehensive fix for essay issues:
1. Fix broken cover image references
2. Add EN/ES language toggle
3. Fix remaining orthography issues
"""

import re
from pathlib import Path

# Image replacements for non-existent files
IMAGE_FIXES = {
    '9781917717168.jpg': '9781917717090.jpg',  # Mindkind ES
    '9781917717144.jpg': '9781917717090.jpg',  # Mindkind ES
    '9781917717038.jpg': '9781917717021.jpg',  # UDAIR ES
}

# Essay pairs mapping (EN slug -> ES slug)
ESSAY_PAIRS = {
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

# Reverse mapping
ES_TO_EN = {v: k for k, v in ESSAY_PAIRS.items()}


def get_language_toggle_html(current_slug: str, is_spanish: bool) -> str:
    """Generate the language toggle HTML for an essay."""
    if is_spanish:
        en_slug = ES_TO_EN.get(current_slug)
        if not en_slug:
            return ""
        return f'''<div class="flex justify-end mb-4">
                        <a href="{en_slug}.html" class="font-f3 text-xs px-3 py-1 border border-gray-300 rounded-full hover:border-c3 hover:text-c3 transition-colors">EN</a>
                        <span class="font-f3 text-xs px-3 py-1 bg-c2 text-c4 rounded-full ml-2">ES</span>
                    </div>'''
    else:
        es_slug = ESSAY_PAIRS.get(current_slug)
        if not es_slug:
            return ""
        return f'''<div class="flex justify-end mb-4">
                        <span class="font-f3 text-xs px-3 py-1 bg-c2 text-c4 rounded-full">EN</span>
                        <a href="{es_slug}.html" class="font-f3 text-xs px-3 py-1 border border-gray-300 rounded-full ml-2 hover:border-c3 hover:text-c3 transition-colors">ES</a>
                    </div>'''


def fix_essay(filepath: Path) -> bool:
    """Fix a single essay file. Returns True if modified."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    slug = filepath.stem

    # Determine language
    is_spanish = 'lang="es"' in content[:500]

    # 1. Fix broken image references
    for old_img, new_img in IMAGE_FIXES.items():
        content = content.replace(old_img, new_img)

    # 2. Add language toggle if not present
    if 'flex justify-end mb-4' not in content:
        toggle_html = get_language_toggle_html(slug, is_spanish)
        if toggle_html:
            # Insert after the header opening, before the date line
            # Pattern: <header class="mb-12">
            #          <p class="font-f3 text-xs...
            pattern = r'(<header class="mb-12">)\s*\n(\s*<p class="font-f3 text-xs)'
            replacement = f'\\1\n                    {toggle_html}\n\\2'
            content = re.sub(pattern, replacement, content)

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False


def main():
    essays_dir = Path("essays")

    if not essays_dir.exists():
        print("Error: essays directory not found")
        return

    modified = 0
    total = 0

    for filepath in sorted(essays_dir.glob("*.html")):
        if filepath.name == "index.html":
            continue
        total += 1
        if fix_essay(filepath):
            print(f"  Fixed: {filepath.name}")
            modified += 1

    print(f"\nResults: {modified}/{total} files modified")


if __name__ == "__main__":
    main()
