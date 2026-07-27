"""Reproduce the three core housing-supply regressions from the project."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_YEARS = (2019, 2021, 2022, 2023, 2024)


def load_hpi(data_dir: Path) -> pd.DataFrame:
    """Load and filter the FHFA annual CBSA house-price index."""
    raw = pd.read_excel(data_dir / "hpi_at_cbsa.xlsx", skiprows=5, header=None)
    raw.columns = [
        "CBSA",
        "Name_hpi",
        "Year",
        "Ann_Chg_Pct",
        "HPI",
        "HPI_1990",
        "HPI_2000",
    ]

    for column in ("CBSA", "Year", "Ann_Chg_Pct", "HPI"):
        raw[column] = pd.to_numeric(raw[column], errors="coerce")

    hpi = raw.loc[
        (raw["CBSA"] >= 10000) & raw["Year"].isin(ANALYSIS_YEARS),
        ["CBSA", "Year", "HPI", "Ann_Chg_Pct"],
    ].dropna(subset=["HPI"])
    hpi["CBSA"] = hpi["CBSA"].astype(int)
    return hpi.reset_index(drop=True)


def load_acs(data_dir: Path) -> pd.DataFrame:
    """Load the harmonized ACS controls used by the notebook."""
    acs = pd.read_csv(data_dir / "merged_2010_2024.csv")
    acs["CBSA"] = acs["GEO_ID"].astype(str).str[-5:].astype(int)
    acs["year"] = pd.to_numeric(acs["year"], errors="coerce")

    control_columns = (
        "housing_units",
        "median_household_income",
        "total_population",
    )
    for column in control_columns:
        acs[column] = pd.to_numeric(acs[column], errors="coerce")

    return acs.loc[
        (acs["CBSA"] >= 10000)
        & acs["year"].isin(ANALYSIS_YEARS)
        & (acs["median_household_income"] > 0)
        & (acs["total_population"] > 0)
    ].reset_index(drop=True)


def parse_annual_permits(path: Path) -> pd.DataFrame:
    """Parse one Census Building Permits Survey CBSA workbook."""
    year_match = re.search(r"(\d{4})", path.name)
    if year_match is None:
        raise ValueError(f"Could not determine a year from {path.name}")

    try:
        raw = pd.read_excel(path, engine="xlrd", skiprows=6, header=None)
    except Exception:
        raw = pd.read_excel(path, engine="openpyxl", skiprows=6, header=None)

    rows = raw.iloc[2:].reset_index(drop=True)
    permits = pd.DataFrame(
        {
            "CBSA": pd.to_numeric(rows[1], errors="coerce"),
            "metro_code": pd.to_numeric(rows[3], errors="coerce"),
            "total_permits": pd.to_numeric(rows[4], errors="coerce"),
        }
    ).dropna(subset=["CBSA", "total_permits"])

    permits["CBSA"] = permits["CBSA"].astype(int)
    permits["Year"] = int(year_match.group(1))
    permits["metro_dummy"] = permits["metro_code"].isin([2, 4]).astype(int)
    return permits


def load_permits(data_dir: Path) -> pd.DataFrame:
    """Build the annual permit panel from the checked-in source files."""
    files = sorted((data_dir / "CBSA Permits").glob("*.xls"))
    if not files:
        raise FileNotFoundError(f"No permit workbooks found in {data_dir / 'CBSA Permits'}")

    panel = pd.concat(
        [parse_annual_permits(path) for path in files],
        ignore_index=True,
    )
    return panel.loc[
        panel["Year"].isin(ANALYSIS_YEARS) & (panel["CBSA"] >= 10000)
    ].reset_index(drop=True)


def build_analysis_frame(data_dir: Path) -> pd.DataFrame:
    """Merge the sources and construct the variables used in the models."""
    hpi = load_hpi(data_dir)
    acs = load_acs(data_dir)
    permits = load_permits(data_dir)

    frame = hpi.merge(
        acs[
            [
                "CBSA",
                "year",
                "housing_units",
                "median_household_income",
                "total_population",
            ]
        ],
        left_on=["CBSA", "Year"],
        right_on=["CBSA", "year"],
        how="inner",
    ).merge(
        permits[["CBSA", "Year", "total_permits", "metro_dummy"]],
        on=["CBSA", "Year"],
        how="inner",
    )
    frame = frame.drop(columns="year").reset_index(drop=True)

    frame["log_hpi"] = np.log(frame["HPI"])
    frame["log_permits"] = np.log(frame["total_permits"] + 1)
    frame["log_income"] = np.log(frame["median_household_income"])
    frame["log_pop"] = np.log(frame["total_population"])

    year_dummies = pd.get_dummies(
        frame["Year"],
        prefix="Year",
        drop_first=True,
        dtype=float,
    )
    frame = pd.concat([frame, year_dummies], axis=1)
    return frame.dropna(
        subset=["log_hpi", "log_permits", "log_income", "log_pop"]
    ).reset_index(drop=True)


def fit_models(frame: pd.DataFrame) -> dict[str, object]:
    """Fit the notebook's three nested OLS models with HC0 robust errors."""
    outcome = frame["log_hpi"]
    year_columns = sorted(
        column for column in frame.columns if column.startswith("Year_")
    )
    specifications = {
        "Model 1": ["log_permits"],
        "Model 2": ["log_permits", "metro_dummy", *year_columns],
        "Model 3": [
            "log_permits",
            "log_income",
            "log_pop",
            "metro_dummy",
            *year_columns,
        ],
    }

    return {
        label: sm.OLS(outcome, sm.add_constant(frame[variables])).fit(cov_type="HC0")
        for label, variables in specifications.items()
    }


def result_table(models: dict[str, object]) -> pd.DataFrame:
    """Return the headline comparison in a compact, readable form."""
    rows = {}
    for label, model in models.items():
        rows[label] = {
            "permit_coefficient": model.params["log_permits"],
            "robust_se": model.bse["log_permits"],
            "p_value": model.pvalues["log_permits"],
            "r_squared": model.rsquared,
            "observations": int(model.nobs),
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce the project's three headline housing regressions."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "data",
        help="Directory containing the checked-in FHFA, ACS, and permit files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = build_analysis_frame(args.data_dir.resolve())
    models = fit_models(frame)
    comparison = result_table(models)

    print(
        f"Analysis sample: {len(frame):,} MSA-year observations, "
        f"{frame['CBSA'].nunique():,} MSAs"
    )
    print(comparison.to_string(float_format=lambda value: f"{value:.6f}"))

    short = comparison.loc["Model 1", "permit_coefficient"]
    full = comparison.loc["Model 3", "permit_coefficient"]
    print(f"\nChange in permit coefficient, Model 1 to Model 3: {short - full:.6f}")


if __name__ == "__main__":
    main()
