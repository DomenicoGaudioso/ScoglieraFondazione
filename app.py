# -*- coding: utf-8 -*-
import json
import streamlit as st
import plotly.express as px
from src import (valida_dati, progetto_fondazione, calcola_report,
                 stima_volume_apron, curva_sensitivita_D50, curva_sensitivita_ys,
                 tabella_passaggi, genera_pdf, commenti_progettuali,
                 verifiche_fondazione, massa_e_costo_apron, spessore_filtro_fondazione)

st.set_page_config(page_title="Scogliera - Fondazione (Apron)", layout="wide")
st.title("Apron fondazionale a protezione della pila da ponte")
st.caption("Software professionale: geometria apron, massa totale, stima costo, filtro Terzaghi, verifiche normative, report PDF.")

# ---------------------------------------------------------------------------
# Defaults e session state
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "fond_D50": 0.30, "fond_ys": 2.0,
    "fond_a_pila": 2.0, "fond_L_pila": 8.0,
    "fond_ft": 2.5, "fond_fL": 2.5,
    "fond_Ss": 2.65, "fond_rho": 1000.0, "fond_porosita": 0.40,
    "fond_costo_scogliera": 80.0, "fond_costo_filtro": 40.0,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Sidebar - Input
# ---------------------------------------------------------------------------
with st.sidebar:
    with st.expander("Salva / Carica parametri", expanded=False):
        uploaded = st.file_uploader("Carica parametri (JSON)", type=["json"],
                                    key="fond_upload")
        if uploaded is not None:
            try:
                loaded = json.loads(uploaded.read())
                if st.button("Applica parametri caricati", key="fond_apply"):
                    for k in _DEFAULTS:
                        if k in loaded:
                            st.session_state[k] = loaded[k]
                    st.rerun()
                st.caption(f"File: {uploaded.name}")
            except Exception:
                st.error("File JSON non valido.")

        params_json = json.dumps(
            {k: st.session_state[k] for k in _DEFAULTS}, indent=2
        ).encode()
        st.download_button("Scarica parametri JSON", params_json,
                           "fondazione_parametri.json", "application/json")

    st.divider()
    st.header("Input da app a monte")
    D50 = st.number_input("D50 pezzatura [m]  (da ScoglieraPila)",
                          min_value=0.01, step=0.01, key="fond_D50")
    ys = st.number_input("Scalzamento atteso ys [m]  (da Scalzamento)",
                         min_value=0.10, step=0.1, key="fond_ys")

    st.header("Geometria pila")
    larghezza_pila = st.number_input("Larghezza pila a [m]",
                                     min_value=0.5, step=0.1, key="fond_a_pila")
    lunghezza_pila = st.number_input("Lunghezza pila L [m]",
                                     min_value=0.5, step=0.5, key="fond_L_pila")

    st.header("Fattori di progetto")
    fattore_spessore = st.number_input("Fattore spessore f_t  (spess = f_t\u00b7D50)",
                                       min_value=1.5, max_value=5.0, step=0.1, key="fond_ft")
    fattore_larghezza = st.number_input("Fattore estensione f_L  (ext = f_L\u00b7ys)",
                                        min_value=1.5, max_value=5.0, step=0.1, key="fond_fL")

    st.divider()
    st.header("Materiale e costo")
    S_s = st.number_input("Densit\u00e0 relativa roccia S_s",
                          min_value=1.5, max_value=3.5, step=0.05, key="fond_Ss")
    rho = st.number_input("Densit\u00e0 acqua \u03c1 [kg/m\u00b3]",
                          min_value=900.0, max_value=1100.0, step=10.0, key="fond_rho")
    porosita = st.number_input("Porosit\u00e0 scogliera [-]",
                                min_value=0.20, max_value=0.60, step=0.05, key="fond_porosita")
    costo_scogliera = st.number_input("Costo scogliera posata [EUR/m\u00b3]",
                                       min_value=10.0, max_value=500.0, step=5.0,
                                       key="fond_costo_scogliera")
    costo_filtro = st.number_input("Costo filtro granulare [EUR/m\u00b3]",
                                    min_value=5.0, max_value=200.0, step=5.0,
                                    key="fond_costo_filtro")

# ---------------------------------------------------------------------------
# Calcolo
# ---------------------------------------------------------------------------
errori = valida_dati(D50, ys)
if errori:
    for e in errori:
        st.error(e)
    st.stop()

design = progetto_fondazione(D50, ys, fattore_spessore, fattore_larghezza)
vol = stima_volume_apron(D50, ys, larghezza_pila, lunghezza_pila,
                         fattore_spessore, fattore_larghezza)
t_filt = spessore_filtro_fondazione(D50)
mc = massa_e_costo_apron(vol, S_s, rho, porosita, costo_scogliera,
                          t_filt, costo_filtro)
