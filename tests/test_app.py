from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
PAGES = ["accueil", "q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "synthese"]


def run_page(page: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.session_state["page"] = page
    return app.run()


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders(page):
    app = run_page(page)
    assert not app.exception
    assert not app.error


@pytest.mark.parametrize("page", PAGES[1:9])
def test_question_pages_show_one_static_chart(page):
    app = run_page(page)
    charts = app.get("plotly_chart")
    assert len(charts) == 1
    assert '"staticPlot":true' in charts[0].proto.config.replace(" ", "")


def test_next_button_moves_forward():
    app = run_page("q1")
    next(button for button in app.button if button.key == "next_q1").click().run()
    assert app.session_state["page"] == "q2"


def test_invalid_period_warns_instead_of_crashing():
    app = run_page("q3")
    app.selectbox(key="q3_start").set_value(2024)
    app.selectbox(key="q3_end").set_value(2008).run()
    assert not app.exception
    assert app.warning


def test_destination_view_renders():
    app = run_page("q4")
    app.radio(key="q4_view").set_value("destination").run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
