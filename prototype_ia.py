"""Prototype Henley Passport Index : quatre figures, HTML autonome, sources locales."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path

import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots


BASE = Path(__file__).resolve().parent
YEARS = list(range(2006, 2026))
REGIONS = {
    "AFRICA": ("Afrique", "#A65A16"),
    "AMERICAS": ("Amériques", "#2464AC"),
    "ASIA": ("Asie", "#007D79"),
    "CARIBBEAN": ("Caraïbes", "#A13F76"),
    "EUROPE": ("Europe", "#5149A1"),
    "MIDDLE EAST": ("Moyen-Orient", "#735837"),
    "OCEANIA": ("Océanie", "#4F701D"),
}
CATEGORIES = {
    "visa_free_access": ("Sans visa", "#007D79"),
    "visa_on_arrival": ("Visa à l’arrivée", "#64ACA9"),
    "electronic_travel_authorisation": ("Autorisation électronique (ETA)", "#BDDDE8"),
    "visa_online": ("Visa en ligne", "#DCA75F"),
    "visa_required": ("Visa requis", "#17324D"),
}
SCORE_CATEGORIES = list(CATEGORIES)[:3]
INK, MUTED, GRID, ACCENT = "#17324D", "#65758B", "#E2E8F1", "#007D79"


def fr(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "Indisponible"
    return f"{value:,.{digits}f}".replace(",", "\u202f").replace(".", ",")


def source_hashes(data_dir: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
        for name in ("rank_by_year.csv", "country_lists.csv")
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_destinations(cell: str, context: str = "") -> list[dict]:
    """Accepte les listes JSON et l'enveloppe [[...]] observée dans les CSV."""
    try:
        items = json.loads(cell)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"JSON invalide : {context}") from exc
    if isinstance(items, list) and len(items) == 1 and isinstance(items[0], list):
        items = items[0]
    require(isinstance(items, list), f"Liste de destinations attendue : {context}")
    require(
        all(
            isinstance(item, dict)
            and all(isinstance(item.get(key), str) and item[key].strip() for key in ("code", "name"))
            for item in items
        ),
        f"Destination sans code/nom valide : {context}",
    )
    require(
        len(items) == len({item["code"] for item in items}),
        f"Destination répétée dans une catégorie : {context}",
    )
    return items


def load_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    # « NA » est le code de la Namibie, pas une valeur manquante.
    rank = pd.read_csv(data_dir / "rank_by_year.csv", keep_default_na=False)
    lists = pd.read_csv(data_dir / "country_lists.csv", keep_default_na=False)
    required = {"code", "country", "region", "rank", "visa_free_count", "year"}
    require(required <= set(rank.columns), "Colonnes manquantes dans rank_by_year.csv.")
    require(
        {"code", "country", *CATEGORIES} <= set(lists.columns),
        "Colonnes manquantes dans country_lists.csv.",
    )
    for frame, columns in ((rank, ("code", "country", "region")), (lists, ("code", "country"))):
        for column in columns:
            require(
                frame[column].map(lambda x: isinstance(x, str) and bool(x.strip())).all(),
                f"Identifiant ou libellé vide dans {column}.",
            )
    for column in ("year", "rank", "visa_free_count"):
        rank[column] = pd.to_numeric(rank[column], errors="raise")
        require(
            rank[column].map(lambda x: math.isfinite(x) and x == int(x)).all(),
            f"Valeurs entières et finies attendues dans {column}.",
        )
        rank[column] = rank[column].astype(int)
    require(rank["rank"].gt(0).all(), "Un rang doit être strictement positif.")
    require(rank.visa_free_count.ge(0).all(), "Un score ne peut pas être négatif.")
    require(set(rank.year) == set(YEARS), "Les années attendues sont 2006 à 2025.")
    require(not rank.duplicated(["code", "year"]).any(), "Doublon passeport-année.")
    require(not lists.code.duplicated().any(), "Doublon de passeport dans les listes.")
    require(set(rank.region) <= set(REGIONS), "Région non reconnue.")
    require(
        rank.groupby("code")[["country", "region"]].nunique().eq(1).all().all(),
        "Les libellés/régions varient dans le temps : harmonisation nécessaire.",
    )
    require(set(rank.code) == set(lists.code), "Les deux CSV n'ont pas les mêmes passeports.")
    return rank.sort_values(["code", "year"]).reset_index(drop=True), lists


def quantiles(frame: pd.DataFrame) -> pd.DataFrame:
    result = (
        frame.groupby("year").score.quantile([0.1, 0.25, 0.5, 0.75, 0.9], interpolation="linear")
        .unstack()
        .rename(columns={0.1: "p10", 0.25: "p25", 0.5: "median", 0.75: "p75", 0.9: "p90"})
        .reindex(YEARS)
    )
    result["n"] = frame.groupby("year").score.count().reindex(YEARS, fill_value=0)
    result["gap"] = result.p90 - result.p10
    result["ratio"] = result.p90 / result.p10
    return result


