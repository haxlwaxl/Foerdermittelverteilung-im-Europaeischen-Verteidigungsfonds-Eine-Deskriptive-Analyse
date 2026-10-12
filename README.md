# EDF Funding Analysis – Reproduktion der Ergebnistabellen

Kurzanleitung, wie die Analyse-Tabellen aus den JSON-Daten mit den 4 Python-Skripten generiert werden.

## 1. Voraussetzungen

- Python ≥ 3.12
- Virtuelle Umgebung anlegen und Pakete installieren:

```bash
python -m venv .venv
# Windows:        .venv\Scripts\activate
# Linux/macOS:    source .venv/bin/activate

pip install pandas numpy statsmodels scipy
```

> Hinweis: `analysis_concentration.py`, `analysis_funding_tables.py` und `analysis_rd_integration_tables.py` nutzen nur die Python-Standardbibliothek. `pandas`, `numpy`, `statsmodels` und `scipy` werden ausschließlich für `analysis_regressions.py` benötigt.

## 2. Benötigte Dateien

Folgende Dateien müssen **gemeinsam in einem Ordner** liegen (Skripte + JSON-Daten):

**Python-Skripte:**

- `analysis_common.py` (gemeinsames Modul – wird von den anderen Skripten importiert)
- `analysis_concentration.py`
- `analysis_funding_tables.py`
- `analysis_rd_integration_tables.py`
- `analysis_regressions.py`

**JSON-Daten:**

| Datei | Inhalt / Verwendung |
|---|---|
| `allpwporbis.json` | Hauptdatensatz: Organisationen mit Gruppen-Flags (`sme`, `Bigcorp`, `OtherCorp`, `OtherBig`, `OtherSmall`, `OtherRest`) und `participations` (Projekt, Rolle, `eu_contribution`, `part_share`, `rd_type`, `integration_level`) |
| `JVList.json` | Liste der Joint Ventures (nur Konzentrations-Skript) |
| `BigCorpGroup.json` | Konzerngruppen der Bigcorps (nur Konzentrations-Skript) |
| `OtherCorpGroup.json` | Konzerngruppen der OtherCorps (nur Konzentrations-Skript) |
| `Konzernfund.json` | Adjustierte Konzern-Funding-Werte (nur Konzentrations-Skript) |

Die Pfade werden in `analysis_common.py` (gemeinsames Modul mit Hilfsfunktionen, Gruppen-Definitionen und Konstanten) gesetzt – keine Skript-Argumente nötig.

## 3. Ausführung

Im Ordner mit den Skripten und JSON-Dateien ausführen (Reihenfolge beliebig, die Skripte sind unabhängig voneinander):

```bash
python analysis_concentration.py
python analysis_funding_tables.py
python analysis_rd_integration_tables.py
python analysis_regressions.py
```

Alle Ergebnisse werden auf **stdout** ausgegeben (Pipe-`|` getrennt). Zum Speichern in einer Datei:

```bash
python analysis_funding_tables.py > results_funding.txt
```

## 4. Output der Skripte

| Skript | Generierte Tabellen |
|---|---|
| `analysis_concentration.py` | `CURRENT_KONZERNFUND_METRICS` (CR1/CR4/CR10/CR20, HHI, adjusted), `top20_current`, `UNADJUSTED_JV_METRICS`, `top20_unadjusted` |
| `analysis_funding_tables.py` | `TABLE_1` (Entities/Participations/Projects je Gruppe), `TABLE_2` (Funding-Statistiken), `TABLE_3` (Funding-Share vs. Participation-Share, RFR), `TABLE_4` (Koordinator-Rollen), `PRC_SHARE_PER_PARTICIPATION`, `PROJECT_LEVEL_GROUP_SHARE_ALL_PROJECTS` |
| `analysis_rd_integration_tables.py` | `TABLE_A_COUNTS` bis `TABLE_F_GROUP_SHARE_BY_CATEGORY` (Projektzahlen, Funding-Summen/-Shares, Mean-Funding, Funding/Project-Share-Ratio nach `rd_type` × `integration_level` und Gruppe) |
| `analysis_regressions.py` | `CROSSTAB_GROUP_INTEGRATION_LEVEL` (+ Cramér's V, χ²), `NESTED_MODELS`/`NESTED_GROUP_TERMS`/`NESTED_COEFFICIENT_CHANGES` (OLS mit projekt-geclusterten SE), `FE_LN_FUNDING_MODEL` und `FE_PART_SHARE_MODEL` (Projekt-Fixed-Effects-Modelle, inkl. QA-Block `FE_PART_SHARE_QA`) |

## 5. Hinweise

- Referenzwerte: 1.034 Legal Entities, 2.496 Participations, 222 Projekte, Total Funding 3.171.545.781,05 €.
- `analysis_rd_integration_tables.py` deckt nur 218 Projekte ab (3,145 Mrd. €), da 4 Projekte ohne `rd_type`/`integration_level`-Klassifizierung ausfallen.
- Die `Pandas4Warning` bei `analysis_regressions.py` ist harmlos (Deprecation-Hinweis).
