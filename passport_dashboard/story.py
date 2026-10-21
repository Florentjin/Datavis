"""Messages clés calculés à partir des données : titres des graphiques et synthèse."""

from __future__ import annotations

import pandas as pd

from passport_dashboard.metrics import WORLD
from passport_dashboard.theme import REGION_LABELS

NNBSP = "\u202f"

# Formes grammaticales des régions : (de …, en …, à …, le …).
_FORMS = {
    "AFRICA": ("d'Afrique", "en Afrique", "à l'Afrique", "l'Afrique"),
    "AMERICAS": ("des Amériques", "dans les Amériques", "aux Amériques", "les Amériques"),
    "ASIA": ("d'Asie", "en Asie", "à l'Asie", "l'Asie"),
    "CARIBBEAN": ("des Caraïbes", "dans les Caraïbes", "aux Caraïbes", "les Caraïbes"),
    "EUROPE": ("d'Europe", "en Europe", "à l'Europe", "l'Europe"),
    "MIDDLE EAST": ("du Moyen-Orient", "au Moyen-Orient", "au Moyen-Orient", "le Moyen-Orient"),
    "OCEANIA": ("d'Océanie", "en Océanie", "à l'Océanie", "l'Océanie"),
}


def fr(value: float, digits: int = 0) -> str:
    """Nombre au format français : virgule décimale, espace fine pour les milliers."""
    text = f"{value:,.{digits}f}".replace(",", NNBSP).replace(".", ",")
    if text.lstrip("-").strip("0,") == "":
        text = text.lstrip("-")
    return text.replace("-", "−")


def signed(value: float) -> str:
    return ("+" if value > 0 else "") + fr(value)


def pct(value: float) -> str:
    return f"{fr(value)}{NNBSP}%"


def region(code: str) -> str:
    return "Monde" if code == WORLD else REGION_LABELS.get(code, code)


def _de(code: str) -> str:
    return _FORMS[code][0]


def _en(code: str) -> str:
    return _FORMS[code][1]


def _a(code: str) -> str:
    return _FORMS[code][2]


def _le(code: str) -> str:
    return _FORMS[code][3]


def q1(scores: pd.DataFrame, year: int) -> str:
    medians = scores.groupby("region")["score"].median().sort_values()
    low = medians.iloc[0]
    return (
        f"En {year}, le passeport médian {_de(medians.index[-1])} ouvre {fr(medians.iloc[-1])} destinations, "
        f"contre {fr(low, 1 if low % 1 else 0)} {_en(medians.index[0])}"
    )


def q2(series: pd.DataFrame) -> str:
    measured = series.dropna(subset=["gap"])
    first, last = measured.iloc[0], measured.iloc[-1]
    verb = "s'est creusé" if last["gap"] > first["gap"] else "s'est réduit"
    return (
        f"L'écart entre passeports forts et faibles {verb} : "
        f"de {fr(first['gap'])} à {fr(last['gap'])} destinations ({int(first['year'])}–{int(last['year'])})"
    )


def q3(changes: pd.DataFrame, start: int, end: int) -> str:
    losers = changes.loc[changes["delta"] < 0]
    best = changes.sort_values("delta").iloc[-1]
    if losers.empty:
        loss = "aucun ne recule"
    elif len(losers) == 1:
        row = losers.iloc[0]
        loss = f"un seul recule : {row['country']} ({signed(row['delta'])})"
    else:
        loss = f"{len(losers)} reculent"
    return (
        f"{start}–{end} : {len(changes) - len(losers)} passeports sur {len(changes)} progressent, {loss}. "
        f"Record : {best['country']} ({signed(best['delta'])})"
    )


def q4(shares: pd.DataFrame, perspective: str) -> str:
    regional = shares.loc[shares["region"] != WORLD].sort_values("open")
    low, high = regional.iloc[0], regional.iloc[-1]
    if perspective == "origin":
        return (
            f"Sans démarche préalable, un passeport {_de(high['region'])} entre dans {pct(high['open'])} "
            f"des destinations, un passeport {_de(low['region'])} dans {pct(low['open'])}"
        )
    return (
        f"Les pays {_de(high['region'])} accueillent {pct(high['open'])} des passeports sans démarche "
        f"préalable, ceux {_de(low['region'])} {pct(low['open'])}"
    )


def q5(shares: pd.DataFrame) -> str:
    regional = shares.loc[shares["region"] != WORLD].sort_values("balance")
    worst, best = regional.iloc[0], regional.iloc[-1]
    return (
        f"Les relations à sens unique profitent {_a(best['region'])} "
        f"({pct(best['favourable'])} en sa faveur, {pct(best['unfavourable'])} en sa défaveur) "
        f"et pèsent sur {_le(worst['region'])} ({pct(worst['favourable'])} contre {pct(worst['unfavourable'])})"
    )


def q6(frame: pd.DataFrame) -> str:
    correlation = frame["welcomed"].corr(frame["score"])
    strength = "quasi nul" if abs(correlation) < 0.3 else "modéré" if abs(correlation) < 0.6 else "fort"
    return (
        "Accueillir largement ne garantit pas un passeport puissant : "
        f"lien {strength} (r\u00a0=\u00a0{fr(correlation, 2)})"
    )


def q7(matrix: pd.DataFrame) -> str:
    inside_first = sum(
        matrix.loc[code, code] > matrix.loc[code].drop(code).mean() for code in matrix.index
    )
    stacked = matrix.stack()
    origin, destination = stacked.idxmin()
    return (
        f"Dans {inside_first} régions sur {len(matrix)}, on circule plus librement dans sa région qu'ailleurs. "
        f"Verrou le plus fort : {region(origin)} → {region(destination)} ({pct(stacked.min())})"
    )


def q8(clubs: pd.DataFrame) -> str:
    top = clubs.iloc[0]
    opener = sum(clubs["inside"] > clubs["outside"])
    return (
        f"{opener} clubs régionaux sur {len(clubs)} s'ouvrent davantage entre membres. "
        f"Écart maximal : {top['club'].split(' (')[0]} ({signed(top['gap'])} points)"
    )