def prepare_data(rank: pd.DataFrame, lists: pd.DataFrame) -> dict:
    clean = rank.copy()
    clean["score"] = clean.visa_free_count.astype(float).mask(clean.visa_free_count.eq(0))
    valid_years = sorted(clean.loc[clean.score.notna(), "year"].unique())
    require(2006 in valid_years and 2025 in valid_years, "Scores absents aux bornes de comparaison.")
    counts = clean.groupby("code").score.count()
    panel_codes = counts[counts.eq(len(valid_years))].index
    require(len(panel_codes) > 0, "Aucun passeport dans le panel complet.")
    panel = clean[clean.code.isin(panel_codes)].copy()
    excluded = clean[~clean.code.isin(panel_codes)].groupby(["code", "country", "region"]).agg(
        premiere_annee=("year", "min"), scores_exploitables=("score", "count")
    ).reset_index()
    annual = clean.groupby("year").agg(
        lignes=("code", "size"),
        scores_exploitables=("score", "count"),
        zeros=("visa_free_count", lambda x: x.eq(0).sum()),
    ).reindex(YEARS)
    regional = {
        region: quantiles(panel[panel.region.eq(region)])
        for region in REGIONS if panel.region.eq(region).any()
    }
    meta = rank[["code", "country", "region"]].drop_duplicates()
    endpoints = panel.pivot(index="code", columns="year", values="score")[[2006, 2025]]
    endpoints = endpoints.rename(columns={2006: "score_2006", 2025: "score_2025"})
    endpoints["gain"] = endpoints.score_2025 - endpoints.score_2006
    endpoint_ranks = panel.pivot(index="code", columns="year", values="rank")[[2006, 2025]]
    endpoint_ranks = endpoint_ranks.rename(columns={2006: "rang_2006", 2025: "rang_2025"})
    endpoints = endpoints.join(endpoint_ranks).join(meta.set_index("code")).reset_index()

    records, universe = [], set()
    for row in lists.to_dict("records"):
        parsed = {
            key: parse_destinations(row[key], f"{row['code']}/{key}")
            for key in CATEGORIES
        }
        codes = [item["code"] for items in parsed.values() for item in items]
        require(len(codes) == len(set(codes)), f"Catégories chevauchantes pour {row['code']}.")
        universe.update(codes)
        records.append({
            "code": row["code"], "country_list": row["country"],
            **{key: len(items) for key, items in parsed.items()}, "total": len(codes),
        })
    snapshot = pd.DataFrame(records).merge(
        rank[rank.year.eq(2025)][["code", "country", "region", "visa_free_count"]],
        on="code", how="left", validate="one_to_one",
    )
    require(snapshot.country.eq(snapshot.country_list).all(), "Libellés incohérents entre les CSV.")
    snapshot["score_listes"] = snapshot[SCORE_CATEGORIES].sum(axis=1)
    snapshot["ecart_score"] = snapshot.score_listes - snapshot.visa_free_count
    composition = snapshot.groupby("region")[[*CATEGORIES, "total", "score_listes"]].mean()
    composition["n"] = snapshot.groupby("region").size()
    composition = composition.sort_values("score_listes", ascending=False)
    return {
        "raw": rank, "clean": clean, "panel": panel, "annual": annual,
        "panel_n": len(panel_codes), "missing_years": sorted(set(YEARS) - set(valid_years)),
        "excluded": excluded, "global": quantiles(panel), "available": quantiles(clean),
        "regional": regional, "endpoints": endpoints, "snapshot": snapshot,
        "composition": composition, "destination_universe": len(universe),
    }


def style_figure(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=height,
        font={"family": "Segoe UI, Arial, sans-serif", "size": 13, "color": INK},
        paper_bgcolor="white", plot_bgcolor="white",
        margin={"l": 65, "r": 35, "t": 45, "b": 65},
        separators=", ", hoverlabel={"bgcolor": "white"},
        legend={"orientation": "h", "y": 1.09, "x": 0, "font": {"size": 12}},
    )
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    return fig


def nullable(values) -> list:
    return [None if pd.isna(value) else float(value) for value in values]


def contiguous_segments(table: pd.DataFrame) -> list[pd.DataFrame]:
    # Plotly peut refermer une surface remplie au-delà d'un trou : segmenter les rubans.
    segments, years = [], []
    for year in table.index:
        if pd.notna(table.loc[year, "median"]):
            years.append(year)
        elif years:
            segments.append(table.loc[years])
            years = []
    if years:
        segments.append(table.loc[years])
    return segments


