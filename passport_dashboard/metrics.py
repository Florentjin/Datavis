"""Indicateurs descriptifs sur un panel constant, sans reclassement des passeports."""

from __future__ import annotations

from numbers import Integral

import pandas as pd

from passport_dashboard.data import REGIONS, DataError

__all__ = [
    "comparison",
    "comparison_exclusions",
    "timeseries",
    "spread",
    "extremes",
    "regional_summary",
]

_PANEL_COLUMNS = [
    "code", "country", "region", "score_start", "score_end", "rank_start", "rank_end", "delta"
]
_SPREAD_DTYPES = {
    "period": "string", "n": "Int64", "median": "Float64",
    "p10": "Float64", "p90": "Float64", "gap": "Float64",
}
_REGIONAL_DTYPES = {
    "region": "string", "n": "Int64", "median_start": "Float64", "median_end": "Float64"
}


def _validate_dates(rank: pd.DataFrame, start: int, end: int, *, allow_equal: bool = False) -> None:
    if any(not isinstance(year, Integral) or isinstance(year, bool) for year in (start, end)):
        raise DataError("Les années de début et de fin doivent être des entiers.")
    if start > end or (start == end and not allow_equal):
        relation = "antérieure ou égale" if allow_equal else "strictement antérieure"
        raise DataError(f"L'année de début doit être {relation} à l'année de fin.")
    missing = sorted({start, end} - set(rank["year"]))
    if missing:
        raise DataError(f"Année absente du classement : {', '.join(map(str, missing))}.")


def _validate_regions(regions: list[str] | tuple[str, ...]) -> None:
    if not isinstance(regions, (list, tuple)) or any(not isinstance(region, str) for region in regions):
        raise DataError("Les régions doivent être fournies sous forme de liste ou de tuple de noms.")
    unknown = sorted(set(regions) - set(REGIONS))
    if unknown:
        raise DataError(f"Région inconnue : {', '.join(unknown)}.")


def _catalog(rank: pd.DataFrame) -> pd.DataFrame:
    return (
        rank.sort_values(["year", "code"], kind="stable")
        .drop_duplicates("code", keep="last")[["code", "country", "region"]]
    )


def _endpoints(
    rank: pd.DataFrame, start: int, end: int, regions: list[str] | tuple[str, ...]
) -> pd.DataFrame:
    _validate_dates(rank, start, end)
    _validate_regions(regions)
    members = _catalog(rank)
    result = members.loc[members["region"].isin(regions)].copy()
    for suffix, year in (("start", start), ("end", end)):
        endpoint = rank.loc[rank["year"].eq(year), ["code", "year", "score", "rank"]]
        endpoint = endpoint.rename(columns={name: f"{name}_{suffix}" for name in ("year", "score", "rank")})
        result = result.merge(endpoint, how="left", on="code", validate="one_to_one")
    return result.sort_values(["country", "code"], kind="stable").reset_index(drop=True)


def comparison(
    rank: pd.DataFrame, start: int, end: int, regions: list[str] | tuple[str, ...]
) -> pd.DataFrame:
    """Compare seulement les passeports aux deux scores exploitables.

    Une sélection régionale vide produit un panel vide. Les rangs renvoyés
    sont les rangs mondiaux source : aucun filtre ne les recalcule.
    """
    endpoints = _endpoints(rank, start, end, regions)
    panel = endpoints.dropna(subset=["score_start", "score_end"]).copy()
    panel["delta"] = panel["score_end"] - panel["score_start"]
    return panel.loc[:, _PANEL_COLUMNS].reset_index(drop=True)


