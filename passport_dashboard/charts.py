"""Huit graphiques lisibles en projection : valeurs écrites, aucune info au survol.

Règles communes (cours Visualisation de données, séances 2 à 4) :
- une seule couleur d'accent pour ce que dit le titre, du gris pour le contexte ;
- pas de double encodage inutile, peu de grilles, valeurs écrites directement ;
- texte à 16 px minimum, hauteur unique pour tenir dans un écran 1920×1080.
"""

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
    CONTEXT_COLOR,
    HIGHLIGHT_COLOR,
    LABEL_SIZE,
    MIN_TEXT_SIZE,
    MUTED_COLOR,
    NOTE_SIZE,
    RECIPROCITY_COLORS,
    RECIPROCITY_LABELS,
    REGIME_COLORS,
    REGIME_LABELS,
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

# Sept exemples au plus : la mémoire de travail retient 5 à 9 éléments (séance 2).
DEFAULT_SCATTER_LABELS = ("SG", "US", "FR", "IN", "AF", "RW", "SC")
_DARK_TEXT = {"electronic_travel_authorisation", "visa_online", "favourable", "mutual_closed"}
_OPAQUE = "rgba(255,255,255,0.92)"


def _note(text: str, **kwargs) -> dict:
    base = {"showarrow": False, "font": {"size": NOTE_SIZE, "color": MUTED_COLOR}}
    base.update(kwargs)
    return {"text": text, **base}


def _row_label(code: str, detail: str = "") -> str:
    name = "<b>Monde</b>" if code == WORLD else REGION_LABELS[code]
    if detail:
        name += f"<br><span style='font-size:{MIN_TEXT_SIZE}px;color:{MUTED_COLOR}'>{detail}</span>"
    return name


# Q1 ---------------------------------------------------------------------------
def _extreme_label(group: pd.DataFrame, row: pd.Series) -> str:
    """Nomme un extrême et signale honnêtement les ex æquo."""
    ties = int(group["score"].eq(row["score"]).sum()) - 1
    suffix = f" (+{ties})" if ties else ""
    return f"{row['country']}{suffix} <b>{fr(row['score'])}</b>"


def regional_distribution(scores: pd.DataFrame, year: int) -> go.Figure:
    """Un point par passeport, une ligne par région, médiane et extrêmes nommés.

    La position verticale porte déjà la région : une seule teinte suffit
    (pas de double encodage), la médiane est l'élément mis en avant.
    """
    medians = scores.groupby("region")["score"].median().sort_values()
    figure = go.Figure()
    annotations = []
    for position, code in enumerate(medians.index):
        group = scores.loc[scores["region"].eq(code)].sort_values(["score", "code"])
        offsets = [((index % 5) - 2) * 0.06 for index in range(len(group))]
        figure.add_trace(go.Scatter(
            x=group["score"], y=[position + offset for offset in offsets], mode="markers",
            marker={"size": 15, "color": "#6B9BC8", "opacity": 0.55, "line": {"width": 1, "color": "white"}},
            showlegend=False,
        ))
        figure.add_trace(go.Scatter(
            x=[medians[code]], y=[position], mode="markers", showlegend=False,
            marker={"symbol": "line-ns", "size": 46, "line": {"width": 7, "color": TEXT_COLOR}},
        ))
        low, high = group.iloc[0], group.iloc[-1]
        for row, anchor in ((low, "left"), (high, "right")):
            annotations.append(_note(
                _extreme_label(group, row), x=row["score"], y=position, yshift=30, xanchor=anchor,
                font={"size": NOTE_SIZE, "color": TEXT_COLOR}, bgcolor=_OPAQUE,
            ))
    world = scores["score"].median()
    figure.add_vline(x=world, line={"dash": "dot", "color": MUTED_COLOR, "width": 2}, layer="below")
    annotations.append(_note(
        f"Médiane mondiale : {fr(world)}", x=world, y=1.0, yref="paper", yanchor="bottom", xanchor="center",
        font={"size": NOTE_SIZE, "color": MUTED_COLOR},
    ))
    ticks = [
        _row_label(code, f"médiane <b>{fr(medians[code], 1 if medians[code] % 1 else 0)}</b> · "
                         f"{int((scores['region'] == code).sum())} pays")
        for code in medians.index
    ]
    figure.update_layout(
        title_text=title_text(
            story.q1(scores, year),
            "Chaque point est un passeport · trait noir : médiane de la région · "
            "noms : passeport le plus faible et le plus fort (+n : ex æquo)",
        ),
        annotations=annotations,
    )
    figure.update_yaxes(tickvals=list(range(len(medians))), ticktext=ticks, range=[-0.5, len(medians) - 0.35],
                        showgrid=False, tickfont={"color": TEXT_COLOR})
    figure.update_xaxes(range=[0, 205], dtick=50, showgrid=False,
                        title_text=f"Destinations accessibles sans démarche préalable en {year}")
    return apply_theme(figure, top_extra=26)


