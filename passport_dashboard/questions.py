"""Textes du récit : problématique, plan et fiche de chaque question.

Ces textes sont partagés par l'application et par l'export HTML afin que les
deux supports racontent exactement la même histoire.
"""

from dataclasses import dataclass

import pandas as pd

from passport_dashboard import charts, metrics, story

PROBLEM = (
    "Le régime mondial des visas organise-t-il une hiérarchie durable de la mobilité : "
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
    how_to_read: str
    limit: str


QUESTIONS = (
    Question(
        "q1", 1, 1,
        "Comment la puissance des passeports se répartit-elle entre les régions du monde ?",
        "Répartition régionale",
        "Chaque point est un passeport. Plus il est à droite, plus il ouvre de destinations sans "
        "démarche préalable. Le trait noir marque la médiane de la région ; les noms désignent "
        "le passeport le plus faible et le plus fort.",
        "Le score compte des destinations, sans pondérer leur intérêt (population, économie).",
    ),
    Question(
        "q2", 1, 2,
        "L'écart entre passeports forts et faibles s'est-il creusé depuis 2006 ?",
        "Évolution des inégalités",
        "Chaque barre bleue va du 10e centile (P10, les passeports faibles) au 90e centile (P90, les "
        "forts) ; la ligne noire suit la médiane. Une barre plus longue signifie un écart plus grand.",
        "Panel constant des passeports mesurés chaque année ; 2007 et 2009 sont absentes de la source. "
        "L'écart absolu grandit mais le rapport P90/P10 diminue : les faibles progressent aussi.",
    ),
    Question(
        "q3", 1, 3,
        "Quels passeports ont le plus progressé, et lesquels ont stagné ou reculé ?",
        "Gagnants et perdants",
        "Longueur de la barre : destinations gagnées entre les deux années. En haut les plus fortes "
        "progressions, en bas les plus faibles.",
        "Une forte progression part souvent d'un score bas : comparer aussi les scores de départ.",
    ),
    Question(
        "q4", 1, 4,
        "Selon sa région, à quelles formalités un voyageur fait-il face ?",
        "Formalités d'entrée",
        "Chaque barre fait 100 % des relations de la région. Les bleus n'exigent aucune démarche "
        "préalable, les orangés imposent un visa électronique ou classique. À droite : total des bleus.",
        "Photographie 2025 : la source ne donne pas l'historique des régimes.",
    ),
    Question(
        "q5", 2, 5,
        "Les ouvertures sont-elles réciproques ou à sens unique ?",
        "Réciprocité",
        "Pour chaque pays et chaque partenaire : les deux s'ouvrent (bleu foncé), seul mon passeport "
        "entre (bleu clair), seul le sien entre (orange) ou aucun (gris). Le solde compare bleu clair et orange.",
        "Seules les relations renseignées dans les deux sens entre les 199 pays sont comptées.",
    ),
    Question(
        "q6", 2, 6,
        "Les pays qui accueillent le plus ont-ils aussi les passeports les plus puissants ?",
        "Accueillir ou voyager",
        "Horizontal : passeports étrangers accueillis sans démarche. Vertical : destinations ouvertes "
        "à son propre passeport. Les pointillés (médianes) découpent quatre profils.",
        "Une corrélation faible n'exclut pas des logiques régionales : il ne s'agit pas d'un lien causal.",
    ),
    Question(
        "q7", 2, 7,
        "Les régions s'ouvrent-elles davantage à leurs voisins qu'au reste du monde ?",
        "Ouverture entre régions",
        "Ligne : région du passeport ; colonne : région visitée. Chaque case donne la part des "
        "relations sans démarche préalable. Cadre noir (diagonale) : voyages dans sa propre région ; "
        "cadre orange : la relation la plus fermée.",
        "Moyenne de relations pays à pays, non pondérée par la population ni par les flux réels.",
    ),
    Question(
        "q8", 2, 8,
        "Les grands blocs régionaux forment-ils des « clubs » de mobilité ?",
        "Clubs de mobilité",
        "Pour chaque organisation : à droite, l'ouverture entre membres ; à gauche, vers les non-membres. "
        "Plus le trait gris est long, plus l'appartenance au club compte.",
        "La liste des membres (2025) provient des sites officiels des organisations, pas du jeu de données.",
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
        "q3": (charts.biggest_changes(metrics.extremes(changes, 10), changes, first, latest),
               story.q3(changes, first, latest)),
        "q4": (charts.entry_modes(modes), story.q4(modes, "origin")),
        "q5": (charts.reciprocity(mutual), story.q5(mutual)),
        "q6": (charts.hospitality_vs_power(welcome), story.q6(welcome)),
        "q7": (charts.regional_openness(matrix), story.q7(matrix)),
        "q8": (charts.clubs(clubs, world_rate), story.q8(clubs)),
    }