def add_band(fig, table, low, high, color, name, row=1, col=1, legend=True):
    for index, segment in enumerate(contiguous_segments(table)):
        x = segment.index.tolist()
        fig.add_trace(go.Scatter(
            x=x + x[::-1], y=segment[low].tolist() + segment[high].tolist()[::-1],
            mode="lines", line={"width": 0}, fill="toself", fillcolor=color,
            name=name, legendgroup=name, showlegend=legend and index == 0,
            hoverinfo="skip",
        ), row=row, col=col)
        if len(segment) == 1:
            lower, upper = segment.iloc[0][low], segment.iloc[0][high]
            fig.add_trace(go.Scatter(
                x=x, y=[(lower + upper) / 2], mode="markers",
                marker={"size": 0, "opacity": 0, "color": color},
                showlegend=False, legendgroup=name, hoverinfo="skip",
                error_y={"type": "data", "array": [(upper - lower) / 2], "visible": True,
                         "color": color, "thickness": 5, "width": 4},
            ), row=row, col=col)


def shade_missing(fig, years, row=1, col=1):
    for year in years:
        fig.add_vrect(
            x0=year - 0.4, x1=year + 0.4, fillcolor=GRID, opacity=0.65,
            line_width=0, layer="below", row=row, col=col,
        )


def global_figure(data: dict) -> go.Figure:
    table = data["global"]
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.13,
        subplot_titles=("Distribution des scores", "Écart absolu entre P90 et P10"),
    )
    add_band(fig, table, "p10", "p90", "#DCE5F3", "80 % centraux · P10–P90")
    add_band(fig, table, "p25", "p75", "#A9CDCE", "50 % centraux · P25–P75")
    for column, label, color, dash in (
        ("p10", "P10", MUTED, "dot"),
        ("p90", "P90", MUTED, "dot"),
        ("median", "Médiane", ACCENT, "solid"),
    ):
        fig.add_trace(go.Scatter(
            x=YEARS, y=nullable(table[column]), mode="lines+markers",
            name=label, showlegend=column == "median", connectgaps=False,
            line={"color": color, "width": 3 if column == "median" else 1, "dash": dash},
            marker={"size": 5}, customdata=table.n.tolist(),
            hovertemplate=f"{label} · %{{x}} : %{{y:.1f}} destinations<br>n = %{{customdata}}<extra></extra>",
        ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=YEARS, y=nullable(table.gap), mode="lines+markers", connectgaps=False,
        line={"color": INK, "width": 2}, name="P90 − P10", showlegend=False,
        hovertemplate="%{x} · écart P90 − P10 : %{y:.1f} destinations<extra></extra>",
    ), row=2, col=1)
    for row in (1, 2):
        shade_missing(fig, data["missing_years"], row=row)
        fig.update_xaxes(range=[2005.6, 2025.5], tickvals=[2006, 2008, 2010, 2015, 2020, 2025], row=row)
    fig.update_yaxes(title_text="Destinations", range=[0, 205], row=1)
    fig.update_yaxes(title_text="Destinations d’écart", range=[0, 160], row=2)
    fig.update_xaxes(title_text="Année · bandes grises : scores indisponibles", row=2)
    return style_figure(fig, 630)


def regional_figure(data: dict) -> go.Figure:
    regions = list(data["regional"])
    rows = math.ceil(len(regions) / 2)
    titles = [
        f"{REGIONS[region][0]} · n = {int(data['regional'][region].n.max())}"
        for region in regions
    ]
    fig = make_subplots(rows=rows, cols=2, subplot_titles=titles, vertical_spacing=0.09, horizontal_spacing=0.12)
    for index, region in enumerate(regions):
        row, col = index // 2 + 1, index % 2 + 1
        table = data["regional"][region]
        label, color = REGIONS[region]
        red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        add_band(fig, table, "p25", "p75", f"rgba({red},{green},{blue},0.18)", label, row, col, False)
        custom = [
            [fr(item.p25), fr(item.p75), int(item.n)] for item in table.itertuples()
        ]
        fig.add_trace(go.Scatter(
            x=YEARS, y=nullable(table["median"]), name=label, mode="lines+markers",
            line={"color": color, "width": 2.5}, marker={"size": 4},
            showlegend=False, connectgaps=False, customdata=custom,
            hovertemplate=(
                f"{label} · %{{x}}<br>Médiane : %{{y:.1f}}<br>"
                "P25–P75 : %{customdata[0]}–%{customdata[1]}<br>n = %{customdata[2]}<extra></extra>"
            ),
        ), row=row, col=col)
        shade_missing(fig, data["missing_years"], row, col)
        fig.update_xaxes(range=[2005.6, 2026], tickvals=[2006, 2015, 2025], row=row, col=col)
        fig.update_yaxes(range=[0, 200], tickvals=[0, 50, 100, 150, 200], row=row, col=col)
    if len(regions) % 2:
        fig.update_xaxes(visible=False, row=rows, col=2)
        fig.update_yaxes(visible=False, row=rows, col=2)
        fig.add_annotation(
            x=0.76, y=0.09, xref="paper", yref="paper", showarrow=False, align="left",
            text="Même échelle : 0–200 destinations<br>Trait : médiane · ruban : P25–P75<br>"
                 "Gris : année sans score exploitable<br>Un passeport = une observation",
            font={"color": MUTED, "size": 13},
        )
    return style_figure(fig, rows * 235)


