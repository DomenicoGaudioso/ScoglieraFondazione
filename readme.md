# ScoglieraFondazione – Apron fondazionale a protezione della pila da ponte

Web app professionale per il **dimensionamento preliminare dell'apron fondazionale**
a protezione di una pila da ponte. Raccorda l'output dell'app Scalzamento (ys) e
dell'app ScoglieraPila (D50) in un set dimensionale coerente.

## Stato attuale dell'implementazione

**v2 – completata** (ultima iterazione 2026-03-22)

Funzionalità implementate:
- FondazioneDesign (dataclass frozen) con D50, spessore, larghezza, sottofondo.
- valida_dati(): controlla D50 e ys_atteso.
- spessore_fondazione(): `t = f_t · D50`.
- larghezza_fondazione(): `ext = f_L · ys`.
- affondamento_sottofondo(): `z = max(0.30 m, 0.20·ys)`.
- progetto_fondazione(): wrapper che restituisce FondazioneDesign.
- stima_volume_apron(): volume totale dell'apron (geometria rettangolare semplificata,
  dipende da geometria pila in input: larghezza_pila, lunghezza_pila).
- calcola_report(): DataFrame con tutti i parametri di progetto.
- curva_sensitivita_D50(): spessore apron al variare di D50 (50 punti).
- curva_sensitivita_ys(): estensione e affondamento al variare di ys (50 punti).
- commenti_progettuali(): note automatiche su spessore, estensione, affondamento, filtro.
- app.py: layout wide, 4 metriche, 3 tab (Risultati / Grafici / Note), 2 grafici Plotly
  sensitività con marcatura del punto di progetto, download CSV.

## Struttura del progetto

```text
ScoglieraFondazione/
├── app.py           # UI Streamlit (nessuna formula)
├── src.py           # Calcoli, volume apron, sensitività, validazione, commenti
├── requirements.txt # streamlit, numpy, pandas, plotly
├── readme.md        # questo file
└── prompt.txt       # prompt per iterazioni future
```

## Input

| Parametro | Descrizione | Provenienza |
|-----------|-------------|-------------|
| D50 | Diametro caratteristico massi | Da ScoglieraPila |
| ys | Scalzamento atteso | Da Scalzamento |
| larghezza_pila | Larghezza caratteristica a | Input utente |
| lunghezza_pila | Lunghezza pila L | Input utente |
| f_t | Fattore spessore (spess = f_t·D50) | Input utente |
| f_L | Fattore estensione (ext = f_L·ys) | Input utente |

## Output principali

- Spessore apron `f_t·D50 [m]`
- Estensione laterale `f_L·ys [m]`
- Affondamento sotto fondo attuale `[m]`
- Volume totale apron `[m³]`
- Curve sensitività: spessore vs D50, estensione vs ys
- CSV risultati

## Flusso dati nella suite

```
App Scalzamento → ys → ScoglieraPila → D50 → ScoglieraFondazione → Volume apron
```

## Avvio rapido

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estensioni future consigliate

- Stima massa totale apron (richiede densità roccia in input)
- Dettaglio filtro granulare (regola di Terzaghi / Sherard)
- Sezione schematica verticale dell'apron (grafico Plotly)
- Confronto fra più scenari di progetto (diversi f_t, f_L)
- Report PDF
- Accoppiamento diretto con ScoglieraPila (pass-through D50 senza input manuale)
