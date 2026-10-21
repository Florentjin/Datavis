"""Charte visuelle pensée pour la projection : tout se lit sans survol."""

import textwrap

import plotly.graph_objects as go

REGION_LABELS = {
    "AFRICA": "Afrique",
    "AMERICAS": "Amériques",
    "ASIA": "Asie",
    "CARIBBEAN": "Caraïbes",
    "EUROPE": "Europe",
    "MIDDLE EAST": "Moyen-Orient",
    "OCEANIA": "Océanie",
}

# Palette Okabe-Ito : distinguable par les principales formes de daltonisme.
REGION_COLORS = {
    "AFRICA": "#0072B2",
    "AMERICAS": "#E69F00",
    "ASIA": "#009E73",
    "CARIBBEAN": "#CC79A7",
    "EUROPE": "#D55E00",
    "MIDDLE EAST": "#56B4E9",
    "OCEANIA": "#6B6B6B",
}
REGIONS = tuple(REGION_COLORS)

# Du plus ouvert (bleu foncé) au plus fermé (orange foncé) : divergente bleu-orange.
REGIME_LABELS = {
    "visa_free_access": "Sans visa",
    "visa_on_arrival": "Visa à l'arrivée",
    "electronic_travel_authorisation": "Autorisation électronique (ETA)",
    "visa_online": "E-visa (accord préalable)",
    "visa_required": "Visa classique",
}
REGIME_COLORS = {
    "visa_free_access": "#08306B",
    "visa_on_arrival": "#2171B5",
    "electronic_travel_authorisation": "#9ECAE1",
    "visa_online": "#FDB863",
    "visa_required": "#B35806",
}

RECIPROCITY_LABELS = {
    "mutual_open": "Ouverture mutuelle",
    "favourable": "À sens unique, en sa faveur",
    "unfavourable": "À sens unique, en sa défaveur",
    "mutual_closed": "Fermeture mutuelle",
}
RECIPROCITY_COLORS = {
    "mutual_open": "#2166AC",
    "favourable": "#92C5DE",
    "unfavourable": "#E08214",
    "mutual_closed": "#BDBDBD",
}

TEXT_COLOR = "#17233B"
MUTED_COLOR = "#5B6578"
GRID_COLOR = "#E3E8EF"
ACCENT_COLOR = "#B35806"
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
BASE_FONT_SIZE = 16
TITLE_LINE_PX = 27

# Graphiques figés : pas de zoom accidentel ni d'information réservée au survol.
STATIC_CONFIG = {"staticPlot": True, "displayModeBar": False, "responsive": True}


def title_text(message: str, subtitle: str) -> str:
    """Titre-message en gras et sous-titre de lecture, coupés pour tenir à l'écran."""
    head = "<br>".join(textwrap.wrap(message, 78))
    sub = "<br>".join(textwrap.wrap(subtitle, 120))
    return f"<b>{head}</b><br><span style='font-size:15px;color:{MUTED_COLOR}'>{sub}</span>"


def apply_theme(figure: go.Figure, *, height: int = 620) -> go.Figure:
    """Applique la charte sans écraser les marges choisies par le graphique.

    La marge haute grandit avec le nombre de lignes du titre pour qu'il ne
    chevauche jamais la légende ni la zone de tracé.
    """
    margin = {"l": 20, "r": 30, "t": 110, "b": 60}
    current = figure.layout.margin
    margin.update({side: getattr(current, side) for side in margin if getattr(current, side) is not None})
    lines = (figure.layout.title.text or "").count("<br>") + 1
    extra = TITLE_LINE_PX * max(0, lines - 2)
    margin["t"] += extra
    total = height + extra
    # Plotly centre les titres multilignes : on fixe donc leur centre en pixels.
    center = 14 + lines * TITLE_LINE_PX / 2
    figure.update_layout(
        template="plotly_white",
        height=total,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": FONT_FAMILY, "size": BASE_FONT_SIZE, "color": TEXT_COLOR},
        title={"x": 0.01, "xanchor": "left", "y": 1 - center / total, "yref": "container",
               "yanchor": "middle", "font": {"size": 21}},
        margin=margin,
        hovermode=False,
        legend={
            "title": {"text": ""},
            "orientation": "h",
            "x": 0,
            "y": 1.0,
            "xanchor": "left",
            "yanchor": "bottom",
            "font": {"size": 15},
            "bgcolor": "rgba(255,255,255,0)",
            "traceorder": "normal",
        },
    )
    figure.update_xaxes(
        gridcolor=GRID_COLOR, zeroline=False, showline=False, automargin=True,
        tickfont={"size": 15}, title_font={"size": 16},
    )
    figure.update_yaxes(
        gridcolor=GRID_COLOR, zeroline=False, showline=False, automargin=True,
        tickfont={"size": 15}, title_font={"size": 16},
    )
    return figure
