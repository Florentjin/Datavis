"""Pure Plotly figures: all inputs are prepared data, never application state.

Encodages volontairement simples, alignés sur le cadre du cours :
position et longueur pour comparer précisément (Séance 2), une couleur par
catégorie, pas de double encodage inutile et densité limitée (Séance 3).
Chaque figure porte un titre sous forme de question dans l'application.
"""

from math import ceil, isfinite

import pandas as pd
import plotly.graph_objects as go

from .theme import (
    COUNTRY_COLORS,
    GAIN_COLOR,
    GRID_COLOR,
    LOSS_COLOR,
    REGION_COLORS,
    REGION_LABELS,
    REGIONS,
    START_DOT_COLOR,
    TEXT_COLOR,
    apply_theme,
)


def _region_keys(frame: pd.DataFrame) -> list[str]:
    present = set(frame["region"].dropna())
    return [region for region in REGIONS if region in present] + sorted(
        present.difference(REGIONS)
    )


def _label(region: str) -> str:
    return REGION_LABELS.get(region, region)


def _color(region: str) -> str:
    return REGION_COLORS.get(region, "#666666")


def _numbers(values) -> list[float | None]:
    """Use ordinary lists and JSON nulls, including with pandas nullable dtypes."""
    return [
        None if pd.isna(value) or not isfinite(float(value)) else float(value)
        for value in values
    ]


def _score_upper(*columns) -> float:
    observed = [
        number
        for column in columns
        for number in _numbers(column)
        if number is not None
    ]
    maximum = max(observed, default=0)
    return float(max(10, ceil(maximum / 10) * 10 + 10))


def _empty(title: str) -> go.Figure:
    figure = apply_theme(go.Figure())
    figure.update_layout(title_text=title, height=300, showlegend=False)
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.add_annotation(
        text="Aucune donnée disponible pour cette sélection.<br>Modifiez la période ou les pays.",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
        font={"size": 14, "color": TEXT_COLOR},
    )
    return figure


def _endpoint_data(frame: pd.DataFrame) -> list[list]:
    return [
        [
            row.code,
            row.country,
            float(row.score_start),
            float(row.score_end),
            float(row.delta),
            _label(row.region),
        ]
        for row in frame.itertuples(index=False)
    ]


def _endpoint_hover(start: int, end: int) -> str:
    return (
        "<b>%{customdata[1]}</b><br>%{customdata[5]}"
        f"<br>Score {start} : %{{customdata[2]:.0f}}"
        f"<br>Score {end} : %{{customdata[3]:.0f}}"
        "<br>Variation : %{customdata[4]:+.0f} destinations"
        "<extra></extra>"
    )


def _label_shifts(
    values: list[float], top: float, inner: float, low: float, high: float,
    min_gap: float = 17.0,
) -> list[int]:
    """Décalages verticaux en pixels pour écarter des étiquettes proches.

    L'ancre reste la vraie valeur ; seul le texte bouge, de façon symétrique
    autour des positions d'origine pour limiter la dérive.
    """
    if not values or high == low:
        return [0] * len(values)
    pixels = [top + (1 - (value - low) / (high - low)) * inner for value in values]
    order = sorted(range(len(pixels)), key=lambda index: pixels[index])
    spread = [pixels[index] for index in order]
    for index in range(1, len(spread)):
        if spread[index] - spread[index - 1] < min_gap:
            spread[index] = spread[index - 1] + min_gap
    drift = sum(spread) / len(spread) - sum(pixels) / len(pixels)
    shifts = [0] * len(values)
    for index, position in zip(order, spread):
        shifts[index] = int(round(position - drift - pixels[index]))
    return shifts


