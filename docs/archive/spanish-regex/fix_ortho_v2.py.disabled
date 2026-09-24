#!/usr/bin/env python3
"""
Fix remaining Spanish orthography in essays - Version 2.
Focuses on future tense verbs and other missed words.
"""

import re
from pathlib import Path

# Additional accent fixes
ACCENT_FIXES = {
    # Future tense verbs (3rd person singular and plural)
    r'\bexistiran\b': 'existirán',
    r'\bseran\b': 'serán',
    r'\btendran\b': 'tendrán',
    r'\bhabran\b': 'habrán',
    r'\bpodran\b': 'podrán',
    r'\bestaran\b': 'estarán',
    r'\bharan\b': 'harán',
    r'\bvendran\b': 'vendrán',
    r'\bsabran\b': 'sabrán',
    r'\bquerran\b': 'querrán',
    r'\bdiran\b': 'dirán',
    r'\bveran\b': 'verán',
    r'\bdaran\b': 'darán',
    r'\bsaldran\b': 'saldrán',
    r'\bpondran\b': 'pondrán',
    r'\bvaldran\b': 'valdrán',
    r'\bcaeran\b': 'caerán',
    r'\btraeran\b': 'traerán',
    r'\bmoriran\b': 'morirán',
    r'\bviviran\b': 'vivirán',
    r'\bsentiran\b': 'sentirán',
    r'\bpensaran\b': 'pensarán',
    r'\brecordaran\b': 'recordarán',
    r'\bolvidaran\b': 'olvidarán',
    r'\bcambiaran\b': 'cambiarán',
    r'\bdescubriran\b': 'descubrirán',
    r'\bdesapareceran\b': 'desaparecerán',
    r'\bconvertiran\b': 'convertirán',
    r'\bdefineran\b': 'definirán',
    r'\bdefiniran\b': 'definirán',

    # Future tense 1st person plural
    r'\bestaremos\b': 'estaremos',  # correct
    r'\bharemos\b': 'haremos',  # correct

    # Adjectives
    r'\bdificil\b': 'difícil',
    r'\bDificil\b': 'Difícil',
    r'\bfacil\b': 'fácil',
    r'\bFacil\b': 'Fácil',
    r'\butil\b': 'útil',
    r'\bUtil\b': 'Útil',
    r'\binutiles\b': 'inútiles',
    r'\bdebil\b': 'débil',
    r'\bfragil\b': 'frágil',
    r'\bagil\b': 'ágil',
    r'\bmetafisico\b': 'metafísico',
    r'\bMetafisico\b': 'Metafísico',
    r'\bmetafisica\b': 'metafísica',
    r'\bfisico\b': 'físico',
    r'\bfisica\b': 'física',
    r'\bautentico\b': 'auténtico',
    r'\bautentica\b': 'auténtica',
    r'\bAutentico\b': 'Auténtico',
    r'\bsimpatico\b': 'simpático',
    r'\besceptico\b': 'escéptico',
    r'\besceptica\b': 'escéptica',
    r'\bpractico\b': 'práctico',
    r'\bpractica\b': 'práctica',
    r'\btecnico\b': 'técnico',
    r'\btecnica\b': 'técnica',
    r'\beconomico\b': 'económico',
    r'\beconomica\b': 'económica',
    r'\bpolitico\b': 'político',
    r'\bpolitica\b': 'política',
    r'\betico\b': 'ético',
    r'\betica\b': 'ética',
    r'\bEtico\b': 'Ético',
    r'\blogico\b': 'lógico',
    r'\blogica\b': 'lógica',
    r'\bpsicologico\b': 'psicológico',
    r'\bpsicologica\b': 'psicológica',
    r'\bbiologico\b': 'biológico',
    r'\bbiologica\b': 'biológica',
    r'\btecnologico\b': 'tecnológico',
    r'\btecnologica\b': 'tecnológica',
    r'\bhistorico\b': 'histórico',
    r'\bhistorica\b': 'histórica',
    r'\bsimbolico\b': 'simbólico',
    r'\bsimbolica\b': 'simbólica',
    r'\bironicamente\b': 'irónicamente',

    # Nouns
    r'\bproximo\b': 'próximo',
    r'\bproxima\b': 'próxima',
    r'\bProximo\b': 'Próximo',
    r'\bProxima\b': 'Próxima',
    r'\bexito\b': 'éxito',
    r'\bExito\b': 'Éxito',
    r'\btitulo\b': 'título',
    r'\btitulos\b': 'títulos',
    r'\barticulo\b': 'artículo',
    r'\barticulos\b': 'artículos',
    r'\bparrafo\b': 'párrafo',
    r'\bparrafos\b': 'párrafos',
    r'\bcapitulo\b': 'capítulo',
    r'\bcapitulos\b': 'capítulos',
    r'\bmusica\b': 'música',
    r'\bMusica\b': 'Música',
    r'\bmedico\b': 'médico',
    r'\bmedica\b': 'médica',
    r'\bmedicos\b': 'médicos',
    r'\bpublico\b': 'público',
    r'\bpublica\b': 'pública',
    r'\bPublico\b': 'Público',
    r'\btrafico\b': 'tráfico',
    r'\bpanico\b': 'pánico',
    r'\bunico\b': 'único',
    r'\bunica\b': 'única',
    r'\bunicos\b': 'únicos',
    r'\bespecifico\b': 'específico',
    r'\bespecifica\b': 'específica',
    r'\bespecificos\b': 'específicos',
    r'\bcientifico\b': 'científico',
    r'\bcientifica\b': 'científica',
    r'\belectronico\b': 'electrónico',
    r'\belectronica\b': 'electrónica',
    r'\bmecanico\b': 'mecánico',
    r'\bmecanica\b': 'mecánica',
    r'\borganico\b': 'orgánico',
    r'\borganica\b': 'orgánica',
    r'\bclasico\b': 'clásico',
    r'\bclasica\b': 'clásica',
    r'\bbasico\b': 'básico',
    r'\bbasica\b': 'básica',
    r'\bpropito\b': 'propósito',
    r'\bproposito\b': 'propósito',
    r'\bpropositos\b': 'propósitos',
    r'\bmetodo\b': 'método',
    r'\bmetodos\b': 'métodos',
    r'\bperiodo\b': 'período',
    r'\bperiodos\b': 'períodos',
    r'\btermino\b': 'término',
    r'\bterminos\b': 'términos',
    r'\bcodigo\b': 'código',
    r'\bcodigos\b': 'códigos',
    r'\bgenero\b': 'género',
    r'\bgeneros\b': 'géneros',
    r'\bcaracter\b': 'carácter',
    r'\bcaracteres\b': 'caracteres',
    r'\bdialogo\b': 'diálogo',
    r'\bdialogos\b': 'diálogos',
    r'\bcatalogo\b': 'catálogo',
    r'\banalogo\b': 'análogo',
    r'\banalisis\b': 'análisis',
    r'\bAnalisis\b': 'Análisis',
    r'\bsintesis\b': 'síntesis',
    r'\bhipotesis\b': 'hipótesis',
    r'\bHipotesis\b': 'Hipótesis',
    r'\benfasis\b': 'énfasis',
    r'\bparentesis\b': 'paréntesis',
    r'\btesis\b': 'tesis',  # no accent
    r'\bcrisis\b': 'crisis',  # no accent
    r'\binteres\b': 'interés',
    r'\binteres\b': 'interés',
    r'\bjovenes\b': 'jóvenes',
    r'\bimagenes\b': 'imágenes',
    r'\bordenes\b': 'órdenes',
    r'\borigenes\b': 'orígenes',
    r'\bmargenes\b': 'márgenes',
    r'\bvolumenes\b': 'volúmenes',
    r'\bexamenes\b': 'exámenes',
    r'\bcrimenes\b': 'crímenes',
    r'\bregimen\b': 'régimen',
    r'\bregimenes\b': 'regímenes',
    r'\boceano\b': 'océano',

    # Verbs - past tense
    r'\bocurrio\b': 'ocurrió',
    r'\bsucedio\b': 'sucedió',
    r'\bconvirtio\b': 'convirtió',
    r'\bdecidio\b': 'decidió',
    r'\bexistio\b': 'existió',
    r'\bsurgio\b': 'surgió',
    r'\bcontribuyo\b': 'contribuyó',
    r'\bdesarrollo(?=\s+[a-z])': 'desarrolló',  # verb not noun
    r'\bcomenzo\b': 'comenzó',
    r'\bComenzo\b': 'Comenzó',
    r'\btermino(?=\s+[a-z])': 'terminó',  # verb not noun
    r'\bpaso(?=\s+[a-z])': 'pasó',  # verb not noun
    r'\bllego\b': 'llegó',
    r'\bLlego\b': 'Llegó',
    r'\bpenso\b': 'pensó',
    r'\bcambio(?=\s+[a-z])': 'cambió',  # verb not noun
    r'\bdijo\b': 'dijo',  # no accent
    r'\bhizo\b': 'hizo',  # no accent
    r'\bfue\b': 'fue',  # no accent
    r'\bvio\b': 'vio',  # no accent (monosyllabic)
    r'\bdio\b': 'dio',  # no accent (monosyllabic)
    r'\btomo\b': 'tomó',
    r'\brecibio\b': 'recibió',
    r'\bescribio\b': 'escribió',
    r'\baprendio\b': 'aprendió',
    r'\bentendio\b': 'entendió',
    r'\bperdio\b': 'perdió',
    r'\bsintio\b': 'sintió',
    r'\bmurio\b': 'murió',
    r'\bnacio\b': 'nació',
    r'\bvivio\b': 'vivió',
    r'\bsiguio\b': 'siguió',
    r'\beligio\b': 'eligió',
    r'\bdescubrio\b': 'descubrió',
    r'\brepitio\b': 'repitió',
    r'\bsirvio\b': 'sirvió',
    r'\bdurmio\b': 'durmió',
    r'\bprefirio\b': 'prefirió',
    r'\bsugiro\b': 'sugirió',
    r'\bsugirio\b': 'sugirió',
    r'\bexigio\b': 'exigió',
    r'\bimpidio\b': 'impidió',
    r'\bconsiguio\b': 'consiguió',
    r'\bpersiguio\b': 'persiguió',
    r'\bprohibio\b': 'prohibió',
    r'\binvento\b': 'inventó',
    r'\bcreo(?=\s+[a-z])': 'creó',  # verb
    r'\bconto\b': 'contó',

    # More verbs - present subjunctive and conditional
    r'\bseria\b': 'sería',
    r'\bpodria\b': 'podría',
    r'\bdeberia\b': 'debería',
    r'\btendria\b': 'tendría',
    r'\bhabria\b': 'habría',
    r'\bestaria\b': 'estaría',
    r'\bharia\b': 'haría',
    r'\bdiria\b': 'diría',
    r'\bveria\b': 'vería',
    r'\bqueria\b': 'quería',
    r'\bvendria\b': 'vendría',
    r'\bsabria\b': 'sabría',
    r'\bpasaria\b': 'pasaría',
    r'\bexistiria\b': 'existiría',
    r'\bcreeria\b': 'creería',
    r'\bpareceria\b': 'parecería',
    r'\bimportaria\b': 'importaría',
    r'\bdejaria\b': 'dejaría',
    r'\bllevaria\b': 'llevaría',
    r'\btomare\b': 'tomaría',
    r'\bpermitira\b': 'permitiría',
    r'\bpermitiran\b': 'permitirán',
    r'\bdeberian\b': 'deberían',
    r'\bDeberian\b': 'Deberían',
    r'\bpodrian\b': 'podrían',
    r'\btendrian\b': 'tendrían',
    r'\bharian\b': 'harían',
    r'\bestarian\b': 'estarían',
    r'\bserian\b': 'serían',
    r'\bdirian\b': 'dirían',
    r'\bverian\b': 'verían',
    r'\bsabrian\b': 'sabrían',
    r'\bquerrian\b': 'querrían',
    r'\bvendrian\b': 'vendrían',
    r'\bharian\b': 'harían',

    # Common verbs - imperfect
    r'\bsolian\b': 'solían',
    r'\btenian\b': 'tenían',
    r'\bhacian\b': 'hacían',
    r'\bdecian\b': 'decían',
    r'\bpodian\b': 'podían',
    r'\bquerian\b': 'querían',
    r'\bsabian\b': 'sabían',
    r'\bvenian\b': 'venían',
    r'\bvivian\b': 'vivían',
    r'\bexistian\b': 'existían',
    r'\bestaban\b': 'estaban',  # no accent needed
    r'\beran\b': 'eran',  # no accent needed
    r'\bhabian\b': 'habían',
    r'\bparecian\b': 'parecían',
    r'\bsentian\b': 'sentían',
    r'\bpensaban\b': 'pensaban',  # no accent
    r'\bcreian\b': 'creían',

    # Interrogatives (need accents)
    r'\bque (?=pasa|es|significa|hace|haces|hacemos|tipo|clase|habilidad|pensamientos|tecnolog)': 'qué ',
    r'\bQue (?=pasa|es|significa|hace|haces|hacemos|tipo|clase|habilidad|pensamientos|tecnolog)': 'Qué ',
    r'\bcomo (?=sabes|saber|piensas|pensar|hacer|funciona|se |la |lo |nos |los |las |verificamos|ensenam)': 'cómo ',
    r'\bComo (?=sabes|saber|piensas|pensar|hacer|funciona|se |la |lo |nos |los |las |verificamos|ensenam)': 'Cómo ',
    r'\bcuando (?=confiar|fue|es|sera|viene|llega|mi )': 'cuándo ',
    r'\bCuando (?=confiar|fue|es|sera|viene|llega|mi )': 'Cuándo ',
    r'\bdonde (?=esta|estan|hay|vive|queda)': 'dónde ',
    r'\bDonde (?=esta|estan|hay|vive|queda)': 'Dónde ',
    r'\bpor que\b': 'por qué',
    r'\bPor que\b': 'Por qué',
    r'\bcual (?=es|fue|sera)': 'cuál ',
    r'\bCual (?=es|fue|sera)': 'Cuál ',
    r'\bquien (?=es|fue|sabe|puede|posee|gobierna|decide)': 'quién ',
    r'\bQuien (?=es|fue|sabe|puede|posee|gobierna|decide)': 'Quién ',

    # Common words
    r'\btodavia\b': 'todavía',
    r'\bTodavia\b': 'Todavía',
    r'\bdetras\b': 'detrás',
    r'\bdemas\b': 'demás',
    r'\bademas\b': 'además',
    r'\bAdemas\b': 'Además',
    r'\baqui\b': 'aquí',
    r'\bAqui\b': 'Aquí',
    r'\bahi\b': 'ahí',
    r'\bAhi\b': 'Ahí',
    r'\balli\b': 'allí',
    r'\bAlli\b': 'Allí',
    r'\balla\b': 'allá',
    r'\bAlla\b': 'Allá',
    r'\bdespues\b': 'después',
    r'\bDespues\b': 'Después',
    r'\bsegun\b': 'según',
    r'\bSegun\b': 'Según',
    r'\bmas\b': 'más',
    r'\bMas\b': 'Más',
    r'\balgun\b': 'algún',
    r'\bningun\b': 'ningún',
    r'\bcomun\b': 'común',
    r'\bSocrates\b': 'Sócrates',
    r'\bPlaton\b': 'Platón',
    r'\bAristoteles\b': 'Aristóteles',

    # Words with ñ
    r'\banos\b': 'años',
    r'\bano\b': 'año',
    r'\bAno\b': 'Año',
    r'\bdano\b': 'daño',
    r'\bdanos\b': 'daños',
    r'\bnino\b': 'niño',
    r'\bnina\b': 'niña',
    r'\bninos\b': 'niños',
    r'\bninas\b': 'niñas',
    r'\bmanana\b': 'mañana',
    r'\bManana\b': 'Mañana',
    r'\bsueno\b': 'sueño',
    r'\bsuenos\b': 'sueños',
    r'\botono\b': 'otoño',
    r'\bmontana\b': 'montaña',
    r'\bmontanas\b': 'montañas',
    r'\bcompania\b': 'compañía',
    r'\bcompanias\b': 'compañías',
    r'\bcompanero\b': 'compañero',
    r'\bcompaneros\b': 'compañeros',
    r'\bcompanera\b': 'compañera',
    r'\bcampana\b': 'campaña',
    r'\bcampanas\b': 'campañas',
    r'\bespanol\b': 'español',
    r'\bespanola\b': 'española',
    r'\bespanoles\b': 'españoles',
    r'\bEspana\b': 'España',
    r'\bengano\b': 'engaño',
    r'\benganos\b': 'engaños',
    r'\btamano\b': 'tamaño',
    r'\btamanos\b': 'tamaños',
    r'\bextrano\b': 'extraño',
    r'\bextranos\b': 'extraños',
    r'\bextrana\b': 'extraña',
    r'\bsenales\b': 'señales',
    r'\bsenal\b': 'señal',
    r'\bdiseno\b': 'diseño',
    r'\bdisenos\b': 'diseños',
    r'\bensenanza\b': 'enseñanza',
    r'\bensenanzas\b': 'enseñanzas',
    r'\bensenar\b': 'enseñar',
    r'\bensenamos\b': 'enseñamos',

    # Adverbs
    r'\brapidamente\b': 'rápidamente',
    r'\bfacilmente\b': 'fácilmente',
    r'\bdificilmente\b': 'difícilmente',
    r'\bautomaticamente\b': 'automáticamente',
    r'\bsistematicamente\b': 'sistemáticamente',
    r'\bpracticamente\b': 'prácticamente',
    r'\btecnicamente\b': 'técnicamente',
    r'\bpoliticamente\b': 'políticamente',
    r'\beticamente\b': 'éticamente',
    r'\bhistoricamente\b': 'históricamente',
    r'\bfisicamente\b': 'físicamente',
    r'\bpsicologicamente\b': 'psicológicamente',
    r'\beconomicamente\b': 'económicamente',
    r'\bultimamente\b': 'últimamente',
    r'\bunicamente\b': 'únicamente',
    r'\bpublicamente\b': 'públicamente',
    r'\bespecificamente\b': 'específicamente',
    r'\bironicamente\b': 'irónicamente',
}