def country_figure(data: dict) -> go.Figure:
    endpoints = data["endpoints"]
    fig = go.Figure()
    symbols = ["circle", "square", "diamond", "triangle-up", "cross", "x", "triangle-down"]
    for (region, (label, color)), symbol in zip(REGIONS.items(), symbols):
        subset = endpoints[endpoints.region.eq(region)]
        fig.add_trace(go.Scatter(
            x=subset.score_2006.tolist(), y=subset.gain.tolist(), mode="markers", name=label,
            marker={"color": color, "size": 9, "symbol": symbol, "opacity": 0.8,
                    "line": {"width": 0.5, "color": "white"}},
            customdata=subset[["country", "code", "score_2025", "rang_2006", "rang_2025"]].values.tolist(),
            hovertemplate=(
                "<b>%{customdata[0]} (%{customdata[1]})</b><br>"
                f"{label}<br>2006 : %{{x:.0f}} · 2025 : %{{customdata[2]:.0f}}<br>"
                "Variation : %{y:+.0f} destinations<br>"
                "Rangs source : %{customdata[3]} → %{customdata[4]}<extra></extra>"
            ),
        ))
    fig.add_hline(y=0, line={"color": MUTED, "width": 1.5, "dash": "dash"})
    labelled = endpoints.loc[
        [endpoints.gain.idxmax(), endpoints.gain.idxmin(),
         endpoints.score_2025.idxmax(), endpoints.score_2025.idxmin()]
    ].drop_duplicates("code")
    for item in labelled.itertuples():
        fig.add_annotation(
            x=item.score_2006, y=item.gain, ax=25 if item.score_2006 < 100 else -35,
            ay=-28 if item.gain < 130 else 28,
            text=f"{html.escape(item.country)} · {item.gain:+.0f}",
            arrowhead=0, arrowcolor=MUTED, bgcolor="rgba(255,255,255,0.9)",
            borderpad=3, font={"size": 12},
        )
    fig.update_xaxes(title="Score en 2006 · destinations", range=[0, endpoints.score_2006.max() + 12])
    fig.update_yaxes(title="Variation 2025 − 2006 · destinations",
                     range=[min(-15, endpoints.gain.min() - 10), endpoints.gain.max() + 20])
    return style_figure(fig, 560)


def snapshot_figure(data: dict) -> go.Figure:
    composition = data["composition"]
    labels = [f"{REGIONS[region][0]} · n = {int(row.n)}" for region, row in composition.iterrows()]
    fig = go.Figure()
    for key, (label, color) in CATEGORIES.items():
        values = composition[key].tolist()
        fig.add_trace(go.Bar(
            x=values, y=labels, orientation="h", name=label, marker_color=color,
            text=[fr(value) if value >= 7 else "" for value in values], textposition="inside",
            insidetextfont={"color": "white" if key in ("visa_free_access", "visa_required") else INK},
            customdata=composition[["n", "total"]].values.tolist(),
            hovertemplate=(
                f"{label}<br>%{{y}}<br>Moyenne : %{{x:.2f}} destinations<br>"
                "Total moyen des cinq listes : %{customdata[1]:.2f}<extra></extra>"
            ),
        ))
    fig.update_layout(barmode="stack", bargap=0.28, uniformtext={"minsize": 11, "mode": "hide"})
    fig.update_xaxes(title="Nombre moyen de destinations par passeport · cinq catégories disjointes",
                     range=[0, math.ceil(composition.total.max() / 10) * 10])
    fig.update_yaxes(autorange="reversed")
    style_figure(fig, 520)
    fig.update_layout(margin={"l": 175, "r": 30, "t": 95, "b": 70},
                      legend={"y": 1.27, "font": {"size": 12}, "traceorder": "normal"})
    return fig


def table_html(frame: pd.DataFrame, caption: str) -> str:
    table = frame.to_html(index=False, border=0, escape=True, na_rep="Indisponible",
                          float_format=lambda value: fr(value))
    return (
        '<div class="table-scroll" tabindex="0" role="region" aria-label="'
        + html.escape(caption, quote=True) + '">'
        + table.replace('<thead>', f"<caption>{html.escape(caption)}</caption><thead>") + "</div>"
    )


