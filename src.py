# -*- coding: utf-8 -*-
"""
SCOGLIERA FONDAZIONE - Modulo di calcolo (src.py)
Dimensionamento dell'apron fondazionale a protezione di una pila da ponte.
Input principali: D50 (da ScoglieraPila) e ys (da Scalzamento).
Versione professionale:
- Spessore, larghezza e affondamento dell'apron
- Volume totale + massa totale (con stima costo)
- Spessore strato filtro granulare
- Verifiche normative tabellari
- Tabella passaggi di calcolo estesa
- Generazione report PDF professionale
- Curve di sensitivita vs D50 e vs ys
- Validazione e commenti progettuali
"""
from __future__ import annotations

import datetime
import math
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

G = 9.81


# ---------------------------------------------------------------------------
# Dataclass risultati
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FondazioneDesign:
    D50: float
    spessore: float     # spessore apron [m]
    larghezza: float    # estensione laterale rispetto alla pila [m]
    sottofondo: float   # affondamento sotto il fondo attuale [m]


# ---------------------------------------------------------------------------
# Validazione
# ---------------------------------------------------------------------------

def valida_dati(D50: float, ys_atteso: float) -> List[str]:
    errori: List[str] = []
    if D50 <= 0:
        errori.append("Il diametro D50 deve essere positivo.")
    if D50 > 3.0:
        errori.append("Il diametro D50 sembra eccessivo (> 3 m): verificare i valori in input.")
    if ys_atteso <= 0:
        errori.append("Lo scalzamento atteso ys deve essere positivo.")
    return errori


# ---------------------------------------------------------------------------
# Calcoli di dimensionamento
# ---------------------------------------------------------------------------

def spessore_fondazione(D50: float, fattore: float = 2.5) -> float:
    """Spessore apron [m] = fattore x D50."""
    if D50 <= 0:
        return float("nan")
    return fattore * D50


def larghezza_fondazione(ys_atteso: float, fattore: float = 2.5) -> float:
    """Estensione laterale dell'apron oltre la pila [m] = fattore x ys."""
    if ys_atteso <= 0:
        return float("nan")
    return fattore * ys_atteso


def affondamento_sottofondo(ys_atteso: float, margine: float = 0.3) -> float:
    """Affondamento dell'apron sotto il fondo attuale [m] = max(margine, 0.20*ys)."""
    if ys_atteso <= 0:
        return margine
    return max(margine, 0.20 * ys_atteso)


def progetto_fondazione(D50: float, ys_atteso: float,
                        fattore_spessore: float = 2.5,
                        fattore_larghezza: float = 2.5) -> FondazioneDesign:
    t = spessore_fondazione(D50, fattore_spessore)
    L = larghezza_fondazione(ys_atteso, fattore_larghezza)
    z = affondamento_sottofondo(ys_atteso)
    return FondazioneDesign(D50=D50, spessore=t, larghezza=L, sottofondo=z)


def stima_volume_apron(D50: float, ys_atteso: float,
                       larghezza_pila: float = 2.0,
                       lunghezza_pila: float = 8.0,
                       fattore_spessore: float = 2.5,
                       fattore_larghezza: float = 2.5) -> dict:
    """Stima del volume totale dell'apron (geometria rettangolare semplificata)."""
    t = spessore_fondazione(D50, fattore_spessore)
    ext = larghezza_fondazione(ys_atteso, fattore_larghezza)
    L_apron = lunghezza_pila + 2.0 * ext
    B_apron = larghezza_pila + 2.0 * ext
    V_apron = L_apron * B_apron * t
    return {
        "spessore [m]": t,
        "estensione laterale [m]": ext,
        "L_apron [m]": L_apron,
        "B_apron [m]": B_apron,
        "Volume_apron [m3]": V_apron,
    }


