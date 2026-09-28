# Sales Intelligence Dashboard: Build Guide, Answers and Insights

All numbers below were computed from your workbook (10,889 orders, 1 Jan 2021 to 15 Mar 2023). After you build the report, check your visuals against them.

## 1. Data traps you must handle (and mention in your presentation)

| # | Finding | What to do |
|---|---------|-----------|
| 1 | **2023 is partial**: only 1 Jan to 15 Mar 2023 (1,000 orders). | Never compare 2023 with a full year. Use YTD vs PY YTD. Dim_Date ends at the last sales date so this works automatically. |
| 2 | **Budgeting sheet is three tables in one sheet**: A-C annual budget per location, D-E empty, F-H month allocation (sums to 100%). 449 nulls. | Split into Budget_Annual and Budget_Season, drop the empty columns. |
| 3 | **Budget location names do not match Locations**: 97 budget IDs (A100-A196) but only 74 exist in Locations, and all 97 budget names differ from the Locations names (for example A100 is "Bridgeport" in Budgeting but "Anaheim" in Locations). Budget cities are East Coast; Locations are all California. | Join on Location ID (the only feasible key), drop the 23 orphan IDs, and **state this as an assumption**. Ask your trainer which sheet is the source of truth. |
| 4 | **Budget has no year**. | Assumed the same annual budget applies each year. |
| 5 | **Only one state (California)**. State-level visuals are meaningless. | Use **County** (22) and City (74) instead; keep a State slicer only because the brief asks. |
| 6 | **Customer names are not unique**: 801 IDs but 509 names. | Use CustomerLabel = Name (ID). Grouping by name inflates customers (Jesse Hill shows $171K by name vs $67.8K by ID). |
| 7 | Discount = 0 for all products; Original Sale Price = Current Price = order Price; Taxes unused. | Drop Discount, Original Sale Price and Taxes. |
| 8 | No nulls or duplicate orders in the sales tables; all three yearly tables share an identical 8-column structure; no orphan keys. | Document as "checked, clean". |
| 9 | Date Ranges sheet is just 7d/14d/30d/90d/180d/360d. | Optional: use it as a "Last N days" what-if selector. Not needed in the model. |

## 2. Data model (star schema)

```
Dim_Product ──┐
Dim_Customer ─┤
Dim_Location ─┼──► Fact_Sales ◄── Dim_Date ──► Fact_Budget ◄── Dim_Location
Dim_Salesperson ┘
```
- All relationships one-to-many, single direction (dimension to fact).
- Fact_Sales: OrderID, ProductID, LocationID, SalespersonID, CustomerID, OrderDate, Quantity, UnitPrice, LineSales.
- Fact_Budget (calculated table): Date, LocationID, DailyBudget. Dim_Location filters both facts, which is what makes Budget vs Actual by location work.
- Hide the foreign-key columns; sort MonthName by MonthNumber; mark Dim_Date as the date table.
- Keep Budget_Annual and Budget_Season in the model but hide them.

## 3. Page design (deliberately different from a standard 7-tab layout)

Use the theme file (dark navy header band, teal for good, amber for caution, red for bad). Put a left-hand **navigation rail** (page-navigator buttons) on every page and a top-right **"Reset filters"** bookmark.

| Page | Name to use | Key visuals |
|------|------------|-------------|
| 1 | **Pulse** (executive) | 8 KPI cards with ▲/▼ from `KPI Arrow`; monthly line with 3-month moving average; sales by year column; top 10 products bar; county bar; Actual vs Budget gauge |
| 2 | **Momentum** (trends) | Drillable Year>Quarter>Month>Day line; YoY clustered column by month (2021 vs 2022 vs 2023); running total; spike-day scatter (`Is Spike Day`) |
| 3 | **Product Lab** | Scatter Sales vs Profit (size = quantity, colour = margin); Pareto (columns + `Cumulative Product %` line); Top N with parameter slicer; bottom 10; profitability table with data bars |
| 4 | **Customer Radar** | Top 10 customers (by CustomerLabel); `Top 10 Customer Share` card; sales vs margin scatter; customer contribution table |
| 5 | **Sales Team** | Ranked bar by `Salesperson Rank`; sales vs margin scatter; YoY % bar with conditional colour (`YoY Colour`); orders card |
| 6 | **Territory** | Bubble map (latitude/longitude, size = sales); county bar; Sales vs Population scatter; location matrix with conditional formatting; `Sales per 1K Residents` |
| 7 | **Target Tracker** | Actual vs Budget column by location; variance bar; monthly budget vs actual line; location matrix with icons from `Actual vs Budget Status` |

