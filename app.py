"""Application Streamlit : la hiérarchie mondiale de la mobilité en 8 questions.

Une page par question, comme des diapositives : chaque graphique est figé
(aucun survol nécessaire) et porte ses valeurs clés pour être lu en projection.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from passport_dashboard import charts, metrics
from passport_dashboard.data import DataError, access_audit, load_access, load_rank
from passport_dashboard.questions import AUDIENCE, METHOD_NOTES, PARTS, PROBLEM, QUESTIONS, default_figures
from passport_dashboard.theme import RECIPROCITY_LABELS, REGIME_LABELS, REGION_LABELS, STATIC_CONFIG

ROOT = Path(__file__).resolve().parent
PAGES = ["accueil", *(question.key for question in QUESTIONS), "synthese"]
BY_KEY = {question.key: question for question in QUESTIONS}
# 5 pays par groupe : 10 barres au total, dans la limite de la mémoire de travail (5 à 9 éléments).
DEFAULT_START, DEFAULT_END, DEFAULT_N = 2006, 2025, 5

# Barre latérale repliée : le graphique occupe toute la largeur de l'écran projeté.
st.set_page_config(page_title="Passeports · Hiérarchie de la mobilité", page_icon="🌐", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    .stMainBlockContainer { max-width: 1800px; padding: 2.4rem 2rem 2rem; }
    [data-testid="stToolbar"] { display: none; }
    h1, h2, h3 { font-family: "Segoe UI", Arial, sans-serif; letter-spacing: -0.01em; }
    .stMainBlockContainer p, .stMainBlockContainer li { font-size: 1.2rem; }
    .stMainBlockContainer h2 { font-size: 2.3rem; padding: 0.1rem 0 0.3rem; }
    [data-testid="stWidgetLabel"] p { font-size: 1.05rem; }
    .eyebrow { color: #2166AC; font-weight: 700; letter-spacing: 0.1em; font-size: 1rem;
               text-transform: uppercase; margin-bottom: 0; }
    .takeaway { border-left: 6px solid #2166AC; background: #F1F6FB; padding: 0.8rem 1rem;
                font-size: 1.4rem; border-radius: 4px; margin: 0.4rem 0 0.8rem; }
    [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
    </style>
    """,
    unsafe_allow_html=True,
)


# Données ------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_sources(rank_stamp: int, access_stamp: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rank = load_rank(ROOT / "rank_by_year.csv")
    access = load_access(ROOT / "country_lists.csv")
    audit = access_audit(rank, access)
    if not audit["matches"].all():
        mismatches = audit.loc[~audit["matches"], "country"].tolist()
        raise DataError(
            "Les listes de visas ne reproduisent pas les scores du dernier millésime : " + ", ".join(mismatches)
        )
    return rank, access


@st.cache_data(show_spinner=False)
def synthesis_messages(rank_stamp: int, access_stamp: int) -> dict[str, str]:
    rank, access = load_sources(rank_stamp, access_stamp)
    return {key: message for key, (_, message) in default_figures(rank, access).items()}


def stamps() -> tuple[int, int]:
    return (ROOT / "rank_by_year.csv").stat().st_mtime_ns, (ROOT / "country_lists.csv").stat().st_mtime_ns


# Navigation ---------------------------------------------------------------------
def page_label(key: str) -> str:
    if key == "accueil":
        return "Accueil"
    if key == "synthese":
        return "Synthèse"
    question = BY_KEY[key]
    return f"Q{question.number} · {question.short}"


def go_to(key: str) -> None:
    st.session_state["page"] = key


def navigation_buttons(key: str) -> None:
    index = PAGES.index(key)
    left, _, right = st.columns([1, 3, 1])
    if index > 0:
        left.button(f"← {page_label(PAGES[index - 1])}", on_click=go_to, args=(PAGES[index - 1],),
                    key=f"prev_{key}", width="stretch")
    if index < len(PAGES) - 1:
        right.button(f"{page_label(PAGES[index + 1])} →", on_click=go_to, args=(PAGES[index + 1],),
                     key=f"next_{key}", type="primary", width="stretch")


def sidebar() -> str:
    st.session_state.setdefault("page", "accueil")
    with st.sidebar:
        st.markdown("### 🌐 Hiérarchie de la mobilité")
        st.caption("Henley Passport Index · 2006–2025")
        return st.radio("Aller à", PAGES, format_func=page_label, key="page")


