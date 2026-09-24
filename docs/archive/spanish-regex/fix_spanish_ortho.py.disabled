#!/usr/bin/env python3
"""
Fix Spanish orthography in essays.
Adds missing accents, ñ, and punctuation marks.
"""

import re
from pathlib import Path

# Dictionary of common words that need accents
# Format: wrong -> correct
ACCENT_FIXES = {
    # Common words with acute accents
    r'\bmovil\b': 'móvil',
    r'\bMovil\b': 'Móvil',
    r'\bmaquina\b': 'máquina',
    r'\bMaquina\b': 'Máquina',
    r'\bmaquinas\b': 'máquinas',
    r'\bMaquinas\b': 'Máquinas',
    r'\bnumero\b': 'número',
    r'\bNumero\b': 'Número',
    r'\bnumeros\b': 'números',
    r'\btelefono\b': 'teléfono',
    r'\bTelefono\b': 'Teléfono',
    r'\btelefonos\b': 'teléfonos',
    r'\bpequeno\b': 'pequeño',
    r'\bPequeno\b': 'Pequeño',
    r'\bpequena\b': 'pequeña',
    r'\bpequenas\b': 'pequeñas',
    r'\bpequenos\b': 'pequeños',
    r'\bultima\b': 'última',
    r'\bUltima\b': 'Última',
    r'\bultimo\b': 'último',
    r'\bUltimo\b': 'Último',
    r'\bultimos\b': 'últimos',
    r'\bultimas\b': 'últimas',
    r'\bdecada\b': 'década',
    r'\bdecadas\b': 'décadas',
    r'\bmayoria\b': 'mayoría',
    r'\bMayoria\b': 'Mayoría',
    r'\bcuestion\b': 'cuestión',
    r'\bcuestiones\b': 'cuestiones',
    r'\bexito\b': 'éxito',
    r'\bExito\b': 'Éxito',
    r'\bexitos\b': 'éxitos',
    r'\binformacion\b': 'información',
    r'\bInformacion\b': 'Información',
    r'\bcraneo\b': 'cráneo',
    r'\bcraneos\b': 'cráneos',
    r'\bfilosofo\b': 'filósofo',
    r'\bfilosofos\b': 'filósofos',
    r'\bFilosofo\b': 'Filósofo',
    r'\bfilosofia\b': 'filosofía',
    r'\bFilosofia\b': 'Filosofía',
    r'\bdireccion\b': 'dirección',
    r'\bDireccion\b': 'Dirección',
    r'\bdirecciones\b': 'direcciones',
    r'\bfusion\b': 'fusión',
    r'\bFusion\b': 'Fusión',
    r'\bfusiones\b': 'fusiones',
    r'\bdistopico\b': 'distópico',
    r'\bdistopica\b': 'distópica',
    r'\bautomatico\b': 'automático',
    r'\bAutomatico\b': 'Automático',
    r'\bautomatica\b': 'automática',
    r'\bautomaticos\b': 'automáticos',
    r'\bautomaticas\b': 'automáticas',
    r'\bhibrido\b': 'híbrido',
    r'\bhibridos\b': 'híbridos',
    r'\bhibrida\b': 'híbrida',
    r'\bhabito\b': 'hábito',
    r'\bhabitos\b': 'hábitos',
    r'\bnavegacion\b': 'navegación',
    r'\borientacion\b': 'orientación',
    r'\bincomodo\b': 'incómodo',
    r'\bincomoda\b': 'incómoda',
    r'\blimite\b': 'límite',
    r'\blimites\b': 'límites',
    r'\bLimite\b': 'Límite',
    r'\batencion\b': 'atención',
    r'\bAtencion\b': 'Atención',
    r'\bsabiduria\b': 'sabiduría',
    r'\brazon\b': 'razón',
    r'\brazones\b': 'razones',
    r'\bRazon\b': 'Razón',
    r'\bepico\b': 'épico',
    r'\bepicos\b': 'épicos',
    r'\bepica\b': 'épica',
    r'\bironia\b': 'ironía',
    r'\bironias\b': 'ironías',
    r'\breflexion\b': 'reflexión',
    r'\breflexiones\b': 'reflexiones',
    r'\bextension\b': 'extensión',
    r'\bextensiones\b': 'extensiones',
    r'\btambien\b': 'también',
    r'\bTambien\b': 'También',
    r'\bversion\b': 'versión',
    r'\bVersion\b': 'Versión',
    r'\bversiones\b': 'versiones',
    r'\bcognicion\b': 'cognición',
    r'\basi\b': 'así',
    r'\bAsi\b': 'Así',
    r'\bficcion\b': 'ficción',
    r'\bFiccion\b': 'Ficción',
    r'\bcapitulo\b': 'capítulo',
    r'\bCapitulo\b': 'Capítulo',
    r'\bcapitulos\b': 'capítulos',
    r'\bexternalizacion\b': 'externalización',

    # Más/mas distinction (adverb vs conjunction)
    r'\bmas alla\b': 'más allá',
    r'\bMas alla\b': 'Más allá',
    r'\bmas de\b': 'más de',
    r'\bmas que\b': 'más que',
    r'\bmas o menos\b': 'más o menos',
    r'\bnada mas\b': 'nada más',
    r'\bmucho mas\b': 'mucho más',
    r'\bpoco mas\b': 'poco más',
    r'\bcada vez mas\b': 'cada vez más',
    r'\bmas tarde\b': 'más tarde',
    r'\bmas temprano\b': 'más temprano',
    r'\bmas bien\b': 'más bien',
    r'\bmas importante\b': 'más importante',
    r'\bmas potente\b': 'más potente',
    r'\bmas profundo\b': 'más profundo',
    r'\bmas complejo\b': 'más complejo',
    r'\bmas simple\b': 'más simple',
    r'\bMas de Kwalia\b': 'Más de Kwalia',
    r'\bSaber mas\b': 'Saber más',
    r'\bmas adentro\b': 'más adentro',
    r'\binfinitamente mas\b': 'infinitamente más',
    r'\bvolviernos mas\b': 'volviéndonos más',
    r'\bvolvernos mas\b': 'volvernos más',
    r'(?<![a-záéíóú])mas(?![a-záéíóú])': 'más',  # standalone más

    # Años
    r'\banos\b': 'años',
    r'\bAno\b': 'Año',
    r'\bano\b': 'año',
    r'\bdano\b': 'daño',
    r'\bdanos\b': 'daños',

    # Verb forms with accents
    r'\bocurrio\b': 'ocurrió',
    r'\bOcurrio\b': 'Ocurrió',
    r'\bargumento\b': 'argumentó',
    r'\bdestruiria\b': 'destruiría',
    r'\bpredijo\b': 'predijo',
    r'\bsucedio\b': 'sucedió',
    r'\bconvirtio\b': 'convirtió',
    r'\bdecidio\b': 'decidió',
    r'\bexistio\b': 'existió',
    r'\bsurgio\b': 'surgió',
    r'\bcambio(?!\s+de)\b': 'cambió',  # verb, not noun
    r'\banuncio(?=\s+que|\s+la|\s+el)\b': 'anunció',  # verb form

    # Conditional/future verb endings
    r'\bseria\b': 'sería',
    r'\bpodria\b': 'podría',
    r'\bPodria\b': 'Podría',
    r'\bdeberia\b': 'debería',
    r'\bDeberia\b': 'Debería',
    r'\btendria\b': 'tendría',
    r'\bhabria\b': 'habría',
    r'\bqueria\b': 'quería',
    r'\bestaria\b': 'estaría',
    r'\bharia\b': 'haría',
    r'\bdiria\b': 'diría',
    r'\bveria\b': 'vería',
    r'\bvendria\b': 'vendría',
    r'\bsabria\b': 'sabría',
    r'\bpasaria\b': 'pasaría',
    r'\bexistiria\b': 'existiría',
    r'\bcreeria\b': 'creería',
    r'\bpareceria\b': 'parecería',
    r'\bimportaria\b': 'importaría',

    # Imperfect tense
    r'\bsolian\b': 'solían',
    r'\btenian\b': 'tenían',
    r'\bhacian\b': 'hacían',
    r'\bdecian\b': 'decían',
    r'\bpodian\b': 'podían',
    r'\bquerian\b': 'querían',
    r'\bsabian\b': 'sabían',
    r'\bestaban\b': 'estaban',
    r'\beran\b': 'eran',
    r'\bvenian\b': 'venían',
    r'\bvivian\b': 'vivían',
    r'\bexistian\b': 'existían',

    # Conditional plural
    r'\bseriamos\b': 'seríamos',
    r'\bpodriamos\b': 'podríamos',
    r'\bdeberiamos\b': 'deberíamos',
    r'\bfusionaramos\b': 'fusionáramos',
    r'\bllevariamos\b': 'llevaríamos',
    r'\bbuscariamos\b': 'buscaríamos',
    r'\bhariamos\b': 'haríamos',
    r'\btendriamos\b': 'tendríamos',

    # Present tense with accents
    r'\bestas\b': 'estás',
    r'\bEstas\b': 'Estás',
    r'\besta(?=\s+(?:a\s+punto|en|siendo|pasando|ocurriendo|sucediendo|trabajando|escribiendo))\b': 'está',

    # Common words
    r'\btecnologia\b': 'tecnología',
    r'\bTecnologia\b': 'Tecnología',
    r'\btecnologias\b': 'tecnologías',
    r'\bbiologia\b': 'biología',
    r'\bpsicologia\b': 'psicología',
    r'\bsociologia\b': 'sociología',
    r'\beconomia\b': 'economía',
    r'\bEconomia\b': 'Economía',
    r'\bdemocratica\b': 'democrática',
    r'\bdemocratico\b': 'democrático',
    r'\bautomatica\b': 'automática',
    r'\bsistematico\b': 'sistemático',
    r'\bsistematica\b': 'sistemática',
    r'\bpractica\b': 'práctica',
    r'\bpractico\b': 'práctico',
    r'\bPractica\b': 'Práctica',
    r'\btecnica\b': 'técnica',
    r'\btecnico\b': 'técnico',
    r'\bcritica\b': 'crítica',
    r'\bcritico\b': 'crítico',
    r'\bCritica\b': 'Crítica',
    r'\bpolitica\b': 'política',
    r'\bPolitica\b': 'Política',
    r'\bpolitico\b': 'político',
    r'\bpoliticos\b': 'políticos',
    r'\betica\b': 'ética',
    r'\bEtica\b': 'Ética',
    r'\betico\b': 'ético',
    r'\balgoritmo\b': 'algoritmo',  # no accent needed
    r'\balgoritmica\b': 'algorítmica',
    r'\balgoritmico\b': 'algorítmico',
    r'\bproposito\b': 'propósito',
    r'\bpropositos\b': 'propósitos',
    r'\bmetodo\b': 'método',
    r'\bmetodos\b': 'métodos',
    r'\btermino\b': 'término',
    r'\bterminos\b': 'términos',
    r'\bcodigo\b': 'código',
    r'\bcodigos\b': 'códigos',
    r'\bperiodo\b': 'período',
    r'\bperiodos\b': 'períodos',
    r'\bnumerico\b': 'numérico',
    r'\bnumerica\b': 'numérica',
    r'\bhistorico\b': 'histórico',
    r'\bhistorica\b': 'histórica',
    r'\bhistoria\b': 'historia',  # no accent
    r'\bteorico\b': 'teórico',
    r'\bteoria\b': 'teoría',
    r'\bteoricamente\b': 'teóricamente',
    r'\bfisico\b': 'físico',
    r'\bfisica\b': 'física',
    r'\bquimico\b': 'químico',
    r'\bquimica\b': 'química',
    r'\bbiologico\b': 'biológico',
    r'\bbiologica\b': 'biológica',
    r'\bgenero\b': 'género',
    r'\bgeneros\b': 'géneros',
    r'\bcaracter\b': 'carácter',
    r'\bcaracteres\b': 'caracteres',
    r'\bdialoogo\b': 'diálogo',
    r'\bdialogo\b': 'diálogo',
    r'\bdialogos\b': 'diálogos',
    r'\bmonopologo\b': 'monólogo',
    r'\bcatalogo\b': 'catálogo',
    r'\banalogo\b': 'análogo',
    r'\banaloga\b': 'análoga',
    r'\banalisis\b': 'análisis',
    r'\bAnalisis\b': 'Análisis',
    r'\bsintesis\b': 'síntesis',
    r'\bhipotesis\b': 'hipótesis',
    r'\bparentesis\b': 'paréntesis',
    r'\benfasis\b': 'énfasis',
    r'\btesis\b': 'tesis',  # no accent
    r'\bcrisis\b': 'crisis',  # no accent
    r'\bbasico\b': 'básico',
    r'\bbasica\b': 'básica',
    r'\bbasicos\b': 'básicos',
    r'\bbasicamente\b': 'básicamente',
    r'\bclasico\b': 'clásico',
    r'\bclasica\b': 'clásica',
    r'\borganico\b': 'orgánico',
    r'\borganica\b': 'orgánica',
    r'\bmecanico\b': 'mecánico',
    r'\bmecanica\b': 'mecánica',
    r'\belectrico\b': 'eléctrico',
    r'\belectrica\b': 'eléctrica',
    r'\belectronico\b': 'electrónico',
    r'\belectronica\b': 'electrónica',
    r'\bdigital\b': 'digital',  # no accent
    r'\bartificial\b': 'artificial',  # no accent
    r'\bnatural\b': 'natural',  # no accent
    r'\breal\b': 'real',  # no accent
    r'\bvirtual\b': 'virtual',  # no accent
    r'\bmental\b': 'mental',  # no accent
    r'\bmoral\b': 'moral',  # no accent
    r'\bsocial\b': 'social',  # no accent
    r'\bglobal\b': 'global',  # no accent
    r'\blocal\b': 'local',  # no accent
    r'\bnacional\b': 'nacional',  # no accent
    r'\binternacional\b': 'internacional',  # no accent
    r'\btradicional\b': 'tradicional',  # no accent
    r'\bracional\b': 'racional',  # no accent
    r'\bemocional\b': 'emocional',  # no accent
    r'\bpersonal\b': 'personal',  # no accent
    r'\buniversal\b': 'universal',  # no accent
    r'\boriginal\b': 'original',  # no accent
    r'\bfinal\b': 'final',  # no accent
    r'\bgeneral\b': 'general',  # no accent
    r'\bespecial\b': 'especial',  # no accent
    r'\bpotencial\b': 'potencial',  # no accent
    r'\besencial\b': 'esencial',  # no accent
    r'\bexistencial\b': 'existencial',  # no accent

    # Interrogatives and exclamatives (need accent)
    r'\bque pasa\b': 'qué pasa',
    r'\bQue pasa\b': 'Qué pasa',
    r'\bque es\b': 'qué es',
    r'\bQue es\b': 'Qué es',
    r'\bque significa\b': 'qué significa',
    r'\bque significa\b': 'qué significa',
    r'\bque hace\b': 'qué hace',
    r'\bque haces\b': 'qué haces',
    r'\bque hacemos\b': 'qué hacemos',
    r'\bque pensamientos\b': 'qué pensamientos',
    r'\bque tipo\b': 'qué tipo',
    r'\bque clase\b': 'qué clase',
    r'\bque habilidad\b': 'qué habilidad',
    r'\bcomo sabes\b': 'cómo sabes',
    r'\bComo sabes\b': 'Cómo sabes',
    r'\bcomo saber\b': 'cómo saber',
    r'\bcomo piensas\b': 'cómo piensas',
    r'\bcomo pensar\b': 'cómo pensar',
    r'\bcomo hacer\b': 'cómo hacer',
    r'\bcomo funciona\b': 'cómo funciona',
    r'\bComo funciona\b': 'Cómo funciona',
    r'\bcomo se\b': 'cómo se',
    r'\bComo se\b': 'Cómo se',
    r'\bcomo la\b': 'cómo la',
    r'\bcomo lo\b': 'cómo lo',
    r'\bcomo nos\b': 'cómo nos',
    r'\bcomo los\b': 'cómo los',
    r'\bcomo las\b': 'cómo las',
    r'\bcuando confiar\b': 'cuándo confiar',
    r'\bCuando confiar\b': 'Cuándo confiar',
    r'\bdonde esta\b': 'dónde está',
    r'\bdonde estan\b': 'dónde están',
    r'\bpor que\b': 'por qué',
    r'\bPor que\b': 'Por qué',
    r'\bpara que\b': 'para qué',
    r'\bcual es\b': 'cuál es',
    r'\bCual es\b': 'Cuál es',
    r'\bcuales son\b': 'cuáles son',
    r'\bquien es\b': 'quién es',
    r'\bQuien es\b': 'Quién es',
    r'\bquien sabe\b': 'quién sabe',
    r'\bquienes son\b': 'quiénes son',
    r'\bcuanto\b': 'cuánto',
    r'\bcuanta\b': 'cuánta',
    r'\bcuantos\b': 'cuántos',
    r'\bcuantas\b': 'cuántas',
    r'\bQuieres\b': '¿Quieres',  # Opening question mark

    # Demonstratives with accent (when pronouns, not adjectives)
    # These are tricky - modern RAE allows both, but traditionally:
    # éste/ésta/éstos/éstas (pronouns) vs este/esta/estos/estas (adjectives)
    # We'll leave most as-is but fix obvious pronoun cases

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
    r'\bcognitivamente\b': 'cognitivamente',
    r'\bultimamente\b': 'últimamente',
    r'\bunicamente\b': 'únicamente',
    r'\bpublicamente\b': 'públicamente',
    r'\bspecificamente\b': 'específicamente',

    # Common nouns
    r'\balgun\b': 'algún',
    r'\bningun\b': 'ningún',
    r'\bcomun\b': 'común',
    r'\bsegun\b': 'según',
    r'\bSegun\b': 'Según',
    r'\binteres\b': 'interés',
    r'\bintereses\b': 'intereses',  # plural no accent
    r'\bjoven\b': 'joven',  # no accent
    r'\bjovenes\b': 'jóvenes',
    r'\bimagen\b': 'imagen',  # no accent
    r'\bimagenes\b': 'imágenes',
    r'\borden\b': 'orden',  # no accent
    r'\bordenes\b': 'órdenes',
    r'\borigen\b': 'origen',  # no accent
    r'\borigenes\b': 'orígenes',
    r'\bmargen\b': 'margen',  # no accent
    r'\bmargenes\b': 'márgenes',
    r'\bvolumen\b': 'volumen',  # no accent
    r'\bvolumenes\b': 'volúmenes',
    r'\bexamen\b': 'examen',  # no accent
    r'\bexamenes\b': 'exámenes',
    r'\bcrimen\b': 'crimen',  # no accent
    r'\bcrimenes\b': 'crímenes',
    r'\bregimen\b': 'régimen',
    r'\bregimenes\b': 'regímenes',
    r'\bocean\b': 'océano',
    r'\boceano\b': 'océano',

    # Miscellaneous
    r'\btravés\b': 'través',  # already correct but ensuring
    r'\btraves\b': 'través',
    r'\ba traves\b': 'a través',
    r'\bdespues\b': 'después',
    r'\bDespues\b': 'Después',
    r'\bantes\b': 'antes',  # no accent
    r'\bahora\b': 'ahora',  # no accent
    r'\btodavia\b': 'todavía',
    r'\bTodavia\b': 'Todavía',
    r'\bquiza\b': 'quizá',
    r'\bquizas\b': 'quizás',
    r'\bdetras\b': 'detrás',
    r'\bmas\b': 'más',
    r'\bMas\b': 'Más',
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
    r'\bdonde\b': 'donde',  # relative - no accent
    r'\bcomo\b': 'como',  # relative - no accent
    r'\bcuando\b': 'cuando',  # relative - no accent
    r'\bSocrates\b': 'Sócrates',
    r'\bPlaton\b': 'Platón',
    r'\bAristoteles\b': 'Aristóteles',

    # Proper nouns and titles
    r'\bEspana\b': 'España',
    r'\bEspanol\b': 'Español',
    r'\bespanol\b': 'español',
    r'\bespanoles\b': 'españoles',
    r'\bBritanico\b': 'Británico',
    r'\bbritanico\b': 'británico',
    r'\bAmericano\b': 'Americano',  # no accent
    r'\bMexico\b': 'México',
    r'\bmexicano\b': 'mexicano',  # no accent

    # UI elements
    r'\bAvisame\b': 'Avísame',
    r'\bSuscribete\b': 'Suscríbete',

    # Sólo/solo - modern RAE says no accent needed, but many still use it
    # We'll keep it without accent as per modern standard

    # Specific patterns for this content
    r'\bsenales\b': 'señales',
    r'\bsenal\b': 'señal',
    r'\bdeseno\b': 'diseño',
    r'\bdiseno\b': 'diseño',
    r'\bdisenos\b': 'diseños',
    r'\bensenanza\b': 'enseñanza',
    r'\bensenanzas\b': 'enseñanzas',
    r'\bempeno\b': 'empeño',
    r'\bsueno\b': 'sueño',
    r'\bsuenos\b': 'sueños',
    r'\botono\b': 'otoño',
    r'\binverno\b': 'invierno',  # no ñ
    r'\bmontana\b': 'montaña',
    r'\bmontanas\b': 'montañas',
    r'\bcompania\b': 'compañía',
    r'\bcompanias\b': 'compañías',
    r'\bespanol\b': 'español',
    r'\bcampana\b': 'campaña',
    r'\bcampanas\b': 'campañas',
    r'\bbanera\b': 'bañera',
    r'\bnino\b': 'niño',
    r'\bnina\b': 'niña',
    r'\bninos\b': 'niños',
    r'\bninas\b': 'niñas',
    r'\bmanana\b': 'mañana',
    r'\bManana\b': 'Mañana',
    r'\bengano\b': 'engaño',
    r'\benganos\b': 'engaños',
    r'\btamano\b': 'tamaño',
    r'\btamanos\b': 'tamaños',
    r'\bestrano\b': 'extraño',
    r'\bextrano\b': 'extraño',
    r'\bextranos\b': 'extraños',
    r'\bextrana\b': 'extraña',

    # Words ending in -cion
    r'\baccion\b': 'acción',
    r'\bAccion\b': 'Acción',
    r'\bacciones\b': 'acciones',
    r'\breaccion\b': 'reacción',
    r'\breacciones\b': 'reacciones',
    r'\brelacion\b': 'relación',
    r'\bRelacion\b': 'Relación',
    r'\brelaciones\b': 'relaciones',
    r'\bsituacion\b': 'situación',
    r'\bSituacion\b': 'Situación',
    r'\bsituaciones\b': 'situaciones',
    r'\bpoblacion\b': 'población',
    r'\bcomunicacion\b': 'comunicación',
    r'\beducacion\b': 'educación',
    r'\bEducacion\b': 'Educación',
    r'\borganizacion\b': 'organización',
    r'\borganizaciones\b': 'organizaciones',
    r'\bcivilizacion\b': 'civilización',
    r'\bgeneracion\b': 'generación',
    r'\bGeneracion\b': 'Generación',
    r'\bgeneraciones\b': 'generaciones',
    r'\bconversacion\b': 'conversación',
    r'\bconversaciones\b': 'conversaciones',
    r'\bcreacion\b': 'creación',
    r'\bCreacion\b': 'Creación',
    r'\bevolucion\b': 'evolución',
    r'\bEvolucion\b': 'Evolución',
    r'\brevolucion\b': 'revolución',
    r'\bRevolucion\b': 'Revolución',
    r'\bsolucion\b': 'solución',
    r'\bsoluciones\b': 'soluciones',
    r'\bconclusión\b': 'conclusión',
    r'\bconclusion\b': 'conclusión',
    r'\bconclusiones\b': 'conclusiones',
    r'\bdecision\b': 'decisión',
    r'\bDecision\b': 'Decisión',
    r'\bdecisiones\b': 'decisiones',
    r'\bproduccion\b': 'producción',
    r'\bconstruccion\b': 'construcción',
    r'\bdestruccion\b': 'destrucción',
    r'\binstitucion\b': 'institución',
    r'\binstituciones\b': 'instituciones',
    r'\bconstitucion\b': 'constitución',
    r'\bconcentracion\b': 'concentración',
    r'\badministracion\b': 'administración',
    r'\bimaginacion\b': 'imaginación',
    r'\bautorizacion\b': 'autorización',
    r'\bidentificacion\b': 'identificación',
    r'\bverificacion\b': 'verificación',
    r'\bprogramacion\b': 'programación',
    r'\bintencion\b': 'intención',
    r'\bintenciones\b': 'intenciones',
    r'\bemocion\b': 'emoción',
    r'\bemociones\b': 'emociones',
    r'\bnocion\b': 'noción',
    r'\bnociones\b': 'nociones',
    r'\bfuncion\b': 'función',
    r'\bfunciones\b': 'funciones',
    r'\bopcion\b': 'opción',
    r'\bopciones\b': 'opciones',
    r'\bseccion\b': 'sección',
    r'\bsecciones\b': 'secciones',
    r'\bleccion\b': 'lección',
    r'\blecciones\b': 'lecciones',
    r'\bconexion\b': 'conexión',
    r'\bconexiones\b': 'conexiones',
    r'\breflexion\b': 'reflexión',
    r'\breflexiones\b': 'reflexiones',
    r'\bexpresion\b': 'expresión',
    r'\bexpresiones\b': 'expresiones',
    r'\bimpresion\b': 'impresión',
    r'\bcompresion\b': 'compresión',
    r'\bcomprension\b': 'comprensión',
    r'\bdimension\b': 'dimensión',
    r'\bdimensiones\b': 'dimensiones',
    r'\bextension\b': 'extensión',
    r'\bextensiones\b': 'extensiones',
    r'\bpension\b': 'pensión',
    r'\btension\b': 'tensión',
    r'\bversion\b': 'versión',
    r'\bversiones\b': 'versiones',
    r'\binversion\b': 'inversión',
    r'\bconversion\b': 'conversión',
    r'\bdiscusion\b': 'discusión',
    r'\bconfusion\b': 'confusión',
    r'\bilusion\b': 'ilusión',
    r'\bilusiones\b': 'ilusiones',
    r'\bconclusion\b': 'conclusión',
    r'\bexclusion\b': 'exclusión',
    r'\binclusion\b': 'inclusión',
    r'\bprofesion\b': 'profesión',
    r'\bprofesiones\b': 'profesiones',
    r'\bposesion\b': 'posesión',
    r'\bobsesion\b': 'obsesión',
    r'\bdepresion\b': 'depresión',
    r'\bopresion\b': 'opresión',
    r'\bregresion\b': 'regresión',
    r'\bprogresion\b': 'progresión',
    r'\bagresion\b': 'agresión',
    r'\bsesion\b': 'sesión',
    r'\bsesiones\b': 'sesiones',
    r'\bmision\b': 'misión',
    r'\bmisiones\b': 'misiones',
    r'\bvision\b': 'visión',
    r'\bvisiones\b': 'visiones',
    r'\brevision\b': 'revisión',
    r'\bprovision\b': 'provisión',
    r'\bdivision\b': 'división',
    r'\bdivisiones\b': 'divisiones',
    r'\bprecision\b': 'precisión',
    r'\bdecision\b': 'decisión',
    r'\bcolision\b': 'colisión',
    r'\bocasion\b': 'ocasión',
    r'\bocasiones\b': 'ocasiones',
    r'\bpersuasion\b': 'persuasión',
    r'\binvasion\b': 'invasión',
    r'\bevasion\b': 'evasión',
    r'\bexplosion\b': 'explosión',
    r'\bimplosion\b': 'implosión',

    # Words ending in -miento (no accent needed, but verify)

    # Exclamation handling
    r'\bGracias!': '¡Gracias!',
    r'\bAnotado!': '¡Anotado!',
    r'^Gracias!': '¡Gracias!',

    # Specific to these essays
    r'\bconocimiento-de-como-acceder\b': 'conocimiento-de-cómo-acceder',
    r'\bEl espectro\b': 'El espectro',  # no change
    r'\bespectro\b': 'espectro',  # no change
}

