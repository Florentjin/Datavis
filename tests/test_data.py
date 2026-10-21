import csv
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
import pytest

from passport_dashboard.data import (
    ACCESS_REGIMES,
    INCLUDED_REGIMES,
    REGIONS,
    DataError,
    access_audit,
    load_access,
    load_rank,
)

ROOT = Path(__file__).resolve().parents[1]
RANK_FIELDS = ["code", "country", "region", "rank", "visa_free_count", "year"]
RANK_ROW = ["NA", "Namibia", "AFRICA", "60", "80", "2025"]


def _csv_text(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(fields)
    writer.writerows(rows)
    return stream.getvalue()


def _access_row():
    return {
        "code": "NA",
        "country": "Namibia",
        **{regime: "[[]]" for regime in ACCESS_REGIMES},
        "visa_required": json.dumps([[{"code": "FR", "name": "France"}]]),
    }


@pytest.fixture
def csv_file(monkeypatch):
    """Exercise both CSV parsers without creating scratch files."""
    documents = {}
    original_open = Path.open

    def open_document(path, *args, **kwargs):
        if path in documents:
            return io.StringIO(documents[path], newline="")
        return original_open(path, *args, **kwargs)

    def create(content):
        path = ROOT / "tests" / f"virtual_input_{len(documents)}.csv"
        documents[path] = content
        return path

    monkeypatch.setattr(Path, "open", open_document)
    return create


@pytest.fixture(scope="module")
def rank():
    return load_rank(ROOT / "rank_by_year.csv")


@pytest.fixture(scope="module")
def access():
    return load_access(ROOT / "country_lists.csv")


def test_real_rank_schema_counts_and_namibia(rank):
    assert rank.columns.tolist() == RANK_FIELDS + ["score", "score_status"]
    assert len(rank) == 3950
    assert rank["code"].nunique() == 199
    assert rank["code"].eq("NA").sum() == 20
    assert set(rank["region"]) == set(REGIONS)
    assert str(rank["code"].dtype).startswith("string")
    assert str(rank["score"].dtype) == "Int64"
    assert str(rank["score_status"].dtype).startswith("string")
    assert not rank.duplicated(["code", "year"]).any()
    assert rank["rank"].gt(0).all()


def test_source_zeros_are_nullable_but_original_counts_and_ranks_remain(rank):
    zeros = rank["visa_free_count"].eq(0)
    assert zeros.sum() == 447
    assert rank["score"].isna().eq(zeros).all()
    assert rank.loc[zeros, "score_status"].eq("zero_uninterpretable").all()
    assert rank.loc[~zeros, "score_status"].eq("valid").all()
    pd.testing.assert_series_equal(
        rank.loc[~zeros, "score"], rank.loc[~zeros, "visa_free_count"], check_names=False
    )
    with (ROOT / "rank_by_year.csv").open(encoding="utf-8", newline="") as stream:
        original = list(csv.DictReader(stream))
    assert rank["rank"].tolist() == [int(row["rank"]) for row in original]
    assert rank["visa_free_count"].tolist() == [int(row["visa_free_count"]) for row in original]
    for year, count in ((2007, 185), (2009, 198)):
        year_rows = rank.loc[rank["year"].eq(year)]
        assert len(year_rows) == count
        assert year_rows["score"].isna().all()
        assert year_rows["rank"].notna().all()
        assert year_rows["rank"].gt(0).all()


def test_loading_does_not_change_source_files():
    paths = (ROOT / "rank_by_year.csv", ROOT / "country_lists.csv")
    before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    load_rank(paths[0])
    load_access(paths[1])
    assert before == [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]


def test_real_access_regimes_codes_and_unobserved_bilateral_pair(access):
    assert access.columns.tolist() == [
        "code", "country", "destination_code", "destination_name", "regime"
    ]
    assert isinstance(ACCESS_REGIMES, tuple)
    assert len(ACCESS_REGIMES) == 5
    assert INCLUDED_REGIMES == frozenset(
        {"visa_free_access", "visa_on_arrival", "electronic_travel_authorisation"}
    )
    assert set(access["regime"]) == set(ACCESS_REGIMES)
    assert access["code"].nunique() == 199
    assert access["code"].eq("NA").any()
    assert access["destination_code"].eq("NA").any()
    assert not access.duplicated(["code", "destination_code"]).any()
    assert not access["code"].eq(access["destination_code"]).any()
    assert access.loc[access["code"].eq("IL") & access["destination_code"].eq("MV")].empty


def test_all_199_latest_reported_scores_match_bilateral_counts(rank, access):
    audit = access_audit(rank, access)
    assert audit.columns.tolist() == ["code", "country", "reported_score", "computed_score", "matches"]
    assert len(audit) == 199
    assert audit["matches"].all()
    assert not audit["code"].duplicated().any()


def test_audit_uses_maximum_available_year_not_a_hardcoded_year(rank, access):
    historical = rank.loc[rank["year"].le(2024)]
    audit = access_audit(historical, access).set_index("code")
    expected = historical.loc[historical["year"].eq(2024)].set_index("code")
    pd.testing.assert_series_equal(
        audit["reported_score"].sort_index(), expected["score"].sort_index(), check_names=False
    )
    assert not audit["matches"].all()


@pytest.mark.parametrize("loader", [load_rank, load_access])
def test_missing_file_is_a_readable_error_with_cause(loader):
    with pytest.raises(DataError, match="Fichier introuvable") as caught:
        loader(ROOT / "tests" / "missing_source_does_not_exist.csv")
    assert isinstance(caught.value.__cause__, FileNotFoundError)


def test_filesystem_failure_is_wrapped_with_cause(monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("Lecture refusée")

    monkeypatch.setattr(Path, "open", denied)
    with pytest.raises(DataError, match="Impossible de lire") as caught:
        load_rank(ROOT / "rank_by_year.csv")
    assert isinstance(caught.value.__cause__, PermissionError)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("code", "", "Valeur vide"),
        ("code", "na", "Code pays invalide"),
        ("code", "NAM", "Code pays invalide"),
        ("country", "  ", "Valeur vide"),
        ("region", "EUROPA", "Région inconnue"),
        ("rank", "0", "hors limites"),
        ("rank", "-3", "hors limites"),
        ("rank", "2.5", "entier"),
        ("rank", "9223372036854775808", "hors limites"),
        ("visa_free_count", "-1", "hors limites"),
        ("visa_free_count", "228", "hors limites"),
        ("visa_free_count", "NA", "entier"),
        ("visa_free_count", "nan", "entier"),
        ("visa_free_count", "inf", "entier"),
        ("year", "", "Valeur vide"),
        ("year", "2025.5", "entier"),
        ("year", "0", "hors limites"),
        ("year", "10000", "hors limites"),
    ],
)
def test_rank_rejects_blank_type_and_range_errors(csv_file, field, value, message):
    row = RANK_ROW.copy()
    row[RANK_FIELDS.index(field)] = value
    with pytest.raises(DataError, match=message):
        load_rank(csv_file(_csv_text(RANK_FIELDS, [row])))


