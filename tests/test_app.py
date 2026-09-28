from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def make_app() -> AppTest:
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()


def test_initial_application_and_rank_toggle():
    app = make_app()
    assert not app.exception
    assert any("183 passeports comparables" in item.value for item in app.markdown)
    assert any("6,56 à 3,98" in item.value for item in app.caption)
    assert len(app.get("plotly_chart")) == 4
    app.radio(key="metric").set_value("rank").run()
    assert not app.exception
    assert app.radio(key="metric").value == "rank"


def test_empty_filter_and_reset():
    app = make_app()
    app.multiselect(key="regions").set_value([]).run()
    assert not app.exception
    assert any("Aucune région sélectionnée" in item.value for item in app.info)
    assert len(app.get("plotly_chart")) == 0
    app.button[0].click().run()
    assert not app.exception
    assert any("183 passeports comparables" in item.value for item in app.markdown)


def test_date_change_and_region_filter():
    app = make_app()
    app.selectbox(key="end").set_value(2008).run()
    app.selectbox(key="start").set_value(2024).run()
    assert not app.exception
    assert app.selectbox(key="end").value == 2025
    app.multiselect(key="regions").set_value(["AFRICA"]).run()
    assert not app.exception
    assert any("54 passeports comparables" in item.value for item in app.markdown)
    assert any("hors des régions" in item.value for item in app.info)


def test_unavailable_baseline_focus_and_no_focus():
    app = make_app()
    app.multiselect(key="focus").set_value(["ME"]).run()
    assert not app.exception
    assert any("Montenegro" in item.value for item in app.warning)
    app.multiselect(key="focus").set_value([]).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2


def test_access_snapshot_discloses_unknown_relationship():
    app = make_app()
    app.multiselect(key="focus").set_value(["IL"]).run()
    assert not app.exception
    assert any("Relations non renseignées" in item.value and "MV" in item.value for item in app.warning)
    assert any("indépendant des dates filtrées" in item.value for item in app.caption)