**Interactivity checklist:** slicers for Year, Month, County/State, City (Location), Product, Customer, Salesperson; drill-through pages for Product, Customer, Salesperson and Location (each with a report tooltip page showing sales, profit, margin, orders and a sparkline); edit interactions so the KPI cards are not cross-filtered by the trend chart; dynamic titles from section 8 of the DAX file.

## 4. Answers to the 25 management questions

**Business performance**
1. Total revenue: **$25,661,209**.
2. Total profit: **$8,343,893**.
3. Overall margin: **32.5%** (2021: 32.5%, 2022: 32.5%).
4. Is revenue growing? **No, it is flat.** 2022 was $11.57M vs $11.69M in 2021 (**-1.1%**). Orders fell 1.4% (4,980 to 4,909). 2023 YTD (to 15 Mar) is $2.40M, which is **+3.7%** vs the same window of 2022 ($2.32M) but still below 2021's $2.47M.
5. Best year: **2021** ($11.69M sales, $3.81M profit). 2023 cannot be judged yet.

**Products (101 products)**
6. Top 10 by revenue: Product 63 ($628K), 28 ($604K), 47 ($557K), 29 ($534K), 84 ($529K), 59 ($524K), 56 ($484K), 66 ($474K), 33 ($468K), 81 ($466K). Together they are 20.5% of sales.
7. Top 10 by profit: Product 28 ($248K), 41 ($214K), 79 ($209K), 47 ($206K), 64 ($203K), 51 ($197K), 31 ($197K), 29 ($187K), 34 ($184K), 96 ($178K).
8. Poor margins: Product 4 (15.0%), 95 (16.0%), 27 (17.0%), 84 (17.0%), 36, 12, 25, 6 (all around 18%). **High sales but low margin:** Product 84 ($529K at 17%), Product 66 ($474K at 18%), Product 4 ($417K at 15%).
9. Highest demand (units): Product 24 (289), 55 (256), 63 (255), 79 (253), 23 (250). Product 55 is a volume item with only $32.5K revenue, so it is cheap and low-value.

**Customers (801, all active)**
10. Top 10 by sales: Mark Morales C1374 ($69.7K), Jesse Hill C1246 ($67.8K), Craig Reyes C1712 ($66.2K), Fred Russell, Jeremy Arnold, Victor Gray, Andrew Adams, Russell Boyd, Jeffrey Sanders, William Medina.
11. Top 10 customers are only **2.6%** of sales. Revenue is very evenly spread, so there is no customer concentration risk.
12. Top profit: Andrew Adams C1212 ($23.4K), Jeffrey Sanders C1364 ($23.4K), Andrew Butler C1345 ($23.1K), Craig Reyes ($22.8K), Mark Morales ($22.6K). Most orders: Aaron Miller C1543 (27).

**Sales team (45 people)**
13. Best salesperson: **Kenneth Bradley** ($679K).
14. Highest profit: **Kenneth Bradley** ($227K), then Ryan Welch ($222K) and Bobby Russell ($214K).
15. Most orders: **Ryan Welch** (273), then Eugene Holmes (271) and Brian Davis (269).
Margins only range from 31.0% to 34.3% across the team, so differences are about volume, not pricing discipline. 23 of 45 grew from 2021 to 2022. Best improvers: Carl Hall (+40%), Sean Miller (+33%), Joe Sims (+31%). Biggest declines: Brian Thomas (-25%), **Kenneth Bradley (-19%)**, Jimmy Young (-19%), Robert Reed (-18%). These four need coaching.

**Geography**
16. There is only one state, **California**. By county, **Los Angeles County leads with $5.63M (22%)**, then Orange ($2.60M), San Diego ($2.46M), San Bernardino ($2.41M), Riverside ($2.08M).
17. Underperforming locations (lowest sales): Antioch ($277K), Costa Mesa ($278K), San Francisco ($284K), Norwalk ($290K), Sunnyvale ($290K). Best: Rialto ($466K), Roseville ($437K), Victorville ($423K), El Monte ($420K), Escondido ($412K).
18. Growth potential (huge population, low sales per resident): **Los Angeles** (3.97M people, $96 per 1,000 residents, the lowest of all 74 locations), San Diego ($237), San Francisco ($328), San Jose ($389). Population and sales are essentially uncorrelated (r = 0.07), so population does not drive sales today and big cities are under-penetrated. Income is also uncorrelated (r = -0.17).