# Additional patterns for UI elements that need both opening and closing marks
PUNCTUATION_FIXES = [
    # Questions starting sentences
    (r'(?<![¿\w])Quieres\s', '¿Quieres '),
    (r'(?<![¿\w])Que\s+(?=pasa|significa|es|hace|haces|tal)', '¿Qué '),
    (r'(?<![¿\w])Como\s+(?=estas|esta|sabes|se|funciona|hacer|piensas|pensar)', '¿Cómo '),
    (r'(?<![¿\w])Donde\s+(?=esta|estan|hay|vive|queda)', '¿Dónde '),
    (r'(?<![¿\w])Cuando\s+(?=fue|es|sera|viene|llega)', '¿Cuándo '),
    (r'(?<![¿\w])Por que\s+', '¿Por qué '),
    (r'(?<![¿\w])Cual\s+(?=es|fue|sera)', '¿Cuál '),
    (r'(?<![¿\w])Quien\s+(?=es|fue|sabe|puede)', '¿Quién '),
    (r'(?<![¿\w])Cuanto\s+', '¿Cuánto '),
    (r'(?<![¿\w])Cuanta\s+', '¿Cuánta '),

    # Questions ending
    (r'(?<!\?)(\s*)$', r'?\1'),  # Not applicable for HTML

    # Exclamations
    (r'(?<![¡\w])Gracias!', '¡Gracias!'),
    (r'(?<![¡\w])Anotado!', '¡Anotado!'),
    (r'(?<![¡\w])Felicidades!', '¡Felicidades!'),
    (r'(?<![¡\w])Bienvenido!', '¡Bienvenido!'),
    (r'(?<![¡\w])Excelente!', '¡Excelente!'),
]