def chart_section(anchor, scope, title, message, figure, encoding, limitation, table):
    chart = pio.to_html(
        figure, full_html=False, include_plotlyjs=False, include_mathjax=False,
        div_id=f"plot-{anchor}", config={"responsive": True, "displayModeBar": False,
                                      "displaylogo": False, "scrollZoom": False},
    )
    return f"""
    <section id="{anchor}" aria-labelledby="title-{anchor}">
      <p class="scope">{scope}</p><h2 id="title-{anchor}">{title}</h2>
      <p class="message" id="message-{anchor}">{message}</p>
      <div class="chart-scroll" tabindex="0" role="region"
           aria-label="{html.escape(title, quote=True)}" aria-describedby="message-{anchor}">
        <div class="chart">{chart}</div>
      </div>
      <div class="reading"><p><strong>Lire le graphique.</strong> {encoding}</p>
        <p><strong>Limite.</strong> {limitation}</p></div>
      <details><summary>Consulter les valeurs du graphique</summary>{table}</details>
    </section>"""


CSS = """
:root{--ink:#17324D;--muted:#65758B;--accent:#007D79;--ground:#EDF1F9;--line:#D3DDEB}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--ground);
color:var(--ink);font:16px/1.6 "Segoe UI",Arial,sans-serif}
main{max-width:1240px;margin:auto;padding:36px 28px 70px}
header{display:grid;grid-template-columns:1.7fr 1fr;gap:40px;padding:20px 0 32px}
h1,h2{font-family:Bahnschrift,"Arial Narrow","Segoe UI",sans-serif;font-weight:600;line-height:1.12}
h1{font-size:clamp(34px,4vw,56px);letter-spacing:-1.4px;margin:12px 0 20px;max-width:760px}
h2{font-size:29px;margin:0 0 18px}p{margin:0 0 14px}
.eyebrow,.scope{font:600 12px/1.6 Consolas,monospace;letter-spacing:1.4px;text-transform:uppercase}
.scope{color:var(--accent);margin:0 0 9px}.intro{font-size:18px;max-width:720px}
.passage{align-self:center;border-left:5px solid var(--accent);padding:18px 22px;background:white}
.passage dt{font-size:14px;color:var(--muted)}.passage dd{margin:2px 0 14px;font:600 25px Bahnschrift,sans-serif}
.passage dd:last-child{margin-bottom:0}.arrow{color:var(--accent)}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 25px}a{color:var(--accent)}
nav a{border:1px solid var(--line);border-radius:18px;padding:5px 16px;text-decoration:none;background:white}
:focus-visible{outline:3px solid #A65A16;outline-offset:4px}
.notice{background:#E2EAF5;border-left:5px solid #A65A16;padding:18px 22px;margin-bottom:28px}
.notice p:last-child{margin-bottom:0}section{background:white;border:1px solid var(--line);
border-radius:10px;padding:30px;margin-bottom:28px;scroll-margin-top:18px}
.message{font-size:18px;max-width:1020px}.chart-scroll{overflow-x:auto}
.chart{min-width:780px}.reading{display:grid;grid-template-columns:1fr 1fr;gap:30px;margin-top:12px;
font-size:14px;color:var(--muted)}.reading strong{color:var(--ink)}
details{border-top:1px solid var(--line);padding-top:14px;margin-top:10px}
summary{cursor:pointer;font-weight:600;color:var(--accent)}.table-scroll{overflow:auto;max-height:480px;margin-top:15px}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
caption{text-align:left;font-weight:600;padding:10px 0}th,td{border-bottom:1px solid var(--line);
padding:7px 10px;text-align:right;white-space:nowrap}th{background:#EDF1F9;position:sticky;top:0}
td:first-child,th:first-child{text-align:left}code{overflow-wrap:anywhere;font-size:12px}
.footnote{font-size:14px;color:var(--muted)}.methods li{margin-bottom:9px}
footer{padding:0 8px;color:var(--muted);font-size:13px}
@media(max-width:800px){main{padding:18px 12px 40px}header{grid-template-columns:1fr;gap:10px}
section{padding:20px 14px}h2{font-size:25px}.reading{grid-template-columns:1fr;gap:0}
.chart-scroll{border-bottom:2px solid var(--line)}.passage{padding:14px 18px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{body{background:white}main{max-width:none;padding:0}nav,summary{display:none}
section{break-inside:avoid}.chart{min-width:0}details:not([open]){display:none}}
"""


