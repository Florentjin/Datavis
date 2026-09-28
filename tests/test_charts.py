"""Visual encoding contracts, independent of the production data pipeline."""

import json

import pandas as pd
import plotly.graph_objects as go
import pytest

from passport_dashboard.charts import changes, country_slopes, regional_medians, trajectories
from passport_dashboard.theme import (
    COUNTRY_COLORS,
    FONT_FAMILY,
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


@pytest.fixture
def panel():
    return pd.DataFrame(
        [
            ("FRA", "France", "EUROPE", 150, 185, 3, 2),
            ("DEU", "Allemagne", "EUROPE", 165, 180, 1, 3),
            ("JPN", "Japon", "ASIA", 140, 190, 4, 1),
            ("IND", "Inde", "ASIA", 50, 60, 70, 65),
            ("NGA", "Nigeria", "AFRICA", 45, 40, 85, 90),
            ("KEN", "Kenya", "AFRICA", 65, 65, 60, 60),
        ],
        columns=["code", "country", "region", "score_start", "score_end", "rank_start", "rank_end"],
    ).assign(delta=lambda frame: frame["score_end"] - frame["score_start"])


@pytest.fixture
def series():
    return pd.DataFrame(
        {
            "code": ["FRA"] * 3 + ["DEU"] * 3,
            "country": ["France"] * 3 + ["Allemagne"] * 3,
            "region": ["EUROPE"] * 6,
            "year": [2006, 2007, 2008] * 2,
            "score": pd.Series([150, pd.NA, 185, 165, 170, 180], dtype="Float64"),
            "rank": pd.Series([3, 2, 1, 1, pd.NA, 3], dtype="Int64"),
        }
    )


@pytest.fixture
def extremes(panel):
    result = panel.loc[panel["code"].isin(["NGA", "KEN", "FRA", "JPN"])].copy()
    result["group"] = result["code"].map(
        {"NGA": "Faibles variations", "KEN": "Faibles variations",
         "FRA": "Fortes variations", "JPN": "Fortes variations"}
    )
    return result


def test_theme_is_local_responsive_and_uses_shared_tokens():
    figure = go.Figure(go.Scatter(x=[0, 1], y=[1, 2]))

    themed = apply_theme(figure)

    assert themed is figure
    assert figure.layout.paper_bgcolor == figure.layout.plot_bgcolor == "#FFFFFF"
    assert figure.layout.font.family == FONT_FAMILY
    assert figure.layout.font.color == TEXT_COLOR
    assert figure.layout.xaxis.gridcolor == figure.layout.yaxis.gridcolor == GRID_COLOR
    assert figure.layout.width is None
    assert figure.layout.autosize is True
    assert tuple(REGION_COLORS) == REGIONS
    assert set(REGION_COLORS) == set(REGION_LABELS)
    assert len(COUNTRY_COLORS) == 4


@pytest.mark.parametrize("title", ["Titre simple", "<b>Titre déjà en gras</b>"])
def test_theme_does_not_rewrap_titles_when_applied_repeatedly(title):
    figure = go.Figure(layout={"title": {"text": title}})

    apply_theme(figure)
    first = figure.to_plotly_json()
    apply_theme(figure)

    assert figure.layout.title.text == title
    assert "<b><b>" not in figure.layout.title.text
    assert figure.to_plotly_json() == first


@pytest.mark.parametrize(
    "constructor",
    [
        lambda frame: regional_medians(frame, 2006, 2026),
        lambda frame: trajectories(frame),
        lambda frame: trajectories(frame, "rank"),
        lambda frame: country_slopes(frame, 2006, 2026, ["FRA"]),
        lambda frame: changes(frame, 2006, 2026),
    ],
)
def test_empty_frames_have_explicit_no_data_state(constructor):
    figure = constructor(pd.DataFrame())

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 0
    assert any("Aucune donnée" in item.text for item in figure.layout.annotations)
    assert figure.layout.xaxis.visible is False
    assert figure.layout.yaxis.visible is False
    assert figure.layout.title.text
    json.loads(figure.to_json())


@pytest.mark.parametrize("metric", ["delta", "Score", "", None])
def test_trajectories_reject_invalid_metrics_even_for_empty_frames(metric):
    with pytest.raises(ValueError, match="metric"):
        trajectories(pd.DataFrame(), metric)


def test_dumbbell_shows_median_positions_with_written_values(panel):
    figure = regional_medians(panel, 2006, 2026)

    traces = [trace for trace in figure.data if trace.mode and "lines" in trace.mode]
    assert len(traces) == panel["region"].nunique()
    for trace in traces:
        region = trace.legendgroup
        rows = panel.loc[panel["region"].eq(region)]
        start_median = float(rows["score_start"].median())
        end_median = float(rows["score_end"].median())
        assert trace.x == (start_median, end_median)
        assert trace.text == (f"{start_median:.0f}", f"{end_median:.0f}")
        assert trace.marker.color == (START_DOT_COLOR, REGION_COLORS[region])
        assert trace.marker.size[1] > trace.marker.size[0]
        assert trace.name == REGION_LABELS[region]
        assert "2006" in trace.hovertemplate and "2026" in trace.hovertemplate
        assert len({label for label in trace.y}) == 1
        assert "n = " in trace.y[0]
    assert figure.layout.xaxis.range[0] == 0
    assert figure.layout.xaxis.range[1] > max(panel["score_start"].max(), panel["score_end"].max())
    assert figure.layout.showlegend is False
    assert figure.layout.yaxis.autorange == "reversed"


def test_dumbbell_orders_regions_by_arrival_median_descending(panel):
    figure = regional_medians(panel, 2006, 2026)

    order = figure.layout.yaxis.categoryarray
    medians = panel.groupby("region", observed=True)["score_end"].median()
    expected = sorted(
        medians.index, key=lambda region: (-medians[region], region)
    )
    labels = [label.split(" (n")[0] for label in order]
    assert labels == [REGION_LABELS[region] for region in expected]


def test_trajectories_keep_explicit_annual_nulls_despite_available_rank(series):
    figure = trajectories(series.sample(frac=1, random_state=7), "score")
    france = next(trace for trace in figure.data if trace.name == "France")
    serialized = json.loads(figure.to_json())
    json_france = next(trace for trace in serialized["data"] if trace["name"] == "France")

    assert tuple(france.x) == (2006, 2007, 2008)
    assert tuple(france.y) == (150, None, 185)
    assert json_france["y"] == [150, None, 185]
    assert json_france["x"] == [2006, 2007, 2008]
    assert all(trace.connectgaps is False for trace in figure.data)
    assert figure.layout.yaxis.range[0] == 0
    assert figure.layout.xaxis.type == "linear"
    assert figure.layout.xaxis.dtick >= 1
    assert float(figure.layout.xaxis.dtick).is_integer()
    assert figure.layout.xaxis.tickformat == ".0f"


def test_trajectories_use_one_color_and_one_label_per_country(series):
    figure = trajectories(series)

    assert {trace.name for trace in figure.data} == {"France", "Allemagne"}
    colors = [trace.line.color for trace in figure.data]
    assert all(trace.line.color == trace.marker.color for trace in figure.data)
    assert len(set(colors)) == len(colors)
    assert all(color in COUNTRY_COLORS for color in colors)
    assert all(trace.line.dash in (None, "solid") for trace in figure.data)
    labels = {item.text for item in figure.layout.annotations}
    assert labels == {"France", "Allemagne"}
    for item in figure.layout.annotations:
        trace = next(trace for trace in figure.data if trace.name == item.text)
        assert item.font.color == trace.line.color
    assert figure.layout.showlegend is False
    for trace in figure.data:
        assert "%{customdata[0]}" in trace.hovertemplate


def test_trajectory_labels_sit_on_the_last_observed_point(series):
    figure = trajectories(series)
    france = next(trace for trace in figure.data if trace.name == "France")
    label = next(item for item in figure.layout.annotations if item.text == "France")

    assert (label.x, label.y) == (2008, 185)
    assert label.xanchor == "left"


def test_ranks_are_reversed_start_at_one_and_preserve_their_own_missing_values(series):
    figure = trajectories(series, "rank")
    germany = next(trace for trace in figure.data if trace.name == "Allemagne")

    assert tuple(germany.y) == (1, None, 3)
    assert all(trace.connectgaps is False for trace in figure.data)
    assert figure.layout.yaxis.range[0] > figure.layout.yaxis.range[1] == 1
    assert figure.layout.yaxis.tick0 == 1
    assert "1 = meilleur" in figure.layout.yaxis.title.text


def test_all_missing_metric_has_no_data_state_without_rank_fallback(series):
    series["score"] = pd.NA

    figure = trajectories(series)

    assert not figure.data
    assert any("Aucune donnée" in annotation.text for annotation in figure.layout.annotations)
    assert trajectories(series, "rank").data


def test_slopes_draw_one_line_per_focus_country_with_both_scores(panel):
    figure = country_slopes(panel, 2006, 2026, ["FRA", "NGA", "UNKNOWN"])

    traces = [trace for trace in figure.data if trace.type == "scatter"]
    assert sorted(trace.name for trace in traces) == ["France", "Nigeria"]
    for trace in traces:
        row = panel.loc[panel["code"].eq(trace.ids[0][:3])].iloc[0]
        assert trace.x == (0, 1)
        assert trace.y == (float(row["score_start"]), float(row["score_end"]))
        assert trace.mode == "lines+markers"
        assert "2006" in trace.hovertemplate and "2026" in trace.hovertemplate
    assert figure.layout.xaxis.ticktext == ("2006", "2026")
    assert figure.layout.yaxis.range[0] == 0


def test_slopes_share_country_colors_with_trajectories(panel, series):
    slopes = country_slopes(panel, 2006, 2026, ["FRA", "DEU"])
    both = series.loc[series["code"].isin(["FRA", "DEU"])]

    slope_colors = {
        trace.name: trace.line.color for trace in slopes.data if trace.type == "scatter"
    }
    figure = trajectories(both)
    trajectory_colors = {trace.name: trace.line.color for trace in figure.data}

    assert slope_colors == trajectory_colors


def test_slopes_annotate_absolute_and_relative_variation(panel):
    figure = country_slopes(panel, 2006, 2026, ["FRA", "NGA"])

    annotations = figure.layout.annotations
    texts = [item.text for item in annotations]
    assert "150" in texts  # France au départ
    assert "France · 185" in texts  # France à l'arrivée
    deltas = [item for item in annotations if "·" in str(item.text) and "%" in str(item.text)]
    assert {item.text for item in deltas} == {"+35 · +23 %", "-5 · -11 %"}
    gain = next(item for item in deltas if item.text.startswith("+35"))
    loss = next(item for item in deltas if item.text.startswith("-5"))
    assert gain.font.color == GAIN_COLOR
    assert loss.font.color == LOSS_COLOR


def test_close_endpoint_labels_are_staggered_without_moving_their_anchor(panel, series):
    close_panel = panel.loc[panel["code"].isin(["FRA", "DEU"])]

    slopes = country_slopes(close_panel, 2006, 2026, ["FRA", "DEU"])
    end_labels = [
        item
        for item in slopes.layout.annotations
        if "·" in str(item.text) and "%" not in str(item.text)
    ]
    assert {item.text for item in end_labels} == {"France · 185", "Allemagne · 180"}
    for item in end_labels:
        row = close_panel.loc[close_panel["country"].eq(str(item.text).split(" · ")[0])].iloc[0]
        assert item.y == float(row["score_end"])  # l'ancre reste la vraie valeur
    shifts = {item.text: item.yshift for item in end_labels}
    assert shifts["France · 185"] != shifts["Allemagne · 180"]

    figure = trajectories(series)
    labels = {item.text: item for item in figure.layout.annotations}
    assert labels["France"].y == 185 and labels["Allemagne"].y == 180
    assert labels["France"].yshift != labels["Allemagne"].yshift


def test_dumbbell_hover_shows_relative_variation_too(panel):
    figure = regional_medians(panel, 2006, 2026)

    for trace in figure.data:
        assert "%" in trace.hovertemplate


def test_years_without_any_observation_are_shaded(series):
    series.loc[series["year"].eq(2007), "score"] = pd.NA

    figure = trajectories(series)

    bands = [shape for shape in figure.layout.shapes if shape.type == "rect"]
    assert len(bands) == 1
    assert bands[0].x0 == 2007 - 0.45 and bands[0].x1 == 2007 + 0.45
    assert any("aucun score" in str(item.text) for item in figure.layout.annotations)
    series.loc[series["year"].eq(2007), "rank"] = pd.NA
    rank_figure = trajectories(series, "rank")
    rank_bands = [shape for shape in rank_figure.layout.shapes if shape.type == "rect"]
    assert len(rank_bands) == 1
    assert any("aucun rang" in str(item.text) for item in rank_figure.layout.annotations)


def test_years_with_partial_observations_are_not_shaded(series):
    figure = trajectories(series)

    assert not [shape for shape in figure.layout.shapes if shape.type == "rect"]


def test_rank_mode_labels_both_ends_like_a_bump_chart(series):
    figure = trajectories(series, "rank")

    texts = [item.text for item in figure.layout.annotations]
    assert any(text == "France · 1" for text in texts)
    assert any(text == "Allemagne · 3" for text in texts)
    left_numbers = [item for item in figure.layout.annotations if str(item.text).isdigit()]
    assert {item.text for item in left_numbers} == {"3", "1"}
    assert all(item.xanchor == "right" for item in left_numbers)


def test_changes_use_diverging_colors_zero_baseline_and_signed_labels(extremes):
    figure = changes(extremes, 2006, 2026)

    (bar,) = figure.data
    assert bar.type == "bar"
    assert bar.orientation == "h"
    assert bar.base == 0
    for code, value, color, label in zip(bar.ids, bar.x, bar.marker.color, bar.text):
        expected = extremes.loc[extremes["code"].eq(code), "delta"].iloc[0]
        assert value == expected
        assert color == (GAIN_COLOR if expected > 0 else LOSS_COLOR)
        assert label == (f"+{expected:g}" if expected > 0 else f"{expected:g}")
    assert len(set(bar.ids)) == len(bar.ids) == len(extremes)
    assert 0 >= figure.layout.xaxis.range[0]
    assert 0 <= figure.layout.xaxis.range[1]
    assert figure.layout.xaxis.zeroline is True


def test_changes_sort_extremes_from_biggest_gain_to_biggest_loss(extremes):
    figure = changes(extremes.sample(frac=1, random_state=8), 2006, 2026)

    (bar,) = figure.data
    deltas = list(bar.x)
    assert deltas == sorted(deltas, reverse=True)
    assert figure.layout.yaxis.categoryarray == tuple(bar.y)
    assert figure.layout.yaxis.autorange == "reversed"


@pytest.mark.parametrize(
    ("deltas", "title_fragment", "excluded"),
    [
        ([1, 2, 3, 4], "Gains les plus forts", "Reculs"),
        ([-4, -3, -2, -1], "Reculs les plus marqués", "Gains"),
        ([0, 0, 0, 0], "Scores inchangés", "Gains"),
        ([-4, -3, -2, 0], "Reculs et scores inchangés", "Gains"),
    ],
)
def test_changes_titles_reflect_the_signs_really_present(extremes, deltas, title_fragment, excluded):
    extremes["delta"] = deltas
    extremes["score_end"] = extremes["score_start"] + extremes["delta"]

    figure = changes(extremes, 2006, 2026)

    assert title_fragment in figure.layout.title.text
    assert excluded not in figure.layout.title.text


def test_small_change_cohorts_are_not_duplicated(extremes):
    tiny = extremes.iloc[:3]

    figure = changes(tiny, 2006, 2026)

    (bar,) = figure.data
    assert len(set(bar.ids)) == len(bar.ids) == 3


def test_region_palette_is_consistent_for_all_seven_regions():
    panel = pd.DataFrame(
        [
            {
                "code": f"C{index}",
                "country": f"Pays {index}",
                "region": region,
                "score_start": 40 + index,
                "score_end": 50 + index,
                "rank_start": 9 - index,
                "rank_end": 9 - index,
                "delta": 10,
                "group": "Fortes variations",
            }
            for index, region in enumerate(REGIONS)
        ]
    )
    figure = regional_medians(panel, 2006, 2026)

    for trace in figure.data:
        region = trace.legendgroup
        assert trace.marker.color[1] == REGION_COLORS[region]
        assert trace.name == REGION_LABELS[region]


def test_constructors_do_not_mutate_input_frames(panel, series, extremes):
    original_panel = panel.copy(deep=True)
    original_series = series.copy(deep=True)
    original_extremes = extremes.copy(deep=True)

    regional_medians(panel, 2006, 2026)
    country_slopes(panel, 2006, 2026, ["FRA"])
    trajectories(series)
    changes(extremes, 2006, 2026)

    pd.testing.assert_frame_equal(panel, original_panel)
    pd.testing.assert_frame_equal(series, original_series)
    pd.testing.assert_frame_equal(extremes, original_extremes)
