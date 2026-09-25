from pathlib import Path

import pandas as pd
import pytest

from passport_dashboard.data import REGIONS, DataError, load_rank
from passport_dashboard.metrics import (
    comparison,
    comparison_exclusions,
    extremes,
    regional_summary,
    spread,
    timeseries,
)

ROOT = Path(__file__).resolve().parents[1]
PANEL_COLUMNS = [
    "code", "country", "region", "score_start", "score_end", "rank_start", "rank_end", "delta"
]


@pytest.fixture(scope="module")
def rank():
    return load_rank(ROOT / "rank_by_year.csv")


@pytest.fixture(scope="module")
def panel(rank):
    return comparison(rank, 2006, 2025, REGIONS)


def test_complete_panel_has_183_passports_and_keeps_namibia(panel):
    assert panel.columns.tolist() == PANEL_COLUMNS
    assert len(panel) == 183
    assert not panel["code"].duplicated().any()
    assert panel[["score_start", "score_end"]].notna().all().all()
    assert "NA" in set(panel["code"])
    assert not {"ME", "CI"} & set(panel["code"])


def test_reference_deltas_and_us_world_rank_are_preserved(panel):
    by_code = panel.set_index("code")
    assert by_code.loc["AE", "delta"] == 149
    assert by_code.loc["US", "delta"] == 52
    assert by_code.loc["BO", "delta"] == -5
    assert by_code.loc["BO", "score_start"] == 83
    assert by_code.loc["BO", "score_end"] == 78
    assert by_code.loc["AE", "score_start"] == 35
    assert by_code.loc["AE", "score_end"] == 184
    assert by_code.loc["US", "score_start"] == 130
    assert by_code.loc["US", "score_end"] == 182
    assert by_code.loc["US", "rank_start"] == 1
    assert by_code.loc["US", "rank_end"] == 10


def test_region_filter_does_not_rerank_and_does_not_mutate_source(rank, panel):
    before = rank.copy(deep=True)
    filtered = comparison(rank, 2006, 2025, ["AMERICAS"])
    expected = panel.loc[panel["region"].eq("AMERICAS")].reset_index(drop=True)
    pd.testing.assert_frame_equal(filtered, expected)
    pd.testing.assert_frame_equal(rank, before)
    assert filtered.set_index("code").loc["US", "rank_end"] == 10


def test_reference_spread_uses_linear_quantiles_on_constant_panel(panel):
    result = spread(panel)
    assert result.columns.tolist() == ["period", "n", "median", "p10", "p90", "gap"]
    assert result["period"].tolist() == ["start", "end"]
    assert result["n"].tolist() == [183, 183]
    assert result["gap"].tolist() == pytest.approx([105.6, 140.0])
    for row in result.itertuples():
        scores = panel[f"score_{row.period}"]
        assert row.median == pytest.approx(scores.median())
        assert row.p10 == pytest.approx(scores.quantile(0.1))
        assert row.p90 == pytest.approx(scores.quantile(0.9))


def test_exclusions_cover_all_missing_endpoints_and_explain_zero_vs_absence(rank, panel):
    excluded = comparison_exclusions(rank, 2006, 2025, REGIONS)
    assert excluded.columns.tolist() == ["code", "country", "region", "reason"]
    assert len(excluded) == 16
    assert not excluded["code"].duplicated().any()
    assert set(excluded["code"]) | set(panel["code"]) == set(rank["code"])
    assert not set(excluded["code"]) & set(panel["code"])
    by_code = excluded.set_index("code")
    assert "Score non exploitable en 2006" in by_code.loc["ME", "reason"]
    assert "Score non exploitable en 2006" in by_code.loc["CI", "reason"]
    assert "Donnée absente en 2006" in by_code.loc["SS", "reason"]


def test_exclusions_include_a_passport_absent_at_both_dates(rank):
    without_endpoints = rank.loc[
        ~(rank["code"].eq("US") & rank["year"].isin([2006, 2025]))
    ]
    excluded = comparison_exclusions(without_endpoints, 2006, 2025, ["AMERICAS"]).set_index("code")
    assert excluded.loc["US", "reason"] == "Donnée absente en 2006 ; Donnée absente en 2025"


