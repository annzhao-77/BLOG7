# Blog 7: Which Everyday Expenses Have Increased the Most Since 2019?

This project uses Python and Plotly to compare six everyday price categories, inspired by the Chinese expression **衣食住行**: clothing, food, housing, and transportation. The article asks which selected expenses increased most relative to their 2019 average, and lets readers distinguish cumulative price increases from year-over-year inflation.

## Files

```text
BLOG7/
  index.qmd                     Blog source; edit the narrative here
  BLOG7.Rproj                   RStudio project
  README.md
  requirements.txt
  code/
    analysis.py                 Data preparation, calculations, and HTML generation
    chart_template.html         Tab layout, styling, and Plotly interactions
  data/
    raw/                        Seven original FRED CSV downloads
    processed/
      monthly_prices.csv        Monthly indexes and calculated changes
  results/
    figures/
      everyday_prices.html      Self-contained interactive Plotly figure
    tables/
      data_quality.csv          Coverage, duplicates, missing months, baseline counts
      sources.csv               Series IDs, source URLs, and file paths
      december_2025.csv          Endpoint comparisons for every series
      peaks.csv                 Maximum cumulative increase and month by series
      annual_changes.csv        Complete-year averages and changes since 2019, 2019–2024
```


## Data

Source: U.S. Bureau of Labor Statistics, Consumer Price Index for All Urban Consumers (CPI-U), retrieved through FRED. All series are **U.S. city average, monthly, not seasonally adjusted**, with index units of 1982–1984 = 100. The saved downloads cover **January 2018–December 2025**. The chart begins in January 2019; 2018 provides the previous-year observations needed for 2019's year-over-year changes.

