"""Huit graphiques lisibles en projection : valeurs écrites, aucune info au survol."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from passport_dashboard import story
from passport_dashboard.metrics import WORLD
from passport_dashboard.story import fr, pct, signed
from passport_dashboard.theme import (
    ACCENT_COLOR,
    MUTED_COLOR,
    RECIPROCITY_COLORS,
    RECIPROCITY_LABELS,
    REGIME_COLORS,
    REGIME_LABELS,
    REGION_COLORS,
    REGION_LABELS,
    TEXT_COLOR,
    apply_theme,
    title_text,
)

__all__ = [
    "DEFAULT_SCATTER_LABELS",
    "regional_distribution",
    "inequality_trend",
    "biggest_changes",
    "entry_modes",
    "reciprocity",
    "hospitality_vs_power",
    "regional_openness",
    "clubs",
]

DEFAULT_SCATTER_LABELS = ("SG", "US", "AU", "FR", "CN", "IN", "AF", "RW", "SC")
_DARK_TEXT = {"electronic_travel_authorisation", "visa_online", "favourable", "mutual_closed"}


def _note(text: str, **kwargs) -> dict:
    base = {"showarrow": False, "font": {"size": 14, "color": MUTED_COLOR}}
    base.update(kwargs)
    return {"text": text, **base}


def _row_label(code: str, detail: str = "") -> str:
    name = "<b>Monde</b>" if code == WORLD else REGION_LABELS[code]
    if detail:
        name += f"<br><span style='font-size:13px;color:{MUTED_COLOR}'>{detail}</span>"
    return name


# Q1 ---------------------------------------------------------------------------
def _extreme_label(group: pd.DataFrame, row: pd.Series) -> str:
    """Nomme un extrême et signale honnêtement les ex æquo."""
    ties = int(group["score"].eq(row["score"]).sum()) - 1
    suffix = f" (+{ties} ex æquo)" if ties else ""
    return f"{row['country']}{suffix} : {fr(row['score'])}"


def regional_distribution(scores: pd.DataFrame, year: int) -> go.Figure:
    """Un point par passeport, une ligne par région, médiane et extrêmes nommés."""
    medians = scores.groupby("region")["score"].median().sort_values()
    figure = go.Figure()
    annotations = []
    for position, code in enumerate(medians.index):
        group = scores.loc[scores["region"].eq(code)].sort_values(["score", "code"])
        offsets = [((index % 5) - 2) * 0.07 for index in range(len(group))]
        figure.add_trace(go.Scatter(
            x=group["score"], y=[position + offset for offset in offsets], mode="markers",
            marker={"size": 12, "color": REGION_COLORS[code], "opacity": 0.6,
                    "line": {"width": 1, "color": "white"}},
            showlegend=False,
        ))
        figure.add_trace(go.Scatter(
            x=[medians[code]], y=[position], mode="markers", showlegend=False,
            marker={"symbol": "line-ns", "size": 40, "line": {"width": 5, "color": TEXT_COLOR}},
        ))
        low, high = group.iloc[0], group.iloc[-1]
        annotations.append(_note(
            _extreme_label(group, low), x=low["score"], y=position, yshift=25,
            xanchor="left", font={"size": 13, "color": TEXT_COLOR}, bgcolor="rgba(255,255,255,0.85)",
        ))
        annotations.append(_note(
            _extreme_label(group, high), x=high["score"], y=position, yshift=25,
            xanchor="right", font={"size": 13, "color": TEXT_COLOR}, bgcolor="rgba(255,255,255,0.85)",
        ))
    world = scores["score"].median()
    figure.add_vline(x=world, line={"dash": "dash", "color": MUTED_COLOR, "width": 2})
    annotations.append(_note(
        f"Médiane mondiale : {fr(world)}", x=world, y=len(medians) - 0.45, xanchor="left",
        xshift=6, font={"size": 14, "color": MUTED_COLOR},
    ))
    ticks = [
        _row_label(code, f"médiane {fr(medians[code], 1 if medians[code] % 1 else 0)} · {int((scores['region'] == code).sum())} pays")
        for code in medians.index
    ]
    figure.update_layout(
        title_text=title_text(
            story.q1(scores, year),
            "Chaque point est un passeport · trait noir : médiane de la région · noms : passeport le plus faible et le plus fort",
        ),
        annotations=annotations,
    )
    figure.update_yaxes(tickvals=list(range(len(medians))), ticktext=ticks, range=[-0.6, len(medians) - 0.25],
                        showgrid=False)
    figure.update_xaxes(range=[0, 205], dtick=25, title_text=f"Destinations accessibles sans démarche préalable en {year}")
    return apply_theme(figure, height=700)


# Q2 ---------------------------------------------------------------------------
def inequality_trend(series: pd.DataFrame) -> go.Figure:
    """Barres flottantes P10–P90 par an, médiane, valeurs d'écart écrites."""
    measured = series.dropna(subset=["gap"])
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=measured["year"], y=measured["gap"], base=measured["p10"], width=0.62,
        marker={"color": "#C6DBEF"}, showlegend=False,
    ))
    lines = (
        ("p90", "P90 : 10 % les mieux dotés", "#08306B"),
        ("median", "Médiane", TEXT_COLOR),
        ("p10", "P10 : 10 % les moins dotés", ACCENT_COLOR),
    )
    annotations = []
    last = measured.iloc[-1]
    for column, label, color in lines:
        figure.add_trace(go.Scatter(
            x=series["year"], y=series[column], mode="lines+markers", connectgaps=False,
            line={"color": color, "width": 3}, marker={"size": 7, "color": color}, showlegend=False,
        ))
        annotations.append(_note(
            f"<b>{fr(last[column])}</b> {label}", x=last["year"], y=last[column], xanchor="left",
            xshift=14, font={"size": 15, "color": color},
        ))
    for row in (measured.iloc[0], measured.iloc[-1]):
        annotations.append(_note(
            f"écart<br><b>{fr(row['gap'])}</b>", x=row["year"], y=(row["p10"] + row["p90"]) / 2,
            font={"size": 15, "color": TEXT_COLOR}, bgcolor="rgba(255,255,255,0.85)",
        ))
    for year in series.loc[series["gap"].isna(), "year"]:
        annotations.append(_note("pas de<br>données", x=year, y=8, font={"size": 12, "color": MUTED_COLOR}))
    first_year, last_year = int(series["year"].min()), int(series["year"].max())
    ticks = [year for year in range(first_year, last_year, 2)] + [last_year]
    if len(ticks) > 1 and ticks[-1] - ticks[-2] < 2:
        ticks.pop(-2)
    figure.update_layout(
        title_text=title_text(
            story.q2(series),
            f"Barre bleue : du 10e au 90e percentile · panel constant de {int(series['n'].iloc[0])} passeports, "
            "mesurés chaque année",
        ),
        annotations=annotations, bargap=0.3,
        margin={"r": 290},
    )
    figure.update_xaxes(tickvals=ticks, range=[first_year - 0.7, last_year + 0.7], showgrid=False)
    figure.update_yaxes(range=[0, 210], dtick=50, title_text="Destinations accessibles")
    return apply_theme(figure, height=640)


