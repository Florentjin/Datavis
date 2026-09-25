"""Lecture stricte des deux fichiers sources, sans les modifier."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

__all__ = [
    "ACCESS_REGIMES",
    "INCLUDED_REGIMES",
    "REGIONS",
    "DataError",
    "load_rank",
    "load_access",
    "access_audit",
]

REGIONS = (
    "AFRICA",
    "AMERICAS",
    "ASIA",
    "CARIBBEAN",
    "EUROPE",
    "MIDDLE EAST",
    "OCEANIA",
)
ACCESS_REGIMES = (
    "visa_required",
    "visa_online",
    "visa_on_arrival",
    "visa_free_access",
    "electronic_travel_authorisation",
)
INCLUDED_REGIMES = frozenset(
    ("visa_free_access", "visa_on_arrival", "electronic_travel_authorisation")
)
_RANK_COLUMNS = ("code", "country", "region", "rank", "visa_free_count", "year")
_ACCESS_COLUMNS = ("code", "country", *ACCESS_REGIMES)
_LONG_COLUMNS = ("code", "country", "destination_code", "destination_name", "regime")


class DataError(ValueError):
    """Données ou paramètres invalides, avec un message présentable à l'utilisateur."""


def _read_csv(path: Path, columns: tuple[str, ...]) -> pd.DataFrame:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            header = next(reader, None)
            if header is None:
                raise DataError(f"Le fichier « {path.name} » est vide.")
            if len(header) != len(columns) or set(header) != set(columns):
                raise DataError(
                    f"Schéma CSV invalide dans « {path.name} » : "
                    f"colonnes attendues : {', '.join(columns)}."
                )
            # pandas peut interpréter une colonne surnuméraire comme un index.
            for row in reader:
                if len(row) != len(columns):
                    raise DataError(
                        f"Ligne CSV {reader.line_num} invalide dans « {path.name} » : "
                        f"{len(columns)} champs attendus, {len(row)} reçus."
                    )
            stream.seek(0)
            frame = pd.read_csv(
                stream,
                dtype={column: "string" for column in columns},
                keep_default_na=False,
                skip_blank_lines=False,
                on_bad_lines="error",
            )
    except FileNotFoundError as exc:
        raise DataError(f"Fichier introuvable : « {path} ».") from exc
    except (OSError, UnicodeError, csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DataError(f"Impossible de lire le fichier CSV « {path.name} » : {exc}") from exc
    if frame.empty:
        raise DataError(f"Le fichier « {path.name} » ne contient aucune donnée.")
    for column in columns:
        blank = frame[column].isna() | frame[column].str.strip().eq("")
        if blank.any():
            line = int(blank[blank].index[0]) + 2
            raise DataError(f"Valeur vide dans « {column} », ligne {line} de « {path.name} ».")
    return frame.loc[:, list(columns)].copy()


def _validate_codes(values: pd.Series, label: str) -> None:
    invalid = ~values.str.fullmatch(r"[A-Z]{2}", na=False)
    if invalid.any():
        raise DataError(
            f"Code pays invalide dans {label} : « {values[invalid].iloc[0]} ». "
            "Deux lettres majuscules sont attendues."
        )


def _integer_column(frame: pd.DataFrame, column: str, minimum: int, maximum: int) -> None:
    invalid = ~frame[column].str.fullmatch(r"[+-]?[0-9]+", na=False)
    if invalid.any():
        raise DataError(f"Type invalide dans « {column} » : un nombre entier est attendu.")
    try:
        values = pd.to_numeric(frame[column], errors="raise")
    except (ValueError, OverflowError) as exc:
        raise DataError(f"Nombre entier invalide ou trop grand dans « {column} ».") from exc
    if not values.between(minimum, maximum).all():
        raise DataError(
            f"Valeur hors limites dans « {column} » : "
            f"un entier entre {minimum} et {maximum} est attendu."
        )
    frame[column] = values.astype("Int64")


def load_rank(path: Path) -> pd.DataFrame:
    """Charge les six champs d'origine et ajoute ``score`` et ``score_status``.

    Les zéros source (447 dans le fichier local) ne sont pas interprétables :
    la source ne permet pas de distinguer une absence de mesure d'un véritable
    score nul. Ils deviennent donc des valeurs manquantes dans ``score``, sans
    interpolation, sans modifier ``visa_free_count`` ni le rang mondial source.
    ``NA`` reste le code littéral de la Namibie. Les scores sont des comptes
    entiers bornés par les 227 destinations de ce jeu Henley.
    """
    frame = _read_csv(path, _RANK_COLUMNS)
    _validate_codes(frame["code"], "le classement")
    invalid_regions = sorted(set(frame["region"]) - set(REGIONS))
    if invalid_regions:
        raise DataError(f"Région inconnue dans le classement : {', '.join(invalid_regions)}.")
    _integer_column(frame, "rank", 1, 2**63 - 1)
    _integer_column(frame, "visa_free_count", 0, 227)
    _integer_column(frame, "year", 1, 9999)
    duplicates = frame.duplicated(["code", "year"], keep=False)
    if duplicates.any():
        row = frame.loc[duplicates].iloc[0]
        raise DataError(f"Doublon de classement pour {row['code']} en {row['year']}.")
    identity = frame.groupby("code")[["country", "region"]].nunique()
    if identity.gt(1).any(axis=None):
        raise DataError("Pays ou région incohérent pour un même code dans le classement.")
    frame["score"] = frame["visa_free_count"].mask(frame["visa_free_count"].eq(0))
    frame["score_status"] = pd.Series("valid", index=frame.index, dtype="string")
    frame.loc[frame["score"].isna(), "score_status"] = "zero_uninterpretable"
    return frame


def load_access(path: Path) -> pd.DataFrame:
    """Déplie les listes JSON ``[[{code, name}, ...]]`` du snapshot bilatéral.

    Seuls les couples explicitement présents sont conservés. Une destination
    absente n'est ni un refus, ni un accès libre, et n'est jamais imputée.
    Une liste de régime vide s'écrit ``[[]]``.
    """
    source = _read_csv(path, _ACCESS_COLUMNS)
    _validate_codes(source["code"], "les origines d'accès")
    if source["code"].duplicated().any():
        raise DataError("Doublon de code pays d'origine dans les données d'accès.")
    records = []
    pairs = set()
    for row in source.to_dict("records"):
        for regime in ACCESS_REGIMES:
            context = f"{row['code']} / {regime}"
            try:
                nested = json.loads(row[regime])
            except json.JSONDecodeError as exc:
                raise DataError(f"JSON invalide pour {context} : {exc.msg}.") from exc
            if not isinstance(nested, list) or len(nested) != 1 or not isinstance(nested[0], list):
                raise DataError(f"Structure JSON invalide pour {context} : une liste [[...]] est attendue.")
            for destination in nested[0]:
                if (
                    not isinstance(destination, dict)
                    or set(destination) != {"code", "name"}
                    or any(
                        not isinstance(destination[key], str) or not destination[key].strip()
                        for key in ("code", "name")
                    )
                ):
                    raise DataError(
                        f"Destination JSON invalide pour {context} : "
                        "un objet avec code et name non vides est attendu."
                    )
                code = destination["code"]
                if len(code) != 2 or any(letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for letter in code):
                    raise DataError(f"Code de destination invalide pour {context} : « {code} ».")
                pair = (row["code"], code)
                if pair[0] == pair[1]:
                    raise DataError(f"Accès vers soi-même interdit pour {row['code']}.")
                if pair in pairs:
                    raise DataError(f"Doublon d'accès pour le couple {pair[0]} → {pair[1]}.")
                pairs.add(pair)
                records.append((row["code"], row["country"], code, destination["name"], regime))
    return pd.DataFrame.from_records(records, columns=_LONG_COLUMNS).astype("string")


def access_audit(rank: pd.DataFrame, access: pd.DataFrame) -> pd.DataFrame:
    """Compare le comptage des trois régimes inclus au dernier millésime de rank.

    Le fichier bilatéral est le snapshot publié dans le jeu de données 2025 :
    il ne contient aucun horodatage de mesure. L'audit utilise ``max(year)`` du
    classement fourni, sans prétendre dater précisément les accès ni reconstruire
    leur historique. Aucun couple bilatéral absent n'est ajouté.
    """
    if rank.empty:
        raise DataError("Le classement est vide : aucun millésime à auditer.")
    latest = rank.loc[rank["year"].eq(rank["year"].max()), ["code", "country", "score"]]
    known_codes = set(rank["code"])
    access_codes = set(access["code"])
    unknown = access_codes - known_codes
    if unknown:
        raise DataError(f"Origines d'accès inconnues du classement : {', '.join(sorted(unknown))}.")
    missing = set(latest["code"]) - access_codes
    extra = access_codes - set(latest["code"])
    if missing or extra:
        raise DataError(
            "Les codes des deux sources ne correspondent pas au dernier millésime. "
            f"Absents des accès : {', '.join(sorted(missing)) or 'aucun'} ; "
            f"absents du classement : {', '.join(sorted(extra)) or 'aucun'}."
        )
    if not access["regime"].isin(ACCESS_REGIMES).all():
        raise DataError("Régime d'accès inconnu : les cinq régimes Henley sont attendus.")
    if access.duplicated(["code", "destination_code"]).any():
        raise DataError("Doublon de couple origine-destination dans l'audit des accès.")
    counts = access.loc[access["regime"].isin(INCLUDED_REGIMES)].groupby("code").size()
    result = latest.rename(columns={"score": "reported_score"}).copy()
    result["computed_score"] = result["code"].map(counts).fillna(0).astype("Int64")
    result["matches"] = result["reported_score"].eq(result["computed_score"]).fillna(False).astype("boolean")
    return result.sort_values(["country", "code"], kind="stable").reset_index(drop=True)
