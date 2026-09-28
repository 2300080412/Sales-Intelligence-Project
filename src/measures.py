"""Phase 4: Python equivalents of the DAX measures. kpis(df) works on any filtered slice."""
import pandas as pd


def kpis(df: pd.DataFrame) -> dict:
    sales, cost = df.LineSales.sum(), df.TotalCost.sum()
    orders, qty = df.OrderID.nunique(), df.Quantity.sum()
    return {
        "Total Sales": sales, "Total Cost": cost, "Gross Profit": sales - cost,
        "Gross Margin %": (sales - cost) / sales if sales else None,
        "Total Orders": orders, "Total Quantity": qty,
        "Average Order Value": sales / orders if orders else None,
        "Average Selling Price": sales / qty if qty else None,
        "Profit per Unit": (sales - cost) / qty if qty else None,
        "Active Customers": df.CustomerID.nunique(),
    }


def by(df, key):
    """Sales / profit / margin / orders / qty / share, grouped by any column(s)."""
    g = df.groupby(key).agg(Sales=("LineSales", "sum"), Profit=("Profit", "sum"),
                            Qty=("Quantity", "sum"), Orders=("OrderID", "nunique")).reset_index()
    g["Margin"] = g.Profit / g.Sales
    g["Share"] = g.Sales / g.Sales.sum()
    g["Rank"] = g.Sales.rank(ascending=False, method="dense").astype(int)
    return g.sort_values("Sales", ascending=False)


def yoy(df, key=None):
    """YoY growth (like-for-like: 2023 compared with the same Jan1-Mar15 window of 2022)."""
    cutoff = df.OrderDate.max()
    md = lambda s: s.dt.month * 100 + s.dt.day
    cut = cutoff.month * 100 + cutoff.day
    ytd = df[md(df.OrderDate) <= cut]
    out = {"2021 vs 2022 (full year)": _g(df[df.Year == 2022].LineSales.sum(), df[df.Year == 2021].LineSales.sum()),
           "2023 YTD vs 2022 same window": _g(ytd[ytd.Year == 2023].LineSales.sum(), ytd[ytd.Year == 2022].LineSales.sum()),
           "2023 YTD vs 2021 same window": _g(ytd[ytd.Year == 2023].LineSales.sum(), ytd[ytd.Year == 2021].LineSales.sum())}
    return out


def _g(a, b):
    return (a - b) / b if b else None


def pareto(df, key="ProductName"):
    g = by(df, key).reset_index(drop=True)
    g["CumShare"] = g.Sales.cumsum() / g.Sales.sum()
    return g


def budget_vs_actual(df, fb, key="LocationID", years=(2021, 2022)):
    a = df[df.Year.isin(years)].groupby([key, "Year", "Month"]).LineSales.sum().rename("Actual").reset_index()
    b = fb[fb.Year.isin(years)].rename(columns={"MonthNumber": "Month"})
    m = a.merge(b, left_on=[key, "Year", "Month"], right_on=["LocationID", "Year", "Month"], how="outer") \
        if key != "LocationID" else a.merge(b, on=["LocationID", "Year", "Month"], how="outer")
    m["Variance"] = m.Actual - m.Budget
    return m
