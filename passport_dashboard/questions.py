"""Textes du récit : problématique, plan et fiche de chaque question.

Ces textes sont partagés par l'application et par l'export HTML afin que les
deux supports racontent exactement la même histoire.
"""

from dataclasses import dataclass

import pandas as pd

from passport_dashboard import charts, metrics, story

PROBLEM = (
    "Le régime mondial des visas organise-t-il une hiérarchie de la mobilité : "
    "qui peut circuler, qui accueille, et selon quelles réciprocités ?"
)
AUDIENCE = "Analystes, journalistes et décideurs publics intéressés par les inégalités de mobilité."

PARTS = {
    1: "Partie 1 · Qui peut voyager ?",
    2: "Partie 2 · Qui accueille, et à quelles conditions ?",
}


@dataclass(frozen=True)
class Question:
    key: str
    part: int
    number: int
    question: str
    short: str


QUESTIONS = (
    Question(
        "q1", 1, 1,
        "Comment la puissance des passeports se répartit-elle entre les régions du monde ?",
        "Répartition régionale",
    ),
    Question(
        "q2", 1, 2,
        "L'écart entre passeports forts et faibles s'est-il creusé depuis 2006 ?",
        "Évolution des inégalités",
    ),
    Question(
        "q3", 1, 3,
        "Quels passeports ont le plus progressé, et lesquels ont stagné ou reculé ?",
        "Gagnants et perdants",
    ),
    Question(
        "q4", 1, 4,
        "Selon sa région, à quelles formalités un voyageur fait-il face ?",
        "Formalités d'entrée",
    ),
    Question(
        "q5", 2, 5,
        "Les ouvertures sont-elles réciproques ou à sens unique ?",
        "Réciprocité",
    ),
    Question(
        "q6", 2, 6,
        "Les pays qui accueillent le plus ont-ils aussi les passeports les plus puissants ?",
        "Accueillir ou voyager",
    ),
    Question(
        "q7", 2, 7,
        "Les régions s'ouvrent-elles davantage à leurs voisins qu'au reste du monde ?",
        "Ouverture entre régions",
    ),
    Question(
        "q8", 2, 8,
        "Les grands blocs régionaux forment-ils des « clubs » de mobilité ?",
        "Clubs de mobilité",
    ),
)

METHOD_NOTES = (
    "Source : Henley Passport Index (TidyTuesday 2025-09-09), fichiers rank_by_year.csv et country_lists.csv.",
    "« Sans démarche préalable » = sans visa, visa à l'arrivée ou autorisation électronique (ETA) ; "
    "le visa électronique (e-visa) et le visa classique sont des démarches préalables.",
    "Les scores nuls de la source sont traités comme manquants ; 2007 et 2009 ne sont pas mesurées.",
    "Les régimes d'entrée (Q4 à Q8) sont une photographie 2025 ; seuls les scores (Q1 à Q3) ont un historique.",
    "Les relations (Q5 à Q8) sont limitées aux 199 pays qui disposent d'un passeport classé.",
    "Les résultats décrivent des écarts ; ils ne prouvent aucune causalité.",
)


def default_figures(rank: pd.DataFrame, access: pd.DataFrame) -> dict[str, tuple[object, str]]:
    """Les huit graphiques et messages avec les réglages par défaut de l'oral."""
    latest = int(rank["year"].max())
    first = metrics.valid_years(rank)[0]
    scores = metrics.scores_for_year(rank, latest)
    series = metrics.inequality_over_time(rank)
    changes = metrics.score_changes(rank, first, latest)
    modes = metrics.entry_modes(access, rank)
    mutual = metrics.reciprocity(access, rank)
    welcome = metrics.hospitality_vs_power(access, rank)
    matrix = metrics.regional_openness(access, rank)
    clubs = metrics.club_openness(access, rank)
    world_rate = metrics.bilateral(access, rank)["open"].mean() * 100
    return {
        "q1": (charts.regional_distribution(scores, latest), story.q1(scores, latest)),
        "q2": (charts.inequality_trend(series), story.q2(series)),
        "q3": (charts.biggest_changes(metrics.extremes(changes, 5), changes, first, latest),
               story.q3(changes, first, latest)),
        "q4": (charts.entry_modes(modes), story.q4(modes, "origin")),
        "q5": (charts.reciprocity(mutual), story.q5(mutual)),
        "q6": (charts.hospitality_vs_power(welcome), story.q6(welcome)),
        "q7": (charts.regional_openness(matrix), story.q7(matrix)),
        "q8": (charts.clubs(clubs, world_rate), story.q8(clubs)),
    }