@pytest.mark.parametrize(
    "text",
    [
        "",
        "code,country\nNA,Namibia\n",
        ",".join(RANK_FIELDS) + "\n",
        ",".join(RANK_FIELDS) + "\nNA,Namibia,AFRICA,1,80,2025,unexpected\n",
        ",".join(RANK_FIELDS) + "\nNA,Namibia,AFRICA,1,80\n",
        ",".join(RANK_FIELDS) + '\n"NA,Namibia,AFRICA,1,80,2025\n',
        "code,country,region,rank,visa_free_count,code\nNA,Namibia,AFRICA,1,80,2025\n",
        ",".join(RANK_FIELDS) + "\n\n",
    ],
)
def test_malformed_csv_and_schema_raise_data_error(csv_file, text):
    with pytest.raises(DataError):
        load_rank(csv_file(text))


def test_csv_parsing_failure_keeps_cause(csv_file):
    text = ",".join(RANK_FIELDS) + '\n"NA,Namibia,AFRICA,1,80,2025\n'
    with pytest.raises(DataError) as caught:
        load_rank(csv_file(text))
    assert isinstance(caught.value.__cause__, csv.Error)


def test_rank_rejects_duplicate_country_year(csv_file):
    with pytest.raises(DataError, match="Doublon.*NA.*2025"):
        load_rank(csv_file(_csv_text(RANK_FIELDS, [RANK_ROW, RANK_ROW])))


@pytest.mark.parametrize(("index", "value"), [(1, "Another country"), (2, "ASIA")])
def test_rank_rejects_inconsistent_identity(csv_file, index, value):
    second = RANK_ROW.copy()
    second[-1] = "2024"
    second[index] = value
    with pytest.raises(DataError, match="incohérent"):
        load_rank(csv_file(_csv_text(RANK_FIELDS, [RANK_ROW, second])))


def test_rank_reorders_columns_and_accepts_valid_zero(csv_file):
    row = RANK_ROW.copy()
    row[4] = "0"
    frame = load_rank(csv_file(_csv_text(RANK_FIELDS[::-1], [row[::-1]])))
    assert frame.columns.tolist() == RANK_FIELDS + ["score", "score_status"]
    assert frame.loc[0, "code"] == "NA"
    assert frame.loc[0, "rank"] == 60
    assert frame.loc[0, "visa_free_count"] == 0
    assert pd.isna(frame.loc[0, "score"])