# Mise en page commune -----------------------------------------------------------
def question_header(key: str) -> None:
    """La question en en-tête ; la réponse est le titre du graphique (dite une seule fois)."""
    question = BY_KEY[key]
    text, previous, following = st.columns([14, 1, 1], vertical_alignment="center")
    text.markdown(f"<div class='eyebrow'>{PARTS[question.part]} · question {question.number}/8</div>",
                  unsafe_allow_html=True)
    text.header(question.question, anchor=False)
    index = PAGES.index(key)
    previous.button("←", on_click=go_to, args=(PAGES[index - 1],), key=f"top_prev_{key}",
                    help=page_label(PAGES[index - 1]), width="stretch")
    following.button("→", on_click=go_to, args=(PAGES[index + 1],), key=f"top_next_{key}",
                     help=page_label(PAGES[index + 1]), type="primary", width="stretch")


def question_footer(key: str, table: pd.DataFrame) -> None:
    question = BY_KEY[key]
    reading, limit = st.columns(2)
    reading.markdown(f"**Comment lire.** {question.how_to_read}")
    limit.markdown(f"**Limite.** {question.limit}")
    with st.expander("Voir les données du graphique"):
        st.dataframe(table, hide_index=True, width="stretch")
    navigation_buttons(key)


def show(figure) -> None:
    st.plotly_chart(figure, width="stretch", config=STATIC_CONFIG)


