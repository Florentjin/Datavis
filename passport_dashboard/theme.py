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
MUTED_COLOR = "#4A5568"
GRID_COLOR = "#EDF1F5"
CONTEXT_COLOR = "#B8C2CE"
HIGHLIGHT_COLOR = "#2166AC"
ACCENT_COLOR = "#B35806"
FONT_FAMILY = "Segoe UI, Arial, sans-serif"

# Typographie pour un vidéoprojecteur : rien sous 16 px, valeurs clés à 18 px et plus.
BASE_FONT_SIZE = 20
TITLE_SIZE = 28
SUBTITLE_SIZE = 19
TICK_SIZE = 19
LABEL_SIZE = 19
NOTE_SIZE = 17
MIN_TEXT_SIZE = 16
TITLE_LINE_PX = 36
LEGEND_PX = 46
# Hauteur unique : graphique + question + contrôles tiennent dans un écran 1920×1080.
FIGURE_HEIGHT = 780

# Graphiques figés : pas de zoom accidentel ni d'information réservée au survol.
STATIC_CONFIG = {"staticPlot": True, "displayModeBar": False, "responsive": True}


def title_text(message: str, subtitle: str) -> str:
    """Titre-message en gras et sous-titre de lecture, coupés pour tenir à l'écran."""
    head = "<br>".join(textwrap.wrap(message, 92))
    sub = "<br>".join(textwrap.wrap(subtitle, 140))
    return f"<b>{head}</b><br><span style='font-size:{SUBTITLE_SIZE}px;color:{MUTED_COLOR}'>{sub}</span>"


def title_lines(figure: go.Figure) -> int:
    return (figure.layout.title.text or "").count("<br>") + 1


def apply_theme(figure: go.Figure, *, height: int = FIGURE_HEIGHT, legend: bool = False,
                top_extra: int = 0) -> go.Figure:
    """Applique la charte sans écraser les marges latérales choisies par le graphique.

    La hauteur totale est fixe ; la marge haute est calculée à partir du nombre de
    lignes du titre (et de la légende) pour qu'ils ne chevauchent jamais le tracé.
    """
    margin = {"l": 20, "r": 30, "b": 70}
    current = figure.layout.margin
    margin.update({side: getattr(current, side) for side in margin if getattr(current, side) is not None})
    lines = title_lines(figure)
    margin["t"] = 40 + lines * TITLE_LINE_PX + (LEGEND_PX if legend else 0) + top_extra
    # Plotly centre les titres multilignes : on fixe donc leur centre en pixels.
    center = 12 + lines * TITLE_LINE_PX / 2
    figure.update_layout(
        template="plotly_white",
        height=height,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font={"family": FONT_FAMILY, "size": BASE_FONT_SIZE, "color": TEXT_COLOR},
        title={"x": 0.01, "xanchor": "left", "y": 1 - center / height, "yref": "container",
               "yanchor": "middle", "font": {"size": TITLE_SIZE}},
        margin=margin,
        hovermode=False,
        showlegend=legend,
        legend={
            "title": {"text": ""},
            "orientation": "h",
            "x": 0,
            "y": 1.0,
            "xanchor": "left",
            "yanchor": "bottom",
            "font": {"size": LABEL_SIZE},
            "bgcolor": "rgba(255,255,255,0)",
            "traceorder": "normal",
            "itemwidth": 40,
        },
    )
    axis = {"gridcolor": GRID_COLOR, "zeroline": False, "showline": False, "automargin": True,
            "tickfont": {"size": TICK_SIZE, "color": MUTED_COLOR}, "title_font": {"size": TICK_SIZE, "color": MUTED_COLOR}}
    figure.update_xaxes(**axis)
    figure.update_yaxes(**axis)
    return figure
