"""Shared, local-only visual tokens for the passport dashboard."""

import plotly.graph_objects as go

REGION_LABELS = {
    "ASIA": "Asie",
    "EUROPE": "Europe",
    "AFRICA": "Afrique",
    "CARIBBEAN": "Caraïbes",
    "AMERICAS": "Amériques",
    "MIDDLE EAST": "Moyen-Orient",
    "OCEANIA": "Océanie",
}

REGION_COLORS = {
    "AFRICA": "#0072B2",
    "AMERICAS": "#E69F00",
    "ASIA": "#009E73",
    "CARIBBEAN": "#CC79A7",
    "EUROPE": "#D55E00",
    "MIDDLE EAST": "#56B4E9",
    "OCEANIA": "#666666",
}
REGIONS = tuple(REGION_COLORS)

TEXT_COLOR = "#17233B"
GRID_COLOR = "#DCE3EC"
FONT_FAMILY = "Segoe UI, sans-serif"

# Une couleur par passeport suivi (échelle catégorielle du cours, daltonisme-safe).
COUNTRY_COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7")
# Échelle divergente du cours : bleu/orange plutôt que rouge/vert.
GAIN_COLOR = "#0072B2"
LOSS_COLOR = "#E69F00"
START_DOT_COLOR = "#8491A5"


def apply_theme(figure: go.Figure) -> go.Figure:
    """Style in place without global state or rewriting existing title markup."""
    figure.update_layout(
        template="plotly_white",
        autosize=True,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": FONT_FAMILY, "size": 14, "color": TEXT_COLOR},
        title={"x": 0, "xanchor": "left", "font": {"size": 19}},
        margin={"l": 35, "r": 30, "t": 85, "b": 85},
        colorway=list(REGION_COLORS.values()),
        legend={
            "title": {"text": ""},
            "orientation": "h",
            "x": 0,
            "y": -0.20,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 12},
            "groupclick": "toggleitem",
            "bgcolor": "rgba(255,255,255,0)",
        },
        hoverlabel={
            "bgcolor": "#FFFFFF",
            "bordercolor": GRID_COLOR,
            "font": {"family": FONT_FAMILY, "size": 13, "color": TEXT_COLOR},
        },
    )
    figure.update_xaxes(
        gridcolor=GRID_COLOR,
        gridwidth=1,
        showline=False,
        zeroline=False,
        automargin=True,
        tickfont={"size": 12},
        title_font={"size": 13},
    )
    figure.update_yaxes(
        gridcolor=GRID_COLOR,
        gridwidth=1,
        showline=False,
        zeroline=False,
        automargin=True,
        tickfont={"size": 12},
        title_font={"size": 13},
    )
    return figure