def labelled(frame: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    table = frame.copy()
    for column in ("region", "origin_region"):
        if column in table:
            table[column] = table[column].map(lambda code: REGION_LABELS.get(code, "Monde"))
    return table[list(columns)].rename(columns=columns).round(1)


# Pages ----------------------------------------------------------------------------
def home(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    st.markdown("<div class='eyebrow'>Projet Dataviz &amp; IA · M2 MIAGE</div>", unsafe_allow_html=True)
    st.title("Passeports : une hiérarchie durable de la mobilité ?")
    st.markdown(f"<div class='takeaway'><b>Problématique.</b> {PROBLEM}</div>", unsafe_allow_html=True)
    st.caption(f"Public visé : {AUDIENCE}")
    years = metrics.valid_years(rank)
    cols = st.columns(4)
    cols[0].metric("Passeports classés", rank["code"].nunique())
    cols[1].metric("Destinations", access["destination_code"].nunique())
    cols[2].metric("Période des scores", f"{years[0]}–{years[-1]}")
    cols[3].metric("Relations pays → destination (2025)", f"{len(access):,}".replace(",", "\u202f"))
    st.subheader("Plan")
    for part, title in PARTS.items():
        st.markdown(f"**{title}**")
        for question in (item for item in QUESTIONS if item.part == part):
            st.markdown(f"- **Q{question.number}.** {question.question}")
    st.caption("Chaque page présente un graphique lisible sans souris : les valeurs clés sont écrites dessus.")
    navigation_buttons("accueil")


def q1(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q1")
    years = metrics.valid_years(rank)
    year = st.select_slider("Année", years, value=years[-1], key="q1_year")
    scores = metrics.scores_for_year(rank, year)
    show(charts.regional_distribution(scores, year))
    table = labelled(scores.sort_values("score", ascending=False),
                     {"country": "Pays", "region": "Région", "score": "Destinations"})
    question_footer("q1", table)


def q2(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q2")
    series = metrics.inequality_over_time(rank)
    show(charts.inequality_trend(series))
    table = series.rename(columns={"year": "Année", "n": "Passeports", "p10": "P10", "median": "Médiane",
                                   "p90": "P90", "gap": "Écart P90 − P10"}).round(1)
    question_footer("q2", table)


def q3(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q3")
    years = metrics.valid_years(rank)
    c1, c2, c3 = st.columns(3)
    start = c1.selectbox("Année de départ", years[:-1], index=years.index(DEFAULT_START), key="q3_start")
    end = c2.selectbox("Année d'arrivée", years[1:], index=years[1:].index(DEFAULT_END), key="q3_end")
    n = c3.slider("Pays affichés par groupe", 5, 15, DEFAULT_N, key="q3_n")
    if start >= end:
        st.warning("L'année de départ doit précéder l'année d'arrivée.")
        navigation_buttons("q3")
        return
    changes = metrics.score_changes(rank, start, end)
    show(charts.biggest_changes(metrics.extremes(changes, n), changes, start, end))
    table = labelled(changes.sort_values("delta", ascending=False), {
        "country": "Pays", "region": "Région", "score_start": f"Score {start}",
        "score_end": f"Score {end}", "delta": "Variation"})
    question_footer("q3", table)


def q4(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q4")
    views = {"origin": "Vu du voyageur (région du passeport)", "destination": "Vu du pays d'accueil (région visitée)"}
    perspective = st.radio("Point de vue", list(views), format_func=views.get, horizontal=True, key="q4_view")
    shares = metrics.entry_modes(access, rank, perspective)
    show(charts.entry_modes(shares, perspective))
    table = labelled(shares, {"region": "Région", **REGIME_LABELS, "open": "Sans démarche préalable"})
    question_footer("q4", table)


def q5(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q5")
    shares = metrics.reciprocity(access, rank)
    show(charts.reciprocity(shares))
    table = labelled(shares, {"region": "Région", **RECIPROCITY_LABELS, "balance": "Solde (pts)",
                              "pairs": "Relations"})
    question_footer("q5", table)


def q6(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q6")
    frame = metrics.hospitality_vs_power(access, rank)
    names = frame.set_index("code")["country"]
    focus = st.multiselect("Pays nommés sur le graphique", list(names.index), default=list(charts.DEFAULT_SCATTER_LABELS),
                           format_func=names.get, key="q6_focus", max_selections=12)
    show(charts.hospitality_vs_power(frame, focus))
    table = labelled(frame.sort_values("welcomed", ascending=False), {
        "country": "Pays", "region": "Région", "welcomed": "Passeports accueillis (sur 198)",
        "score": "Destinations de son passeport"})
    question_footer("q6", table)


def q7(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q7")
    matrix = metrics.regional_openness(access, rank)
    show(charts.regional_openness(matrix))
    table = matrix.rename(index=REGION_LABELS, columns=REGION_LABELS).round(1)
    table = table.rename_axis("Passeport \\ destination").reset_index()
    question_footer("q7", table)


def q8(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    question_header("q8")
    clubs = metrics.club_openness(access, rank)
    world_rate = metrics.bilateral(access, rank)["open"].mean() * 100
    show(charts.clubs(clubs, world_rate))
    table = clubs.rename(columns={"club": "Organisation", "members": "Membres présents", "missing": "Absents des données",
                                  "inside": "Entre membres (%)", "outside": "Vers non-membres (%)",
                                  "gap": "Écart (pts)"}).round(1)
    question_footer("q8", table)
    with st.expander("Composition des clubs utilisée"):
        names = metrics.catalog(rank).set_index("code")["country"]
        for club, members in metrics.CLUBS.items():
            st.markdown(f"**{club}** : " + ", ".join(sorted(names.get(code, code) for code in members)))


def synthesis(rank: pd.DataFrame, access: pd.DataFrame) -> None:
    st.markdown("<div class='eyebrow'>Synthèse</div>", unsafe_allow_html=True)
    st.title("Ce que montrent les huit graphiques")
    st.markdown(f"<div class='takeaway'><b>Problématique.</b> {PROBLEM}</div>", unsafe_allow_html=True)
    messages = synthesis_messages(*stamps())
    for part, title in PARTS.items():
        st.subheader(title)
        for question in (item for item in QUESTIONS if item.part == part):
            st.markdown(f"**Q{question.number} · {question.short}.** {messages[question.key]}")
    st.subheader("Réponse")
    st.markdown(
        "Oui, une hiérarchie durable existe : presque tous les passeports progressent, mais l'écart absolu entre "
        "forts et faibles s'est creusé et suit la géographie (Europe en tête ; Afrique, Asie et Moyen-Orient en "
        "retrait). Elle se lit aussi dans les conditions d'entrée : les relations à sens unique profitent aux "
        "passeports déjà puissants. Accueillir largement ne garantit pas la réciprocité, et la mobilité facile "
        "se joue surtout entre voisins et au sein des blocs régionaux."
    )
    with st.expander("Méthode et limites"):
        for note in METHOD_NOTES:
            st.markdown(f"- {note}")
    navigation_buttons("synthese")


RENDERERS = {"accueil": home, "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6, "q7": q7, "q8": q8,
             "synthese": synthesis}


def main() -> None:
    page = sidebar()
    try:
        rank, access = load_sources(*stamps())
    except (DataError, OSError) as error:
        st.error(f"Impossible de charger les données : {error}")
        st.stop()
    RENDERERS[page](rank, access)


main()