def fix_spanish_text(text: str) -> str:
    """Apply all orthographic fixes to Spanish text."""
    result = text

    for pattern, replacement in ACCENT_FIXES.items():
        try:
            result = re.sub(pattern, replacement, result)
        except re.error as e:
            print(f"  Warning: Skipping pattern '{pattern}': {e}")

    return result


def process_spanish_essays(essays_dir: Path) -> dict:
    """Process all Spanish essays and fix orthography."""
    stats = {
        'processed': 0,
        'modified': 0,
        'files': []
    }

    for filepath in sorted(essays_dir.glob("*.html")):
        if filepath.name == "index.html":
            continue

        content = filepath.read_text(encoding='utf-8')

        # Check if Spanish
        if 'lang="es"' not in content[:500]:
            continue

        stats['processed'] += 1

        # Apply fixes
        fixed_content = fix_spanish_text(content)

        if fixed_content != content:
            stats['modified'] += 1
            stats['files'].append(filepath.name)
            filepath.write_text(fixed_content, encoding='utf-8')
            print(f"  Fixed: {filepath.name}")

    return stats


if __name__ == "__main__":
    essays_dir = Path("essays")

    if not essays_dir.exists():
        print("Error: essays directory not found")
        exit(1)

    print("Processing Spanish essays for remaining orthography issues...")
    stats = process_spanish_essays(essays_dir)

    print(f"\nResults:")
    print(f"  Processed: {stats['processed']} Spanish essays")
    print(f"  Modified: {stats['modified']} files")