# Q2 ---------------------------------------------------------------------------
def inequality_trend(series: pd.DataFrame) -> go.Figure:
    """Barre flottante P10–P90 par année mesurée et ligne de la médiane.

    La barre porte seule l'écart (pas de lignes P10/P90 en double) ; la première
    et la dernière année sont mises en avant, les années absentes sont signalées.
    """
    measured = series.dropna(subset=["gap"])
    first, last = measured.iloc[0], measured.iloc[-1]
    colors = [HIGHLIGHT_COLOR if year in (first["year"], last["year"]) else "#C6DBEF" for year in measured["year"]]
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=measured["year"], y=measured["gap"], base=measured["p10"], width=0.66,
        marker={"color": colors}, showlegend=False,
    ))
    figure.add_trace(go.Scatter(
        x=series["year"], y=series["median"], mode="lines+markers", connectgaps=False,
        line={"color": TEXT_COLOR, "width": 4}, marker={"size": 10, "color": TEXT_COLOR}, showlegend=False,
    ))
    annotations = []
    for row in (first, last):
        annotations.append(_note(
            f"écart <b>{fr(row['gap'])}</b>", x=row["year"], y=row["p90"], yanchor="bottom", yshift=6,
            font={"size": LABEL_SIZE + 3, "color": HIGHLIGHT_COLOR},
        ))
    for column, label, color in (("p90", "P90", HIGHLIGHT_COLOR), ("median", "médiane", TEXT_COLOR),
                                 ("p10", "P10", HIGHLIGHT_COLOR)):
        annotations.append(_note(
            f"{label} <b>{fr(last[column])}</b>", x=last["year"], y=last[column], xanchor="left", xshift=26,
            font={"size": LABEL_SIZE, "color": color},
        ))
        annotations.append(_note(
            f"<b>{fr(first[column])}</b>", x=first["year"], y=first[column], xanchor="right", xshift=-26,
            font={"size": LABEL_SIZE, "color": color},
        ))
    for year in series.loc[series["gap"].isna(), "year"]:
        annotations.append(_note("n.d.", x=year, y=0, yanchor="bottom", yshift=4,
                                 font={"size": NOTE_SIZE, "color": MUTED_COLOR}))
    first_year, last_year = int(series["year"].min()), int(series["year"].max())
    ticks = [year for year in range(first_year, last_year, 3)] + [last_year]
    if len(ticks) > 1 and ticks[-1] - ticks[-2] < 2:
        ticks.pop(-2)
    figure.update_layout(
        title_text=title_text(
            story.q2(series),
            f"Barre : des 10 % les moins dotés (P10, bas) aux 10 % les mieux dotés (P90, haut) · trait noir : médiane · "
            f"{int(series['n'].iloc[0])} passeports mesurés chaque année · n.d. : année non publiée",
        ),
        annotations=annotations, bargap=0.3, margin={"r": 170, "l": 70},
    )
    figure.update_xaxes(tickvals=ticks, range=[first_year - 0.8, last_year + 0.6], showgrid=False)
    figure.update_yaxes(range=[0, 215], dtick=50, title_text="Destinations accessibles")
    return apply_theme(figure)