def test_exclusions_report_both_unusable_score_dates(rank):
    assert comparison(rank, 2007, 2009, REGIONS).empty
    excluded = comparison_exclusions(rank, 2007, 2009, REGIONS).set_index("code")
    assert len(excluded) == 199
    assert "Score non exploitable en 2007" in excluded.loc["US", "reason"]
    assert "Score non exploitable en 2009" in excluded.loc["US", "reason"]


def test_empty_regions_is_intentionally_empty_everywhere(rank):
    panel = comparison(rank, 2006, 2025, [])
    assert panel.empty
    assert panel.columns.tolist() == PANEL_COLUMNS
    assert comparison_exclusions(rank, 2006, 2025, []).empty
    summary = spread(panel)
    assert summary.empty
    assert summary.columns.tolist() == ["period", "n", "median", "p10", "p90", "gap"]
    assert str(summary["period"].dtype).startswith("string")
    assert str(summary["n"].dtype) == "Int64"
    assert str(summary["gap"].dtype) == "Float64"
    selected = extremes(panel)
    assert selected.empty
    assert selected.columns.tolist() == PANEL_COLUMNS + ["group"]
    assert str(selected["group"].dtype).startswith("string")
    regions = regional_summary(panel)
    assert regions.empty
    assert regions.columns.tolist() == ["region", "n", "median_start", "median_end"]
    assert str(regions["n"].dtype) == "Int64"
    assert str(regions["median_end"].dtype) == "Float64"


@pytest.mark.parametrize("function", [comparison, comparison_exclusions])
@pytest.mark.parametrize(
    ("start", "end"),
    [(2025, 2006), (2025, 2025), (2005, 2025), (2006, 2026), (2006.0, 2025), (True, 2025)],
)
def test_comparison_rejects_invalid_dates(rank, function, start, end):
    with pytest.raises(DataError, match="année|Année"):
        function(rank, start, end, REGIONS)


@pytest.mark.parametrize("function", [comparison, comparison_exclusions])
@pytest.mark.parametrize("regions", [["EUROPA"], ["AFRICA", "unknown"], "EUROPE", None, [1]])
def test_comparison_rejects_invalid_regions(rank, function, regions):
    with pytest.raises(DataError, match="régions|Région"):
        function(rank, 2006, 2025, regions)


def test_timeseries_has_complete_calendar_and_original_score_holes(rank):
    result = timeseries(rank, ["US", "NA"], 2006, 2025)
    assert result.columns.tolist() == ["code", "country", "region", "year", "score", "rank"]
    assert len(result) == 40
    assert not result.duplicated(["code", "year"]).any()
    assert result.loc[result["code"].eq("NA"), "country"].eq("Namibia").all()
    for code in ("US", "NA"):
        assert result.loc[result["code"].eq(code), "year"].tolist() == list(range(2006, 2026))
    gaps = result.loc[result["year"].isin([2007, 2009])]
    assert gaps["score"].isna().all()
    assert gaps["rank"].notna().all()
    source_ranks = rank.set_index(["code", "year"])["rank"]
    for row in gaps.itertuples():
        assert row.rank == source_ranks.loc[(row.code, row.year)]


def test_timeseries_fills_removed_source_rows_but_not_values(rank):
    without_row = rank.loc[~(rank["code"].eq("US") & rank["year"].eq(2010))]
    result = timeseries(without_row, ["US"], 2006, 2025).set_index("year")
    assert result.index.tolist() == list(range(2006, 2026))
    assert pd.isna(result.loc[2010, "score"])
    assert pd.isna(result.loc[2010, "rank"])
    assert result.loc[2010, "country"] == "United States"
    assert result.loc[2010, "region"] == "AMERICAS"
    assert result.loc[2011, "score"] > 0


def test_timeseries_inserts_globally_absent_interior_year(rank):
    without_year = rank.loc[rank["year"].ne(2010)]
    result = timeseries(without_year, ["US"], 2006, 2025).set_index("year")
    assert len(result) == 20
    assert pd.isna(result.loc[2010, "score"])
    assert pd.isna(result.loc[2010, "rank"])


