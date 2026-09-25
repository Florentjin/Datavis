from pathlib import Path

from passport_dashboard import charts
from passport_dashboard.data import load_rank
from passport_dashboard.metrics import comparison, extremes, spread, timeseries
from passport_dashboard.theme import REGIONS


def main() -> None:
    root = Path(__file__).resolve().parent
    rank = load_rank(root / "rank_by_year.csv")
    panel = comparison(rank, 2006, 2025, list(REGIONS))
    if panel.empty:
        raise ValueError("Aucun passeport comparable entre 2006 et 2025.")
    distribution = spread(panel).set_index("period")
    gaps = distribution["gap"]
    first_gap = f"{gaps['start']:.1f}".replace(".", ",")
    last_gap = f"{gaps['end']:.1f}".replace(".", ",")
    ratios = distribution["p90"] / distribution["p10"]
    first_ratio = f"{ratios['start']:.2f}".replace(".", ",")
    last_ratio = f"{ratios['end']:.2f}".replace(".", ",")
    focus = ["SG", "AF", "AE", "US"]
    figures = [
        charts.regional_distribution(panel, 2006, 2025, focus),
        charts.trajectories(timeseries(rank, focus, 2006, 2025), "score"),
        charts.positions(panel, 2006, 2025, focus),
        charts.changes(extremes(panel), 2006, 2025),
    ]
    fragments = [
        figure.to_html(
            full_html=False, include_plotlyjs=index == 0,
            config={"displaylogo": False, "responsive": True},
            div_id=f"vue-{index + 1}",
        )
        for index, figure in enumerate(figures)
    ]
    html = """<!doctype html><html lang="fr"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Passeports et inégalités de mobilité</title>
<style>body{font:16px "Segoe UI",sans-serif;color:#17233B;background:#F3F6FA;
max-width:1160px;margin:32px auto;padding:0 20px}section{background:white;
margin:24px 0;padding:16px}h1{font-family:Bahnschrift,sans-serif}
p{line-height:1.6}.plotly-graph-div{max-width:100%}</style>
<h1>Passeports et inégalités de mobilité</h1>
"""
    html += f"<p>2006–2025 · {len(panel)} passeports comparables · TidyTuesday / Henley Passport Index.</p>"
    html += """
<p>Export de présentation : survols et légendes actifs ; les filtres coordonnés
restent dans l'application Streamlit. Les scores nuls sont traités comme
anomalies présumées, sans interpolation. Le score inclut sans visa, visa à
l'arrivée et ETA. Il exclut les e-visas à approbation préalable.</p>
"""
    html += (
        f"<p>Sur ce panel, P90–P10 passe de {first_gap} à {last_gap} destinations. "
        f"Le rapport P90/P10 passe de {first_ratio} à {last_ratio} (sans unité) : "
        "l'écart absolu et le rapport relatif peuvent évoluer différemment. "
        "Accès et rang ne sont pas interchangeables. Aucune causalité n'est établie.</p>"
    )
    html += "".join(f"<section>{fragment}</section>" for fragment in fragments)
    html += """<p>Sources :
<a href="https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-09-09">TidyTuesday</a>,
<a href="https://www.henleyglobal.com/passport-index/methodology">méthodologie Henley</a>.
Données historiques, pas des conseils de voyage actualisés.</p></html>"""
    output = root / "livrables" / "dashboard.html"
    output.parent.mkdir(exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Export : {output}")


if __name__ == "__main__":
    main()