def comparison_exclusions(
    rank: pd.DataFrame, start: int, end: int, regions: list[str] | tuple[str, ...]
) -> pd.DataFrame:
    """Explique chaque exclusion, y compris les passeports absents aux deux dates."""
    endpoints = _endpoints(rank, start, end, regions)
    excluded = endpoints.loc[endpoints[["score_start", "score_end"]].isna().any(axis=1)].copy()
    reasons = []
    for _, row in excluded.iterrows():
        parts = []
        for suffix, year in (("start", start), ("end", end)):
            if pd.isna(row[f"year_{suffix}"]):
                parts.append(f"Donnée absente en {year}")
            elif pd.isna(row[f"score_{suffix}"]):
                parts.append(f"Score non exploitable en {year} (zéro source ou valeur manquante)")
        reasons.append(" ; ".join(parts))
    excluded["reason"] = pd.array(reasons, dtype="string")
    return excluded[["code", "country", "region", "reason"]].reset_index(drop=True)


def timeseries(rank: pd.DataFrame, codes: list[str], start: int, end: int) -> pd.DataFrame:
    """Construit un calendrier annuel complet sans imputer scores ni rangs.

    Les métadonnées du pays restent présentes même lorsqu'une observation
    annuelle manque. Un zéro source conserve son rang mais pas son score.
    """
    _validate_dates(rank, start, end, allow_equal=True)
    if not isinstance(codes, list) or any(not isinstance(code, str) for code in codes):
        raise DataError("Les codes des passeports doivent être fournis sous forme de liste de textes.")
    unknown = sorted(set(codes) - set(rank["code"]))
    if unknown:
        raise DataError(f"Code de passeport inconnu : {', '.join(unknown)}.")
    unique_codes = list(dict.fromkeys(codes))
    calendar = pd.MultiIndex.from_product(
        [unique_codes, range(start, end + 1)], names=["code", "year"]
    ).to_frame(index=False)
    observations = rank.loc[
        rank["code"].isin(unique_codes) & rank["year"].between(start, end),
        ["code", "year", "score", "rank"],
    ]
    result = calendar.merge(observations, how="left", on=["code", "year"], validate="one_to_one")
    result = result.merge(_catalog(rank), how="left", on="code", validate="many_to_one")
    dtypes = {
        "code": "string", "country": "string", "region": "string",
        "year": "Int64", "score": rank["score"].dtype, "rank": "Int64",
    }
    return result[list(dtypes)].astype(dtypes).reset_index(drop=True)


def spread(panel: pd.DataFrame) -> pd.DataFrame:
    """Médiane et écart P90–P10 aux deux dates, quantiles linéaires pandas."""
    rows = []
    if not panel.empty:
        for period in ("start", "end"):
            scores = panel[f"score_{period}"]
            p10, p90 = scores.quantile([0.1, 0.9])
            rows.append(
                (period, len(panel), scores.median(), p10, p90, p90 - p10)
            )
    return pd.DataFrame(rows, columns=list(_SPREAD_DTYPES)).astype(_SPREAD_DTYPES)


def extremes(panel: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Sélectionne les n plus faibles/fortes variations, sans doublons de pays.

    Les égalités sont départagées par nom puis code. Si les deux groupes se
    recouvrent, le premier groupe (« Faibles variations ») garde le passeport.
    """
    if not isinstance(n, Integral) or isinstance(n, bool) or n < 1:
        raise DataError("Le nombre de passeports extrêmes (n) doit être un entier strictement positif.")
    low = panel.sort_values(["delta", "country", "code"], kind="stable").head(n).copy()
    high = panel.sort_values(
        ["delta", "country", "code"], ascending=[False, True, True], kind="stable"
    ).head(n).copy()
    low["group"] = pd.Series("Faibles variations", index=low.index, dtype="string")
    high["group"] = pd.Series("Fortes variations", index=high.index, dtype="string")
    return pd.concat([low, high], ignore_index=True).drop_duplicates("code").reset_index(drop=True)


def regional_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Médianes par région sur le même panel apparié, sans nouveau classement."""
    if panel.empty:
        return pd.DataFrame({name: pd.Series(dtype=dtype) for name, dtype in _REGIONAL_DTYPES.items()})
    result = panel.groupby("region", observed=True, sort=True).agg(
        n=("code", "size"), median_start=("score_start", "median"), median_end=("score_end", "median")
    )
    return result.reset_index().astype(_REGIONAL_DTYPES)