def regional_medians(panel: pd.DataFrame, start: int, end: int) -> go.Figure:
    """Médiane régionale aux deux dates : deux points reliés par région.

    Lecture par position (attribut le plus précis du cours) : le point gris
    situe la médiane de départ, le point coloré la médiane d'arrivée. Les
    valeurs sont écrites à côté des points pour une lecture sans survol.
    """
    title = f"Quel niveau d'accès par région, de {start} à {end} ?"
    if panel.empty:
        return _empty(title)

    summary = panel.groupby("region", observed=True).agg(
        n=("code", "size"),
        score_start=("score_start", "median"),
        score_end=("score_end", "median"),
    )
    stable = {region: index for index, region in enumerate(_region_keys(panel))}
    summary = (
        summary.assign(_order=summary.index.map(stable))
        .sort_values(["score_end", "_order"], ascending=[False, True], kind="stable")
    )
    labels = {
        region: f"{_label(region)} (n = {int(row.n)})"
        for region, row in summary.iterrows()
    }
    order = [labels[region] for region in summary.index]
    upper = _score_upper(panel["score_start"], panel["score_end"])
    figure = go.Figure()
    for region, row in summary.iterrows():
        values = _numbers([row.score_start, row.score_end])
        delta = float(row.score_end - row.score_start)
        count = int(row.n)
        # Écart absolu et écart relatif affichés ensemble : le plus grand gain
        # en destinations n'est pas forcément le plus grand en pourcentage.
        relative = f" ({delta / values[0] * 100:+.0f} %)" if values[0] else ""
        figure.add_trace(
            go.Scatter(
                x=values,
                y=[labels[region]] * 2,
                ids=[f"{region}-start", f"{region}-end"],
                customdata=[
                    [_label(region), count, values[0], values[1], delta]
                ] * 2,
                mode="lines+markers+text",
                text=[f"{values[0]:.0f}", f"{values[1]:.0f}"],
                textposition="top center",
                textfont={"size": 12, "color": TEXT_COLOR},
                line={"color": GRID_COLOR, "width": 3},
                marker={
                    "color": [START_DOT_COLOR, _color(region)],
                    "size": [9, 12],
                    "line": {"color": "#FFFFFF", "width": 1},
                },
                name=_label(region),
                legendgroup=region,
                showlegend=False,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>%{customdata[1]} passeports"
                    f"<br>Médiane {start} : %{{customdata[2]:.0f}}"
                    f"<br>Médiane {end} : %{{customdata[3]:.0f}}"
                    f"<br>Variation : %{{customdata[4]:+.0f}}{relative}"
                    "<extra></extra>"
                ),
            )
        )

    apply_theme(figure)
    figure.update_layout(
        title_text=(
            f"{title}<br><sup>Point gris : médiane {start} · point coloré : "
            f"médiane {end} · la moitié des pays au-dessus, la moitié en dessous</sup>"
        ),
        height=max(340, 58 * len(summary) + 150),
        margin={"t": 105, "b": 80},
        hovermode="closest",
        showlegend=False,
    )
    figure.update_xaxes(
        title_text="Destinations accessibles (médiane)",
        range=[0, upper],
        dtick=25,
        tickformat=".0f",
    )
    figure.update_yaxes(
        type="category",
        categoryorder="array",
        categoryarray=order,
        autorange="reversed",
        showgrid=False,
        title_text=None,
    )
    return figure