# Q3 ---------------------------------------------------------------------------
def biggest_changes(selection: pd.DataFrame, changes: pd.DataFrame, start: int, end: int) -> go.Figure:
    """Deux classements alignés sur le même axe : plus fortes et plus faibles évolutions."""
    high = selection.loc[selection["group"].eq("high")].sort_values("delta")
    low = selection.loc[selection["group"].eq("low")].sort_values("delta", ascending=False)
    n = max(len(high), len(low))
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
        subplot_titles=(f"<b>Les {len(high)} plus fortes progressions</b>", f"<b>Les {len(low)} plus faibles évolutions</b>"),
    )
    for row, group in ((1, high), (2, low)):
        colors = [
            "#2166AC" if row == 1 else (ACCENT_COLOR if delta < 0 else "#FDB863")
            for delta in group["delta"]
        ]
        labels = [
            "" if item.delta < 0 else f"<b>{signed(item.delta)}</b>  ({fr(item.score_start)} → {fr(item.score_end)})"
            for item in group.itertuples()
        ]
        names = [f"{item.country} · {REGION_LABELS[item.region]}" for item in group.itertuples()]
        figure.add_trace(go.Bar(
            x=group["delta"], y=names, orientation="h", marker={"color": colors},
            text=labels, textposition="outside", cliponaxis=False, textfont={"size": 14},
            showlegend=False,
        ), row=row, col=1)
        # Une étiquette à gauche d'une barre négative masquerait le nom du pays.
        for item, name in zip(group.itertuples(), names):
            if item.delta < 0:
                figure.add_annotation(
                    x=0, y=name, xanchor="left", xshift=6, showarrow=False,
                    text=f"<b>{signed(item.delta)}</b>  ({fr(item.score_start)} → {fr(item.score_end)})",
                    font={"size": 14, "color": ACCENT_COLOR}, row=row, col=1,
                )
    lowest = min(0.0, float(selection["delta"].min()))
    highest = float(selection["delta"].max())
    figure.update_xaxes(range=[lowest - 8, highest * 1.42], showgrid=True, dtick=25)
    figure.update_xaxes(title_text=f"Destinations gagnées ou perdues entre {start} et {end}", row=2, col=1)
    figure.update_yaxes(showgrid=False, tickfont={"size": 14})
    figure.add_vline(x=0, line={"color": TEXT_COLOR, "width": 1.5})
    for annotation in figure.layout.annotations[:2]:
        annotation.update(font={"size": 16, "color": TEXT_COLOR}, x=0, xanchor="left")
    figure.update_layout(
        title_text=title_text(
            story.q3(changes, start, end),
            f"Barre : variation du nombre de destinations · entre parenthèses : score {start} → {end}",
        ),
        margin={"t": 130},
    )
    return apply_theme(figure, height=280 + 2 * n * 34)


