"""Run:  python src/main.py     (from the project folder)
Creates: outputs/clean/*.csv, outputs/answers.md, outputs/dashboard.html"""
from pathlib import Path
import pandas as pd
import etl, measures as M, dashboard

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"; (OUT / "clean").mkdir(parents=True, exist_ok=True)


def money(v): return f"${v:,.0f}"


def main():
    tables, fx, report = etl.load()
    for n, t in tables.items():
        t.to_csv(OUT / "clean" / f"{n}.csv", index=False)
    print("== Data quality log =="); [print(" -", r) for r in report]

    k = M.kpis(fx); y = M.yoy(fx)
    ba = M.budget_vs_actual(fx, tables["Fact_Budget"]); ach = ba.Actual.sum() / ba.Budget.sum()
    yr = M.by(fx, "Year").sort_values("Year"); pr = M.by(fx, "ProductName"); cu = M.by(fx, "CustomerLabel")
    sp = M.by(fx, "SalespersonName"); lo = M.by(fx, "City"); co = M.by(fx, "County")
    par = M.pareto(fx)
    mo = fx[fx.Year < 2023].groupby("Month").LineSales.sum(); qt = fx[fx.Year < 2023].groupby("Quarter").LineSales.sum()
    lb = ba.groupby("LocationID")[["Actual", "Budget"]].sum(); lb["Ach"] = lb.Actual / lb.Budget
    pp = lo.merge(tables["Dim_Location"][["City", "Population"]], on="City"); pp["Per1K"] = pp.Sales / pp.Population * 1000
    yy = fx[fx.Year < 2023].pivot_table(index="SalespersonName", columns="Year", values="LineSales", aggfunc="sum"); yy["YoY"] = yy[2022] / yy[2021] - 1
    top = lambda d, c, n=5, asc=False: ", ".join(f"{r[0]} ({r[1]})" for r in d.sort_values(c, ascending=asc).head(n)[[d.columns[0], c]].values)
    L = []; a = L.append
    a("# Answers generated from the data\n")
    a("## Business performance")
    a(f"1. Total revenue: {money(k['Total Sales'])}\n2. Total profit: {money(k['Gross Profit'])}\n3. Margin: {k['Gross Margin %']:.1%}")
    a("4. YoY: " + "; ".join(f"{n}: {v:+.1%}" for n, v in y.items()))
    a("5. Sales by year: " + ", ".join(f"{int(r.Year)} {money(r.Sales)}" for r in yr.itertuples()) + " (2023 is partial)")
    a("\n## Products")
    a("6. Top 10 by revenue: " + ", ".join(f"{r.ProductName} ({money(r.Sales)})" for r in pr.head(10).itertuples()))
    a("7. Top 10 by profit: " + ", ".join(f"{r.ProductName} ({money(r.Profit)})" for r in pr.sort_values('Profit', ascending=False).head(10).itertuples()))
    a("8. Lowest margins: " + ", ".join(f"{r.ProductName} ({r.Margin:.1%})" for r in pr.sort_values('Margin').head(8).itertuples()))
    hs = pr[(pr.Sales > pr.Sales.median()) & (pr.Margin < 0.20)]
    a("   High sales but margin < 20%: " + ", ".join(f"{r.ProductName} ({money(r.Sales)}, {r.Margin:.0%})" for r in hs.itertuples()))
    a("9. Highest demand (units): " + ", ".join(f"{r.ProductName} ({r.Qty})" for r in pr.sort_values('Qty', ascending=False).head(5).itertuples()))
    a(f"   Pareto: {int((par.CumShare <= .8).sum() + 1)} of {len(par)} products give 80% of sales; top 10 = {pr.head(10).Share.sum():.1%}")
    a("\n## Customers")
    a("10. Top 10: " + ", ".join(f"{r.CustomerLabel} ({money(r.Sales)})" for r in cu.head(10).itertuples()))
    a(f"11. Top-10 share of sales: {cu.head(10).Share.sum():.1%} across {len(cu)} customers")
    a("12. Top profit: " + ", ".join(f"{r.CustomerLabel} ({money(r.Profit)})" for r in cu.sort_values('Profit', ascending=False).head(5).itertuples()))
    a("\n## Sales team")
    a("13. Best salesperson: " + f"{sp.iloc[0].SalespersonName} ({money(sp.iloc[0].Sales)})")
    a("14. Highest profit: " + ", ".join(f"{r.SalespersonName} ({money(r.Profit)})" for r in sp.sort_values('Profit', ascending=False).head(3).itertuples()))
    a("15. Most orders: " + ", ".join(f"{r.SalespersonName} ({r.Orders})" for r in sp.sort_values('Orders', ascending=False).head(3).itertuples()))
    a("   Improvers: " + ", ".join(f"{i} ({v:+.0%})" for i, v in yy.YoY.nlargest(3).items()) + " | Decliners: " + ", ".join(f"{i} ({v:+.0%})" for i, v in yy.YoY.nsmallest(4).items()))
    a("\n## Geography")
    a("16. States: " + ", ".join(f"{s}" for s in tables['Dim_Location'].State.unique()) + " only. Top counties: " + ", ".join(f"{r.County} ({money(r.Sales)})" for r in co.head(5).itertuples()))
    a("17. Lowest locations: " + ", ".join(f"{r.City} ({money(r.Sales)})" for r in lo.tail(5).itertuples()))
    a("18. Big cities with lowest sales per 1K residents: " + ", ".join(f"{r.City} (pop {r.Population:,}, ${r.Per1K:,.0f}/1K)" for r in pp[pp.Population > 500000].sort_values('Per1K').head(4).itertuples()))
    a(f"    Correlation population vs sales: {pp.Population.corr(pp.Sales):.2f}")
    a("\n## Budget (Location-ID join assumption)")
    a(f"19. Overall achievement 2021-22: {ach:.0%}\n20/21. Locations above budget: {(lb.Ach >= 1).sum()} / below: {(lb.Ach < 1).sum()} (min achievement {lb.Ach.min():.0%})")
    mv = ba.groupby("Month")[["Actual", "Budget"]].sum(); mv["Var"] = mv.Actual - mv.Budget
    a("22. Largest monthly variances: " + ", ".join(f"month {i} ({money(v)})" for i, v in mv.Var.abs().nlargest(3).items()))
    a("\n## Seasonality (2021-22 combined)")
    a("Best months: " + ", ".join(f"{i} ({money(v)})" for i, v in mo.nlargest(3).items()) + " | Weakest: " + ", ".join(f"{i} ({money(v)})" for i, v in mo.nsmallest(3).items()))
    a("Quarters: " + ", ".join(f"Q{i} {money(v)}" for i, v in qt.items()))
    dd = fx.groupby("OrderDate").LineSales.sum()
    a("Biggest sales days: " + ", ".join(f"{d:%d-%b-%Y} ({money(v)})" for d, v in dd.nlargest(3).items()))
    (OUT / "answers.md").write_text("\n".join(L), encoding="utf-8")
    print("\n" + "\n".join(L))

    dashboard.build(fx, tables, OUT / "dashboard.html")
    print(f"\nDone. Open {OUT / 'dashboard.html'} in your browser.")


if __name__ == "__main__":
    main()
