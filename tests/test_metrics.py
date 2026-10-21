from pathlib import Path

import pandas as pd
import pytest

from passport_dashboard import metrics
from passport_dashboard.data import DataError, load_access, load_rank

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rank() -> pd.DataFrame:
    return load_rank(ROOT / "rank_by_year.csv")


@pytest.fixture(scope="module")
def access() -> pd.DataFrame:
    return load_access(ROOT / "country_lists.csv")


def test_q1_regional_medians(rank):
    scores = metrics.scores_for_year(rank, 2025)
    medians = scores.groupby("region")["score"].median()
    assert medians["EUROPE"] == 183
    assert medians["AFRICA"] == 58.5
    assert scores["score"].median() == 94


def test_q1_rejects_year_without_scores(rank):
    with pytest.raises(DataError):
        metrics.scores_for_year(rank, 2007)


def test_q2_constant_panel_and_gap(rank):
    series = metrics.inequality_over_time(rank).set_index("year")
    assert series["n"].nunique() == 1 and series["n"].iloc[0] == 183
    assert series.loc[[2007, 2009], "gap"].isna().all()
    assert series.loc[2006, "gap"] == pytest.approx(105.6, abs=0.5)
    assert series.loc[2025, "gap"] == pytest.approx(140, abs=0.5)
    ratio = series["p90"] / series["p10"]
    assert ratio[2025] < ratio[2006]


def test_q3_only_bolivia_declines(rank):
    changes = metrics.score_changes(rank, 2006, 2025)
    losers = changes.loc[changes["delta"] < 0]
    assert losers["code"].tolist() == ["BO"]
    assert changes.iloc[-1]["code"] == "AE" and changes.iloc[-1]["delta"] == 149
    picked = metrics.extremes(changes, 10)
    assert picked["group"].value_counts().to_dict() == {"high": 10, "low": 10}


def test_q3_rejects_inverted_period(rank):
    with pytest.raises(DataError):
        metrics.score_changes(rank, 2025, 2006)


def test_q4_shares_sum_to_100(access, rank):
    shares = metrics.entry_modes(access, rank).set_index("region")
    regimes = shares.drop(columns="open")
    assert regimes.sum(axis=1).round(6).eq(100).all()
    assert round(shares.loc["EUROPE", "open"]) == 73
    assert round(shares.loc["AFRICA", "open"]) == 28
    assert round(shares.loc[metrics.WORLD, "open"]) == 48


def test_q4_destination_view(access, rank):
    shares = metrics.entry_modes(access, rank, "destination").set_index("region")
    assert shares["open"].drop(metrics.WORLD).idxmax() == "CARIBBEAN"
    with pytest.raises(DataError):
        metrics.entry_modes(access, rank, "other")


def test_q5_reciprocity_balance(access, rank):
    shares = metrics.reciprocity(access, rank).set_index("region")
    categories = shares[["mutual_open", "favourable", "unfavourable", "mutual_closed"]]
    assert categories.sum(axis=1).round(6).eq(100).all()
    assert round(shares.loc["EUROPE", "balance"]) == 26
    assert round(shares.loc["AFRICA", "balance"]) == -16
    assert shares.loc[metrics.WORLD, "balance"] == pytest.approx(0, abs=1e-9)


def test_q6_weak_link(access, rank):
    frame = metrics.hospitality_vs_power(access, rank)
    assert frame["welcomed"].between(0, 198).all()
    assert frame["welcomed"].corr(frame["score"]) == pytest.approx(0.13, abs=0.01)


def test_q7_regions_more_open_internally(access, rank):
    matrix = metrics.regional_openness(access, rank)
    assert matrix.shape == (7, 7)
    for region in matrix.index:
        assert matrix.loc[region, region] > matrix.loc[region].drop(region).mean()
    assert matrix.stack().idxmin() == ("AFRICA", "EUROPE")
    assert round(matrix.loc["AFRICA", "EUROPE"]) == 4


def test_q8_clubs(access, rank):
    clubs = metrics.club_openness(access, rank).set_index("club")
    assert (clubs["inside"] > clubs["outside"]).all()
    assert clubs.index[0].startswith("CEDEAO")
    assert clubs.iloc[0]["inside"] == 100 and round(clubs.iloc[0]["outside"]) == 25
    assert clubs["missing"].eq("").all()


def test_q8_requires_two_members(access, rank):
    with pytest.raises(DataError):
        metrics.club_openness(access, rank, {"Solo": ["FR", "ZZ"]})
