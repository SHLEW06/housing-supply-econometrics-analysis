# Housing Supply and Home Prices: Evidence from U.S. Metropolitan Areas

*An empirical study of residential building permits and home-price dynamics across 530 U.S. Metropolitan Statistical Areas, 2019–2024.*

**Authors:** Tessa Butler, Siya Kumar, Ania Ting, Naman Keswani, Shunji Lewandowski
**Course:** ECON 320 — Econometrics, Emory University

---

## Abstract

This project examines whether new residential construction is associated with lower home prices across U.S. Metropolitan Statistical Areas (MSAs). Using a pooled cross-section of annual building permits matched to 530 MSAs over five years — 2019 and 2021–2024 (2020 is excluded because the Census Bureau did not release American Community Survey one-year estimates that year due to COVID-related data-collection disruptions) — we construct an MSA–year panel of *N* = 2,036 observations. The dependent variable is the natural log of the FHFA All-Transactions House Price Index (HPI); the main regressor is the natural log of annual building permits from the Census Building Permits Survey (BPS). Demand-side controls include median household income and population from the ACS, a metropolitan/micropolitan dummy, and year fixed effects.

Across all specifications, building-permit activity is **positively** associated with home prices — the opposite of the naive supply-and-demand prediction. The permit coefficient declines from +0.149 in the bivariate model to +0.081 in the fully controlled model, a 46% reduction consistent with upward omitted-variable bias from demand factors (income, population). Breusch–Pagan and White tests reject homoskedasticity, so HC0 heteroskedasticity-robust standard errors are used throughout; variance inflation factors remain below 5. The results indicate that demand-side pressures dominate the cross-MSA price signal and that OLS cannot, on its own, recover a causal supply effect without an instrument for local housing-supply constraints.

---

## 1. Research Question and Motivation

**Research question.** Is greater housing supply — measured by new residential building permits — associated with lower home prices across U.S. metropolitan areas?

**Motivation.** The U.S. housing-supply gap is estimated at roughly four million homes (Realtor.com, 2026), and more than 42 million households spend over 30% of income on housing. The textbook supply-and-demand argument is direct: constrained supply pushes prices above competitive equilibrium, so building more homes should lower prices. This study tests whether that prediction is borne out in the cross-section of U.S. metros.

## 2. Data

| Source | Variable | Description |
|---|---|---|
| FHFA | `HPI` | All-Transactions House Price Index (annual, CBSA-level; repeat-sales index) |
| FHFA | `Ann_Chg_Pct` | Year-over-year percent change in HPI (used in robustness) |
| Census BPS | `total_permits` | Privately-owned residential units authorized by building permit (annual, CBSA × year) |
| Census BPS | `metro_dummy` | 1 = Metropolitan, 0 = Micropolitan |
| ACS 1-Year | `median_household_income` | Table B19013 |
| ACS 1-Year | `total_population` | Table B01003 |
| ACS 1-Year | `housing_units` | Table B25001 |

The unit of observation is an MSA–year pair. Sources are merged on CBSA code and year, yielding 530 MSAs across five years (2019, 2021–2024) for *N* = 2,036 observations after cleaning.

## 3. Empirical Strategy

The baseline specification is a log–log OLS regression with year fixed effects:

$$
\ln(\text{HPI}_{it}) \;=\; \beta_0 \;+\; \beta_1\ln(\text{Permits}_{it}) \;+\; \beta_2\ln(\text{Income}_{it}) \;+\; \beta_3\ln(\text{Pop}_{it}) \;+\; \gamma\,\text{Metro}_i \;+\; \sum_{t}\delta_t\,\text{Year}_t \;+\; u_{it}.
$$

The coefficient of interest, $\beta_1$, is the elasticity of the house-price index with respect to permitted units. The log–log form addresses right-skew in HPI and permits and yields a direct elasticity interpretation. To handle the small number of MSA–years with zero permits, we use $\ln(\text{Permits} + 1)$ in the main specification and verify in robustness that dropping zero-permit observations leaves the result unchanged.

