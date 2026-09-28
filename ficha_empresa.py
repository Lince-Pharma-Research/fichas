"""
FICHA DE EMPRESA — Lince Pharma Research
========================================================

Qué hace este script:
1. Consulta ClinicalTrials.gov (API pública, sin clave) y trae los ensayos
   EN CURSO de cada empresa (reclutando, activos, próximos a empezar).
2. Los agrupa por fase (I, II, III, IV...) y cuenta cuántos hay en cada una.
3. Lee tus datos manuales (datos_manuales.py): calendario regulatorio y
   contexto bursátil.
4. Genera una página web por empresa dentro de la carpeta `docs/`, más un
   índice. GitHub Pages publica esa carpeta como web.

Cómo funciona en este repositorio:
   Un robot (GitHub Actions, ver .github/workflows/fichas.yml) ejecuta este
   script cada lunes y cada vez que editas datos_manuales.py. No hace falta
   ejecutarlo a mano ni instalar nada.

Si ClinicalTrials.gov falla para una empresa, su ficha anterior se conserva
tal cual (no se borra ni se vacía) y el aviso queda en el registro del robot.
"""

import html
import os
import sys
from datetime import datetime

import requests

from datos_manuales import CALENDARIO_REGULATORIO, CONTEXTO_BURSATIL

# ============================================================
# CONFIG
# ============================================================

# "patrocinadores": nombres con los que la empresa figura como PATROCINADOR
# PRINCIPAL en ClinicalTrials.gov. El primero es obligatorio; los demás se suman
# (sin duplicar ensayos). Si un nombre no existe, simplemente no suma nada.
# Comprobado en el registro: el nombre "GSK" solo recogía 5 ensayos en curso,
# porque la mayoría siguen registrados como "GlaxoSmithKline".
EMPRESAS = [
    {"nombre": "GSK", "patrocinadores": ["GlaxoSmithKline", "GSK", "ViiV Healthcare"]},
    {"nombre": "Bayer", "patrocinadores": ["Bayer"]},
    {"nombre": "Pfizer", "patrocinadores": ["Pfizer"]},
    {"nombre": "Novartis", "patrocinadores": ["Novartis Pharmaceuticals"]},
    {"nombre": "Johnson & Johnson",
     "patrocinadores": ["Janssen Research & Development, LLC",
                        "Johnson & Johnson Innovative Medicine"]},
]

SITIO_WEB = "https://lincepharmaresearch.beehiiv.com/"
NOMBRE_MARCA = "Lince Pharma Research"

MAX_ENSAYOS_POR_FASE = 6
CARPETA_SALIDA = "docs"

CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
ESTADOS_EN_CURSO = "RECRUITING,ACTIVE_NOT_RECRUITING,NOT_YET_RECRUITING,ENROLLING_BY_INVITATION"

NOMBRES_FASE = {
    "PHASE3": "Fase III",
    "PHASE2": "Fase II",
    "PHASE1": "Fase I",
    "PHASE4": "Fase IV (tras la comercialización)",
    "NA": "Sin fase (estudios observacionales, etc.)",
    "OTRA": "Fase no especificada",
}
ORDEN_FASES = ["PHASE3", "PHASE2", "PHASE1", "PHASE4", "NA", "OTRA"]

NOMBRES_ESTADO = {
    "RECRUITING": "Reclutando",
    "ACTIVE_NOT_RECRUITING": "Activo, sin reclutar",
    "NOT_YET_RECRUITING": "Aún sin reclutar",
    "ENROLLING_BY_INVITATION": "Reclutando por invitación",
}

# ============================================================
# LÓGICA
# ============================================================


def slug(nombre):
    return nombre.lower().replace("&", "and").replace(" ", "-")


def fase_principal(fases):
    """Si un ensayo tiene varias fases (p. ej. II y III), cuenta la más alta."""
    normalizadas = ["PHASE1" if f == "EARLY_PHASE1" else f for f in (fases or [])]
    for f in ["PHASE4", "PHASE3", "PHASE2", "PHASE1", "NA"]:
        if f in normalizadas:
            return f
    return "OTRA"


