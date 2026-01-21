#!/usr/bin/env python3
"""
Move EN/ES toggle from article header to navigation menu.
"""

import re
from pathlib import Path

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

ES_TO_EN = {v: k for k, v in ESSAY_PAIRS.items()}


def get_other_lang_slug(slug: str, is_spanish: bool) -> str:
    """Get the slug for the other language version."""
    if is_spanish:
        return ES_TO_EN.get(slug, '')
    else:
        return ESSAY_PAIRS.get(slug, '')


def fix_essay(filepath: Path) -> bool:
    """Fix navigation toggle in a single essay file."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    slug = filepath.stem

    # Skip index
    if slug == 'index':
        return False

    # Determine language
    is_spanish = 'lang="es"' in content[:500]
    other_slug = get_other_lang_slug(slug, is_spanish)

    if not other_slug:
        return False

    # 1. Remove old toggle from article header (the one we added before)
    # Pattern: the div with flex justify-end mb-4 containing the toggle
    content = re.sub(
        r'\s*<div class="flex justify-end mb-4">.*?</div>\s*(?=<p class="font-f3 text-xs)',
        '\n                    ',
        content,
        flags=re.DOTALL
    )

    # 2. Create nav toggle HTML based on language
    if is_spanish:
        # Spanish page - ES is active, EN is link
        nav_toggle_desktop = f'''<div class="flex items-center border border-gray-300 rounded-full overflow-hidden ml-4">
                            <a href="{other_slug}.html" class="font-f3 text-xs px-3 py-1 hover:bg-gray-100 transition-colors">EN</a>
                            <span class="font-f3 text-xs px-3 py-1 bg-c2 text-c4">ES</span>
                        </div>'''
        nav_toggle_mobile = f'''<div class="flex items-center justify-center mt-4 pt-4 border-t border-gray-200">
                <a href="{other_slug}.html" class="font-f3 text-sm px-4 py-1 border border-gray-300 rounded-full hover:bg-gray-100">EN</a>
                <span class="font-f3 text-sm px-4 py-1 bg-c2 text-c4 rounded-full ml-2">ES</span>
            </div>'''
    else:
        # English page - EN is active, ES is link
        nav_toggle_desktop = f'''<div class="flex items-center border border-gray-300 rounded-full overflow-hidden ml-4">
                            <span class="font-f3 text-xs px-3 py-1 bg-c2 text-c4">EN</span>
                            <a href="{other_slug}.html" class="font-f3 text-xs px-3 py-1 hover:bg-gray-100 transition-colors">ES</a>
                        </div>'''
        nav_toggle_mobile = f'''<div class="flex items-center justify-center mt-4 pt-4 border-t border-gray-200">
                <span class="font-f3 text-sm px-4 py-1 bg-c2 text-c4 rounded-full">EN</span>
                <a href="{other_slug}.html" class="font-f3 text-sm px-4 py-1 border border-gray-300 rounded-full ml-2 hover:bg-gray-100">ES</a>
            </div>'''

    # 3. Add toggle to desktop nav (after Subscribe button)
    # First remove any existing toggle in nav
    content = re.sub(
        r'<div class="flex items-center border border-gray-300 rounded-full overflow-hidden ml-4">.*?</div>\s*(?=</div>\s*<div class="md:hidden">)',
        '',
        content,
        flags=re.DOTALL
    )

    # Now add the toggle after Subscribe button in desktop nav
    if is_spanish:
        content = re.sub(
            r'(<a href="/#contact" class="font-f2 bg-c2 text-c4 rounded-md py-2 px-4 hover:bg-c3 transition-colors">Suscribirse</a>)\s*(</div>)\s*(<div class="md:hidden">)',
            f'\\1\n                        {nav_toggle_desktop}\n                    \\2\n\n            \\3',
            content
        )
    else:
        content = re.sub(
            r'(<a href="/#contact" class="font-f2 bg-c2 text-c4 rounded-md py-2 px-4 hover:bg-c3 transition-colors">Subscribe</a>)\s*(</div>)\s*(<div class="md:hidden">)',
            f'\\1\n                        {nav_toggle_desktop}\n                    \\2\n\n            \\3',
            content
        )

    # 4. Add toggle to mobile menu (at the end, before closing div)
    # First remove any existing mobile toggle
    content = re.sub(
        r'<div class="flex items-center justify-center mt-4 pt-4 border-t border-gray-200">.*?</div>\s*(?=</div>\s*</header>)',
        '',
        content,
        flags=re.DOTALL
    )

    # Add mobile toggle before closing mobile menu div
    content = re.sub(
        r'(<a href="/#contact" class="block py-2 px-6 text-sm font-f2 mobile-nav-link">(?:Suscribirse|Subscribe)</a>)\s*(</div>)\s*(</header>)',
        f'\\1\n            {nav_toggle_mobile}\n        \\2>\n    \\3',
        content
    )

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
    for filepath in sorted(essays_dir.glob("*.html")):
        if filepath.name == "index.html":
            continue
        if fix_essay(filepath):
            print(f"  Fixed: {filepath.name}")
            modified += 1

    print(f"\nModified {modified} files")


if __name__ == "__main__":
    main()
