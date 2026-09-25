"""Pure Plotly figures: all inputs are prepared data, never application state."""

from collections import defaultdict
from math import ceil, isfinite

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .theme import GRID_COLOR, REGION_COLORS, REGION_LABELS, REGIONS, TEXT_COLOR, apply_theme


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


def regional_distribution(
    panel: pd.DataFrame,
    start: int,
    end: int,
    focus: list[str],
    stacked: bool = False,
) -> go.Figure:
    """Compare a common cohort; ``stacked`` gives both dates full-width panels."""
    title = f"Distribution des scores par région — {start} et {end}"
    if panel.empty:
        return _empty(title)

    medians = panel.groupby("region", observed=True)["score_end"].median()
    stable_order = {region: index for index, region in enumerate(_region_keys(panel))}
    regions = sorted(medians.index, key=lambda region: (-medians[region], stable_order[region]))
    counts = panel.groupby("region", observed=True).size()
    labels = {region: f"{_label(region)} (n = {counts[region]})" for region in regions}
    order = [labels[region] for region in regions]
    upper = _score_upper(panel["score_start"], panel["score_end"])
    selected = set(focus)
    figure = make_subplots(
        rows=2 if stacked else 1,
        cols=1 if stacked else 2,
        shared_xaxes=stacked,
        shared_yaxes=not stacked,
        horizontal_spacing=0.075,
        vertical_spacing=0.18,
        subplot_titles=(str(start), str(end)),
    )
    for endpoint, score_column in enumerate(("score_start", "score_end"), start=1):
        subplot_row, subplot_column = (endpoint, 1) if stacked else (1, endpoint)
        for region in regions:
            rows = panel.loc[panel["region"].eq(region)]
            color = _color(region)
            red, green, blue = (int(color[index:index + 2], 16) for index in (1, 3, 5))
            figure.add_trace(
                go.Box(
                    x=_numbers(rows[score_column]),
                    y=[labels[region]] * len(rows),
                    ids=rows["code"].tolist(),
                    orientation="h",
                    quartilemethod="linear",
                    boxpoints="outliers",
                    whiskerwidth=0.5,
                    width=0.52,
                    line={"color": color, "width": 2},
                    fillcolor=f"rgba({red}, {green}, {blue}, 0.18)",
                    opacity=1,
                    marker={"color": color, "size": 4},
                    name=_label(region),
                    legendgroup=region,
                    showlegend=endpoint == 1,
                    hoverinfo="x+y",
                ),
                row=subplot_row,
                col=subplot_column,
            )
            highlighted = rows.loc[rows["code"].isin(selected)]
            if not highlighted.empty:
                figure.add_trace(
                    go.Scatter(
                        x=_numbers(highlighted[score_column]),
                        y=[labels[region]] * len(highlighted),
                        ids=highlighted["code"].tolist(),
                        customdata=_endpoint_data(highlighted),
                        mode="markers",
                        marker={
                            "symbol": "diamond",
                            "size": 11,
                            "color": color,
                            "line": {"color": TEXT_COLOR, "width": 1.8},
                        },
                        name="Pays sélectionnés",
                        legendgroup=f"focus-{region}",
                        showlegend=False,
                        hovertemplate=_endpoint_hover(start, end),
                    ),
                    row=subplot_row,
                    col=subplot_column,
                )

    apply_theme(figure)
    subtitle = "Même cohorte aux deux dates"
    if panel["code"].isin(selected).any():
        subtitle += ("<br>" if stacked else " · ") + "Diamants : pays sélectionnés"
    if stacked:
        title = "Distribution des scores par région"
    figure.update_layout(
        title_text=f"{title}<br><sup>{subtitle}</sup>",
        height=max(650, 88 * len(regions) + 280) if stacked else max(380, 55 * len(regions) + 190),
        margin={"t": 145 if stacked else 115, "b": 110 if stacked else 95},
        boxmode="overlay",
        hovermode="closest",
        showlegend=False,
    )
    if stacked:
        figure.update_layout(legend_y=-0.10)
    figure.update_xaxes(
        title_text="Score (destinations)",
        range=[0, upper],
        dtick=50,
        tickangle=0,
        tickformat=".0f",
        showticklabels=True,
    )
    figure.update_yaxes(
        type="category",
        categoryorder="array",
        categoryarray=order,
        autorange="reversed",
        showgrid=False,
        title_text=None,
    )
    if stacked:
        figure.update_yaxes(showticklabels=True)
    return figure