def test_timeseries_keeps_passports_that_only_appear_after_start(rank):
    result = timeseries(rank, ["SS"], 2006, 2025).set_index("year")
    assert len(result) == 20
    assert pd.isna(result.loc[2006, "score"])
    assert pd.isna(result.loc[2006, "rank"])
    assert result.loc[2006, "country"] == "South Sudan"
    assert result.loc[2025, "score"] > 0


def test_timeseries_allows_single_year_empty_codes_and_deduplicates_selections(rank):
    one = timeseries(rank, ["NA", "NA"], 2025, 2025)
    assert len(one) == 1
    assert one.loc[0, "code"] == "NA"
    assert one.loc[0, "year"] == 2025
    empty = timeseries(rank, [], 2006, 2025)
    assert empty.empty
    assert empty.columns.tolist() == ["code", "country", "region", "year", "score", "rank"]
    assert str(empty["score"].dtype) == "Int64"
    assert str(empty["rank"].dtype) == "Int64"


@pytest.mark.parametrize(
    ("codes", "start", "end"),
    [(["ZZ"], 2006, 2025), (["US", "ZZ"], 2006, 2025), ("US", 2006, 2025),
     ([1], 2006, 2025), (None, 2006, 2025), (["US"], 2005, 2025),
     (["US"], 2006, 2026), (["US"], 2025, 2006), (["US"], 2006, "2025"),
     (["US"], 2006, True)],
)
def test_timeseries_rejects_unknown_codes_dates_and_invalid_types(rank, codes, start, end):
    with pytest.raises(DataError):
        timeseries(rank, codes, start, end)


def test_missing_endpoint_year_is_not_silently_accepted(rank):
    without_year = rank.loc[rank["year"].ne(2006)]
    for function in (comparison, comparison_exclusions):
        with pytest.raises(DataError, match="Année absente.*2006"):
            function(without_year, 2006, 2025, [])
    with pytest.raises(DataError, match="Année absente.*2006"):
        timeseries(without_year, [], 2006, 2025)


def test_extremes_have_correct_groups_and_stable_tie_breaks(panel):
    selected = extremes(panel)
    assert len(selected) == 10
    assert selected.columns.tolist() == PANEL_COLUMNS + ["group"]
    assert not selected["code"].duplicated().any()
    assert selected["group"].value_counts().to_dict() == {
        "Faibles variations": 5, "Fortes variations": 5
    }
    low = panel.sort_values(["delta", "country", "code"]).head(5)
    high = panel.sort_values(["delta", "country", "code"], ascending=[False, True, True]).head(5)
    assert selected["code"].tolist() == low["code"].tolist() + high["code"].tolist()
    pd.testing.assert_frame_equal(selected, extremes(panel.sample(frac=1, random_state=17)))


@pytest.mark.parametrize("size", [0, 1, 3, 6, 9])
def test_extremes_do_not_duplicate_small_panels(panel, size):
    small = panel.head(size)
    result = extremes(small, n=5)
    assert len(result) == size
    assert not result["code"].duplicated().any()
    assert set(result["code"]) == set(small["code"])


@pytest.mark.parametrize("n", [0, -1, 1.5, "5", True, None])
def test_extremes_reject_invalid_n_even_for_empty_panel(panel, n):
    with pytest.raises(DataError, match="entier strictement positif"):
        extremes(panel, n=n)
    with pytest.raises(DataError, match="entier strictement positif"):
        extremes(panel.iloc[:0], n=n)


def test_regional_summary_reuses_constant_panel(panel):
    result = regional_summary(panel)
    assert result.columns.tolist() == ["region", "n", "median_start", "median_end"]
    assert result["region"].tolist() == sorted(set(panel["region"]))
    assert result["n"].sum() == 183
    for row in result.itertuples():
        members = panel.loc[panel["region"].eq(row.region)]
        assert row.n == len(members)
        assert row.median_start == pytest.approx(members["score_start"].median())
        assert row.median_end == pytest.approx(members["score_end"].median())