**Identification and bias.** We compare nested ("short" vs. "long") regressions to assess omitted-variable bias on $\hat{\beta}_1$ as income, population, metro status, and year effects are added. We do not claim causal identification: permits are plausibly endogenous to expected prices (reverse causality), and we have no instrument for local supply constraints. The analysis is therefore best read as a description of the conditional cross-MSA association between permitting activity and prices.

## 4. Methods

The notebook executes the following pipeline end-to-end:

1. **Data ingestion.** Load FHFA HPI (`hpi_at_cbsa.xlsx`), Census BPS annual CBSA permit files, and a merged ACS extract for housing units, median household income, and total population.
2. **Cleaning and merging.** Coerce numeric types, filter to CBSA codes ≥ 10000 and years {2019, 2021–2024}, derive `metro_dummy` from BPS metro codes, and inner-join on (CBSA, year).
3. **Feature construction.** Log-transform HPI, permits (+1), income, and population. Create year dummies using `pd.get_dummies(..., drop_first=True)` with 2019 as the omitted base.
4. **Descriptive analysis.** Summary statistics and bivariate visualization of log permits against log HPI to motivate the OVB discussion.
5. **Estimation.** Three nested OLS models with HC0 heteroskedasticity-robust standard errors throughout:
   - **Model 1** — bivariate: log_hpi on log_permits.
   - **Model 2** — adds metro_dummy and year dummies.
   - **Model 3** — full specification: adds log_income and log_pop.
6. **Diagnostics.**
   - Variance inflation factors for multicollinearity (all below 5).
   - Breusch–Pagan and White tests for heteroskedasticity (both reject homoskedasticity, motivating HC0 SEs).
   - $F$-test of joint significance for the year dummies.
   - Q–Q plot of residuals.
7. **Robustness checks.**
   - **R1.** Replace the dependent variable with the annual HPI percent change.
   - **R2.** Drop zero-permit MSAs and use the strict log of permits.
   - **R3.** Trim the top and bottom 2.5% of log permits to test outlier sensitivity.

## 5. Results

**Main regression table (HC0 robust SEs in parentheses).**

| Variable | Model 1 | Model 2 | Model 3 |
|---|---:|---:|---:|
| `log_permits` | **0.149** (0.006) | **0.145** (0.006) | **0.081** (0.008) |
| `log_income`  |  |  | **1.560** (0.047) |
| `log_pop`     |  |  | **−0.028** (0.012) |
| `metro_dummy` |  | **0.162** (0.041) | **0.096** (0.037) |
| Year 2021     |  | 0.121 (0.030) | 0.047 (0.023) |
| Year 2022     |  | 0.286 (0.030) | 0.093 (0.024) |
| Year 2023     |  | 0.367 (0.030) | 0.111 (0.024) |
| Year 2024     |  | 0.193 (0.041) | −0.063 (0.037) |
| Constant      | 5.441 (0.039) | 5.247 (0.042) | −11.142 (0.482) |
| *R²*          | 0.221 | 0.301 | **0.577** |
| *N*           | 2,036 | 2,036 | 2,036 |

**Key findings.**

- **$\hat{\beta}_1 > 0$ in every specification.** A 1% increase in annual permits is associated with a 0.081% *increase* in HPI in the fully controlled model — statistically significant ($p < 0.001$) but economically small.
- **Omitted-variable bias is large and signed as predicted.** Adding income and population shrinks $\hat{\beta}_1$ from 0.149 to 0.081, a 46% reduction consistent with positive correlation between permits and unobserved demand.
- **Income dominates the price signal.** $\hat{\beta}_2 = 1.56$ is the largest and most precisely estimated coefficient in Model 3, confirming that cross-MSA price variation is primarily a demand-side phenomenon.
- **Year effects track the macro cycle.** Prices rose sharply through 2022 (post-COVID demand surge and low interest rates) and decelerated in 2023–2024 as the Federal Reserve tightened.
- **Robustness.** Sign and significance of $\hat{\beta}_1$ are stable across all three robustness specifications.