def trajectories(series: pd.DataFrame, metric: str = "score") -> go.Figure:
    """Plot annual observations; the application limits the selection to four countries."""
    if metric not in {"score", "rank"}:
        raise ValueError("metric must be 'score' or 'rank'")
    title = "Trajectoires des scores" if metric == "score" else "Trajectoires des rangs"
    if series.empty:
        return _empty(title)
    values = _numbers(series[metric])
    if all(value is None for value in values):
        return _empty(title)

    figure = go.Figure()
    dashes = ("solid", "dash", "dot", "dashdot")
    symbols = ("circle", "diamond", "square", "triangle-up")
    region_indices = defaultdict(int)
    country_order = (
        series[["code", "country"]]
        .drop_duplicates("code")
        .sort_values(["country", "code"], kind="stable")["code"]
    )
    for code in country_order:
        rows = series.loc[series["code"].eq(code)].sort_values("year", kind="stable")
        country = rows["country"].iloc[0]
        region = rows["region"].iloc[0]
        style = region_indices[region] % len(dashes)
        region_indices[region] += 1
        metric_label = "Score : %{y:.0f} destinations" if metric == "score" else "Rang : %{y:.0f}"
        figure.add_trace(
            go.Scatter(
                x=[int(year) for year in rows["year"]],
                y=_numbers(rows[metric]),
                ids=[f"{code}-{int(year)}" for year in rows["year"]],
                customdata=[
                    [country, _label(region), code] for _ in range(len(rows))
                ],
                name=country,
                legendgroup=code,
                mode="lines+markers",
                connectgaps=False,
                line={"color": _color(region), "width": 2.4, "dash": dashes[style]},
                marker={
                    "color": _color(region),
                    "size": 7,
                    "symbol": symbols[style],
                    "line": {"color": "#FFFFFF", "width": 0.8},
                },
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>%{customdata[1]}"
                    "<br>Année : %{x:.0f}<br>" + metric_label + "<extra></extra>"
                ),
            )
        )

    apply_theme(figure)
    first, last = int(series["year"].min()), int(series["year"].max())
    figure.update_layout(
        title_text=f"{title} — {first}–{last}",
        height=460,
        hovermode="closest",
    )
    figure.update_xaxes(
        title_text="Année",
        type="linear",
        range=[first - 0.3, last + 0.3],
        tickmode="linear",
        tick0=first,
        dtick=max(1, ceil((last - first) / 12)),
        tickformat=".0f",
        showgrid=True,
    )
    if metric == "score":
        figure.update_yaxes(
            title_text="Score (destinations)",
            range=[0, _score_upper(series["score"])],
            rangemode="tozero",
            tickformat=".0f",
        )
    else:
        maximum = max(value for value in values if value is not None)
        upper = max(2, ceil(maximum + max(1, maximum * 0.05)))
        figure.update_yaxes(
            title_text="Rang (1 = meilleur)",
            range=[upper, 1],
            autorange=False,
            tickmode="linear",
            tick0=1,
            dtick=max(1, ceil((upper - 1) / 10)),
            tickformat=".0f",
            rangemode="normal",
        )
    return figure


