from pathlib import Path

import pandas as pd
import streamlit as st
from plotly.graph_objects import Figure

from passport_dashboard import charts
from passport_dashboard.data import DataError, access_audit, load_access, load_rank
from passport_dashboard.metrics import (
    comparison,
    comparison_exclusions,
    extremes,
    regional_summary,
    spread,
    timeseries,
)
from passport_dashboard.theme import REGION_LABELS, REGIONS

ROOT = Path(__file__).resolve().parent
DEFAULT_FOCUS = ["SG", "AF", "AE", "US"]
REGIME_LABELS = {
    "visa_free_access": "Sans visa",
    "visa_on_arrival": "Visa à l'arrivée",
    "electronic_travel_authorisation": "Autorisation électronique (ETA)",
    "visa_online": "Visa électronique préalable (e-visa)",
    "visa_required": "Visa requis",
}
TABLE_LABELS = {
    "code": "Code",
    "country": "Pays / territoire",
    "region": "Région",
    "score_start": "Destinations au départ",
    "score_end": "Destinations à l'arrivée",
    "rank_start": "Rang mondial au départ",
    "rank_end": "Rang mondial à l'arrivée",
    "delta": "Variation (destinations)",
    "reason": "Motif d'exclusion",
}
CHART_CONFIG = {"displaylogo": False, "scrollZoom": False}