# Q4, Q5 : barres empilées à 100 % ------------------------------------------------
def _stacked(shares: pd.DataFrame, columns: Sequence[str], labels: dict, colors: dict,
             order_by: str, total_text: Sequence[str], total_colors: Sequence[str],
             total_header: str) -> go.Figure:
    regional = shares.loc[shares["region"] != WORLD].sort_values(order_by)
    ordered = pd.concat([shares.loc[shares["region"] == WORLD], regional])
    rows = [_row_label(code) for code in ordered["region"]]
    figure = go.Figure()
    for column in columns:
        values = ordered[column]
        figure.add_trace(go.Bar(
            x=values, y=rows, orientation="h", name=labels[column],
            marker={"color": colors[column], "line": {"color": "white", "width": 1}},
            text=[pct(value) if value >= 5 else "" for value in values],
            textposition="inside", insidetextanchor="middle",
            textfont={"size": 15, "color": TEXT_COLOR if column in _DARK_TEXT else "white"},
        ))
    annotations = [
        _note(f"<b>{text}</b>", x=1.01, xref="paper", y=row, xanchor="left",
              font={"size": 17, "color": color})
        for row, text, color in zip(rows, total_text, total_colors)
    ]
    annotations.append(_note(total_header, x=1.01, xref="paper", y=1.0, yref="paper", xanchor="left",
                             yanchor="bottom", font={"size": 13, "color": MUTED_COLOR}))
    figure.update_layout(barmode="stack", bargap=0.28, annotations=annotations,
                         uniformtext={"minsize": 12, "mode": "hide"}, margin={"r": 150, "t": 150})
    figure.update_xaxes(range=[0, 100], ticksuffix=" %", dtick=25, showgrid=False)
    figure.update_yaxes(showgrid=False)
    return figure


def entry_modes(shares: pd.DataFrame, perspective: str = "origin") -> go.Figure:
    regional = shares.loc[shares["region"] != WORLD].sort_values("open")
    ordered = pd.concat([shares.loc[shares["region"] == WORLD], regional])
    figure = _stacked(
        shares, list(REGIME_LABELS), REGIME_LABELS, REGIME_COLORS, "open",
        [pct(value) for value in ordered["open"]], ["#08306B"] * len(ordered),
        "Sans démarche<br>préalable (bleus)",
    )
    if perspective == "origin":
        subtitle = "Région du passeport · part de ses relations avec les 227 destinations, selon la formalité exigée"
        axis = "Part des destinations (%)"
    else:
        subtitle = "Région du pays d'accueil · part des 199 passeports reçus, selon la formalité exigée"
        axis = "Part des passeports reçus (%)"
    figure.update_layout(title_text=title_text(story.q4(shares, perspective), subtitle))
    figure.update_xaxes(title_text=axis)
    return apply_theme(figure, height=640)