def trajectories(series: pd.DataFrame, metric: str = "score") -> go.Figure:
    """Courbes annuelles : une couleur et une étiquette par passeport suivi.

    Un seul encodage par pays (la couleur), le nom écrit au bout de la
    courbe remplace la légende. Les années sans score interrompent la
    ligne : aucun trou n'est interpolé.
    """
    if metric not in {"score", "rank"}:
        raise ValueError("metric must be 'score' or 'rank'")
    title = "Comment l'accès des passeports suivis a-t-il évolué ?"
    if series.empty:
        return _empty(title)
    values = _numbers(series[metric])
    if all(value is None for value in values):
        return _empty(title)

    figure = go.Figure()
    country_order = (
        series[["code", "country"]]
        .drop_duplicates("code")
        .sort_values(["country", "code"], kind="stable")["code"]
    )
    prepared = []
    for index, code in enumerate(country_order):
        rows = series.loc[series["code"].eq(code)].sort_values("year", kind="stable")
        observed = rows.dropna(subset=[metric])
        if observed.empty:
            continue
        prepared.append((index, code, rows, observed))

    if metric == "score":
        low, high = 0.0, _score_upper(series["score"])
    else:
        observed_values = [value for value in values if value is not None]
        maximum = max(observed_values)
        low = float(max(2, ceil(maximum + max(1, maximum * 0.05))))
        high = 1.0  # axe inversé : le rang 1 reste en haut
    # Écarter les noms d'arrivée trop proches sans déplacer leur ancre.
    geometry = {"top": 100, "inner": 460 - 100 - 80, "low": low, "high": high}
    end_shifts = _label_shifts(
        [float(observed.iloc[-1][metric]) for (_, _, _, observed) in prepared],
        **geometry,
    )
    start_shifts = _label_shifts(
        [float(observed.iloc[0][metric]) for (_, _, _, observed) in prepared],
        **geometry,
    )

    for (index, code, rows, observed), end_shift, start_shift in zip(
        prepared, end_shifts, start_shifts
    ):
        country = str(rows["country"].iloc[0])
        region = str(rows["region"].iloc[0])
        color = COUNTRY_COLORS[index % len(COUNTRY_COLORS)]
        metric_label = (
            "Score : %{y:.0f} destinations" if metric == "score" else "Rang : %{y:.0f}"
        )
        figure.add_trace(
            go.Scatter(
                x=[int(year) for year in rows["year"]],
                y=_numbers(rows[metric]),
                ids=[f"{code}-{int(year)}" for year in rows["year"]],
                customdata=[[country, _label(region), code] for _ in range(len(rows))],
                name=country,
                legendgroup=code,
                mode="lines+markers",
                connectgaps=False,
                line={"color": color, "width": 2.6},
                marker={"color": color, "size": 7},
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>%{customdata[1]}"
                    "<br>Année : %{x:.0f}<br>" + metric_label + "<extra></extra>"
                ),
            )
        )
        last = observed.iloc[-1]
        label_text = country if metric == "score" else f"{country} · {int(last[metric])}"
        figure.add_annotation(
            x=int(last["year"]),
            y=float(last[metric]),
            text=label_text,
            showarrow=False,
            xanchor="left",
            xshift=10,
            yshift=end_shift,
            font={"size": 12.5, "color": color},
            bgcolor="rgba(255,255,255,0.85)",
        )
        if metric == "rank":
            # Style bump chart : le rang de départ est écrit à gauche de la ligne.
            first = observed.iloc[0]
            figure.add_annotation(
                x=int(first["year"]),
                y=float(first[metric]),
                text=f"{int(first[metric])}",
                showarrow=False,
                xanchor="right",
                xshift=-10,
                yshift=start_shift,
                font={"size": 11.5, "color": color},
                bgcolor="rgba(255,255,255,0.85)",
            )

    apply_theme(figure)
    first, last_year = int(series["year"].min()), int(series["year"].max())
    # Rendre le manque visible (Séance 4) : une bande grise couvre chaque
    # année sans aucune observation exploitable pour la mesure choisie.
    missing_years = [
        int(year)
        for year in sorted(series["year"].unique())
        if series.loc[series["year"].eq(year), metric].isna().all()
    ]
    for year in missing_years:
        figure.add_vrect(
            x0=year - 0.45,
            x1=year + 0.45,
            fillcolor="#EBEFF5",
            opacity=0.7,
            layer="below",
            line_width=0,
        )
        figure.add_annotation(
            x=year,
            y=0.5,
            yref="paper",
            text=(
                "aucun score<br>exploitable" if metric == "score"
                else "aucun rang<br>exploitable"
            ),
            showarrow=False,
            textangle=90,
            font={"size": 10.5, "color": "#6B7A90"},
        )
    figure.update_layout(
        title_text=f"{title} — {first}–{last_year}",
        height=460,
        margin={"t": 100, "r": 150},
        hovermode="closest",
        showlegend=False,
    )
    figure.update_xaxes(
        title_text="Année",
        type="linear",
        range=[first - 0.3, last_year + 0.3],
        tickmode="linear",
        tick0=first,
        dtick=max(1, ceil((last_year - first) / 12)),
        tickformat=".0f",
        showgrid=True,
    )
    if metric == "score":
        figure.update_yaxes(
            title_text="Destinations accessibles",
            range=[low, high],
            rangemode="tozero",
            tickformat=".0f",
        )
    else:
        figure.update_yaxes(
            title_text="Rang mondial (1 = meilleur)",
            range=[low, high],
            autorange=False,
            tickmode="linear",
            tick0=1,
            dtick=max(1, ceil((low - 1) / 10)),
            tickformat=".0f",
            rangemode="normal",
        )
    return figure


