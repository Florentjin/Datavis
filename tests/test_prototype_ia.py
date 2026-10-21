"""Contrôles ciblés, sans écriture dans les CSV et sans accès réseau."""

import json
from html.parser import HTMLParser

import pandas as pd
import pytest

import prototype_ia as prototype


@pytest.fixture(scope="module")
def source_frames():
    return prototype.load_data(prototype.BASE)


@pytest.fixture(scope="module")
def data(source_frames):
    return prototype.prepare_data(*source_frames)


def test_sources_remain_unchanged_and_namibia_is_preserved(source_frames):
    before = prototype.source_hashes(prototype.BASE)
    rank, lists = source_frames
    original_rank, original_lists = rank.copy(deep=True), lists.copy(deep=True)
    prototype.prepare_data(rank, lists)
    pd.testing.assert_frame_equal(rank, original_rank)
    pd.testing.assert_frame_equal(lists, original_lists)
    assert prototype.source_hashes(prototype.BASE) == before
    assert rank.code.eq("NA").sum() == 20
    assert lists.code.eq("NA").sum() == 1


def test_zero_scores_are_missing_without_imputation(data):
    assert data["raw"].shape == (3950, 6)
    assert data["clean"].score.isna().sum() == 447
    assert data["missing_years"] == [2007, 2009]
    assert data["global"].loc[[2007, 2009], "median"].isna().all()
    assert data["global"].loc[[2007, 2009], "n"].eq(0).all()
    assert data["clean"]["rank"].eq(data["raw"]["rank"]).all()


def test_panel_has_constant_valid_membership(data):
    panel = data["panel"]
    assert data["panel_n"] == 183
    assert panel.dropna(subset=["score"]).groupby("year").code.nunique().eq(183).all()
    assert panel.groupby("code").score.count().eq(18).all()
    assert len(data["excluded"]) == 16
    assert not {"CI", "ME", "XK"} & set(panel.code)
    assert len(data["endpoints"]) == 183
    assert data["endpoints"].gain.eq(
        data["endpoints"].score_2025 - data["endpoints"].score_2006
    ).all()


def test_observations_and_sample_sensitivity(data):
    q = data["global"]
    assert q.loc[2006, ["p10", "median", "p90", "gap"]].tolist() == pytest.approx(
        [19, 46, 124.6, 105.6]
    )
    assert q.loc[2025, ["p10", "median", "p90", "gap"]].tolist() == pytest.approx(
        [47, 100, 187, 140]
    )
    assert q.loc[2006, "ratio"] > q.loc[2025, "ratio"]
    assert data["available"].loc[2025, "median"] == 94
    assert data["available"].loc[2025, "gap"] == pytest.approx(141.2)
    endpoints = data["endpoints"].set_index("code")
    assert endpoints.loc["AE", "gain"] == 149
    assert endpoints.loc["BO", "gain"] == -5
    assert endpoints.gain.gt(0).sum() == 182
    assert endpoints.gain.lt(0).sum() == 1


@pytest.mark.parametrize("items", [
    [{"code": "NA", "name": "Namibia"}],
    [[{"code": "NA", "name": "Namibia"}]],
])
def test_json_flat_or_nested_and_na_code(items):
    assert prototype.parse_destinations(json.dumps(items)) == [{"code": "NA", "name": "Namibia"}]


@pytest.mark.parametrize("cell", ["[]", "[[]]"])
def test_empty_json_list_means_zero_destinations(cell):
    assert prototype.parse_destinations(cell) == []


@pytest.mark.parametrize("cell", [
    "", "null", "{}", '[[{"code":"NA"}]]', '[[{"code":1,"name":"Namibia"}]]',
    '[[{"code":"NA","name":"Namibia"},{"code":"NA","name":"Namibia"}]]',
])
def test_invalid_or_duplicate_destinations_fail_loudly(cell):
    with pytest.raises(ValueError):
        prototype.parse_destinations(cell, "test")


def test_overlapping_categories_are_not_double_counted(source_frames):
    rank, lists = source_frames
    changed = lists.copy()
    changed.loc[0, "visa_online"] = changed.loc[0, "visa_required"]
    with pytest.raises(ValueError, match="chevauchantes"):
        prototype.prepare_data(rank, changed)


def test_duplicate_passport_year_is_rejected(source_frames, monkeypatch):
    rank, lists = source_frames
    duplicate_rank = pd.concat([rank, rank.iloc[[0]]], ignore_index=True)
    monkeypatch.setattr(
        prototype.pd, "read_csv",
        lambda path, **kwargs: (duplicate_rank if path.name == "rank_by_year.csv" else lists).copy(),
    )
    with pytest.raises(ValueError, match="Doublon passeport-année"):
        prototype.load_data(prototype.BASE)


def test_snapshot_counts_and_denominators(data):
    snapshot = data["snapshot"]
    assert len(snapshot) == 199
    assert data["destination_universe"] == 227
    assert snapshot.ecart_score.eq(0).all()
    assert snapshot.total.value_counts().to_dict() == {226: 198, 225: 1}
    assert snapshot.set_index("code").loc["IL", "total"] == 225
    assert snapshot[list(prototype.CATEGORIES)].sum(axis=1).eq(snapshot.total).all()
    assert data["composition"].n.sum() == 199


def test_curves_and_bands_do_not_bridge_missing_years(data):
    for fig in (prototype.global_figure(data), prototype.regional_figure(data)):
        for trace in fig.data:
            if trace.error_y.visible:
                assert trace.marker.opacity == 0
            elif trace.fill == "toself":
                assert not set(trace.x) & {2007, 2009}
                assert all(abs(right - left) <= 1 for left, right in zip(trace.x, trace.x[1:]))
            elif trace.mode == "lines+markers":
                by_year = dict(zip(trace.x, trace.y))
                assert by_year[2007] is None
                assert by_year[2009] is None
                assert trace.connectgaps is False
    fig = prototype.regional_figure(data)
    for index in range(1, 8):
        axis = "yaxis" if index == 1 else f"yaxis{index}"
        assert list(fig.layout[axis].range) == [0, 200]


class DocumentInventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.external_resources = []
        self.figures = []
        self.tables = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"script", "img", "iframe"} and attributes.get("src"):
            self.external_resources.append(attributes["src"])
        if tag == "link" and attributes.get("href"):
            self.external_resources.append(attributes["href"])
        if tag == "div" and attributes.get("class") == "plotly-graph-div":
            self.figures.append(attributes["id"])
        if tag == "table":
            self.tables += 1


def test_html_contains_four_figures_tables_and_no_external_resources(data):
    document = prototype.render_html(data, prototype.source_hashes(prototype.BASE))
    inventory = DocumentInventory()
    inventory.feed(document)
    assert inventory.figures == ["plot-monde", "plot-regions", "plot-pays", "plot-conditions"]
    assert inventory.external_resources == []
    assert inventory.tables == 8
    assert document.count("plotly.js v") == 1
    assert "connect-src 'none'" in document
    assert 'lang="fr"' in document