# Q3 ---------------------------------------------------------------------------
def biggest_changes(selection: pd.DataFrame, changes: pd.DataFrame, start: int, end: int) -> go.Figure:
    """Deux classements alignés sur le même axe : plus fortes et plus faibles évolutions."""
    high = selection.loc[selection["group"].eq("high")].sort_values("delta")
    low = selection.loc[selection["group"].eq("low")].sort_values("delta", ascending=False)
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=(f"<b>Les {len(high)} plus fortes progressions</b>",
                        f"<b>Les {len(low)} plus faibles évolutions</b>"),
    )
    for row, group in ((1, high), (2, low)):
        colors = [
            HIGHLIGHT_COLOR if row == 1 else (ACCENT_COLOR if delta < 0 else "#FDB863")
            for delta in group["delta"]
        ]
        labels = [
            "" if item.delta < 0 else f"<b>{signed(item.delta)}</b>  ({fr(item.score_start)} → {fr(item.score_end)})"
            for item in group.itertuples()
        ]
        names = [f"{item.country} <span style='color:{MUTED_COLOR};font-size:{MIN_TEXT_SIZE}px'>· "
                 f"{REGION_LABELS[item.region]}</span>" for item in group.itertuples()]
        figure.add_trace(go.Bar(
            x=group["delta"], y=names, orientation="h", marker={"color": colors},
            text=labels, textposition="outside", cliponaxis=False, textfont={"size": LABEL_SIZE},
            showlegend=False,
        ), row=row, col=1)
        # Une étiquette à gauche d'une barre négative masquerait le nom du pays.
        for item, name in zip(group.itertuples(), names):
            if item.delta < 0:
                figure.add_annotation(
                    x=0, y=name, xanchor="left", xshift=8, showarrow=False,
                    text=f"<b>{signed(item.delta)}</b>  ({fr(item.score_start)} → {fr(item.score_end)})",
                    font={"size": LABEL_SIZE, "color": ACCENT_COLOR}, row=row, col=1,
                )
    lowest = min(0.0, float(selection["delta"].min()))
    highest = float(selection["delta"].max())
    figure.update_xaxes(range=[lowest - 8, highest * 1.45], showgrid=False, dtick=25)
    figure.update_xaxes(title_text=f"Destinations gagnées ou perdues entre {start} et {end}", row=2, col=1)
    figure.update_yaxes(showgrid=False)
    figure.add_vline(x=0, line={"color": TEXT_COLOR, "width": 2})
    for annotation in figure.layout.annotations[:2]:
        annotation.update(font={"size": LABEL_SIZE + 1, "color": TEXT_COLOR}, x=0, xanchor="left")
    figure.update_layout(
        title_text=title_text(
            story.q3(changes, start, end),
            f"Barre : variation du nombre de destinations · entre parenthèses : score {start} → {end}",
        ),
    )
    figure = apply_theme(figure, top_extra=48)
    figure.update_yaxes(tickfont={"color": TEXT_COLOR})
    return figure


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
            marker={"color": colors[column], "line": {"color": "white", "width": 1.5}},
            text=[pct(value) if value >= 6 else "" for value in values],
            textposition="inside", insidetextanchor="middle",
            textfont={"size": LABEL_SIZE, "color": TEXT_COLOR if column in _DARK_TEXT else "white"},
        ))
    annotations = [
        _note(f"<b>{text}</b>", x=1.01, xref="paper", y=row, xanchor="left",
              font={"size": LABEL_SIZE + 4, "color": color})
        for row, text, color in zip(rows, total_text, total_colors)
    ]
    annotations.append(_note(total_header, x=1.01, xref="paper", y=1.0, yref="paper", xanchor="left",
                             yanchor="bottom", font={"size": MIN_TEXT_SIZE, "color": MUTED_COLOR}))
    figure.update_layout(barmode="stack", bargap=0.25, annotations=annotations,
                         uniformtext={"minsize": MIN_TEXT_SIZE, "mode": "hide"}, margin={"r": 170})
    figure.update_xaxes(range=[0, 100], ticksuffix=" %", dtick=25, showgrid=False)
    figure.update_yaxes(showgrid=False, tickfont={"size": LABEL_SIZE})
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
    return apply_theme(figure, legend=True, top_extra=10)


def reciprocity(shares: pd.DataFrame) -> go.Figure:
    regional = shares.loc[shares["region"] != WORLD].sort_values("balance")
    ordered = pd.concat([shares.loc[shares["region"] == WORLD], regional])
    figure = _stacked(
        shares, list(RECIPROCITY_LABELS), RECIPROCITY_LABELS, RECIPROCITY_COLORS, "balance",
        [f"{signed(round(value))} pts" for value in ordered["balance"]],
        [HIGHLIGHT_COLOR if round(value) > 0 else ACCENT_COLOR if round(value) < 0 else MUTED_COLOR
         for value in ordered["balance"]],
        "Solde : faveur<br>− défaveur",
    )
    figure.update_layout(title_text=title_text(
        story.q5(shares),
        "Pour chaque pays et chaque partenaire : mon passeport entre-t-il librement chez lui, et le sien chez moi ?",
    ))
    figure.update_xaxes(title_text="Part des relations bilatérales du pays (%)")
    return apply_theme(figure, legend=True, top_extra=10)