def fix_spanish_text(text: str) -> str:
    """Apply all orthographic fixes to Spanish text."""
    result = text

    # Apply word-level fixes
    for pattern, replacement in ACCENT_FIXES.items():
        try:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE if pattern[0] != '\\' else 0)
        except re.error:
            # If pattern fails, try without flags
            try:
                result = re.sub(pattern, replacement, result)
            except re.error as e:
                print(f"  Warning: Skipping pattern '{pattern}': {e}")

    # Apply punctuation fixes
    for pattern, replacement in PUNCTUATION_FIXES:
        try:
            result = re.sub(pattern, replacement, result)
        except re.error as e:
            print(f"  Warning: Skipping punctuation pattern: {e}")

    return result


def process_spanish_essays(essays_dir: Path, dry_run: bool = False) -> dict:
    """Process all Spanish essays and fix orthography."""
    stats = {
        'processed': 0,
        'modified': 0,
        'errors': 0,
        'files': []
    }

    for filepath in sorted(essays_dir.glob("*.html")):
        if filepath.name == "index.html":
            continue

        try:
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

                if not dry_run:
                    filepath.write_text(fixed_content, encoding='utf-8')
                    print(f"  Fixed: {filepath.name}")
                else:
                    print(f"  Would fix: {filepath.name}")

        except Exception as e:
            stats['errors'] += 1
            print(f"  Error processing {filepath.name}: {e}")

    return stats


if __name__ == "__main__":
    import sys

    essays_dir = Path("essays")

    if not essays_dir.exists():
        print("Error: essays directory not found")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv

    print(f"Processing Spanish essays {'(dry run)' if dry_run else ''}...")
    stats = process_spanish_essays(essays_dir, dry_run=dry_run)

    print(f"\nResults:")
    print(f"  Processed: {stats['processed']} Spanish essays")
    print(f"  Modified: {stats['modified']} files")
    print(f"  Errors: {stats['errors']}")

    if stats['files']:
        print(f"\nModified files:")
        for f in stats['files']:
            print(f"  - {f}")