def massa_e_costo_apron(vol: dict, S_s: float = 2.65,
                        rho: float = 1000.0,
                        porosita: float = 0.40,
                        costo_eur_m3: float = 80.0,
                        spessore_filtro: float = 0.30,
                        costo_filtro_eur_m3: float = 40.0) -> dict:
    """
    Stima massa totale e costo dell'apron fondazionale.
    Include anche il filtro granulare di transizione.
    costo_eur_m3: costo unitario della scogliera posata [EUR/m3]
    costo_filtro_eur_m3: costo unitario del filtro granulare [EUR/m3]
    """
    rho_s = S_s * rho
    V_tot = vol["Volume_apron [m3]"]
    V_roccia = V_tot * (1.0 - porosita)
    M_roccia = V_roccia * rho_s
    costo_scogliera = V_tot * costo_eur_m3
    # Volume filtro: stesso piano orizzontale, solo spessore filtro
    V_filtro = vol["L_apron [m]"] * vol["B_apron [m]"] * spessore_filtro
    costo_filtro = V_filtro * costo_filtro_eur_m3
    costo_totale = costo_scogliera + costo_filtro
    return {
        "Massa_totale_roccia [t]": round(M_roccia / 1000.0, 1),
        "Massa_totale_roccia [kg]": round(M_roccia, 0),
        "V_roccia_netto [m3]": round(V_roccia, 2),
        "Costo_scogliera [EUR]": round(costo_scogliera, 0),
        "V_filtro [m3]": round(V_filtro, 2),
        "Costo_filtro [EUR]": round(costo_filtro, 0),
        "Costo_totale [EUR]": round(costo_totale, 0),
        "Porosita' [-]": porosita,
    }


def spessore_filtro_fondazione(D50_m: float) -> float:
    """
    Spessore del filtro granulare sotto l'apron fondazionale.
    D85_filtro ~ 2 * D50_filtro ~ 2 * 0.25 * D50_riprap
    Spessore filtro = max(0.20 m, 1.5 * D85_filtro)
    """
    D85_filtro = 2.0 * 0.25 * D50_m
    return max(0.20, 1.5 * D85_filtro)


# ---------------------------------------------------------------------------
# Verifiche normative
# ---------------------------------------------------------------------------

def verifiche_fondazione(D50: float, ys_atteso: float,
                         fattore_spessore: float = 2.5,
                         fattore_larghezza: float = 2.5,
                         larghezza_pila: float = 2.0,
                         lunghezza_pila: float = 8.0) -> pd.DataFrame:
    """
    Tabella verifiche normative per apron fondazionale.
    """
    t = spessore_fondazione(D50, fattore_spessore)
    ext = larghezza_fondazione(ys_atteso, fattore_larghezza)
    z = affondamento_sottofondo(ys_atteso)
    vol = stima_volume_apron(D50, ys_atteso, larghezza_pila, lunghezza_pila,
                             fattore_spessore, fattore_larghezza)
    t_filt = spessore_filtro_fondazione(D50)

    rows: List[dict] = []

    # 1. Spessore apron
    t_min = max(0.30, 2.0 * D50)
    rows.append({
        "N.": 1, "Verifica": "Spessore apron fondazionale",
        "Valore calcolato": f"{t:.3f} m",
        "Limite/soglia": f">= {t_min:.3f} m (max(0.30, 2*D50))",
        "Esito": "OK" if t >= t_min else "NON OK",
        "Riferimento normativo": "FHWA HEC-23; CNR-UNI",
    })

    # 2. Estensione laterale
    ext_min = 2.0 * ys_atteso
    rows.append({
        "N.": 2, "Verifica": "Estensione laterale apron",
        "Valore calcolato": f"{ext:.3f} m",
        "Limite/soglia": f">= {ext_min:.3f} m (2 * ys)",
        "Esito": "OK" if ext >= ext_min else "NON OK",
        "Riferimento normativo": "FHWA HEC-23; Richardson & Davis HEC-18",
    })

    # 3. Affondamento sotto fondo
    z_min = 0.30
    rows.append({
        "N.": 3, "Verifica": "Affondamento sotto il fondo attuale",
        "Valore calcolato": f"{z:.3f} m",
        "Limite/soglia": f">= {z_min:.2f} m (min. costruttivo)",
        "Esito": "OK" if z >= z_min else "ATTENZIONE",
        "Riferimento normativo": "FHWA HEC-23; linea guida costruttiva",
    })

    # 4. Spessore filtro
    t_filt_min = 0.20
    rows.append({
        "N.": 4, "Verifica": "Spessore strato filtro granulare",
        "Valore calcolato": f"{t_filt:.3f} m",
        "Limite/soglia": f">= {t_filt_min:.2f} m (min. costruttivo)",
        "Esito": "OK" if t_filt >= t_filt_min else "NON OK",
        "Riferimento normativo": "Terzaghi (1943); USACE EM 1110-2-1913",
    })

    # 5. Dimensioni piano apron vs pila
    L_ap = vol["L_apron [m]"]
    B_ap = vol["B_apron [m]"]
    L_min_ap = lunghezza_pila + 2.0 * ys_atteso
    rows.append({
        "N.": 5, "Verifica": "Lunghezza piano apron",
        "Valore calcolato": f"{L_ap:.3f} m",
        "Limite/soglia": f">= {L_min_ap:.3f} m (L_pila + 2*ys)",
        "Esito": "OK" if L_ap >= L_min_ap else "ATTENZIONE",
        "Riferimento normativo": "FHWA HEC-23",
    })

    # 6. D50 dimensionale
    if D50 < 0.10:
        esito_d50 = "ATTENZIONE"
    elif D50 > 1.5:
        esito_d50 = "ATTENZIONE"
    else:
        esito_d50 = "OK"
    rows.append({
        "N.": 6, "Verifica": "D50 pezzatura apron fondazionale",
        "Valore calcolato": f"{D50:.4f} m",
        "Limite/soglia": "0.10 - 1.50 m (campo tipico)",
        "Esito": esito_d50,
        "Riferimento normativo": "EN 13383-1; FHWA HEC-23",
    })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Report tabellare