def _consultar_un_patrocinador(nombre_patrocinador):
    """Ensayos en curso con ese patrocinador principal. Devuelve lista o None si falla."""
    params = {
        "query.lead": nombre_patrocinador,
        "filter.overallStatus": ESTADOS_EN_CURSO,
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,LastUpdatePostDate",
        "pageSize": 1000,
        "sort": "LastUpdatePostDate:desc",
    }
    try:
        resp = requests.get(CLINICALTRIALS_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  [AVISO] No se pudo consultar '{nombre_patrocinador}': {e}")
        return None

    ensayos = []
    for study in data.get("studies", []):
        protocolo = study.get("protocolSection", {})
        ident = protocolo.get("identificationModule", {})
        estado = protocolo.get("statusModule", {})
        diseno = protocolo.get("designModule", {})
        ensayos.append({
            "nct_id": ident.get("nctId", ""),
            "titulo": ident.get("briefTitle", ""),
            "estado": estado.get("overallStatus", ""),
            "fase": fase_principal(diseno.get("phases", [])),
            "actualizado": estado.get("lastUpdatePostDateStruct", {}).get("date", ""),
        })
    print(f"  '{nombre_patrocinador}': {len(ensayos)} ensayos en curso")
    return ensayos


def consultar_pipeline(patrocinadores):
    """Suma los ensayos de todos los patrocinadores de la empresa, sin duplicados.
    Devuelve (lista, total) o (None, None) si falla el patrocinador principal."""
    unidos = {}
    for i, nombre in enumerate(patrocinadores):
        ensayos = _consultar_un_patrocinador(nombre)
        if ensayos is None:
            if i == 0:
                return None, None  # sin el principal, no publicamos datos parciales
            continue
        for e in ensayos:
            unidos.setdefault(e["nct_id"], e)
    lista = sorted(unidos.values(), key=lambda e: e["actualizado"], reverse=True)
    return lista, len(lista)


def resumir(ensayos, total):
    """Agrupa por fase y cuenta."""
    por_fase = {f: [] for f in ORDEN_FASES}
    for e in ensayos:
        por_fase[e["fase"]].append(e)
    return {
        "por_fase": por_fase,
        "conteo": {f: len(v) for f, v in por_fase.items()},
        "total": total,
        "descargados": len(ensayos),
    }


CSS = """
:root{--navy:#0B1F3A;--teal:#14B8A6;--ink:#1C2B3A;--muted:#5B6B7A;--bg:#F5F7FA;--line:#DDE3EA}
*{box-sizing:border-box}
body{font-family:'IBM Plex Sans',system-ui,sans-serif;background:var(--bg);color:var(--ink);margin:0}
.header{background:var(--navy);color:#fff;padding:26px 24px}
.header .in{max-width:920px;margin:0 auto}
.header a{color:#9FB3C8;text-decoration:none;font-size:14px}
.header h1{margin:8px 0 2px;font-family:'Source Serif 4',Georgia,serif;font-size:34px}
.header .sub{color:#9FB3C8;font-size:14px}
.container{max-width:920px;margin:0 auto;padding:28px 24px 48px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:22px;margin-bottom:22px}
.card h2{margin:0 0 12px;font-family:'Source Serif 4',Georgia,serif;color:var(--navy);font-size:22px}
.card h3{margin:18px 0 6px;font-size:16px;color:var(--navy)}
.badge{display:inline-block;background:#E7F8F5;color:#0F9C8C;border:1px solid #A9E4DB;
  padding:1px 8px;border-radius:5px;font-size:12px;font-weight:700;margin-left:6px}
ul{margin:6px 0 0;padding-left:20px}
li{margin:5px 0;font-size:14.5px;line-height:1.45}
a{color:#0F9C8C}
.note{font-size:12.5px;color:var(--muted);margin-top:10px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
th{background:#E7ECF3;color:var(--navy)}
tr.actual td{font-weight:700;background:#F5F7FA}
.tablewrap{overflow-x:auto}
.footer{max-width:920px;margin:0 auto;padding:0 24px 40px;font-size:12.5px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.grid a{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px;
  text-decoration:none;color:var(--navy);font-weight:700;font-size:18px}
"""

HEAD = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=IBM+Plex+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body>
"""

AVISO_LEGAL = ("Información con fines informativos, elaborada a partir de fuentes públicas. "
               "No constituye asesoramiento de inversión.")


def esc(t):
    return html.escape(str(t), quote=True)


def bloque_pipeline(nombre, resumen, patrocinadores):
    partes = []
    for fase in ORDEN_FASES:
        ensayos = resumen["por_fase"][fase]
        if not ensayos:
            continue
        partes.append(f"<h3>{esc(NOMBRES_FASE[fase])}<span class='badge'>{len(ensayos)}</span></h3><ul>")
        for e in ensayos[:MAX_ENSAYOS_POR_FASE]:
            estado = NOMBRES_ESTADO.get(e["estado"], e["estado"])
            partes.append(
                f"<li><a href='https://clinicaltrials.gov/study/{esc(e['nct_id'])}' target='_blank' rel='noopener'>"
                f"{esc(e['titulo'])}</a> — {esc(estado)}</li>")
        resto = len(ensayos) - MAX_ENSAYOS_POR_FASE
        if resto > 0:
            partes.append(f"<li><em>… y {resto} más</em></li>")
        partes.append("</ul>")
    if not partes:
        partes.append("<p><em>No hay ensayos en curso registrados para esta empresa.</em></p>")
    nota = (f"Ensayos en curso con la compañía como patrocinador principal en ClinicalTrials.gov: "
            f"<strong>{resumen['total']}</strong>. Patrocinadores contados: "
            f"{esc(', '.join(patrocinadores))}. Se muestran los más recientemente actualizados de cada fase.")
    return "".join(partes) + f"<p class='note'>{nota}</p>"


def bloque_lista(items):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def tabla_comparativa(actual, resumenes):
    filas = []
    for nombre, r in resumenes.items():
        clase = " class='actual'" if nombre == actual else ""
        if r is None:
            celdas = "<td>N/D</td><td>N/D</td><td>N/D</td><td>N/D</td>"
        else:
            c = r["conteo"]
            celdas = (f"<td>{r['total']}</td><td>{c['PHASE3']}</td>"
                      f"<td>{c['PHASE2']}</td><td>{c['PHASE1']}</td>")
        filas.append(f"<tr{clase}><td><a href='{slug(nombre)}.html'>{esc(nombre)}</a></td>{celdas}</tr>")
    return ("<div class='tablewrap'><table><tr><th>Empresa</th><th>Ensayos en curso</th>"
            "<th>Fase III</th><th>Fase II</th><th>Fase I</th></tr>" + "".join(filas) + "</table></div>"
            "<p class='note'>Recuento de ensayos en curso según ClinicalTrials.gov. "
            "Más ensayos no significa mejor pipeline: aquí se cuentan estudios, no su valor comercial.</p>")


def generar_html_ficha(empresa, resumen, resumenes):
    nombre = empresa["nombre"]
    hoy = datetime.now().strftime("%d/%m/%Y")
    out = [HEAD.format(titulo=esc(f"{nombre} — Ficha de empresa | {NOMBRE_MARCA}"), css=CSS)]
    out.append(f"<div class='header'><div class='in'><a href='{esc(SITIO_WEB)}'>← {esc(NOMBRE_MARCA)}</a>"
               f"<h1>{esc(nombre)}</h1><div class='sub'>Ficha de empresa · actualizada el {hoy}</div></div></div>")
    out.append("<div class='container'>")

    contexto = CONTEXTO_BURSATIL.get(nombre, "")
    if contexto:
        out.append(f"<div class='card'><h2>Contexto bursátil</h2><p>{esc(contexto)}</p></div>")

    out.append("<div class='card'><h2>Pipeline por fase</h2>"
               + bloque_pipeline(nombre, resumen, empresa["patrocinadores"]) + "</div>")

    calendario = CALENDARIO_REGULATORIO.get(nombre, [])
    if calendario:
        out.append("<div class='card'><h2>Calendario regulatorio</h2>" + bloque_lista(calendario) + "</div>")

    out.append("<div class='card'><h2>Comparativa con el resto de empresas</h2>"
               + tabla_comparativa(nombre, resumenes) + "</div>")
    out.append("</div>")
    out.append(f"<div class='footer'>{esc(AVISO_LEGAL)}<br><a href='index.html'>← Todas las fichas</a></div>")
    out.append("</body></html>")
    return "".join(out)


def generar_indice():
    tarjetas = "".join(f"<a href='{slug(e['nombre'])}.html'>{esc(e['nombre'])}</a>" for e in EMPRESAS)
    return (HEAD.format(titulo=esc(f"Fichas de empresa | {NOMBRE_MARCA}"), css=CSS)
            + f"<div class='header'><div class='in'><a href='{esc(SITIO_WEB)}'>← {esc(NOMBRE_MARCA)}</a>"
              f"<h1>Fichas de empresa</h1></div></div>"
              f"<div class='container'><div class='grid'>{tarjetas}</div></div>"
              f"<div class='footer'>{esc(AVISO_LEGAL)}</div></body></html>")


def main():
    print("Generando fichas de empresa...\n")
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    resumenes = {}
    for empresa in EMPRESAS:
        nombre = empresa["nombre"]
        print(f"Consultando pipeline: {nombre}")
        ensayos, total = consultar_pipeline(empresa["patrocinadores"])
        resumenes[nombre] = resumir(ensayos, total) if ensayos is not None else None

    generadas = 0
    for empresa in EMPRESAS:
        nombre = empresa["nombre"]
        resumen = resumenes[nombre]
        if resumen is None:
            print(f"  -> {nombre}: sin datos, se conserva la ficha anterior.")
            continue
        ruta = os.path.join(CARPETA_SALIDA, f"{slug(nombre)}.html")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(generar_html_ficha(empresa, resumen, resumenes))
        print(f"  -> Ficha generada: {ruta}")
        generadas += 1

    with open(os.path.join(CARPETA_SALIDA, "index.html"), "w", encoding="utf-8") as f:
        f.write(generar_indice())

    print(f"\nListo. {generadas} de {len(EMPRESAS)} fichas generadas en '{CARPETA_SALIDA}/'.")
    if generadas == 0:
        sys.exit(1)  # que el robot aparezca en rojo si no se generó ninguna


if __name__ == "__main__":
    main()