def reciprocity(shares: pd.DataFrame) -> go.Figure:
    regional = shares.loc[shares["region"] != WORLD].sort_values("balance")
    ordered = pd.concat([shares.loc[shares["region"] == WORLD], regional])
    figure = _stacked(
        shares, list(RECIPROCITY_LABELS), RECIPROCITY_LABELS, RECIPROCITY_COLORS, "balance",
        [f"{signed(round(value))} pts" for value in ordered["balance"]],
        ["#2166AC" if round(value) > 0 else ACCENT_COLOR if round(value) < 0 else MUTED_COLOR
         for value in ordered["balance"]],
        "Solde : faveur<br>− défaveur",
    )
    figure.update_layout(title_text=title_text(
        story.q5(shares),
        "Pour chaque pays et chaque partenaire : mon passeport entre-t-il librement chez lui, et le sien chez moi ?",
    ))
    figure.update_xaxes(title_text="Part des relations bilatérales du pays (%)")
    return apply_theme(figure, height=640)


# Q6 ---------------------------------------------------------------------------
def hospitality_vs_power(frame: pd.DataFrame, labels: Sequence[str] = DEFAULT_SCATTER_LABELS) -> go.Figure:
    figure = go.Figure()
    for code in sorted(frame["region"].unique(), key=lambda value: REGION_LABELS[value]):
        group = frame.loc[frame["region"].eq(code)]
        figure.add_trace(go.Scatter(
            x=group["welcomed"], y=group["score"], mode="markers", name=REGION_LABELS[code],
            marker={"size": 13, "color": REGION_COLORS[code], "opacity": 0.75,
                    "line": {"width": 1, "color": "white"}},
        ))
    mx, my = frame["welcomed"].median(), frame["score"].median()
    figure.add_vline(x=mx, line={"dash": "dash", "color": MUTED_COLOR, "width": 1.5})
    figure.add_hline(y=my, line={"dash": "dash", "color": MUTED_COLOR, "width": 1.5})
    corner = {"size": 15, "color": MUTED_COLOR}
    annotations = [
        _note("<i>Accueille peu,<br>voyage beaucoup</i>", x=2, y=203, xanchor="left", yanchor="top", font=corner),
        _note("<i>Accueille et voyage</i>", x=198, y=203, xanchor="right", yanchor="top", font=corner),
        _note("<i>Accueille peu,<br>voyage peu</i>", x=mx - 4, y=4, xanchor="right", yanchor="bottom", font=corner),
        _note("<i>Accueille beaucoup,<br>voyage peu</i>", x=198, y=4, xanchor="right", yanchor="bottom", font=corner),
        _note(f"médiane : {fr(mx)} passeports", x=mx, y=0, yanchor="top", yshift=-4, font={"size": 12, "color": MUTED_COLOR}),
        _note(f"médiane : {fr(my)}", x=0, y=my, xanchor="left", yanchor="bottom", font={"size": 12, "color": MUTED_COLOR}),
    ]
    indexed = frame.set_index("code")
    for code in labels:
        if code not in indexed.index:
            continue
        point = indexed.loc[code]
        dx = -45 if point["welcomed"] > mx else 45
        dy = 35 if point["score"] < my else -35
        if point["score"] < 40:
            dx, dy = 60, 12
        annotations.append({
            "x": point["welcomed"], "y": point["score"], "text": f"<b>{point['country']}</b>",
            "showarrow": True, "arrowhead": 0, "arrowwidth": 1.5, "arrowcolor": TEXT_COLOR,
            "ax": dx, "ay": dy, "font": {"size": 15, "color": TEXT_COLOR},
            "bgcolor": "rgba(255,255,255,0.8)",
        })
    figure.update_layout(
        title_text=title_text(
            story.q6(frame),
            "Chaque point est un pays · horizontal : passeports étrangers qu'il accueille sans démarche · "
            "vertical : destinations ouvertes à son passeport",
        ),
        annotations=annotations, margin={"t": 150},
    )
    figure = apply_theme(figure, height=700)
    figure.update_layout(legend={"y": 1.02})
    figure.update_xaxes(range=[-6, 206], dtick=25,
                        title_text="Passeports étrangers accueillis sans démarche préalable (sur 198)")
    figure.update_yaxes(range=[0, 208], dtick=50, title_text="Destinations ouvertes à son passeport (2025)")
    return figure