# Q6 ---------------------------------------------------------------------------
def hospitality_vs_power(frame: pd.DataFrame, labels: Sequence[str] = DEFAULT_SCATTER_LABELS) -> go.Figure:
    """Nuage gris (contexte) et pays commentés en couleur d'accent.

    Sept teintes régionales n'aident pas à lire une corrélation : on les retire
    et on ne colore que les pays dont on parle à l'oral.
    """
    named = frame.loc[frame["code"].isin(labels)]
    others = frame.loc[~frame["code"].isin(labels)]
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=others["welcomed"], y=others["score"], mode="markers", showlegend=False,
        marker={"size": 14, "color": CONTEXT_COLOR, "opacity": 0.75, "line": {"width": 1, "color": "white"}},
    ))
    figure.add_trace(go.Scatter(
        x=named["welcomed"], y=named["score"], mode="markers", showlegend=False,
        marker={"size": 18, "color": HIGHLIGHT_COLOR, "line": {"width": 2, "color": "white"}},
    ))
    mx, my = frame["welcomed"].median(), frame["score"].median()
    median_line = {"dash": "dot", "color": MUTED_COLOR, "width": 2}
    figure.add_vline(x=mx, line=median_line, layer="below")
    figure.add_hline(y=my, line=median_line, layer="below")
    corner = {"size": NOTE_SIZE + 1, "color": MUTED_COLOR}
    annotations = [
        _note("<i>Accueille peu, voyage beaucoup</i>", x=0, y=212, xanchor="left", yanchor="top", font=corner),
        _note("<i>Accueille et voyage</i>", x=200, y=212, xanchor="right", yanchor="top", font=corner),
        _note("<i>Accueille peu, voyage peu</i>", x=0, y=2, xanchor="left", yanchor="bottom", font=corner),
        _note("<i>Accueille beaucoup, voyage peu</i>", x=200, y=2, xanchor="right", yanchor="bottom", font=corner),
        _note(f"médiane {fr(mx)}", x=mx, y=1.0, yref="paper", yanchor="bottom", font={"size": MIN_TEXT_SIZE}),
        _note(f"médiane {fr(my)}", x=1.0, xref="paper", y=my, xanchor="left", font={"size": MIN_TEXT_SIZE}),
    ]
    for point in named.itertuples():
        dx = -50 if point.welcomed > mx else 50
        dy = 40 if point.score < my else -40
        if point.score < 40:
            dx, dy = 70, -10
        annotations.append({
            "x": point.welcomed, "y": point.score, "text": f"<b>{point.country}</b>",
            "showarrow": True, "arrowhead": 0, "arrowwidth": 2, "arrowcolor": HIGHLIGHT_COLOR,
            "ax": dx, "ay": dy, "font": {"size": LABEL_SIZE, "color": TEXT_COLOR}, "bgcolor": _OPAQUE,
        })
    figure.update_layout(
        title_text=title_text(
            story.q6(frame),
            "Chaque point est un pays · horizontal : passeports étrangers qu'il accueille sans démarche · "
            "vertical : destinations ouvertes à son passeport · pointillés : médianes",
        ),
        annotations=annotations, margin={"r": 120},
    )
    figure = apply_theme(figure, top_extra=26)
    figure.update_xaxes(range=[-4, 204], dtick=50, showgrid=False,
                        title_text="Passeports étrangers accueillis sans démarche préalable (sur 198)")
    figure.update_yaxes(range=[0, 214], dtick=50, showgrid=False,
                        title_text="Destinations ouvertes à son passeport")
    return figure