@pytest.mark.parametrize(
    "payload",
    [
        "not-json", "null", "{}", "[]", '[{"code":"FR","name":"France"}]',
        "[[],[]]", '[[{}]]', '[[{"code":"FR"}]]', '[[{"name":"France"}]]',
        '[[{"code":"","name":"France"}]]', '[[{"code":"FR","name":" "}]]',
        '[[{"code":12,"name":"France"}]]', '[[{"code":"FR","name":null}]]',
        '[[{"code":"fr","name":"France"}]]', '[[{"code":"FRA","name":"France"}]]',
        "[[null]]", "[[[]]]",
    ],
)
def test_access_rejects_invalid_json_shapes_and_destinations(csv_file, payload):
    row = _access_row()
    row["visa_free_access"] = payload
    with pytest.raises(DataError, match="JSON|destination"):
        load_access(csv_file(_csv_text(row.keys(), [row.values()])))


def test_access_json_parse_failure_keeps_cause(csv_file):
    row = _access_row()
    row["visa_required"] = "{"
    with pytest.raises(DataError, match="JSON invalide") as caught:
        load_access(csv_file(_csv_text(row.keys(), [row.values()])))
    assert isinstance(caught.value.__cause__, json.JSONDecodeError)


@pytest.mark.parametrize("same_regime", [True, False])
def test_access_rejects_duplicate_pairs_within_or_between_regimes(csv_file, same_regime):
    row = _access_row()
    destination = {"code": "FR", "name": "France"}
    if same_regime:
        row["visa_required"] = json.dumps([[destination, destination]])
    else:
        row["visa_free_access"] = json.dumps([[destination]])
    with pytest.raises(DataError, match="Doublon d'accès"):
        load_access(csv_file(_csv_text(row.keys(), [row.values()])))


def test_access_rejects_self_pairs(csv_file):
    row = _access_row()
    row["visa_required"] = '[[{"code":"NA","name":"Namibia"}]]'
    with pytest.raises(DataError, match="soi-même"):
        load_access(csv_file(_csv_text(row.keys(), [row.values()])))


def test_access_rejects_duplicate_origin(csv_file):
    row = _access_row()
    with pytest.raises(DataError, match="Doublon de code"):
        load_access(csv_file(_csv_text(row.keys(), [row.values(), row.values()])))


@pytest.mark.parametrize(("field", "value"), [("code", "nam"), ("country", ""), ("visa_online", "")])
def test_access_rejects_invalid_origin_or_blank_cells(csv_file, field, value):
    row = _access_row()
    row[field] = value
    with pytest.raises(DataError):
        load_access(csv_file(_csv_text(row.keys(), [row.values()])))


def test_access_rejects_unknown_regime_column(csv_file):
    row = _access_row()
    row["unknown_regime"] = row.pop("visa_online")
    with pytest.raises(DataError, match="Schéma CSV"):
        load_access(csv_file(_csv_text(row.keys(), [row.values()])))


def test_access_keeps_literal_na_and_accepts_empty_regime_lists(csv_file):
    row = _access_row()
    frame = load_access(csv_file(_csv_text(row.keys(), [row.values()])))
    assert frame.to_dict("records") == [
        {"code": "NA", "country": "Namibia", "destination_code": "FR",
         "destination_name": "France", "regime": "visa_required"}
    ]
    row["visa_required"] = "[[]]"
    assert load_access(csv_file(_csv_text(row.keys(), [row.values()]))).empty


def test_audit_rejects_unknown_origins_and_code_mismatch(rank, access):
    unknown = access.copy()
    unknown.loc[unknown["code"].eq("NA"), "code"] = "ZZ"
    with pytest.raises(DataError, match="Origines.*inconnues"):
        access_audit(rank, unknown)
    with pytest.raises(DataError, match="codes.*correspondent"):
        access_audit(rank, access.loc[access["code"].ne("NA")])
    with pytest.raises(DataError, match="codes.*correspondent"):
        access_audit(rank.loc[~(rank["code"].eq("NA") & rank["year"].eq(2025))], access)


def test_audit_rejects_unknown_regimes_and_duplicate_pairs(rank, access):
    unknown = access.copy()
    unknown.loc[unknown.index[0], "regime"] = "unknown"
    with pytest.raises(DataError, match="Régime d'accès inconnu"):
        access_audit(rank, unknown)
    with pytest.raises(DataError, match="Doublon"):
        access_audit(rank, pd.concat([access, access.iloc[:1]]))
