"""Indicateurs des huit questions, calculés sans imputer ni modifier la source."""

from __future__ import annotations

from numbers import Integral

import pandas as pd

from passport_dashboard.data import ACCESS_REGIMES, INCLUDED_REGIMES, DataError

__all__ = [
    "CLUBS",
    "WORLD",
    "catalog",
    "valid_years",
    "scores_for_year",
    "inequality_over_time",
    "score_changes",
    "extremes",
    "entry_modes",
    "bilateral",
    "reciprocity",
    "hospitality_vs_power",
    "regional_openness",
    "club_openness",
]

WORLD = "WORLD"

# Membres en 2025, d'après les sites officiels des organisations (source externe au dataset).
CLUBS = {
    "Union européenne": (
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE",
        "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    ),
    "CEDEAO (Afrique de l'Ouest)": (
        "BJ", "CV", "CI", "GM", "GH", "GN", "GW", "LR", "NG", "SN", "SL", "TG",
    ),
    "Communauté d'Afrique de l'Est": ("BI", "CD", "KE", "RW", "SO", "SS", "TZ", "UG"),
    "Mercosur": ("AR", "BO", "BR", "PY", "UY"),
    "CARICOM (Caraïbes)": (
        "AG", "BS", "BB", "BZ", "DM", "GD", "GY", "HT", "JM", "KN", "LC", "VC", "SR", "TT",
    ),
    "ASEAN (Asie du Sud-Est)": ("BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "VN"),
    "Conseil de coopération du Golfe": ("AE", "BH", "KW", "OM", "QA", "SA"),
}


def catalog(rank: pd.DataFrame) -> pd.DataFrame:
    """Nom et région les plus récents de chaque passeport."""
    return (
        rank.sort_values(["year", "code"], kind="stable")
        .drop_duplicates("code", keep="last")[["code", "country", "region"]]
        .reset_index(drop=True)
    )


def valid_years(rank: pd.DataFrame) -> list[int]:
    return sorted(int(year) for year in rank.loc[rank["score"].notna(), "year"].unique())


def _check_year(rank: pd.DataFrame, year: int) -> None:
    if not isinstance(year, Integral) or isinstance(year, bool):
        raise DataError("L'année doit être un entier.")
    if year not in valid_years(rank):
        raise DataError(f"Aucun score exploitable en {year}.")


# Q1 ---------------------------------------------------------------------------
def scores_for_year(rank: pd.DataFrame, year: int) -> pd.DataFrame:
    """Scores exploitables d'une année (les zéros source sont déjà mis à l'écart)."""
    _check_year(rank, year)
    frame = rank.loc[rank["year"].eq(year) & rank["score"].notna(), ["code", "country", "region", "score"]]
    frame = frame.astype({"score": "float64"})
    return frame.sort_values(["region", "score", "code"], kind="stable").reset_index(drop=True)


# Q2 ---------------------------------------------------------------------------
def inequality_over_time(rank: pd.DataFrame) -> pd.DataFrame:
    """P10, médiane et P90 par an sur un panel constant de passeports.

    Le panel ne retient que les passeports ayant un score exploitable à chaque
    année mesurée : la courbe ne bouge donc pas parce que des pays entrent ou
    sortent de l'échantillon. Les années sans aucun score restent vides.
    """
    years = valid_years(rank)
    if not years:
        raise DataError("Aucune année ne contient de score exploitable.")
    wide = rank.pivot(index="code", columns="year", values="score").reindex(columns=years)
    panel = wide.dropna().astype("float64")
    if panel.empty:
        raise DataError("Aucun passeport n'a de score exploitable chaque année.")
    rows = []
    for year in range(min(years), max(years) + 1):
        if year in panel.columns:
            p10, median, p90 = panel[year].quantile([0.1, 0.5, 0.9])
            rows.append((year, len(panel), p10, median, p90, p90 - p10))
        else:
            rows.append((year, len(panel), None, None, None, None))
    return pd.DataFrame(rows, columns=["year", "n", "p10", "median", "p90", "gap"]).astype(
        {"year": "int64", "n": "int64", "p10": "float64", "median": "float64", "p90": "float64", "gap": "float64"}
    )


# Q3 ---------------------------------------------------------------------------
def score_changes(rank: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """Variation des destinations pour les passeports exploitables aux deux dates."""
    _check_year(rank, start)
    _check_year(rank, end)
    if start >= end:
        raise DataError("L'année de départ doit précéder l'année d'arrivée.")
    pivot = rank.pivot(index="code", columns="year", values="score")[[start, end]].dropna()
    result = catalog(rank).merge(
        pivot.rename(columns={start: "score_start", end: "score_end"}).reset_index(), on="code"
    )
    result = result.astype({"score_start": "float64", "score_end": "float64"})
    result["delta"] = result["score_end"] - result["score_start"]
    return result.sort_values(["delta", "country"], kind="stable").reset_index(drop=True)


def extremes(changes: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Les n plus fortes et les n plus faibles variations, sans doublon."""
    if not isinstance(n, Integral) or isinstance(n, bool) or n < 1:
        raise DataError("n doit être un entier strictement positif.")
    ordered = changes.sort_values(["delta", "country"], kind="stable")
    n = min(n, len(ordered) // 2)
    low = ordered.head(n).assign(group="low")
    high = ordered.tail(n).assign(group="high")
    return pd.concat([high, low]).reset_index(drop=True)


# Q4 ---------------------------------------------------------------------------
def entry_modes(access: pd.DataFrame, rank: pd.DataFrame, perspective: str = "origin") -> pd.DataFrame:
    """Part de chaque régime d'entrée, par région et pour le monde.

    ``origin`` : vu du voyageur (région du passeport, toutes destinations).
    ``destination`` : vu du pays d'accueil (région de destination, visiteurs
    des 199 passeports).
    """
    if perspective not in ("origin", "destination"):
        raise DataError("Perspective inconnue : « origin » ou « destination » attendu.")
    regions = catalog(rank).set_index("code")["region"]
    frame = access.assign(
        region=(access["code"] if perspective == "origin" else access["destination_code"]).map(regions)
    ).dropna(subset=["region"])
    world = frame.assign(region=WORLD)
    shares = pd.concat([frame, world]).groupby("region")["regime"].value_counts(normalize=True)
    shares = shares.unstack(fill_value=0.0).reindex(columns=list(ACCESS_REGIMES), fill_value=0.0)
    shares = shares * 100
    shares["open"] = shares[sorted(INCLUDED_REGIMES)].sum(axis=1)
    return shares.reset_index().astype({"region": "string"})


# Q5, Q7, Q8 : relations entre les 199 pays dotés d'un passeport classé ----------
def bilateral(access: pd.DataFrame, rank: pd.DataFrame) -> pd.DataFrame:
    """Relations origine → destination entre pays présents des deux côtés."""
    regions = catalog(rank).set_index("code")["region"]
    frame = access.loc[access["destination_code"].isin(regions.index)].copy()
    frame["origin_region"] = frame["code"].map(regions)
    frame["destination_region"] = frame["destination_code"].map(regions)
    frame["open"] = frame["regime"].isin(INCLUDED_REGIMES)
    return frame.dropna(subset=["origin_region"]).reset_index(drop=True)


def reciprocity(access: pd.DataFrame, rank: pd.DataFrame) -> pd.DataFrame:
    """Classe chaque relation selon l'accès dans les deux sens.

    Pour un pays A et un partenaire B : « en sa faveur » signifie que le
    passeport de A entre librement chez B alors que B n'entre pas librement
    chez A. Seuls les couples renseignés dans les deux sens sont comptés.
    """
    links = bilateral(access, rank)
    back = links.set_index(["destination_code", "code"])["open"]
    back.index.names = ["code", "destination_code"]
    pairs = links.join(back.rename("open_back"), on=["code", "destination_code"], how="inner")
    out, back_open = pairs["open"].astype(bool), pairs["open_back"].astype(bool)
    category = pd.Series("mutual_closed", index=pairs.index)
    category[out & back_open] = "mutual_open"
    category[out & ~back_open] = "favourable"
    category[~out & back_open] = "unfavourable"
    pairs = pairs.assign(category=category)
    order = ["mutual_open", "favourable", "unfavourable", "mutual_closed"]
    world = pairs.assign(origin_region=WORLD)
    shares = pd.concat([pairs, world]).groupby("origin_region")["category"].value_counts(normalize=True)
    shares = shares.unstack(fill_value=0.0).reindex(columns=order, fill_value=0.0) * 100
    shares["balance"] = shares["favourable"] - shares["unfavourable"]
    shares["pairs"] = pd.concat([pairs, world]).groupby("origin_region").size()
    return shares.reset_index().rename(columns={"origin_region": "region"}).astype({"region": "string"})


def hospitality_vs_power(access: pd.DataFrame, rank: pd.DataFrame) -> pd.DataFrame:
    """Passeports accueillis librement (sur 198) et force du passeport du pays."""
    links = bilateral(access, rank)
    welcomed = links.groupby("destination_code")["open"].sum().rename("welcomed")
    latest = int(rank["year"].max())
    power = rank.loc[rank["year"].eq(latest), ["code", "score"]].set_index("code")["score"]
    frame = catalog(rank).set_index("code").join(welcomed).join(power.rename("score"))
    frame = frame.dropna(subset=["welcomed", "score"]).astype({"welcomed": "int64", "score": "float64"})
    return frame.reset_index().sort_values(["country", "code"], kind="stable").reset_index(drop=True)


def regional_openness(access: pd.DataFrame, rank: pd.DataFrame) -> pd.DataFrame:
    """Matrice région du passeport × région de destination : % d'accès sans démarche préalable."""
    links = bilateral(access, rank)
    matrix = links.pivot_table(
        index="origin_region", columns="destination_region", values="open", aggfunc="mean"
    )
    return matrix.astype("float64") * 100


def club_openness(access: pd.DataFrame, rank: pd.DataFrame, clubs: dict | None = None) -> pd.DataFrame:
    """Taux d'accès libre des membres d'un club : entre eux, puis vers les non-membres."""
    clubs = CLUBS if clubs is None else clubs
    links = bilateral(access, rank)
    known = set(links["code"])
    rows = []
    for name, members in clubs.items():
        present = sorted(set(members) & known)
        missing = sorted(set(members) - known)
        if len(present) < 2:
            raise DataError(f"Club « {name} » : moins de deux membres présents dans les données.")
        own = links.loc[links["code"].isin(present)]
        inside = own.loc[own["destination_code"].isin(present), "open"].mean() * 100
        outside = own.loc[~own["destination_code"].isin(present), "open"].mean() * 100
        rows.append((name, len(present), ", ".join(missing), inside, outside))
    result = pd.DataFrame(rows, columns=["club", "members", "missing", "inside", "outside"])
    result["gap"] = result["inside"] - result["outside"]
    return result.sort_values("gap", ascending=False, kind="stable").reset_index(drop=True)
