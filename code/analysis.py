"""Read the saved FRED CSVs, calculate price changes, and build Blog 7's figure.

Run from BLOG7: python code/analysis.py
Also copy the article and figure to the local website: python code/analysis.py --website
No downloads or regressions are needed. Original CSVs are never modified.
"""

from pathlib import Path
import argparse
import json
import shutil

import pandas as pd
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
TABLES = ROOT / "results/tables"
FIGURES = ROOT / "results/figures"
MONTHS = pd.date_range("2018-01-01", "2025-12-01", freq="MS")

# FRED sometimes uses an alias instead of the original BLS series ID.
# All seven series: CPI-U, U.S. city average, monthly, not seasonally adjusted.
SERIES = [
    ("CPIAPPNS", "CUUR0000SAA", "Apparel", "#8856a7", "solid"),
    ("CUUR0000SAF11", "CUUR0000SAF11", "Groceries", "#36824b", "solid"),
    ("CUUR0000SEFV", "CUUR0000SEFV", "Dining out", "#008b8b", "solid"),
    ("CUUR0000SAH1", "CUUR0000SAH1", "Shelter", "#b56724", "solid"),
    ("CUUR0000SEHF01", "CUUR0000SEHF01", "Electricity", "#2563a6", "solid"),
    ("CUUR0000SETB01", "CUUR0000SETB01", "Gasoline", "#bd4141", "solid"),
    ("CPIAUCNS", "CUUR0000SA0", "Overall CPI", "#27313c", "dash"),
]


def prepare_data():
    """Keep missing months explicit so a 12-row lag means exactly one year."""
    frames, coverage, sources = [], [], []
    for fred_id, bls_id, category, color, dash in SERIES:
        file = RAW / f"{fred_id}.csv"
        raw = pd.read_csv(file)
        if list(raw.columns) != ["observation_date", fred_id]:
            raise ValueError(f"Unexpected columns in {file.name}")
        raw["date"] = pd.to_datetime(raw["observation_date"], errors="raise")
        if raw["date"].duplicated().any() or not raw["date"].dt.is_month_start.all():
            raise ValueError(f"Duplicate or non-monthly dates in {file.name}")
        values = pd.to_numeric(raw.set_index("date")[fred_id], errors="raise")
        if (values.dropna() <= 0).any():
            raise ValueError(f"Nonpositive price index in {file.name}")
        values = values.reindex(MONTHS)
        missing = values.index[values.isna()]
        # Known source gap. Unexpected gaps stop the analysis for review.
        expected = [] if category == "Gasoline" else [pd.Timestamp("2025-10-01")]
        if list(missing) != expected:
            raise ValueError(f"Review missing months for {category}: {list(missing)}")
        baseline = values.loc["2019"].mean()
        frame = pd.DataFrame({"date": MONTHS, "series_id": fred_id,
                              "category": category, "index": values.to_numpy()})
        frame["baseline_2019"] = baseline
        frame["cumulative_pct"] = 100 * (frame["index"] / baseline - 1)
        # Do not forward-fill: the missing October stays missing in both views.
        frame["mom_pct"] = 100 * (frame["index"] / frame["index"].shift(1) - 1)
        frame["yoy_pct"] = 100 * (frame["index"] / frame["index"].shift(12) - 1)
        frames.append(frame)
        coverage.append({"series_id": fred_id, "category": category,
                         "expected_months": len(MONTHS), "valid_months": values.count(),
                         "missing_months": "; ".join(missing.strftime("%Y-%m")),
                         "duplicate_dates": 0, "baseline_months": values.loc["2019"].count()})
        sources.append({"series_id": fred_id, "bls_id": bls_id, "category": category,
                        "url": f"https://fred.stlouisfed.org/series/{fred_id}",
                        "file": f"data/raw/{file.name}", "frequency": "Monthly",
                        "seasonal_adjustment": "Not seasonally adjusted"})
    data = pd.concat(frames, ignore_index=True)
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    data.to_csv(ROOT / "data/processed/monthly_prices.csv", index=False)
    pd.DataFrame(coverage).to_csv(TABLES / "data_quality.csv", index=False)
    pd.DataFrame(sources).to_csv(TABLES / "sources.csv", index=False)
    return data


def summarize(data):
    """Compare December 2025 with the 2019 mean, not with the 2025 annual mean."""
    endpoint = data.loc[data["date"] == "2025-12-01"].copy()
    endpoint = endpoint.sort_values("cumulative_pct", ascending=False)
    endpoint.to_csv(TABLES / "december_2025.csv", index=False)
    displayed = data.loc[data["date"] >= "2019-01-01"]
    peaks = displayed.loc[displayed.groupby("category")["cumulative_pct"].idxmax()]
    peaks.to_csv(TABLES / "peaks.csv", index=False)
    return endpoint.set_index("category"), peaks.set_index("category")


def make_figure(data):
    """Export reviewed monthly and complete-year measures into the tabbed Plotly view."""
    series = []
    annual_rows = []
    for fred_id, bls_id, category, color, dash in SERIES:
        d = data.loc[data["series_id"] == fred_id].copy()
        d["year"] = d["date"].dt.year
        annual = d.groupby("year")["index"].agg(["mean", "count"])
        # Use the same complete-year window for every category. Six series lack
        # October 2025, so no 2025 annual change is shown, including for gasoline.
        annual.loc[annual["count"] != 12, "mean"] = float("nan")
        annual["change"] = 100 * (annual["mean"] / annual.loc[2019, "mean"] - 1)
        annual = annual.loc[2019:2024]
        for year, row in annual.iterrows():
            annual_rows.append({"category": category, "year": year,
                                "annual_mean": row["mean"], "months": row["count"],
                                "cumulative_since_2019_pct": row["change"]})
        d = d.loc[d["date"] >= "2019-01-01"]
        item = {"name": category, "color": color, "dash": dash,
                "dates": d["date"].dt.strftime("%Y-%m-%d").tolist(),
                "years": annual.index.astype(str).tolist(),
                "annual": annual["change"].tolist()}
        for measure in ["cumulative_pct", "yoy_pct", "mom_pct"]:
            item[measure] = [None if pd.isna(v) else float(v) for v in d[measure]]
        series.append(item)
    pd.DataFrame(annual_rows).to_csv(TABLES / "annual_changes.csv", index=False)
    template = (ROOT / "code/chart_template.html").read_text(encoding="utf-8")
    page = template.replace("__PLOTLY__", get_plotlyjs())
    page = page.replace("__DATA__", json.dumps(series, allow_nan=False))
    (FIGURES / "everyday_prices.html").write_text(page, encoding="utf-8")


def copy_to_website():
    destination = ROOT.parent / "website1/blog/posts/post7"
    (destination / "figures").mkdir(parents=True, exist_ok=True)
    article = (ROOT / "index.qmd").read_text(encoding="utf-8")
    article = article.replace("results/figures/", "figures/")
    (destination / "index.qmd").write_text(article, encoding="utf-8")
    shutil.copy2(FIGURES / "everyday_prices.html", destination / "figures/everyday_prices.html")
    print("Copied article and interactive figure to website1/blog/posts/post7.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--website", action="store_true", help="Also update the local website copy")
    args = parser.parse_args()
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = prepare_data()
    endpoint, peaks = summarize(data)
    make_figure(data)
    print("Checked seven series, 96 months each; six known missing October 2025 values.")
    print(endpoint[["cumulative_pct", "yoy_pct"]].round(2).to_string())
    print("Saved processed data, tables, and interactive HTML.")
    if args.website:
        copy_to_website()


if __name__ == "__main__":
    main()