# Q7 ---------------------------------------------------------------------------
def regional_openness(matrix: pd.DataFrame) -> go.Figure:
    order = matrix.mean(axis=1).sort_values(ascending=False).index.tolist()
    data = matrix.loc[order, order]
    n = len(order)
    figure = go.Figure(go.Heatmap(
        z=data.to_numpy(), x=list(range(n)), y=list(range(n)), zmin=0, zmax=100,
        colorscale=[[0, "#F7FBFF"], [0.5, "#6BAED6"], [1, "#08306B"]], showscale=False, xgap=3, ygap=3,
    ))
    annotations = []
    for row, origin in enumerate(order):
        for column, destination in enumerate(order):
            value = data.loc[origin, destination]
            annotations.append(_note(
                f"<b>{pct(value)}</b>" if origin == destination else pct(value), x=column, y=row,
                font={"size": 17, "color": "white" if value >= 55 else TEXT_COLOR},
            ))
    shapes = [
        {"type": "rect", "x0": index - 0.5, "x1": index + 0.5, "y0": index - 0.5, "y1": index + 0.5,
         "line": {"color": TEXT_COLOR, "width": 3}}
        for index in range(n)
    ]
    origin, destination = data.stack().idxmin()
    row, column = order.index(origin), order.index(destination)
    shapes.append({"type": "rect", "x0": column - 0.5, "x1": column + 0.5, "y0": row - 0.5, "y1": row + 0.5,
                   "line": {"color": ACCENT_COLOR, "width": 4}})
    labels = [REGION_LABELS[code] for code in order]
    figure.update_layout(
        title_text=title_text(
            story.q7(matrix),
            "Case : % des couples passeport → pays où l'entrée se fait sans démarche préalable · "
            "cadre noir : sa propre région · cadre orange : minimum",
        ),
        annotations=annotations, shapes=shapes, margin={"t": 170},
    )
    figure = apply_theme(figure, height=720)
    figure.update_xaxes(tickvals=list(range(n)), ticktext=labels, side="top", showgrid=False,
                        title_text="Pays de destination ➜", title_standoff=8)
    figure.update_yaxes(tickvals=list(range(n)), ticktext=labels, autorange="reversed", showgrid=False,
                        title_text="Région du passeport")
    return figure


# Q8 ---------------------------------------------------------------------------
def clubs(table: pd.DataFrame, world_rate: float) -> go.Figure:
    data = table.sort_values("gap")
    names = [f"<b>{row.club}</b><br><span style='font-size:13px;color:{MUTED_COLOR}'>{row.members} membres</span>"
             for row in data.itertuples()]
    figure = go.Figure()
    for name, row in zip(names, data.itertuples()):
        figure.add_trace(go.Scatter(
            x=[row.outside, row.inside], y=[name, name], mode="lines",
            line={"color": "#BDBDBD", "width": 6}, showlegend=False,
        ))
    for column, label, color in (("outside", "Vers les pays non membres", ACCENT_COLOR),
                                 ("inside", "Entre membres", "#2166AC")):
        larger = data[column] >= data["outside" if column == "inside" else "inside"]
        figure.add_trace(go.Scatter(
            x=data[column], y=names, mode="markers+text", name=label,
            marker={"size": 20, "color": color, "line": {"width": 2, "color": "white"}},
            text=[f"<b>{pct(value)}</b>" for value in data[column]],
            textposition=["middle right" if flag else "middle left" for flag in larger],
            textfont={"size": 16, "color": color},
        ))
    figure.add_vline(x=world_rate, line={"dash": "dash", "color": MUTED_COLOR, "width": 2})
    annotations = [
        _note(f"Moyenne mondiale : {pct(world_rate)}", x=world_rate, y=1.0, yref="paper",
              yanchor="bottom", xanchor="left", xshift=4, font={"size": 14, "color": MUTED_COLOR}),
        _note("Écart", x=1.01, xref="paper", y=1.0, yref="paper", xanchor="left", yanchor="bottom",
              font={"size": 13, "color": MUTED_COLOR}),
    ]
    annotations += [
        _note(f"<b>{signed(row.gap)} pts</b>", x=1.01, xref="paper", y=name, xanchor="left",
              font={"size": 17, "color": TEXT_COLOR})
        for name, row in zip(names, data.itertuples())
    ]
    figure.update_layout(
        title_text=title_text(
            story.q8(table),
            "Part des relations où le passeport d'un membre entre sans démarche préalable · membres 2025 des organisations",
        ),
        annotations=annotations, margin={"r": 120, "t": 160},
    )
    figure = apply_theme(figure, height=660)
    figure.update_layout(legend={"y": 1.06})
    figure.update_xaxes(range=[0, 112], dtick=25, ticksuffix=" %",
                        title_text="Accès sans démarche préalable (%)")
    figure.update_yaxes(showgrid=False)
    return figure