df_report = calcola_report(D50, ys, fattore_spessore, fattore_larghezza,
                           larghezza_pila, lunghezza_pila)
df_pass = tabella_passaggi(D50, ys, fattore_spessore, fattore_larghezza,
                           larghezza_pila, lunghezza_pila,
                           S_s=S_s, rho=rho, porosita=porosita,
                           costo_eur_m3=costo_scogliera)
df_ver = verifiche_fondazione(D50, ys, fattore_spessore, fattore_larghezza,
                               larghezza_pila, lunghezza_pila)
df_sens_D50 = curva_sensitivita_D50(ys, fattore_spessore,
                                    D50_min=max(0.05, D50 * 0.3),
                                    D50_max=D50 * 3.0)
df_sens_ys = curva_sensitivita_ys(D50, fattore_larghezza,
                                  ys_min=max(0.2, ys * 0.3),
                                  ys_max=ys * 3.0)
note = commenti_progettuali(D50, ys, fattore_spessore, fattore_larghezza)

# ---------------------------------------------------------------------------
# Indicatori sintetici
# ---------------------------------------------------------------------------
n_ok  = (df_ver["Esito"] == "OK").sum()
n_att = (df_ver["Esito"] == "ATTENZIONE").sum()
n_no  = (df_ver["Esito"] == "NON OK").sum()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Spessore apron [m]", f"{design.spessore:.3f}")
col2.metric("Estensione laterale [m]", f"{design.larghezza:.2f}")
col3.metric("Affondamento [m]", f"{design.sottofondo:.2f}")
col4.metric("Volume apron [m\u00b3]", f"{vol['Volume_apron [m3]']:.2f}")
col5.metric("Massa roccia [t]", f"{mc['Massa_totale_roccia [t]']:.1f}")
col6.metric("Verif. OK / WARN / NO", f"{n_ok} / {n_att} / {n_no}", delta_color="off")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Risultati", "Grafici", "Verifiche avanzate", "Note tecniche"])

with tab1:
    st.subheader("Passaggi di calcolo (passo per passo)")
    st.dataframe(df_pass, use_container_width=True, hide_index=True)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Geometria apron**")
        st.markdown(f"- Spessore: **{design.spessore:.3f} m** (= {fattore_spessore:.1f} \u00d7 D50)")
        st.markdown(f"- Estensione laterale: **{design.larghezza:.3f} m** (= {fattore_larghezza:.1f} \u00d7 ys)")
        st.markdown(f"- Affondamento: **{design.sottofondo:.3f} m**")
        st.markdown(f"- Piano apron: **{vol['L_apron [m]']:.2f} \u00d7 {vol['B_apron [m]']:.2f} m**")
        st.markdown(f"- Volume totale: **{vol['Volume_apron [m3]']:.3f} m\u00b3**")
        st.markdown(f"- Spessore filtro granulare: **{t_filt:.3f} m**")
    with col_b:
        st.markdown("**Materiale e costo**")
        st.markdown(f"- Massa totale roccia: **{mc['Massa_totale_roccia [t]']:.1f} t**")
        st.markdown(f"- Volume roccia netto: **{mc['V_roccia_netto [m3]']:.2f} m\u00b3**")
        st.markdown(f"- Stima costo scogliera: **{mc['Costo_scogliera [EUR]']:,.0f} EUR**")
        st.markdown(f"- Volume filtro: **{mc['V_filtro [m3]']:.2f} m\u00b3**")
        st.markdown(f"- Stima costo filtro: **{mc['Costo_filtro [EUR]']:,.0f} EUR**")
        st.markdown(f"- **Stima costo totale: {mc['Costo_totale [EUR]']:,.0f} EUR**")

    st.divider()
    st.subheader("Riepilogo dimensionamento apron fondazionale")
    st.dataframe(df_report, use_container_width=True, hide_index=True)

    st.divider()
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        st.download_button("Scarica passaggi CSV",
                           df_pass.to_csv(index=False).encode("utf-8"),
                           "fondazione_passaggi.csv", "text/csv")
    with col_dl2:
        st.download_button("Scarica risultati CSV",
                           df_report.to_csv(index=False).encode("utf-8"),
                           "fondazione_risultati.csv", "text/csv")
    with col_dl3:
        try:
            pdf_bytes = genera_pdf(D50, ys, fattore_spessore, fattore_larghezza,
                                   larghezza_pila, lunghezza_pila, note,
                                   S_s=S_s, rho=rho, porosita=porosita,
                                   costo_eur_m3=costo_scogliera,
                                   costo_filtro_eur_m3=costo_filtro)
            st.download_button("Scarica Report PDF", pdf_bytes,
                               "fondazione_report.pdf", "application/pdf")
        except ImportError:
            st.warning("fpdf2 non installato. Eseguire: pip install fpdf2")