def country_slopes(
    panel: pd.DataFrame, start: int, end: int, focus: list[str]
) -> go.Figure:
    """Diagramme de pente : score de départ à gauche, score d'arrivée à droite.

    Une ligne par passeport suivi, même couleur que dans les trajectoires.
    Monter signifie un gain de destinations, descendre une perte.
    """
    title = f"D'où partent les pays suivis et où arrivent-ils ({start} → {end}) ?"
    rows = panel.loc[panel["code"].isin(set(focus))] if not panel.empty else panel
    if rows.empty:
        return _empty(title)
    rows = rows.sort_values(["country", "code"], kind="stable")
    upper = _score_upper(rows["score_start"], rows["score_end"])
    # Deux arrivées très proches (Émirats 184, États-Unis 182) feraient se
    # chevaucher les noms : les étiquettes d'extrémité sont écartées, l'ancre
    # reste sur la vraie valeur (densité limitée, Séance 3 p. 33-35).
    geometry = {"top": 100, "inner": 520 - 100 - 80, "low": 0.0, "high": upper}
    start_shifts = _label_shifts([float(value) for value in rows["score_start"]], **geometry)
    end_shifts = _label_shifts([float(value) for value in rows["score_end"]], **geometry)

    figure = go.Figure()
    for index, (row, start_shift, end_shift) in enumerate(
        zip(rows.itertuples(index=False), start_shifts, end_shifts)
    ):
        color = COUNTRY_COLORS[index % len(COUNTRY_COLORS)]
        delta = int(row.delta)
        endpoint = [
            row.code,
            row.country,
            float(row.score_start),
            float(row.score_end),
            float(row.delta),
            _label(row.region),
        ]
        figure.add_trace(
            go.Scatter(
                x=[0, 1],
                y=_numbers([row.score_start, row.score_end]),
                ids=[f"{row.code}-start", f"{row.code}-end"],
                customdata=[endpoint] * 2,
                mode="lines+markers",
                line={"color": color, "width": 2.8},
                marker={"color": color, "size": 9},
                name=str(row.country),
                showlegend=False,
                hovertemplate=_endpoint_hover(start, end),
            )
        )
        figure.add_annotation(
            x=0,
            y=float(row.score_start),
            text=f"{int(row.score_start)}",
            showarrow=False,
            xanchor="right",
            xshift=-10,
            yshift=start_shift,
            font={"size": 12.5, "color": TEXT_COLOR},
        )
        figure.add_annotation(
            x=1,
            y=float(row.score_end),
            text=f"{row.country} · {int(row.score_end)}",
            showarrow=False,
            xanchor="left",
            xshift=10,
            yshift=end_shift,
            font={"size": 12.5, "color": color},
        )
        # Variation absolue puis relative (Séance 4) : +30 destinations et +100 %
        # ne disent pas la même chose, les deux sont donc écrites.
        relative = (
            f" · {delta / row.score_start * 100:+.0f} %" if row.score_start else ""
        )
        figure.add_annotation(
            x=0.5,
            xref="paper",
            y=float((row.score_start + row.score_end) / 2),
            text=f"{delta:+d}{relative}",
            showarrow=False,
            font={"size": 12, "color": GAIN_COLOR if delta >= 0 else LOSS_COLOR},
            bgcolor="rgba(255,255,255,0.85)",
        )

    apply_theme(figure)
    figure.update_layout(
        title_text=(
            f"{title}<br><sup>Au milieu de chaque ligne : variation en destinations, "
            "puis en pourcentage du score de départ</sup>"
        ),
        height=520,
        margin={"l": 65, "r": 200, "t": 100},
        hovermode="closest",
    )
    figure.update_xaxes(
        tickmode="array",
        tickvals=[0, 1],
        ticktext=[str(start), str(end)],
        range=[-0.30, 1.30],
        showgrid=False,
    )
    figure.update_yaxes(
        title_text="Destinations accessibles",
        range=[0, upper],
        dtick=25,
        tickformat=".0f",
    )
    return figure