**Diagnostics.** VIFs range from 1.0 to 4.34 (all well below the conventional threshold of 10). Breusch–Pagan and White tests reject homoskedasticity ($p < 0.0001$). The joint $F$-test on year dummies is significant ($F = 11.3$, $p < 0.001$).

## 6. Conclusion

Across 530 U.S. MSAs over 2019–2024, building-permit activity is positively — not negatively — associated with home prices in OLS. The result is not an artifact of any single specification: it survives alternative dependent variables, the exclusion of zero-permit MSAs, and trimming of permit outliers. The most plausible interpretation is that demand-side pressures (income growth, in-migration to high-amenity metros) confound the cross-sectional supply signal and that permits are themselves endogenous to expected prices. Recovering the *causal* supply elasticity requires an instrument for local housing-supply constraints — for example, the geographic supply measures of Saiz (2010) or the regulatory indices of Glaeser, Gyourko, and Saks (2005). The policy implication is that supply expansion alone is unlikely to deliver large price relief in the short run without complementary demand-side instruments such as income support, mortgage-access reform, or targeted subsidies.

## 7. Repository Structure

```
.
├── README.md
├── requirements.txt
├── .gitignore
├── notebooks/
│   └── housing_supply_and_home_prices.ipynb   # End-to-end analysis (data prep, OLS, diagnostics, robustness)
├── data/
│   ├── hpi_at_cbsa.xlsx                       # FHFA HPI (CBSA, annual)
│   ├── cbsamonthly_202601.xls                 # Reference CBSA file
│   ├── permitsbyusreg_cust.xls                # Reference national permits file
│   ├── merged_2010_2024.csv                   # ACS merged extract (income, population, housing units)
│   ├── CBSA Permits/                          # Census BPS annual CBSA permit files
│   ├── Housing Units/                         # ACS Table B25001 (one file per year)
│   ├── Median Household Income/               # ACS Table B19013 (one file per year)
│   └── Total Population/                      # ACS Table B01003 (one file per year)
└── reports/
    ├── housing_supply_and_home_prices.html    # Rendered notebook (viewable without Jupyter)
    └── presentation.pptx                      # Project presentation slides
```

## 8. Reproducibility

To reproduce the analysis locally, clone the repository, create a virtual environment, install the required dependencies, and open the Jupyter notebook:

```bash
git clone https://github.com/SHLEW06/Housing-Supply-and-Home-Prices-Evidence-from-U.S.-Metropolitan-Areas.git
cd Housing-Supply-and-Home-Prices-Evidence-from-U.S.-Metropolitan-Areas

python -m venv venv
source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
jupyter notebook notebooks/housing_supply_and_home_prices.ipynb

```

The notebook is self-contained: it reads from `data/` and produces all tables, figures, and diagnostics in-place. All randomness is deterministic (no Monte Carlo); rerunning the notebook reproduces the numbers reported above exactly.

**Software.** Python 3.13, NumPy, pandas, matplotlib, SciPy, statsmodels. Exact versions are pinned in `requirements.txt`.

## 9. References

- Federal Housing Finance Agency. *House Price Index — All-Transactions CBSA Annual Data.* https://www.fhfa.gov/data/hpi/datasets
- U.S. Census Bureau. *Building Permits Survey — Annual CBSA Files.* https://www.census.gov/construction/bps
- U.S. Census Bureau. *American Community Survey 1-Year Estimates*, Tables B19013, B25001, B01003. https://data.census.gov
- Realtor.com. (2026). *2026 Housing Supply Gap Report.*
- Glaeser, E. L., Gyourko, J., & Saks, R. E. (2005). Why have housing prices gone up? *American Economic Review*, 95(2), 329–333.
- Saiz, A. (2010). The geographic determinants of housing supply. *Quarterly Journal of Economics*, 125(3), 1253–1296.
- Wooldridge, J. M. (2019). *Introductory Econometrics: A Modern Approach* (7th ed.). Cengage.

---

*Coursework completed for ECON 320, Emory University. Data are publicly available from the FHFA and the U.S. Census Bureau.*