with tab2:
    st.subheader("Sensitivit\u00e0 spessore apron vs D50")
    fig_spess = px.line(df_sens_D50, x="D50 [m]", y="Spessore apron [m]",
                        title="Spessore apron in funzione di D50 (ys fisso)")
    fig_spess.add_vline(x=D50, line_dash="dash", line_color="red",
                        annotation_text=f"D50={D50:.3f} m", annotation_position="top right")
    fig_spess.add_hline(y=design.spessore, line_dash="dot", line_color="orange",
                        annotation_text=f"spess={design.spessore:.3f} m",
                        annotation_position="bottom right")
    fig_spess.update_layout(xaxis_title="D50 [m]", yaxis_title="Spessore [m]")
    st.plotly_chart(fig_spess, use_container_width=True)

    st.subheader("Sensitivit\u00e0 estensione apron vs scalzamento ys")
    fig_larg = px.line(df_sens_ys, x="ys [m]", y="Estensione laterale [m]",
                       title="Estensione laterale apron in funzione dello scalzamento atteso")
    fig_larg.add_vline(x=ys, line_dash="dash", line_color="red",
                       annotation_text=f"ys={ys:.2f} m", annotation_position="top right")
    fig_larg.add_hline(y=design.larghezza, line_dash="dot", line_color="orange",
                       annotation_text=f"ext={design.larghezza:.2f} m",
                       annotation_position="bottom right")
    fig_larg.update_layout(xaxis_title="ys [m]", yaxis_title="Estensione laterale [m]")
    st.plotly_chart(fig_larg, use_container_width=True)

with tab3:
    st.subheader("Verifiche normative apron fondazionale")
    _colori = {"OK": "background-color: #d4edda",
               "ATTENZIONE": "background-color: #fff3cd",
               "NON OK": "background-color: #f8d7da",
               "INFO": "background-color: #d1ecf1"}

    def _colora(row):
        c = _colori.get(row["Esito"], "")
        return [c] * len(row)

    styled = df_ver.style.apply(_colora, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Stima economica di massima")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown(f"- Volume scogliera: **{vol['Volume_apron [m3]']:.2f} m\u00b3**")
        st.markdown(f"- Costo unitario scogliera: **{costo_scogliera:.0f} EUR/m\u00b3**")
        st.markdown(f"- **Costo scogliera: {mc['Costo_scogliera [EUR]']:,.0f} EUR**")
    with col_e2:
        st.markdown(f"- Volume filtro: **{mc['V_filtro [m3]']:.2f} m\u00b3**")
        st.markdown(f"- Costo unitario filtro: **{costo_filtro:.0f} EUR/m\u00b3**")
        st.markdown(f"- **Costo filtro: {mc['Costo_filtro [EUR]']:,.0f} EUR**")
    st.info(f"\u2192  **Stima costo totale: {mc['Costo_totale [EUR]']:,.0f} EUR**  "
            f"(scogliera + filtro, IVA esclusa, posa inclusa nel costo unitario)")
    st.caption("I costi sono stime preliminari soggette a variazioni in funzione del sito, "
               "della logistica e del mercato locale.")

    st.divider()
    st.download_button("Scarica verifiche CSV",
                       df_ver.to_csv(index=False).encode("utf-8"),
                       "fondazione_verifiche.csv", "text/csv")

with tab4:
    st.subheader("Note tecniche e commenti di progetto")
    for item in note:
        st.markdown(f"- {item}")
    with st.expander("Come leggere i risultati e riferimenti normativi"):
        st.markdown("""
**Geometria apron:**
- Spessore: t = f_t \u00d7 D50  (FHWA HEC-23 raccomanda f_t \u2265 2.0 per fondazioni)
- Estensione laterale: ext = f_L \u00d7 ys  (estensione minima oltre la sagoma della pila)
- Affondamento: max(0.30 m, 0.20 \u00d7 ys)  (per ancorarsi al di sotto del fondo eroso)

**Filtro granulare (Terzaghi):**
Strato di transizione obbligatorio tra il substrato e la scogliera.
Previene la migrazione del materiale fine attraverso i vuoti della scogliera.
Spessore minimo: max(0.20 m, 1.5 \u00d7 D85_filtro)

**Massa totale:**
M = V_apron \u00d7 (1 - n) \u00d7 \u03c1_s
dove n = porosita' della scogliera posata (tipicamente 0.35 - 0.45).

**Stima costo:**
Costo preliminare a corpo per il dimensionamento di massima.
Non include scavi, trasporti speciali, opere accessorie, oneri progettuali.

**Riferimenti normativi:**
- FHWA HEC-23 (2009): Bridge Scour and Stream Instability Countermeasures
- Terzaghi (1943): Theoretical Soil Mechanics
- USACE EM 1110-2-1913: Design and Construction of Levees
- EN 13383-1:2002+A1:2008: Armourstone
        """)
