"""
DATOS MANUALES DE LAS FICHAS
========================================================

Este es el ÚNICO archivo que tienes que editar a mano. Aquí van las dos
cosas que ningún robot puede rellenar por ti:

  1. CALENDARIO_REGULATORIO: próximas fechas o hitos clave de cada empresa
     (decisiones de la FDA, lecturas de fase III, resultados trimestrales...).
  2. CONTEXTO_BURSATIL: una o dos frases sobre dónde está la acción
     (cerca de máximos, de mínimos, lateral...) con la fuente y la fecha.

Cómo editarlo (desde la web de GitHub, sin instalar nada):
  - Abre este archivo y pulsa el lápiz (Edit).
  - Cambia solo el texto que está entre comillas "...".
  - Cada línea entre comillas acaba en coma. No borres comillas ni comas.
  - Pulsa "Commit changes". En un minuto, las fichas se regeneran solas.

Si dejas una empresa con la lista vacía [] o el texto vacío "", ese bloque
simplemente no se muestra en su ficha. No da error.

IMPORTANTE: revisa lo que hay escrito antes de publicar las fichas. Es un
punto de partida basado en lo investigado en las piezas semanales y puede
haber cambiado.
"""

CALENDARIO_REGULATORIO = {
    "GSK": [
        "26 oct. 2026 — Decisión de la FDA (fecha PDUFA) sobre bepirovirsen en hepatitis B crónica.",
        "Exdensur (depemokimab): la FDA aprobó solo el asma grave en dic. 2025 y no concedió la poliposis nasal; GSK sigue en diálogo con la agencia.",
        "Fase III en reclutamiento: felcorekibart en asma y EPOC (programa PERSIST). Resultados a años vista.",
    ],
    "Bayer": [
        "Asundexian (ictus): solicitud en revisión prioritaria de la FDA; fecha de decisión por confirmar.",
        "Vericiguat en estenosis aórtica calcificada: ensayo de fase II en reclutamiento.",
    ],
    "Pfizer": [
        "Mevrometostat (cáncer de próstata): fase III MEVPRO-1 y MEVPRO-2 en curso; MEVPRO-3 (hormonosensible) planificado.",
        "Berobenatide (obesidad): programa de fase III en marcha; por confirmar hitos.",
    ],
    "Novartis": [
        "Tras los fracasos de fase III de pelacarsen y del-desiran (sept. 2026), vigilar cómo actualiza Novartis su plan de I+D cardiovascular y neuromuscular.",
        "YMI024: estudio de fase 2b en enfermedad coronaria con inflamación residual, en reclutamiento.",
    ],
    "Johnson & Johnson": [
        "Nipocalimab: fase III en lupus (SLE) en reclutamiento; designación Fast Track de la FDA.",
        "Vigilar el próximo informe trimestral: evolución de Stelara frente a Tremfya.",
    ],
}

CONTEXTO_BURSATIL = {
    "GSK": "Cierre del 25/09/2026 (ADR en NYSE): 49,24 $. Unos 6 % por debajo de su media de 200 sesiones y en torno a un 20 % por debajo del máximo de febrero. Fuente: TradingView.",
    "Bayer": "",
    "Pfizer": "",
    "Novartis": "",
    "Johnson & Johnson": "",
}