def _change_title(deltas: list[float]) -> str:
    low, high = min(deltas), max(deltas)
    if low == high == 0:
        return "Scores inchangés"
    if high < 0:
        return "Reculs les plus marqués et les plus limités"
    if high == 0:
        return "Reculs et scores inchangés"
    return "Gains les plus forts et variations les plus faibles"


def changes(extreme_panel: pd.DataFrame, start: int, end: int) -> go.Figure:
    """Barres horizontales autour de zéro : bleu = gain, orange = recul.

    Une seule vue triée par variation, valeurs écrites au bout des barres,
    ligne de zéro explicite (les barres partent de zéro).
    """
    if extreme_panel.empty:
        return _empty(f"Qui a le plus gagné, qui a le plus perdu ({start} → {end}) ?")

    ordered = extreme_panel.sort_values(
        ["delta", "country", "code"], ascending=[False, True, True], kind="stable"
    )
    deltas = [float(value) for value in ordered["delta"]]
    low = min(0.0, min(deltas))
    high = max(0.0, max(deltas))
    span = max(high - low, 1.0)
    limit_low = low - ceil(span * 0.18)
    limit_high = high + ceil(span * 0.18)
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=deltas,
            y=ordered["country"].tolist(),
            ids=ordered["code"].tolist(),
            customdata=_endpoint_data(ordered),
            base=0,
            orientation="h",
            width=0.62,
            marker={
                "color": [GAIN_COLOR if value > 0 else LOSS_COLOR for value in deltas]
            },
            name="Variation",
            showlegend=False,
            text=[f"+{value:g}" if value > 0 else f"{value:g}" for value in deltas],
            textposition="outside",
            textfont={"size": 13, "color": TEXT_COLOR},
            cliponaxis=False,
            hovertemplate=_endpoint_hover(start, end),
        )
    )
    apply_theme(figure)
    figure.update_layout(
        title_text=f"{_change_title(deltas)} — {start} → {end}",
        height=max(360, 38 * len(ordered) + 140),
        margin={"t": 100, "b": 80},
        hovermode="closest",
    )
    figure.update_xaxes(
        title_text=f"Variation du nombre de destinations, {start} → {end}",
        range=[limit_low, limit_high],
        zeroline=True,
        zerolinecolor=TEXT_COLOR,
        zerolinewidth=1.5,
        dtick=max(1, ceil(span / 5)),
        tickformat=".0f",
    )
    figure.update_yaxes(
        type="category",
        categoryorder="array",
        categoryarray=ordered["country"].tolist(),
        autorange="reversed",
        showgrid=False,
        ticks="",
        title_text=None,
    )
    return figure