st.set_page_config(
    page_title="Passeports · Observatoire de la mobilité",
    page_icon="🌐",
    layout="wide",
)
st.markdown(
    """
    <style>
    h1, h2, h3 { font-family: Bahnschrift, "Segoe UI", sans-serif; }
    h1 { letter-spacing: -0.025em; }
    .eyebrow { color:#224878; font-size:0.82rem; font-weight:700;
                letter-spacing:0.12em; margin-bottom:0.4rem; }
    .stMainBlockContainer { max-width:1500px; padding:2rem; }
    @media (max-width:640px) {
        .stMainBlockContainer { padding:1.25rem; }
        h1 { font-size:2rem; }
    }
    [data-testid="stMetricValue"] { font-variant-numeric:tabular-nums; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_sources(rank_stamp: int, access_stamp: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rank = load_rank(ROOT / "rank_by_year.csv")
    access = load_access(ROOT / "country_lists.csv")
    audit = access_audit(rank, access)
    if not audit["matches"].all():
        mismatches = audit.loc[~audit["matches"], "country"].tolist()
        raise DataError(
            "Les listes de visas ne reproduisent pas les scores du dernier millésime : "
            + ", ".join(mismatches)
        )
    return rank, access


def display_table(frame: pd.DataFrame) -> pd.DataFrame:
    display = frame.copy()
    if "region" in display:
        display["region"] = display["region"].map(REGION_LABELS)
    return display.rename(columns=TABLE_LABELS)


def reset_controls() -> None:
    st.session_state["start"] = 2006
    st.session_state["end"] = 2025
    st.session_state["regions"] = list(REGIONS)
    st.session_state["focus"] = DEFAULT_FOCUS.copy()
    st.session_state["metric"] = "score"


def format_number(value: float, digits: int = 1) -> str:
    return f"{value:,.{digits}f}".replace(",", "\u202f").replace(".", ",")


def render_chart(figure: Figure, key: str) -> None:
    figure.update_layout(title_text="")
    st.plotly_chart(figure, use_container_width=True, config=CHART_CONFIG, key=key)


try:
    rank, access = load_sources(
        (ROOT / "rank_by_year.csv").stat().st_mtime_ns,
        (ROOT / "country_lists.csv").stat().st_mtime_ns,
    )
except (DataError, OSError) as error:
    st.error(f"Impossible de charger les données : {error}")
    st.info("Vérifiez les deux CSV placés à côté de app.py, puis rechargez la page.")
    st.stop()

years = sorted(int(year) for year in rank.loc[rank["score"].notna(), "year"].unique())
if len(years) < 2:
    st.error("Deux années avec des scores exploitables sont nécessaires pour comparer.")
    st.stop()

catalogue = rank.drop_duplicates("code").set_index("code")
codes = sorted(catalogue.index, key=lambda code: catalogue.loc[code, "country"])
with st.sidebar:
    st.markdown("### Votre comparaison")
    st.caption("Les contrôles s'appliquent aux quatre vues.")
    st.button("Réinitialiser la comparaison", on_click=reset_controls, use_container_width=True)
    start = st.selectbox("Année de départ", years[:-1], key="start")
    end_options = [year for year in years if year > start]
    if "end" in st.session_state and st.session_state["end"] not in end_options:
        st.session_state["end"] = end_options[-1]
        st.info("L'année d'arrivée a été ajustée pour rester postérieure au départ.")
    end = st.selectbox(
        "Année d'arrivée", end_options, index=len(end_options) - 1, key="end"
    )
    st.caption("2007 et 2009 : aucun score exploitable. Elles apparaissent grisées dans les courbes.")
    regions = st.multiselect(
        "Régions",
        options=list(REGIONS),
        default=list(REGIONS),
        format_func=lambda region: REGION_LABELS[region],
        key="regions",
    )
    focus = st.multiselect(
        "Passeports en focus",
        options=codes,
        default=DEFAULT_FOCUS,
        format_func=lambda code: catalogue.loc[code, "country"],
        max_selections=4,
        key="focus",
        help="Quatre trajectoires maximum pour préserver la lisibilité. Le focus ne réduit pas le panel.",
    )
    st.caption("Les noms des pays et territoires sont ceux du fichier source.")
    st.divider()
    st.markdown("**Accès ≠ classement**")
    st.caption(
        "Le score compte des destinations. Le rang situe un passeport par rapport "
        "aux autres, y compris quand vous filtrez les régions."
    )

st.markdown('<div class="eyebrow">HENLEY PASSPORT INDEX · TIDYTUESDAY</div>', unsafe_allow_html=True)
st.title("Passeports et inégalités de mobilité")
st.markdown(
    "Comment les accès ont-ils évolué et les positions se sont-elles recomposées "
    "**entre les régions et les pays** ?"
)
st.caption(
    "Un observatoire pour les analystes, journalistes de données et décideurs publics. "
    "Données historiques 2006–2025 : ce n'est pas un guide de voyage à jour."
)
with st.expander("Comprendre le score et les limites de la comparaison"):
    st.write(
        "Le score Henley inclut les destinations sans visa, avec visa à l'arrivée et "
        "avec autorisation électronique (ETA), selon la méthodologie du fournisseur. "
        "Il exclut les e-visas nécessitant une approbation préalable."
    )
    st.write(
        "Les scores nuls sont conservés dans la source, mais exclus de l'analyse : "
        "ce sont des anomalies présumées, pas des absences certifiées par Henley. "
        "Aucune interpolation n'est faite. Les comparaisons portent uniquement sur "
        "les passeports ayant un score exploitable aux deux dates."
    )
    st.write(
        "Chaque passeport a le même poids ; les régions suivent le découpage Henley. "
        "Le panel et la couverture historique varient. Le score ne mesure ni les "
        "déplacements réels, ni les coûts, ni toutes les contraintes de mobilité. "
        "Les données seules ne démontrent aucune causalité géopolitique."
    )

if not regions:
    st.info("Aucune région sélectionnée. Choisissez une région pour afficher les comparaisons.")
    st.stop()

try:
    panel = comparison(rank, start, end, regions)
    exclusions = comparison_exclusions(rank, start, end, regions)
except ValueError as error:
    st.error(f"Comparaison impossible : {error}")
    st.stop()

active_focus = [code for code in focus if catalogue.loc[code, "region"] in regions]
outside_focus = [code for code in focus if code not in active_focus]
if outside_focus:
    st.info(
        "Focus hors des régions sélectionnées : "
        + ", ".join(catalogue.loc[code, "country"] for code in outside_focus)
        + ". Ces pays ne sont pas tracés ; la sélection reste conservée."
    )
unavailable_focus = [code for code in active_focus if code not in set(panel["code"])]
if unavailable_focus:
    st.warning(
        "Comparaison des scores indisponible pour : "
        + ", ".join(catalogue.loc[code, "country"] for code in unavailable_focus)
        + ". Les observations disponibles restent consultables dans les trajectoires."
    )

st.markdown(
    f"**{start} → {end}** · **{len(panel)} passeports comparables** · "
    f"{len(regions)} régions · {len(exclusions)} passeports exclus de la comparaison"
)
if panel.empty:
    st.warning("Aucun passeport ne dispose de scores exploitables aux deux dates dans ce filtre.")

if not panel.empty:
    dispersion = spread(panel).set_index("period")
    first_gap = float(dispersion.loc["start", "gap"])
    last_gap = float(dispersion.loc["end", "gap"])
    first_ratio = float(dispersion.loc["start", "p90"] / dispersion.loc["start", "p10"])
    last_ratio = float(dispersion.loc["end", "p90"] / dispersion.loc["end", "p10"])
    direction = "augmente" if last_gap > first_gap else "diminue" if last_gap < first_gap else "reste stable"
    st.markdown(
        f"**Sur ce panel, l'écart entre les passeports les mieux et les moins bien "
        f"placés {direction}** : de **{format_number(first_gap)}** à "
        f"**{format_number(last_gap)}** destinations d'écart (P90–P10)."
    )
    st.caption(
        f"Autre mesure : le rapport P90/P10 passe de "
        f"{format_number(first_ratio, 2)} à {format_number(last_ratio, 2)}. "
        "Écart absolu et rapport relatif peuvent évoluer dans des directions différentes."
    )

tabs = st.tabs(["Niveaux par région", "Trajectoires", "Départs et arrivées", "Gains et pertes"])
with tabs[0]:
    st.subheader(f"Où en est chaque région, de {start} à {end} ?")
    render_chart(
        charts.regional_medians(panel, start, end),
        key="distribution",
    )
    st.caption(
        "Chaque ligne relie la médiane de départ (point gris) à la médiane d'arrivée "
        "(point coloré) des passeports de la région. La médiane est la valeur du milieu : "
        "la moitié des pays au-dessus, la moitié en dessous. Survolez une ligne pour lire "
        "la variation en destinations et en pourcentage."
    )
    with st.expander("Médianes régionales et effectifs"):
        summary = regional_summary(panel)
        summary = display_table(summary).rename(
            columns={"n": "Passeports", "median_start": f"Médiane {start}", "median_end": f"Médiane {end}"}
        )
        st.dataframe(summary, hide_index=True, use_container_width=True)
        if not panel.empty:
            quantiles = dispersion.reset_index().copy()
            quantiles["period"] = quantiles["period"].map({"start": start, "end": end})
            quantiles["ratio"] = quantiles["p90"] / quantiles["p10"]
            st.markdown("**Dispersion sur le panel affiché**")
            st.dataframe(
                quantiles.rename(columns={
                    "period": "Année", "n": "Passeports", "median": "Médiane",
                    "p10": "P10", "p90": "P90", "gap": "Écart P90–P10", "ratio": "Rapport P90/P10",
                }), hide_index=True, use_container_width=True,
            )

with tabs[1]:
    st.subheader("Comment l'accès des passeports suivis a-t-il évolué ?")
    metric = st.radio(
        "Mesure", ["score", "rank"],
        format_func=lambda value: "Destinations accessibles" if value == "score" else "Rang mondial",
        horizontal=True, key="metric",
    )
    if active_focus:
        series = timeseries(rank, active_focus, start, end)
        render_chart(
            charts.trajectories(series, metric), key="trajectories",
        )
        st.caption(
            "Une couleur par passeport suivi, nommé au bout de sa courbe. "
            "Les années grisées n'ont aucun score exploitable et les trous ne sont "
            "pas interpolés. En mode rang, le classement de départ et d'arrivée est "
            "écrit aux extrémités et le meilleur classement est en haut."
        )
        with st.expander("Valeurs des trajectoires"):
            st.dataframe(
                display_table(series).rename(
                    columns={"year": "Année", "score": "Score analytique", "rank": "Rang mondial"}
                ), hide_index=True, use_container_width=True,
            )
    else:
        st.info("Sélectionnez un passeport en focus appartenant aux régions affichées.")

with tabs[2]:
    st.subheader(f"D'où partent les pays suivis et où arrivent-ils ({start} → {end}) ?")
    if active_focus:
        render_chart(
            charts.country_slopes(panel, start, end, active_focus),
            key="slopes",
        )
        st.caption(
            "Monter signifie un gain de destinations, descendre une perte. "
            "Au milieu de chaque ligne : la variation en destinations, puis la même "
            "en pourcentage du score de départ — un petit score progresse vite en "
            "pourcentage sans rattraper les grands."
        )
    else:
        st.info("Sélectionnez un passeport en focus appartenant aux régions affichées.")

with tabs[3]:
    st.subheader("Qui a le plus gagné, qui a le plus perdu ?")
    extreme_panel = extremes(panel)
    render_chart(
        charts.changes(extreme_panel, start, end),
        key="changes",
    )
    st.caption(
        "Cinq variations les plus faibles et cinq plus fortes, sans doublons. "
        "Bleu : gain ; orange : recul. Une faible progression reste un gain, pas un déclin."
    )

with st.expander("Comparer les valeurs et télécharger les résultats"):
    st.dataframe(display_table(panel), hide_index=True, use_container_width=True)
    st.download_button(
        "Télécharger le panel comparé (CSV)",
        data=display_table(panel).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"passeports_{start}_{end}.csv",
        mime="text/csv",
    )
    st.markdown("**Passeports exclus et raisons**")
    st.dataframe(display_table(exclusions), hide_index=True, use_container_width=True)
    st.caption("Le téléchargement reflète les dates et régions sélectionnées, pas uniquement les pays en focus.")

if active_focus:
    with st.expander("Fiche d'un passeport : accès, rang et régimes de visa"):
        selected = st.selectbox(
            "Passeport de la fiche", active_focus,
            format_func=lambda code: catalogue.loc[code, "country"],
        )
        row = panel.loc[panel["code"] == selected]
        st.markdown(f"**{catalogue.loc[selected, 'country']}**")
        if not row.empty:
            observation = row.iloc[0]
            st.write(
                f"Destinations : {int(observation['score_start'])} → {int(observation['score_end'])} "
                f"({int(observation['delta']):+d}). "
                f"Rang mondial : {int(observation['rank_start'])} → {int(observation['rank_end'])}."
            )
        else:
            st.info("Comparaison initiale/finale indisponible : consultez le motif d'exclusion.")
        selected_access = access.loc[access["code"] == selected]
        counts = selected_access["regime"].value_counts().reindex(REGIME_LABELS, fill_value=0)
        st.dataframe(
            pd.DataFrame(
                {"Régime": [REGIME_LABELS[regime] for regime in counts.index],
                 "Destinations": counts.to_numpy()}
            ), hide_index=True, use_container_width=True,
        )
        st.caption(
            "Instantané des listes cohérent avec les scores 2025, indépendant des dates filtrées. "
            "La date exacte de collecte n'est pas renseignée. Les trois premiers régimes "
            "entrent dans le score Henley ; e-visa et visa requis en sont exclus."
        )
        unknown = sorted(set(access["destination_code"]) - {selected} - set(selected_access["destination_code"]))
        if unknown:
            st.warning(
                "Relations non renseignées (ni accès ni refus déduits) : " + ", ".join(unknown)
            )

with st.expander("Méthodologie, qualité des données et audit de l'IA"):
    st.write(
        f"Source : {len(rank):,} observations annuelles, {rank['code'].nunique()} passeports. "
        f"{int(rank['score'].isna().sum())} scores nuls mis à l'écart par prudence. "
        "Le code NA de la Namibie est conservé. Les CSV bruts ne sont jamais modifiés."
    )
    quality = rank.assign(anomalie=rank["score"].isna()).groupby("year", as_index=False).agg(
        observations=("code", "size"), scores_exclus=("anomalie", "sum")
    )
    st.dataframe(
        quality.rename(columns={"year": "Année", "observations": "Observations", "scores_exclus": "Scores exclus"}),
        hide_index=True, use_container_width=True,
    )
    st.write(
        "Le P90–P10 est calculé par interpolation linéaire des quantiles sur le même panel "
        "aux deux dates. Il mesure une dispersion absolue, sans pondération par la population. "
        "Les scores et les rangs ont des unités et des significations différentes."
    )
    st.write(
        "La planche historique affichait les zéros comme de vrais effondrements et attribuait "
        "au Monténégro un gain fondé sur un score initial non interprétable. Ces comparaisons "
        "ont été corrigées. Le prompt historique n'est pas disponible ; la nouvelle itération "
        "IA et ses choix sont conservés dans le dossier docs."
    )
    st.write(
        "Les raisons politiques, économiques ou diplomatiques de ces trajectoires ne sont "
        "pas établies par ce dataset. La couverture historique et les règles de l'indice "
        "limitent les comparaisons : aucune proportion n'est calculée en appliquant "
        "le nombre actuel de destinations à toutes les années."
    )

st.divider()
st.caption(
    "Sources : [TidyTuesday — 9 septembre 2025]"
    "(https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-09-09) · "
    "[Méthodologie Henley](https://www.henleyglobal.com/passport-index/methodology). "
    "Application descriptive : vérifier les conditions d'entrée auprès des autorités avant tout voyage."
)