def positions(
    panel: pd.DataFrame, start: int, end: int, focus: list[str]
) -> go.Figure:
    """Compare endpoint scores with identical units, bounds and physical axis scale."""
    title = f"Position des passeports — {start} → {end}"
    if panel.empty:
        return _empty(title)

    figure = go.Figure()
    selected = set(focus)
    upper = _score_upper(panel["score_start"], panel["score_end"])
    for region in _region_keys(panel):
        rows = panel.loc[panel["region"].eq(region)]
        highlighted = rows["code"].isin(selected).tolist()
        figure.add_trace(
            go.Scatter(
                x=_numbers(rows["score_start"]),
                y=_numbers(rows["score_end"]),
                ids=rows["code"].tolist(),
                customdata=_endpoint_data(rows),
                mode="markers",
                marker={
                    "size": 10,
                    "color": _color(region),
                    "opacity": 0.85,
                    "line": {
                        "color": [TEXT_COLOR if flag else "#FFFFFF" for flag in highlighted],
                        "width": [2.2 if flag else 0.7 for flag in highlighted],
                    },
                },
                name=_label(region),
                legendgroup=region,
                hovertemplate=_endpoint_hover(start, end),
            )
        )

    labels = panel.loc[panel["code"].isin(selected)]
    if not labels.empty:
        figure.add_trace(
            go.Scatter(
                x=_numbers(labels["score_start"]),
                y=_numbers(labels["score_end"]),
                ids=labels["code"].tolist(),
                mode="text",
                text=labels["country"].tolist(),
                textposition=[
                    ("bottom" if row.score_end >= upper * 0.7 else "top")
                    + (" left" if row.score_start > upper * 0.75 else " right")
                    for row in labels.itertuples(index=False)
                ],
                textfont={
                    "size": 12,
                    "color": TEXT_COLOR,
                    "shadow": "0 0 3px #FFFFFF, 0 0 3px #FFFFFF",
                },
                cliponaxis=False,
                name="Pays sélectionnés",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    apply_theme(figure)
    figure.update_layout(title_text=title, height=620, hovermode="closest")
    figure.update_xaxes(
        title_text=f"Score {start} (destinations)",
        range=[0, upper],
        constrain="domain",
        dtick=20 if upper > 100 else 10,
        tickformat=".0f",
    )
    figure.update_yaxes(
        title_text=f"Score {end} (destinations)",
        range=[0, upper],
        scaleanchor="x",
        scaleratio=1,
        constrain="domain",
        dtick=20 if upper > 100 else 10,
        tickformat=".0f",
    )
    figure.add_shape(
        type="line",
        x0=0,
        y0=0,
        x1=upper,
        y1=upper,
        xref="x",
        yref="y",
        layer="below",
        line={"color": "#8491A5", "width": 1.3, "dash": "dot"},
    )
    figure.add_annotation(
        x=upper * 0.72,
        y=upper * 0.72,
        xref="x",
        yref="y",
        text="Score inchangé (y = x)",
        textangle=-45,
        yshift=13,
        showarrow=False,
        font={"size": 12, "color": TEXT_COLOR},
        bgcolor="rgba(255,255,255,0.88)",
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
    return "Variations les plus faibles et les plus fortes"


def changes(extreme_panel: pd.DataFrame, start: int, end: int) -> go.Figure:
    """Show the supplied, non-overlapping extremes as signed bars based at zero."""
    if extreme_panel.empty:
        return _empty(f"Variations des scores — {start} → {end}")

    groups = ("Faibles variations", "Fortes variations")
    present = set(extreme_panel["group"])
    group_order = [group for group in groups if group in present] + sorted(
        present.difference(groups)
    )
    ordered_parts = []
    headings = []
    separators = []
    cursor = 0
    for group in group_order:
        rows = extreme_panel.loc[extreme_panel["group"].eq(group)].sort_values(
            ["delta", "country", "code"], kind="stable"
        ).copy()
        headings.append((cursor, group))
        rows["_position"] = list(range(cursor + 1, cursor + len(rows) + 1))
        ordered_parts.append(rows)
        cursor += len(rows) + 2
        separators.append(cursor - 0.5)
    ordered = pd.concat(ordered_parts, ignore_index=True)
    deltas = [float(value) for value in ordered["delta"]]
    maximum = max(abs(value) for value in deltas)
    limit = max(1, ceil(maximum * 1.3))
    figure = go.Figure()
    for region in _region_keys(ordered):
        rows = ordered.loc[ordered["region"].eq(region)]
        figure.add_trace(
            go.Bar(
                x=_numbers(rows["delta"]),
                y=rows["_position"].tolist(),
                ids=rows["code"].tolist(),
                customdata=_endpoint_data(rows),
                base=0,
                orientation="h",
                width=0.66,
                marker={"color": _color(region)},
                name=_label(region),
                legendgroup=region,
                text=[f"+{value:g}" if value > 0 else f"{value:g}" for value in rows["delta"]],
                textposition="outside",
                textfont={"size": 13, "color": TEXT_COLOR},
                cliponaxis=False,
                hovertemplate=_endpoint_hover(start, end),
            )
        )
    apply_theme(figure)
    figure.update_layout(
        title_text=f"{_change_title(deltas)} — {start} → {end}",
        height=max(370, len(ordered) * 35 + len(group_order) * 45 + 150),
        barmode="overlay",
        hovermode="closest",
    )
    figure.update_xaxes(
        title_text=f"Variation du score entre {start} et {end} (destinations)",
        range=[-limit, limit],
        zeroline=True,
        zerolinecolor=TEXT_COLOR,
        zerolinewidth=1.5,
        dtick=max(1, ceil(limit / 4)),
        tickformat=".0f",
    )
    figure.update_yaxes(
        type="linear",
        range=[float(ordered["_position"].max()) + 0.65, -0.65],
        autorange=False,
        tickmode="array",
        tickvals=ordered["_position"].tolist(),
        ticktext=ordered["country"].tolist(),
        showgrid=False,
        ticks="",
    )
    for position, group in headings:
        figure.add_annotation(
            x=0,
            y=position,
            xref="paper",
            yref="y",
            xanchor="left",
            text=f"<b>{group}</b>",
            showarrow=False,
            font={"size": 12, "color": TEXT_COLOR},
        )
    for position in separators[:-1]:
        figure.add_shape(
            type="line",
            x0=0,
            x1=1,
            xref="paper",
            y0=position,
            y1=position,
            yref="y",
            layer="below",
            line={"color": GRID_COLOR, "width": 1},
        )
    return figure