**Budget** (with the ID-join assumption from section 1)
19. Achievement is about **360%** (2021: 364%, 2022: 360%). Annual budget averages $43K per location against about $157K actual.
20. All 74 locations exceed budget (lowest achievement is about 170%).
21. None missed, and 2022 minimum was 168%.
22. Because budget is spread by fixed seasonality (peaks Jun at 14%, dips Dec/Jan at 4%) but actual sales are flat across months, the largest variances occur in the **low-allocation months (Nov to Jan)**, where actual is far above budget. Read the exact months from your Target Tracker chart.
**Flag this clearly**: a 3.6x overachievement across every location suggests the budget is understated, is not annual, or does not belong to these locations. Do not present it as a business win without confirming.

**Strategic**
23. Strengths: (1) healthy, stable 32.5% margin with no loss-making lines; (2) very diversified: no customer above 0.3% and top 10 locations only 16% of sales; (3) consistent sales team, with every rep within 31-34% margin and demand every single day (804 of 804 days had sales).
24. Concerns: (1) no growth (-1.1% in 2022); (2) 15 to 18% margin products with heavy volume (Products 4, 84, 66); (3) budget data quality and a seasonality mismatch, plus a long tail (45 products make 20% of sales, and Product 18 sold only $7.8K).
25. Recommendations are in section 5.

## 5. Business insights document (use as your deliverable)

**Top 5 findings**
1. Revenue is $25.7M with $8.3M profit (32.5% margin), but sales were flat to slightly down in 2022 (-1.1%).
2. 2023 YTD to 15 March is +3.7% on the same window in 2022, an early sign of recovery, but still 2.7% below 2021.
3. Sales are highly diversified: top 10 customers = 2.6% of revenue, top 10 products = 20.5%, 56 of 101 products deliver 80%.
4. Seasonality is mild: Q4 is best ($6.0M for 2021-22) and Q3 weakest ($5.6M); Jun, Nov and Dec are the strongest months, Aug, Jul and May the weakest. Spikes reach about 2.6x the daily average (20 Jun 2021 $83.7K, 20 Apr 2022 $79.6K, 5 Mar 2023 $75.6K).
5. Los Angeles County is 22% of sales, yet the city of Los Angeles sells $96 per 1,000 residents, among the lowest, so population is not translating into sales.

**Top 5 problems**
1. No year-over-year growth in 2022; orders declined 1.4%.
2. High-volume, low-margin products (84, 66, 4) tie up sales at 15 to 18% margin versus 45 to 50% for the best products.
3. Four reps declined 18 to 25% in 2022, including the top-ranked rep.
4. Large metro locations (Los Angeles, San Diego, San Francisco, San Jose) are heavily under-penetrated.
5. Budget data is inconsistent (23 IDs missing, names mismatch, no year, 360% achievement), so budget tracking cannot be trusted yet.

**Top 5 recommendations**
1. Reprice or renegotiate cost on Products 4, 84, 66 and 95 (target +5 points of margin); prioritize promotion of Products 28, 41, 79, 64 and 96 (41 to 50% margins with strong sales).
2. Launch a growth push in the four large metros, with a sales-per-resident target.
3. Coach the four declining reps and pair them with the top improvers (Carl Hall, Sean Miller, Joe Sims).
4. Rebuild the budget: one budget per location per year, tied to the correct location master, with realistic monthly seasonality based on actuals.
5. Review the bottom 10 products by sales (for example Products 18, 74, 87, 94, 72) for delisting or bundling.

## 6. Presentation outline (8 slides, 10 minutes)
1. Business problem and the one question management asked.
2. Data preparation, including the four data traps (partial 2023, budget mismatch, one state, duplicate customer names).
3. Data model (star schema diagram) and the Fact_Budget design decision.
4. DAX: calculated column vs measure, and 3 advanced examples (Pareto, dynamic Top N, YTD vs PY YTD).
5. Live demo: Pulse, then drill from Year to Day, then drill-through to Product.
6. Key findings (five).
7. Problems and recommendations.
8. Limitations and assumptions (budget, partial 2023).

## 7. Making yours look different from any other submission
- Use the Midnight Teal theme, your own page names (Pulse, Momentum, Product Lab and so on), a navigation rail and different chart choices from the list above.
- Do the build yourself in Power BI Desktop with these scripts so you can explain every step in the presentation. The trainer will ask about your DAX and model.
- Write your insights in your own words and add your own observations from your report.
