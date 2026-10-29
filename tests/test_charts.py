from pathlib import Path

import pytest

from passport_dashboard.data import load_access, load_rank
from passport_dashboard.questions import QUESTIONS, default_figures
from passport_dashboard.theme import FIGURE_HEIGHT, MIN_TEXT_SIZE, REGIME_LABELS, STATIC_CONFIG, TITLE_LINE_PX

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def figures():
    rank = load_rank(ROOT / "rank_by_year.csv")
    access = load_access(ROOT / "country_lists.csv")
    return default_figures(rank, access)


def test_one_figure_per_question(figures):
    assert list(figures) == [question.key for question in QUESTIONS]


@pytest.mark.parametrize("key", [question.key for question in QUESTIONS])
def test_figures_are_readable_without_hover(figures, key):
    figure, message = figures[key]
    layout = figure.layout
    assert layout.hovermode is False
    assert message.split(" ")[0] in layout.title.text
    assert layout.font.size >= 16
    labelled = bool(layout.annotations) or any(getattr(trace, "text", None) is not None for trace in figure.data)
    assert labelled, "les valeurs clés doivent être écrites sur le graphique"


def test_static_config_disables_interaction():
    assert STATIC_CONFIG["staticPlot"] is True
    assert STATIC_CONFIG["displayModeBar"] is False


def test_entry_modes_go_from_open_to_closed(figures):
    figure, _ = figures["q4"]
    names = [trace.name for trace in figure.data if trace.name]
    assert names == list(REGIME_LABELS.values())


def test_titles_fit_in_margin(figures):
    for figure, _ in figures.values():
        lines = figure.layout.title.text.count("<br>") + 1
        assert figure.layout.margin.t >= 14 + lines * TITLE_LINE_PX


def _sizes(figure):
    for annotation in figure.layout.annotations:
        if annotation.font and annotation.font.size:
            yield annotation.font.size
    for trace in figure.data:
        font = getattr(trace, "textfont", None)
        if font is not None and font.size:
            yield font.size
    for axis in (figure.layout.xaxis, figure.layout.yaxis):
        yield axis.tickfont.size


@pytest.mark.parametrize("key", [question.key for question in QUESTIONS])
def test_text_is_large_enough_for_a_projector(figures, key):
    figure, _ = figures[key]
    assert min(_sizes(figure)) >= MIN_TEXT_SIZE
    assert figure.layout.height == FIGURE_HEIGHT
