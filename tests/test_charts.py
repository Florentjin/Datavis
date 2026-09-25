"""Visual encoding contracts, independent of the production data pipeline."""

import json

import pandas as pd
import plotly.graph_objects as go
import pytest

from passport_dashboard.charts import changes, positions, regional_distribution, trajectories
from passport_dashboard.theme import (
    FONT_FAMILY,
    GRID_COLOR,
    REGION_COLORS,
    REGION_LABELS,
    REGIONS,
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
        lambda frame: regional_distribution(frame, 2006, 2026, []),
        lambda frame: regional_distribution(frame, 2006, 2026, [], stacked=True),
        lambda frame: trajectories(frame),
        lambda frame: trajectories(frame, "rank"),
        lambda frame: positions(frame, 2006, 2026, []),
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


@pytest.mark.parametrize("stacked", [False, True])
def test_boxes_use_raw_values_linear_quartiles_and_common_zero_scale(panel, stacked):
    figure = regional_distribution(panel, 2006, 2026, [], stacked=stacked)
    boxes = [trace for trace in figure.data if trace.type == "box"]

    assert len(boxes) == 6
    for trace in boxes:
        endpoint = "score_start" if trace.xaxis == "x" else "score_end"
        rows = panel.loc[panel["region"].eq(trace.legendgroup)]
        assert trace.orientation == "h"
        assert trace.quartilemethod == "linear"
        assert sorted(trace.x) == sorted(rows[endpoint].tolist())
        assert set(trace.ids) == set(rows["code"])
        assert len(trace.y) == len(rows)
        assert all(f"n = {len(rows)}" in label for label in trace.y)
        assert trace.line.color == REGION_COLORS[trace.legendgroup]
        assert trace.line.width >= 2
        assert trace.opacity == 1
        assert trace.fillcolor.startswith("rgba(")
        assert trace.name == REGION_LABELS[trace.legendgroup]
    assert figure.layout.xaxis.range == figure.layout.xaxis2.range
    assert figure.layout.xaxis.dtick == figure.layout.xaxis2.dtick == 50
    assert figure.layout.xaxis.tickangle == figure.layout.xaxis2.tickangle == 0
    assert figure.layout.showlegend is False
    assert figure.layout.xaxis.range[0] == 0
    assert figure.layout.xaxis.range[1] > max(panel["score_start"].max(), panel["score_end"].max())
    assert figure.layout.yaxis.categoryarray == figure.layout.yaxis2.categoryarray
    assert figure.layout.yaxis.categoryarray == (
        "Europe (n = 2)", "Asie (n = 2)", "Afrique (n = 2)"
    )
    assert figure.layout.yaxis.autorange == figure.layout.yaxis2.autorange == "reversed"


def test_stacked_distribution_uses_full_width_and_repeats_count_labels(panel):
    horizontal = regional_distribution(panel, 2006, 2026, ["FRA"])
    stacked = regional_distribution(panel, 2006, 2026, ["FRA"], stacked=True)

    assert stacked.layout.xaxis.domain == stacked.layout.xaxis2.domain == (0, 1)
    assert stacked.layout.yaxis.domain[0] > stacked.layout.yaxis2.domain[1]
    assert horizontal.layout.xaxis.domain[1] < horizontal.layout.xaxis2.domain[0]
    assert horizontal.layout.yaxis.domain == horizontal.layout.yaxis2.domain
    assert stacked.layout.xaxis.showticklabels is True
    assert stacked.layout.xaxis2.showticklabels is True
    assert stacked.layout.yaxis.showticklabels is True
    assert stacked.layout.yaxis2.showticklabels is True
    assert stacked.layout.height > horizontal.layout.height
    assert stacked.layout.width is None
    assert sum(trace.showlegend is True for trace in stacked.data) == panel["region"].nunique()
    assert [trace.to_plotly_json() for trace in stacked.data] == [
        trace.to_plotly_json() for trace in horizontal.data
    ]


@pytest.mark.parametrize("stacked", [False, True])
def test_box_focus_is_unambiguous_and_contains_both_endpoint_scores(panel, stacked):
    figure = regional_distribution(
        panel, 2006, 2026, ["FRA", "NGA", "UNKNOWN"], stacked=stacked
    )
    overlays = [trace for trace in figure.data if trace.type == "scatter"]

    assert len(overlays) == 4
    assert sorted(code for trace in overlays for code in trace.ids) == ["FRA", "FRA", "NGA", "NGA"]
    for trace in overlays:
        assert trace.mode == "markers"
        assert trace.marker.symbol == "diamond"
        assert trace.marker.line.width > 0
        assert "2006" in trace.hovertemplate and "2026" in trace.hovertemplate
        for point in trace.customdata:
            row = panel.loc[panel["code"].eq(point[0])].iloc[0]
            assert point[1] == row["country"]
            assert list(point[2:5]) == [row["score_start"], row["score_end"], row["delta"]]
            assert trace.marker.color == REGION_COLORS[row["region"]]


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
    assert not hasattr(figure.layout, "yaxis2") or figure.layout.yaxis2 is None


def test_annual_point_ids_are_unique_so_isolated_observations_remain_visible(series):
    figure = trajectories(series)
    all_ids = []
    for trace in figure.data:
        assert trace.mode == "lines+markers"
        assert trace.marker.size > 0
        assert len(trace.ids) == len(trace.x) == len(set(trace.ids))
        assert tuple(trace.ids) == tuple(f"{trace.legendgroup}-{year}" for year in trace.x)
        all_ids.extend(trace.ids)
    assert len(all_ids) == len(set(all_ids))


def test_same_region_countries_have_distinct_dash_marker_and_country_legend(series):
    figure = trajectories(series)

    assert {trace.name for trace in figure.data} == {"France", "Allemagne"}
    assert len({trace.line.dash for trace in figure.data}) == 2
    assert len({trace.marker.symbol for trace in figure.data}) == 2
    for trace in figure.data:
        assert trace.line.color == trace.marker.color == REGION_COLORS["EUROPE"]
        assert trace.legendgroup in {"FRA", "DEU"}
        assert "%{customdata[0]}" in trace.hovertemplate


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


def test_positions_axes_are_numerically_and_physically_square(panel):
    figure = positions(panel, 2006, 2026, ["FRA"])
    xaxis, yaxis = figure.layout.xaxis, figure.layout.yaxis

    assert xaxis.range == yaxis.range
    assert xaxis.range[0] == 0
    assert xaxis.range[1] > max(panel["score_start"].max(), panel["score_end"].max())
    assert yaxis.scaleanchor == "x"
    assert yaxis.scaleratio == 1
    assert xaxis.constrain == yaxis.constrain == "domain"
    diagonal = next(shape for shape in figure.layout.shapes if shape.type == "line")
    assert diagonal.x0 == diagonal.y0 == 0
    assert diagonal.x1 == diagonal.y1 == xaxis.range[1]
    assert diagonal.xref == "x" and diagonal.yref == "y"
    assert any("Score inchangé" in item.text for item in figure.layout.annotations)
    assert figure.layout.width is None


def test_positions_use_constant_sizes_selected_labels_and_outlines(panel):
    figure = positions(panel, 2006, 2026, ["FRA", "NGA"])
    sizes = set()
    for trace in figure.data[:-1]:
        assert trace.mode == "markers"
        assert trace.text is None
        sizes.add(trace.marker.size)
        assert trace.marker.color == REGION_COLORS[trace.legendgroup]
        assert trace.name == REGION_LABELS[trace.legendgroup]
        assert "2006" in trace.hovertemplate and "2026" in trace.hovertemplate
        assert "%{customdata[4]" in trace.hovertemplate
        for code, width in zip(trace.ids, trace.marker.line.width):
            if code in {"FRA", "NGA"}:
                assert width > 1
            else:
                assert width < 1
    assert sizes == {10}
    labels = figure.data[-1]
    assert labels.mode == "text"
    assert labels.cliponaxis is False
    assert labels.showlegend is False
    assert labels.hoverinfo == "skip"
    assert labels.textfont.shadow
    assert set(labels.text) == {"France", "Nigeria"}
    assert set(labels.ids) == {"FRA", "NGA"}


def test_positions_focus_labels_face_inward_and_follow_all_regional_points(panel):
    selected = panel.iloc[:3].copy()
    selected["code"] = ["AFG", "USA", "EDGE"]
    selected["country"] = ["Afghanistan", "United States", "Pays à droite"]
    selected["region"] = ["ASIA", "AMERICAS", "EUROPE"]
    selected["score_start"] = [12, 130, 195]
    selected["score_end"] = [24, 181, 195]
    selected["delta"] = selected["score_end"] - selected["score_start"]

    figure = positions(selected, 2006, 2026, ["AFG", "USA", "EDGE"])

    assert all(trace.mode == "markers" for trace in figure.data[:-1])
    labels = figure.data[-1]
    assert labels.mode == "text"
    assert labels.cliponaxis is False
    placement = dict(zip(labels.ids, labels.textposition))
    assert placement["AFG"] == "top right"
    assert placement["USA"] == "bottom right"
    assert placement["EDGE"] == "bottom left"
    assert labels.x == tuple(selected["score_start"])
    assert labels.y == tuple(selected["score_end"])


def test_changes_preserve_unique_codes_signed_values_and_zero_based_bars(extremes):
    figure = changes(extremes, 2006, 2026)
    seen = []
    for trace in figure.data:
        assert trace.type == "bar"
        assert trace.orientation == "h"
        assert trace.base == 0
        assert trace.marker.color == REGION_COLORS[trace.legendgroup]
        assert trace.name == REGION_LABELS[trace.legendgroup]
        for code, value, label in zip(trace.ids, trace.x, trace.text):
            seen.append(code)
            expected = extremes.loc[extremes["code"].eq(code), "delta"].iloc[0]
            assert value == expected
            assert label == (f"+{expected:g}" if expected > 0 else f"{expected:g}")
    assert len(seen) == len(set(seen)) == len(extremes)
    assert set(seen) == set(extremes["code"])
    assert figure.layout.xaxis.range[0] == -figure.layout.xaxis.range[1]
    assert figure.layout.xaxis.range[0] < extremes["delta"].min() < 0
    assert figure.layout.xaxis.zeroline is True
    assert "Variations les plus faibles et les plus fortes" in figure.layout.title.text


def test_changes_sort_within_explicit_groups_and_separate_them(extremes):
    figure = changes(extremes.sample(frac=1, random_state=8), 2006, 2026)

    assert tuple(figure.layout.yaxis.ticktext) == ("Nigeria", "Kenya", "France", "Japon")
    positions_by_country = dict(zip(figure.layout.yaxis.ticktext, figure.layout.yaxis.tickvals))
    assert positions_by_country["France"] - positions_by_country["Kenya"] > 1
    assert len(figure.layout.shapes) == 1
    assert {annotation.text for annotation in figure.layout.annotations} == {
        "<b>Faibles variations</b>", "<b>Fortes variations</b>"
    }


@pytest.mark.parametrize(
    ("deltas", "title_fragment", "excluded"),
    [
        ([1, 2, 3, 4], "Variations les plus faibles", "Reculs"),
        ([-4, -3, -2, -1], "Reculs les plus marqués", "gains"),
        ([0, 0, 0, 0], "Scores inchangés", "gains"),
        ([-4, -3, -2, 0], "Reculs et scores inchangés", "gains"),
    ],
)
def test_changes_titles_do_not_call_positive_low_changes_losses(extremes, deltas, title_fragment, excluded):
    extremes["delta"] = deltas
    extremes["score_end"] = extremes["score_start"] + extremes["delta"]

    figure = changes(extremes, 2006, 2026)

    assert title_fragment in figure.layout.title.text
    assert excluded not in figure.layout.title.text
    assert figure.layout.xaxis.range[0] < 0 < figure.layout.xaxis.range[1]


def test_changes_do_not_describe_a_mixed_bottom_five_as_losses():
    extremes = pd.DataFrame(
        [
            {
                "code": f"C{index}",
                "country": f"Pays {index}",
                "region": "ASIA",
                "score_start": 80,
                "score_end": 80 + delta,
                "rank_start": 20,
                "rank_end": 20,
                "delta": delta,
                "group": "Faibles variations" if index < 5 else "Fortes variations",
            }
            for index, delta in enumerate([-8, 1, 2, 3, 4, 21, 22, 23, 24, 25])
        ]
    )

    figure = changes(extremes, 2006, 2026)

    assert figure.layout.title.text.startswith("Variations les plus faibles et les plus fortes")
    assert "Reculs" not in figure.layout.title.text


@pytest.mark.parametrize("size", [1, 2, 3])
def test_small_change_cohorts_are_not_duplicated(extremes, size):
    tiny = extremes.iloc[:size]

    figure = changes(tiny, 2006, 2026)

    codes = [code for trace in figure.data for code in trace.ids]
    assert len(codes) == len(set(codes)) == size


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
    series = panel.rename(
        columns={"score_start": "score", "rank_start": "rank"}
    ).assign(year=2006)
    figures = (
        regional_distribution(panel, 2006, 2026, []),
        trajectories(series),
        positions(panel, 2006, 2026, []),
        changes(panel, 2006, 2026),
    )

    for figure in figures:
        for trace in figure.data:
            is_trajectory = trace.type == "scatter" and "lines" in trace.mode
            code = trace.legendgroup if is_trajectory else trace.ids[0]
            region = panel.loc[panel["code"].eq(code), "region"].iloc[0]
            assert trace.marker.color == REGION_COLORS[region]
            if trace.type != "scatter" or "lines" not in trace.mode:
                assert trace.name == REGION_LABELS[region]


def test_constructors_do_not_mutate_input_frames(panel, series, extremes):
    original_panel = panel.copy(deep=True)
    original_series = series.copy(deep=True)
    original_extremes = extremes.copy(deep=True)

    regional_distribution(panel, 2006, 2026, ["FRA"])
    positions(panel, 2006, 2026, ["FRA"])
    trajectories(series)
    changes(extremes, 2006, 2026)

    pd.testing.assert_frame_equal(panel, original_panel)
    pd.testing.assert_frame_equal(series, original_series)
    pd.testing.assert_frame_equal(extremes, original_extremes)