# Q7 ---------------------------------------------------------------------------
def regional_openness(matrix: pd.DataFrame) -> go.Figure:
    order = matrix.mean(axis=1).sort_values(ascending=False).index.tolist()
    data = matrix.loc[order, order]
    n = len(order)
    figure = go.Figure(go.Heatmap(
        z=data.to_numpy(), x=list(range(n)), y=list(range(n)), zmin=0, zmax=100,
        colorscale=[[0, "#F7FBFF"], [0.5, "#6BAED6"], [1, "#08306B"]], showscale=False, xgap=4, ygap=4,
    ))
    annotations = []
    for row, origin in enumerate(order):
        for column, destination in enumerate(order):
            value = data.loc[origin, destination]
            annotations.append(_note(
                f"<b>{pct(value)}</b>" if origin == destination else pct(value), x=column, y=row,
                font={"size": LABEL_SIZE + 3, "color": "white" if value >= 55 else TEXT_COLOR},
            ))
    shapes = [
        {"type": "rect", "x0": index - 0.5, "x1": index + 0.5, "y0": index - 0.5, "y1": index + 0.5,
         "line": {"color": TEXT_COLOR, "width": 4}}
        for index in range(n)
    ]
    origin, destination = data.stack().idxmin()
    row, column = order.index(origin), order.index(destination)
    shapes.append({"type": "rect", "x0": column - 0.5, "x1": column + 0.5, "y0": row - 0.5, "y1": row + 0.5,
                   "line": {"color": ACCENT_COLOR, "width": 6}})
    labels = [REGION_LABELS[code] for code in order]
    figure.update_layout(
        title_text=title_text(
            story.q7(matrix),
            "Case : % des couples passeport → pays où l'entrée se fait sans démarche préalable · "
            "cadre noir : sa propre région · cadre orange : minimum",
        ),
        annotations=annotations, shapes=shapes,
    )
    figure = apply_theme(figure, top_extra=70)
    figure.update_xaxes(tickvals=list(range(n)), ticktext=labels, side="top", showgrid=False,
                        title_text="Région visitée ➜", title_standoff=6, tickfont={"color": TEXT_COLOR})
    figure.update_yaxes(tickvals=list(range(n)), ticktext=labels, autorange="reversed", showgrid=False,
                        title_text="Région du passeport", tickfont={"color": TEXT_COLOR})
    return figure


# Q8 ---------------------------------------------------------------------------
def clubs(table: pd.DataFrame, world_rate: float) -> go.Figure:
    data = table.sort_values("gap")
    names = [f"<b>{row.club}</b><br><span style='font-size:{MIN_TEXT_SIZE}px;color:{MUTED_COLOR}'>"
             f"{row.members} membres</span>" for row in data.itertuples()]
    figure = go.Figure()
    for name, row in zip(names, data.itertuples()):
        figure.add_trace(go.Scatter(
            x=[row.outside, row.inside], y=[name, name], mode="lines",
            line={"color": "#D0D5DD", "width": 8}, showlegend=False,
        ))
    for column, label, color in (("outside", "Vers les pays non membres", ACCENT_COLOR),
                                 ("inside", "Entre membres", HIGHLIGHT_COLOR)):
        larger = data[column] >= data["outside" if column == "inside" else "inside"]
        figure.add_trace(go.Scatter(
            x=data[column], y=names, mode="markers+text", name=label,
            marker={"size": 24, "color": color, "line": {"width": 2, "color": "white"}},
            text=[f"<b>{pct(value)}</b>" for value in data[column]],
            textposition=["middle right" if flag else "middle left" for flag in larger],
            textfont={"size": LABEL_SIZE, "color": color},
        ))
    figure.add_vline(x=world_rate, line={"dash": "dot", "color": MUTED_COLOR, "width": 2}, layer="below")
    annotations = [
        _note(f"Moyenne mondiale : {pct(world_rate)}", x=world_rate, y=1.0, yref="paper",
              yanchor="bottom", xanchor="center", font={"size": MIN_TEXT_SIZE, "color": MUTED_COLOR}),
        _note("Écart", x=1.01, xref="paper", y=1.0, yref="paper", xanchor="left", yanchor="bottom",
              font={"size": MIN_TEXT_SIZE, "color": MUTED_COLOR}),
    ]
    annotations += [
        _note(f"<b>{signed(row.gap)} pts</b>", x=1.01, xref="paper", y=name, xanchor="left",
              font={"size": LABEL_SIZE + 3, "color": TEXT_COLOR})
        for name, row in zip(names, data.itertuples())
    ]
    figure.update_layout(
        title_text=title_text(
            story.q8(table),
            "Part des relations où le passeport d'un membre entre sans démarche préalable · membres 2025 des organisations",
        ),
        annotations=annotations, margin={"r": 140},
    )
    figure = apply_theme(figure, legend=True, top_extra=30)
    figure.update_layout(legend={"y": 1.08})
    figure.update_xaxes(range=[0, 112], dtick=25, ticksuffix=" %", showgrid=False,
                        title_text="Accès sans démarche préalable (%)")
    figure.update_yaxes(showgrid=False, tickfont={"color": TEXT_COLOR})
    return figure