def render_html(data: dict, hashes: dict[str, str]) -> str:
    q, endpoints, composition = data["global"], data["endpoints"], data["composition"]
    start, end = q.loc[2006], q.loc[2025]
    n, raw_n = data["panel_n"], data["raw"].code.nunique()
    zeros, missing = int(data["annual"].zeros.sum()), ", ".join(map(str, data["missing_years"]))
    all_end = data["available"].loc[2025]
    country_table = endpoints.rename(columns={
        "country": "Pays / territoire", "code": "Code", "region": "Région",
        "score_2006": "Score 2006", "score_2025": "Score 2025", "gain": "Variation",
        "rang_2006": "Rang source 2006", "rang_2025": "Rang source 2025",
    }).sort_values(["Variation", "Code"], ascending=[False, True])
    region_table = pd.concat(
        [table.assign(region=REGIONS[region][0]).reset_index() for region, table in data["regional"].items()],
        ignore_index=True,
    )[["region", "year", "n", "p25", "median", "p75"]]
    region_table.columns = ["Région", "Année", "n", "P25", "Médiane", "P75"]
    global_table = q.reset_index().rename(columns={
        "year": "Année", "median": "Médiane", "gap": "P90 − P10", "ratio": "P90 / P10",
    })
    global_table.columns = [str(column).upper() if str(column).startswith("p") else column for column in global_table.columns]
    high, low = endpoints.loc[endpoints.gain.idxmax()], endpoints.loc[endpoints.gain.idxmin()]
    region_end = {region: table.loc[2025, "median"] for region, table in data["regional"].items()}
    region_span = max(region_end.values()) - min(region_end.values())
    sections = [
        chart_section(
            "monde", f"Monde · panel constant de {n} passeports",
            "L’accès progresse, l’écart absolu aussi",
            f"La médiane passe de <strong>{fr(start['median'], 0)} à {fr(end['median'], 0)}</strong> destinations. "
            f"L’écart P90 − P10 augmente de <strong>{fr(start.gap)} à {fr(end.gap)}</strong>. "
            f"Mais le rapport P90 / P10 diminue de {fr(start.ratio, 2)} à {fr(end.ratio, 2)} : "
            "inégalité absolue et inégalité relative ne racontent pas la même évolution.",
            global_figure(data),
            "En haut, médiane et intervalles centraux des scores ; en bas, différence entre les "
            "90e et 10e percentiles. Unités en destinations, axes temporels alignés. "
            "Les rubans décrivent la dispersion, pas une incertitude statistique. "
            "Aux années isolées, des segments verticaux montrent les mêmes intervalles.",
            "Les percentiles ne suivent pas les mêmes pays d’une année à l’autre. Les années grises "
            "restent vides, sans interpolation. La taille de l’univers des destinations historique est inconnue.",
            table_html(global_table, "Distribution annuelle du panel constant · quantiles linéaires"),
        ),
        chart_section(
            "regions", "Régions · sept groupes de la source",
            "Des trajectoires régionales à comparer à échelle égale",
            f"En 2025, les médianes du panel vont de <strong>{fr(min(region_end.values()), 1)} "
            f"à {fr(max(region_end.values()), 1)}</strong> destinations "
            f"(écart de {fr(region_span)}). Les rubans rendent visible la dispersion interne.",
            regional_figure(data),
            "Un panneau par région, une couleur stable, une médiane annuelle et un ruban P25–P75. "
            "Tous les axes verticaux couvrent 0–200 destinations ; les effectifs sont constants dans chaque panneau. "
            "Les intervalles des années isolées sont représentés par des segments verticaux.",
            "Ces groupes ne sont pas des blocs homogènes. Les régions sont celles du CSV, conservées "
            "sur toute la période, sans pondération démographique ni reconstitution des frontières passées.",
            table_html(region_table, "Médianes et intervalles interquartiles régionaux du panel"),
        ),
        chart_section(
            "pays", f"Pays et territoires · {n} comparaisons appariées",
            "Le point de départ ne résume pas le gain",
            f"Parmi ces {n} passeports : {int(endpoints.gain.gt(0).sum())} en hausse, "
            f"{int(endpoints.gain.lt(0).sum())} en baisse et {int(endpoints.gain.eq(0).sum())} stables. "
            f"Les variations extrêmes sont {html.escape(high.country)} ({high.gain:+.0f}) et "
            f"{html.escape(low.country)} ({low.gain:+.0f}).",
            country_figure(data),
            "Abscisse : score de 2006 ; ordonnée : score de 2025 moins celui de 2006. Un point de taille "
            "constante par passeport ; couleur et forme indiquent la région. La ligne zéro sépare gains et pertes. "
            "Sont nommés les gains extrêmes et les scores 2025 extrêmes ; les autres noms figurent au survol et dans la table.",
            "Deux bornes ne montrent ni les ruptures ni la régularité du parcours. Le gain dépend "
            "arithmétiquement du score initial : ce nuage ne mesure pas une convergence causale. "
            "Les rangs, ordinaux et avec ex æquo, restent une information secondaire dans le survol.",
            table_html(country_table, "Tous les passeports appariés, triés par variation décroissante"),
        ),
        chart_section(
            "conditions", f"Conditions d’entrée · instantané de {len(data['snapshot'])} passeports",
            "Un score Henley ne signifie pas toujours « sans formalité »",
            "Les cinq listes distinguent l’accès sans visa, à l’arrivée, avec ETA, le visa en ligne et "
            "le visa requis. Les trois premières catégories contribuent au score selon la documentation locale ; "
            "les deux dernières n’y contribuent pas.",
            snapshot_figure(data),
            "Barres empilées : nombre moyen de destinations par passeport et par catégorie. "
            "Régions triées par somme moyenne des trois catégories comptées dans le score. "
            "Ici la couleur désigne la condition d’entrée, et non la région. Ce ne sont pas des pourcentages.",
            "Aucune année dans country_lists.csv : instantané de l’extraction TidyTuesday, pas une série. "
            "Les moyennes portent sur tous les passeports disponibles, pas seulement le panel historique. "
            "L’ordre des catégories n’est pas une échelle mesurée de coût ou de difficulté.",
            table_html(
                composition.rename(index={key: value[0] for key, value in REGIONS.items()})
                .reset_index().rename(columns={"region": "Région", **{key: value[0] for key, value in CATEGORIES.items()}}),
                "Moyennes régionales par catégorie · instantané",
            ),
        ),
    ]
    mismatch = int(data["snapshot"].ecart_score.ne(0).sum())
    total_distribution = "; ".join(
        f"{count} passeport(s) avec {total} destinations"
        for total, count in data["snapshot"].total.value_counts().sort_index().items()
    )
    atypical = data["snapshot"][data["snapshot"].total.ne(data["snapshot"].total.mode().iloc[0])]
    atypical_text = "; ".join(f"{html.escape(row.country)} : {row.total}" for row in atypical.itertuples())
    sensitivity = pd.concat(
        [data[key].loc[[2006, 2025]].assign(echantillon=label).reset_index()
         for key, label in (("global", "Panel constant"), ("available", "Tous scores exploitables"))],
        ignore_index=True,
    )[["echantillon", "year", "n", "median", "p10", "p90", "gap", "ratio"]]
    hash_text = "".join(f"<li>{name} : <code>{digest}</code></li>" for name, digest in hashes.items())
    snapshot_table = data["snapshot"][["code", "country", "region", *CATEGORIES, "total", "score_listes",
                                       "visa_free_count", "ecart_score"]].sort_values("country")
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline';
style-src 'unsafe-inline'; img-src data: blob:; font-src 'none'; connect-src 'none';">
<title>Passeports : les écarts de mobilité · 2006–2025</title>
<style>{CSS}</style><script>{get_plotlyjs()}</script></head>
<body><main>
<header><div><p class="eyebrow">Henley Passport Index / TidyTuesday 2025-09-09 / Proposition 01</p>
<h1>Plus de destinations.<br>Des écarts qui persistent.</h1>
<p class="intro">Comment les inégalités de mobilité associées aux passeports ont-elles évolué
entre 2006 et 2025, selon les pays et les régions ? Quatre vues pour distinguer accès, dispersion et conditions d’entrée.</p>
<p class="footnote">Pour les analystes en relations internationales, journalistes de données et décideurs publics.
Un score mesure des possibilités administratives, pas des voyages effectivement réalisés.</p></div>
<dl class="passage"><dt>Médiane · panel constant · 2006 → 2025</dt>
<dd>{fr(start['median'], 0)} <span class="arrow">→</span> {fr(end['median'], 0)} destinations</dd>
<dt>Écart absolu P90 − P10</dt><dd>{fr(start.gap)} <span class="arrow">→</span> {fr(end.gap)} destinations</dd>
<dt>Rapport relatif P90 / P10</dt><dd>{fr(start.ratio, 2)} <span class="arrow">→</span> {fr(end.ratio, 2)}</dd></dl></header>
<nav aria-label="Sections"><a href="#monde">Monde</a><a href="#regions">Régions</a>
<a href="#pays">Pays</a><a href="#conditions">Conditions d’entrée</a><a href="#methode">Méthode et données</a></nav>
<aside class="notice"><p><strong>Avant de lire : zéro n’est pas interprété comme aucune destination.</strong>
Le fichier contient {zeros} scores nuls, dont toutes les valeurs de {missing}, alors que les rangs sont renseignés.
Par prudence, ces zéros sont considérés comme indisponibles dans cette proposition.
C’est une hypothèse de traitement, à confirmer auprès de la source, pas une correction du CSV.</p>
<p>Vues historiques : <strong>{n} passeports sur {raw_n}</strong>, avec un score positif à chacune des
{len(YEARS) - len(data['missing_years'])} années exploitables. Aucun score imputé. Vues indépendantes :
survol et légende Plotly locaux seulement, sans filtre coordonné. Sur petit écran, les graphiques se font défiler horizontalement.</p></aside>
<noscript><p class="notice">JavaScript est désactivé. Les graphiques nécessitent JavaScript local ;
les messages et les tables détaillées restent disponibles ci-dessous.</p></noscript>
{''.join(sections)}
<section id="methode" class="methods"><p class="scope">Méthode et traçabilité</p>
<h2>Ce que ce prototype permet — et ce qu’il ne prouve pas</h2>
<ul><li><strong>Sources :</strong> uniquement rank_by_year.csv, country_lists.csv et le dictionnaire readme.md
local pour les définitions. Données Henley &amp; Partners, mise à disposition TidyTuesday du 9 septembre 2025.
Cette date de publication n’établit pas la date exacte de chaque observation.</li>
<li><strong>Mesure principale :</strong> visa_free_count au sens Henley : sans visa, visa à l’arrivée
ou ETA, selon les conditions documentées. Une destination n’est pas nécessairement un État souverain.
Les scores ne mesurent ni coût du voyage, ni revenu, ni droit de séjour durable, ni mobilité effective.</li>
<li><strong>Panel :</strong> codes communs à toutes les années ayant au moins un score positif.
Les zéros deviennent manquants en mémoire seulement. Les années {missing} restent dans les axes
et interrompent les courbes et rubans. Les {len(data['excluded'])} exclusions sont détaillées ci-dessous.</li>
<li><strong>Agrégation :</strong> un passeport = une observation, sans pondération par population.
Quantiles pandas à interpolation linéaire ; les décimales sont donc normales.
P10 et P90 bornent les 80 % centraux et ne représentent pas les extrêmes.</li>
<li><strong>Sensibilité à la composition :</strong> en 2025, utiliser les {int(all_end.n)} scores exploitables
plutôt que le panel donne une médiane de {fr(all_end['median'], 0)} (contre {fr(end['median'], 0)})
et un écart P90 − P10 de {fr(all_end.gap)} (contre {fr(end.gap)}).
Le panel stabilise la composition, mais n’est pas représentatif de tous les passeports.</li>
<li><strong>Listes JSON :</strong> enveloppe [[…]] décodée avec json.loads, contrôles des codes uniques
dans et entre catégories, puis comptage et jointure par code. {data['destination_universe']} codes de destination
distincts dans l’union des listes ; {total_distribution}. Cas de total atypique : {atypical_text or 'aucun'}.
Ni dénominateur fixé artificiellement à 226, ni normalisation historique sur l’univers actuel.</li>
<li><strong>Rapprochement descriptif :</strong> {mismatch} écart(s) entre la somme sans visa + arrivée + ETA
et visa_free_count de 2025 sur {len(data['snapshot'])} passeports. Cette concordance ne date pas l’instantané
et ne prouve pas une collecte simultanée. Les catégories ne sont jamais projetées sur les années antérieures.</li>
<li><strong>Interprétation :</strong> ni causalité diplomatique, ni effet attribué à un conflit, une pandémie
ou une réforme. Les changements de couverture et de méthode de l’indice ne sont pas documentés ici ;
une hausse en nombre peut aussi refléter un changement de l’univers des destinations.</li></ul>
<details><summary>Couverture annuelle et scores nuls</summary>
{table_html(data['annual'].reset_index(), 'Couverture des données brutes, avant panel')}</details>
<details><summary>Passeports exclus des comparaisons historiques</summary>
{table_html(data['excluded'], 'Exclusions : absence de ligne et/ou score nul sur au moins une année exploitable')}</details>
<details><summary>Sensibilité : panel constant et tous les scores exploitables</summary>
{table_html(sensitivity, 'Comparaison des échantillons aux deux bornes')}</details>
<details><summary>Contrôle des listes pour chaque passeport</summary>
{table_html(snapshot_table, 'Comptages des listes et rapprochement avec le score 2025')}</details>
<details><summary>Reproduire et vérifier les sources</summary>
<p>Depuis le dossier du projet : <code>.\\.venv\\Scripts\\python.exe prototype_ia.py</code>.
Le script écrit <code>livrables\\proposition_ia.html</code>. Aucun serveur, aucune API ni ressource distante
ne sont nécessaires pour ouvrir ce HTML ; Plotly.js est inclus une seule fois.
Versions de génération : pandas {pd.__version__}, Plotly {plotly.__version__}.</p>
<p>Empreintes SHA-256 des fichiers lus :</p><ul>{hash_text}</ul></details></section>
<footer>Prototype descriptif · Itération 01 · Quatre figures, aucune conclusion causale.
Les tables sont accessibles sans survol ; les libellés de pays conservent ceux de la source.</footer>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=BASE, help="Dossier des deux CSV locaux.")
    parser.add_argument("--output", type=Path, default=BASE / "livrables" / "proposition_ia.html")
    args = parser.parse_args()
    data_dir, output = args.data_dir.resolve(), args.output.resolve()
    require(output.suffix.lower() == ".html", "La sortie doit être un fichier .html.")
    require(
        output not in {data_dir / "rank_by_year.csv", data_dir / "country_lists.csv"},
        "La sortie ne peut pas remplacer une source.",
    )
    before = source_hashes(data_dir)
    data = prepare_data(*load_data(data_dir))
    document = render_html(data, before)
    require(before == source_hashes(data_dir), "Un CSV a changé pendant la génération.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(f"HTML : {output}")
    print(f"4 figures | panel : {data['panel_n']} | scores nuls écartés : {int(data['annual'].zeros.sum())}")
    print(f"SHA-256 sources inchangés | pandas {pd.__version__} | Plotly {plotly.__version__}")


if __name__ == "__main__":
    main()