# ---------------------------------------------------------------------------

def calcola_report(D50: float, ys_atteso: float,
                   fattore_spessore: float = 2.5,
                   fattore_larghezza: float = 2.5,
                   larghezza_pila: float = 2.0,
                   lunghezza_pila: float = 8.0) -> pd.DataFrame:
    design = progetto_fondazione(D50, ys_atteso, fattore_spessore, fattore_larghezza)
    vol = stima_volume_apron(D50, ys_atteso, larghezza_pila, lunghezza_pila,
                             fattore_spessore, fattore_larghezza)
    rows = [
        {"Parametro": "D50 in input [m]",
         "Valore": f"{D50:.3f}"},
        {"Parametro": f"Spessore apron [m]  (= {fattore_spessore:.1f}*D50)",
         "Valore": f"{design.spessore:.3f}"},
        {"Parametro": f"Estensione laterale [m]  (= {fattore_larghezza:.1f}*ys)",
         "Valore": f"{design.larghezza:.2f}"},
        {"Parametro": "Affondamento sotto fondo attuale [m]",
         "Valore": f"{design.sottofondo:.2f}"},
        {"Parametro": "Dimensioni piano apron L x B [m]",
         "Valore": f"{vol['L_apron [m]']:.2f} x {vol['B_apron [m]']:.2f}"},
        {"Parametro": "Volume totale apron [m3]",
         "Valore": f"{vol['Volume_apron [m3]']:.2f}"},
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tabella passaggi di calcolo
# ---------------------------------------------------------------------------

def tabella_passaggi(D50: float, ys_atteso: float,
                     fattore_spessore: float = 2.5,
                     fattore_larghezza: float = 2.5,
                     larghezza_pila: float = 2.0,
                     lunghezza_pila: float = 8.0,
                     S_s: float = 2.65, rho: float = 1000.0,
                     porosita: float = 0.40,
                     costo_eur_m3: float = 80.0) -> pd.DataFrame:
    """
    Tabella con tutti i passaggi intermedi del calcolo apron fondazionale.
    Include: geometria, filtro, massa totale, stima costo.
    Colonne: Passo, Grandezza, Simbolo, Formula, Valore, Unita
    """
    t = spessore_fondazione(D50, fattore_spessore)
    ext = larghezza_fondazione(ys_atteso, fattore_larghezza)
    z = affondamento_sottofondo(ys_atteso)
    L_apron = lunghezza_pila + 2.0 * ext
    B_apron = larghezza_pila + 2.0 * ext
    V_apron = L_apron * B_apron * t
    t_filt = spessore_filtro_fondazione(D50)
    V_filtro = L_apron * B_apron * t_filt
    rho_s = S_s * rho
    M_roccia = V_apron * (1.0 - porosita) * rho_s
    costo = V_apron * costo_eur_m3

    rows = [
        (1,  "D50 pezzatura (input)",       "D50",   "da ScoglieraPila",
             f"{D50:.4f}",           "m",      "Pezzatura adottata per la scogliera: proveniente dal modulo ScoglieraPila"),
        (2,  "Scalzamento atteso (input)",  "ys",    "da Scalzamento",
             f"{ys_atteso:.3f}",     "m",      "Profondita' di scalzamento di progetto: proveniente dal modulo Scalzamento"),
        (3,  "Larghezza pila (input)",      "a",     "input",
             f"{larghezza_pila:.3f}","m",      "Larghezza caratteristica della pila perpendicolare al flusso"),
        (4,  "Lunghezza pila (input)",      "L_p",   "input",
             f"{lunghezza_pila:.3f}","m",      "Lunghezza della pila nella direzione del flusso"),
        (5,  "Spessore apron",              "t",     f"f_t*D50={fattore_spessore:.1f}*D50",
             f"{t:.4f}",             "m",      "Spessore verticale dell'apron fondazionale: deve contenere almeno 2 strati"),
        (6,  "Estensione laterale",         "ext",   f"f_L*ys={fattore_larghezza:.1f}*ys",
             f"{ext:.4f}",           "m",      "Proiezione dell'apron oltre il perimetro della pila: protegge dal bordo"),
        (7,  "Affondamento sotto fondo",    "z_sub", "max(0.30, 0.20*ys)",
             f"{z:.4f}",             "m",      "Quota di posa dell'apron rispetto al fondo attuale: impedisce scalzamento"),
        (8,  "Lunghezza piano apron",       "L_ap",  "L_p + 2*ext",
             f"{L_apron:.4f}",       "m",      "Dimensione longitudinale totale del piano orizzontale dell'apron"),
        (9,  "Larghezza piano apron",       "B_ap",  "a + 2*ext",
             f"{B_apron:.4f}",       "m",      "Dimensione trasversale totale del piano orizzontale dell'apron"),
        (10, "Volume totale apron",         "V_ap",  "L_ap * B_ap * t",
             f"{V_apron:.4f}",       "m^3",    "Volume totale della scogliera in posto (include i vuoti)"),
        (11, "Spessore filtro granulare",   "t_f",   "max(0.20, 1.5*D85_f)",
             f"{t_filt:.3f}",        "m",      "Strato filtro sotto l'apron: previene la migrazione del materiale fine"),
        (12, "Volume strato filtro",        "V_f",   "L_ap * B_ap * t_f",
             f"{V_filtro:.3f}",      "m^3",    "Volume del filtro granulare da approvvigionare"),
        (13, "Densita' roccia rho_s",       "rho_s", "S_s * rho",
             f"{rho_s:.0f}",         "kg/m^3", "Densita' del materiale lapideo"),
        (14, "Massa roccia netta",          "M_r",   "V_ap*(1-n)*rho_s",
             f"{M_roccia/1000:.2f}", "t",      "Tonnellate di roccia necessarie (escluso il volume dei vuoti)"),
        (15, "Stima costo scogliera",       "C",     f"V_ap*{costo_eur_m3:.0f} EUR/m3",
             f"{costo:.0f}",         "EUR",    "Stima del costo a corpo della scogliera (IVA esclusa, posa inclusa)"),
    ]
    return pd.DataFrame(rows, columns=["Passo", "Grandezza", "Simbolo",
                                       "Formula", "Valore", "Unita", "Descrizione"])


# ---------------------------------------------------------------------------
# Curve di sensitivita
# ---------------------------------------------------------------------------

def curva_sensitivita_D50(ys_atteso: float,
                          fattore_spessore: float = 2.5,
                          D50_min: Optional[float] = None,
                          D50_max: Optional[float] = None,
                          n_punti: int = 50) -> pd.DataFrame:
    """Spessore apron al variare di D50 (ys fisso)."""
    if D50_min is None:
        D50_min = 0.05
    if D50_max is None:
        D50_max = 2.0
    records = []
    for D50 in np.linspace(D50_min, D50_max, n_punti):
        t = spessore_fondazione(float(D50), fattore_spessore)
        records.append({"D50 [m]": round(float(D50), 3),
                        "Spessore apron [m]": round(t, 3)})
    return pd.DataFrame(records)


def curva_sensitivita_ys(D50: float,
                         fattore_larghezza: float = 2.5,
                         ys_min: Optional[float] = None,
                         ys_max: Optional[float] = None,
                         n_punti: int = 50) -> pd.DataFrame:
    """Larghezza estensione e affondamento al variare di ys (D50 fisso)."""
    if ys_min is None:
        ys_min = 0.20
    if ys_max is None:
        ys_max = 8.0
    records = []
    for ys in np.linspace(ys_min, ys_max, n_punti):
        L = larghezza_fondazione(float(ys), fattore_larghezza)
        z = affondamento_sottofondo(float(ys))
        records.append({
            "ys [m]": round(float(ys), 3),
            "Estensione laterale [m]": round(L, 3),
            "Affondamento sottofondo [m]": round(z, 3),
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Generazione report PDF
# ---------------------------------------------------------------------------

def _pdf_sezione(pdf, titolo: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_fill_color(41, 98, 155)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, titolo, ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(1)


def _pdf_riga_kv(pdf, chiave: str, valore: str) -> None:
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(70, 5, chiave + ":", border="B")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, valore, border="B", ln=True)


def _pdf_tabella(pdf, df: pd.DataFrame) -> None:
    cols = list(df.columns)
    larghezze = {
        "Passo": 9, "Grandezza": 35, "Simbolo": 18,
        "Formula": 45, "Valore": 24, "Unita": 14, "Descrizione": 45,
        "Parametro": 110, "Valore": 70,
    }
    default_w = 30
    row_h = 5

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(210, 225, 245)
    for col in cols:
        w = larghezze.get(col, default_w)
        pdf.cell(w, row_h + 1, col, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    for _, row in df.iterrows():
        for col in cols:
            w = larghezze.get(col, default_w)
            txt = str(row[col])
            align = "C" if col in ("Passo", "Simbolo", "Valore", "Unita") else "L"
            max_c = max(4, int(w / 2.0))
            if len(txt) > max_c:
                txt = txt[: max_c - 2] + ".."
            pdf.cell(w, row_h, txt, border=1, align=align)
        pdf.ln()


def genera_pdf(D50: float, ys_atteso: float,
               fattore_spessore: float, fattore_larghezza: float,
               larghezza_pila: float, lunghezza_pila: float,
               note: List[str],
               S_s: float = 2.65, rho: float = 1000.0,
               porosita: float = 0.40, costo_eur_m3: float = 80.0,
               costo_filtro_eur_m3: float = 40.0) -> bytes:
    """Genera un report PDF completo e restituisce i bytes."""
    from fpdf import FPDF

    df_pass = tabella_passaggi(D50, ys_atteso, fattore_spessore, fattore_larghezza,
                               larghezza_pila, lunghezza_pila,
                               S_s=S_s, rho=rho, porosita=porosita,
                               costo_eur_m3=costo_eur_m3)
    df_report = calcola_report(D50, ys_atteso, fattore_spessore, fattore_larghezza,
                               larghezza_pila, lunghezza_pila)
    df_ver = verifiche_fondazione(D50, ys_atteso, fattore_spessore, fattore_larghezza,
                                  larghezza_pila, lunghezza_pila)
    vol = stima_volume_apron(D50, ys_atteso, larghezza_pila, lunghezza_pila,
                             fattore_spessore, fattore_larghezza)
    design = progetto_fondazione(D50, ys_atteso, fattore_spessore, fattore_larghezza)
    mc = massa_e_costo_apron(vol, S_s, rho, porosita, costo_eur_m3,
                              spessore_filtro_fondazione(D50), costo_filtro_eur_m3)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(20, 60, 120)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "Report - Apron Fondazionale Protezione Pila",
             ln=True, align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 6, f"Generato il {datetime.date.today().strftime('%d/%m/%Y')}  |  "
             "FHWA HEC-23, Terzaghi (1943)", ln=True, align="C")
    pdf.ln(4)

    _pdf_sezione(pdf, "1. Parametri di input")
    _pdf_riga_kv(pdf, "D50 pezzatura (da ScoglieraPila)", f"{D50:.3f} m")
    _pdf_riga_kv(pdf, "Scalzamento atteso ys (da Scalzamento)", f"{ys_atteso:.3f} m")
    _pdf_riga_kv(pdf, "Larghezza pila a", f"{larghezza_pila:.3f} m")
    _pdf_riga_kv(pdf, "Lunghezza pila L", f"{lunghezza_pila:.3f} m")
    _pdf_riga_kv(pdf, "Fattore spessore f_t", f"{fattore_spessore:.2f}")
    _pdf_riga_kv(pdf, "Fattore estensione f_L", f"{fattore_larghezza:.2f}")
    _pdf_riga_kv(pdf, "Densita' relativa roccia S_s", f"{S_s:.3f}")
    _pdf_riga_kv(pdf, "Porosita' scogliera", f"{porosita:.0%}")
    _pdf_riga_kv(pdf, "Costo scogliera", f"{costo_eur_m3:.0f} EUR/m3")
    pdf.ln(4)

    _pdf_sezione(pdf, "2. Risultati principali")
    _pdf_riga_kv(pdf, "Spessore apron", f"{design.spessore:.4f} m")
    _pdf_riga_kv(pdf, "Estensione laterale", f"{design.larghezza:.4f} m")
    _pdf_riga_kv(pdf, "Affondamento sotto fondo", f"{design.sottofondo:.4f} m")
    _pdf_riga_kv(pdf, "Piano apron L x B",
                 f"{vol['L_apron [m]']:.3f} m x {vol['B_apron [m]']:.3f} m")
    _pdf_riga_kv(pdf, "Volume totale apron", f"{vol['Volume_apron [m3]']:.3f} m3")
    _pdf_riga_kv(pdf, "Massa totale roccia", f"{mc['Massa_totale_roccia [t]']:.1f} t")
    _pdf_riga_kv(pdf, "Spessore filtro granulare", f"{spessore_filtro_fondazione(D50):.3f} m")
    _pdf_riga_kv(pdf, "Stima costo scogliera", f"{mc['Costo_scogliera [EUR]']:,.0f} EUR")
    _pdf_riga_kv(pdf, "Stima costo filtro", f"{mc['Costo_filtro [EUR]']:,.0f} EUR")
    _pdf_riga_kv(pdf, "Stima costo totale", f"{mc['Costo_totale [EUR]']:,.0f} EUR")
    pdf.ln(4)

    _pdf_sezione(pdf, "3. Passaggi di calcolo (passo per passo)")
    _pdf_tabella(pdf, df_pass)
    pdf.ln(4)

    pdf.add_page()
    _pdf_sezione(pdf, "4. Riepilogo dimensionamento apron")
    _pdf_tabella(pdf, df_report)
    pdf.ln(4)

    _pdf_sezione(pdf, "5. Verifiche normative")
    _pdf_tabella(pdf, df_ver)
    pdf.ln(4)

    pdf.add_page()
    _pdf_sezione(pdf, "6. Note tecniche e commenti progettuali")
    pdf.set_font("Helvetica", "", 8)
    for item in note:
        txt = "- " + item.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 5, txt)
        pdf.ln(1)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Commenti progettuali automatici
# ---------------------------------------------------------------------------

def commenti_progettuali(D50: float, ys_atteso: float,
                         fattore_spessore: float = 2.5,
                         fattore_larghezza: float = 2.5) -> List[str]:
    note: List[str] = []
    t = spessore_fondazione(D50, fattore_spessore)
    L = larghezza_fondazione(ys_atteso, fattore_larghezza)
    z = affondamento_sottofondo(ys_atteso)

    if t < 0.30:
        note.append(
            f"Lo spessore dell'apron ({t:.3f} m) e' inferiore a 0.30 m: "
            "valutare l'adozione di un minimo costruttivo di almeno 0.30 m."
        )
    if L < 1.0:
        note.append(
            f"L'estensione laterale dell'apron ({L:.2f} m) e' ridotta: "
            "verificare la protezione contro lo scalzamento di sponda."
        )
    if z < 0.5:
        note.append(
            f"L'affondamento sotto il fondo attuale ({z:.2f} m) e' limitato: "
            "considerare la quota di piena e l'evoluzione morfologica dell'alveo."
        )
    note.append(
        "Valutare sempre uno strato filtro granulare o geotessile sotto l'apron, "
        "per prevenire la migrazione del materiale fine del substrato."
    )
    note.append(
        "I fattori di progetto (f_t, f_L) vanno adattati alle norme locali "
        "e ai risultati di un'analisi morfologica di dettaglio (es. FHWA HEC-23)."
    )
    if not any("inferiore" in n or "ridotta" in n or "limitato" in n for n in note[:-2]):
        note.insert(0,
            "I valori di dimensionamento ricadono in un intervallo tipico. "
            "Verificare con la geometria reale della fondazione e le norme di settore."
        )
    return note