| Figure label | Official category | FRED series / download |
| --- | --- | --- |
| Apparel | Apparel | [CPIAPPNS](https://fred.stlouisfed.org/series/CPIAPPNS) |
| Groceries | Food at home | [CUUR0000SAF11](https://fred.stlouisfed.org/series/CUUR0000SAF11) |
| Dining out | Food away from home | [CUUR0000SEFV](https://fred.stlouisfed.org/series/CUUR0000SEFV) |
| Shelter | Shelter | [CUUR0000SAH1](https://fred.stlouisfed.org/series/CUUR0000SAH1) |
| Electricity | Electricity | [CUUR0000SEHF01](https://fred.stlouisfed.org/series/CUUR0000SEHF01) |
| Gasoline | Gasoline (all types) | [CUUR0000SETB01](https://fred.stlouisfed.org/series/CUUR0000SETB01) |
| Overall CPI | All items | [CPIAUCNS](https://fred.stlouisfed.org/series/CPIAUCNS) |

Download CSVs without transforming the units. Save each as `SERIES_ID.csv` in `data/raw/`. Each file should contain `observation_date` and a column named after its FRED series. FRED aliases `CPIAPPNS` and `CPIAUCNS` correspond to BLS IDs `CUUR0000SAA` and `CUUR0000SA0`.

### Data checks and the October 2025 gap

The supplied snapshot has 96 monthly rows per series, no duplicate dates, and 12 valid baseline observations in 2019. There are **672 rows and 666 nonmissing index values** across the seven series. All six missing values are in October 2025; gasoline has an observation for that month.

This is a documented source gap following the [2025 federal government shutdown](https://www.bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi-faq.htm), not a download error. The script keeps those dates with missing values, performs no interpolation or forward filling, and leaves visible breaks in the affected lines. December 2025 and December 2024 values are available for all seven series, so both endpoint calculations are available. No 2025 annual mean is used.

The script stops for unexpected columns, duplicate dates, nonmonthly dates, nonpositive indexes, or missing months beyond this known gap. It is intentionally configured for this saved period; review those checks before extending the study.

## Run in RStudio

Use RStudio's **Terminal** tab, not the R Console. Open the BLOG7 project so the working directory is BLOG7.

**1. Install the Python packages once:**

```sh
python -m pip install -r requirements.txt
```

**2. Run the complete analysis:**

```sh
python code/analysis.py
```

This reads the saved CSVs, checks coverage, calculates price changes, and saves the tables and interactive figure. It does not modify the raw data or the blog text. The “What the Chart Shows” section is written directly in `index.qmd`; update it using the generated tables if the data or calculations change. No separate results QMD is generated. No API key, live data request, regression, or browser server is required.

**3. View the figure:** open `results/figures/everyday_prices.html` in a browser. Plotly is bundled in the HTML, so the controls work offline. The file is several megabytes because it includes that library.

**4. Render the blog** with Quarto (included with RStudio):

```sh
quarto render index.qmd
```

Open the resulting `index.html`. The article uses a relative iframe link to the interactive figure; keep the `results/figures/` directory alongside it. Rendering does not rerun the Python analysis.

## Calculations and interpretation

For each category, the baseline is the arithmetic mean of its 12 monthly indexes in 2019:

```text
Cumulative change (%) = 100 × (monthly index / 2019 mean index − 1)
Year-over-year change (%) = 100 × (monthly index / index 12 months earlier − 1)
Month-over-month change (%) = 100 × (monthly index / previous month index − 1)
Annual cumulative change (%) = 100 × (calendar-year mean / 2019 mean − 1)
```

The script explicitly reindexes to a monthly calendar before taking the 12-month lag, so missing dates cannot turn a row shift into a comparison with the wrong month. Overall CPI is the official BLS series, not an average of the six chosen categories. The figure changes only the displayed measure and categories; selecting a category does not change its baseline or recompute a household basket.

The cumulative endpoint ranking compares **December 2025 with the 2019 annual average**, not the 2025 annual average with 2019. Rounded cumulative increases are electricity 38.3%, dining out 37.1%, shelter 32.1%, groceries 30.6%, gasoline 12.7%, and apparel 3.3%; overall CPI rose 26.8%. Exact values are generated in `december_2025.csv`.

Gasoline illustrates the value of switching views: it remained 12.7% above its 2019 average in December 2025 but was 3.4% below December 2024. The All categories tab retains category checkboxes and cumulative/year-over-year views. Each category has its own accent color and two views: a monthly line chart and an annual bar chart. Both measure cumulative change from the **2019 annual mean**, so switching frequency does not change the baseline. Monthly view optionally filters to one calendar year. Annual view uses complete 2019–2024 averages; 2019 is exactly zero. The same annual window is used for every category, including gasoline. November 2025 remains available in the monthly cumulative view even though October is missing. Month-over-month changes remain in the processed data for reference but are not the default category charts.

Category cards show the latest, highest, and lowest cumulative changes within the selected window. A lowest positive value means prices were still above the baseline, not that prices declined. Ties use the earliest date. Zoom changes the plotted range but not the cards. Overview cards rank checked expense categories at December 2025; overall CPI remains a separate benchmark. Its year-over-year view is a supplementary short-term comparison. Tabs and controls support keyboard navigation. Plotly is bundled locally for offline viewing.

## Update the local website

When this repository sits beside `website1/`, run:

```sh
python code/analysis.py --website
```

This reruns the analysis and copies `index.qmd` and the interactive HTML to `website1/blog/posts/post7/`. It changes figure references from `results/figures/` to `figures/` in the website copy. **Edit the BLOG7 article first:** this option overwrites the corresponding website copy.

Then, from the `website1` directory, render the new post and listing:

```sh
quarto render blog/posts/post7/index.qmd
quarto render blog/index.qmd
```

These targeted renders do not require the R packages used by other pages. A full `quarto render` is also possible once those pages' dependencies (including `knitr` and `rmarkdown`) are installed. Verify the embedded chart and controls before committing or publishing. The script does not commit, push, or deploy either repository.

## Limitations

- National urban averages do not represent every household or location. These are selected price categories, not a complete budget; shelter measures housing services rather than house sale prices, and gasoline covers only part of transportation.
- The indexes are not seasonally adjusted. Month-specific rankings can reflect seasonal patterns, especially for apparel and energy. The full time series gives context for the December endpoint.
- October 2025 has the documented missing observations described above. Gaps are left unfilled.
- Prices alone do not measure spending, purchasing quantities, wages, or affordability. The comparison does not identify the causal contribution of COVID-19 or other events.

## References

- [BLS CPI data](https://www.bls.gov/cpi/data.htm)
- [EIA: U.S. retail gasoline prices in 2022](https://www.eia.gov/todayinenergy/detail.php?id=55099), cited in the article for context on the 2022 spike
- FRED series pages in the data table above
- [BLS explanation of the October 2025 data gap](https://www.bls.gov/cpi/additional-resources/2025-federal-government-shutdown-impact-cpi-faq.htm)
- [Plotly interactive HTML export](https://plotly.com/python/interactive-html-export/)
