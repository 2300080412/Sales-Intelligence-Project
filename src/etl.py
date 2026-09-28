"""Phase 1-2: load, clean, append, and build the star schema (mirrors the Power Query steps)."""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data" / "PBI_Training_Assignment_Dataset.xlsx"


def load():
    x = pd.ExcelFile(DATA)
    report = []  # data-quality log

    # ---- Fact_Sales: append 3 yearly tables ----
    parts = [x.parse(f"{y} Sales") for y in (2021, 2022, 2023)]
    assert all(list(p.columns) == list(parts[0].columns) for p in parts), "yearly tables differ"
    report.append("Yearly sales tables share identical structure (8 columns).")
    f = pd.concat(parts, ignore_index=True).rename(columns={
        "Order ID": "OrderID", "Product ID": "ProductID", "Location ID": "LocationID",
        "Sales Person ID": "SalespersonID", "Customer ID": "CustomerID",
        "Order Date": "OrderDate", "Price": "UnitPrice"})
    n0 = len(f)
    f = f.dropna().drop_duplicates("OrderID")
    report.append(f"Fact_Sales rows: {n0} -> {len(f)} after null/duplicate removal.")
    f["LineSales"] = f.Quantity * f.UnitPrice          # calculated column
    report.append(f"Date range: {f.OrderDate.min():%d-%b-%Y} to {f.OrderDate.max():%d-%b-%Y} (2023 is PARTIAL).")

    # ---- Dimensions ----
    p = x.parse("Products")[["Product ID", "Product Name", "Cost", "Current Price"]]
    p.columns = ["ProductID", "ProductName", "UnitCost", "ListPrice"]
    l = x.parse("Locations")[["Location ID", "Name", "County", "State Code", "State", "Latitude",
                              "Longitude", "Population", "Households", "Median Income"]]
    l.columns = ["LocationID", "City", "County", "StateCode", "State", "Latitude", "Longitude",
                 "Population", "Households", "MedianIncome"]
    c = x.parse("Customers"); c.columns = ["CustomerID", "CustomerName"]
    c["CustomerLabel"] = c.CustomerName + " (" + c.CustomerID + ")"
    s = x.parse("Sales People"); s.columns = ["SalespersonID", "SalespersonName"]
    report.append(f"Customers: {len(c)} IDs but only {c.CustomerName.nunique()} distinct names -> use CustomerLabel.")
    report.append(f"Locations: {l.State.nunique()} state ({l.State.iloc[0]}), {l.County.nunique()} counties, {len(l)} cities.")

    # ---- Budget sheet = 3 tables side by side ----
    b = x.parse("Budgeting")
    ba = b[["Location ID", "Name", "Revenue"]].dropna(subset=["Location ID"])
    ba.columns = ["LocationID", "BudgetLabel", "AnnualBudget"]
    bs = b[["Month", "Month Number", "Monthly Allocation2"]].dropna(subset=["Month Number"])
    bs.columns = ["MonthShort", "MonthNumber", "Allocation"]
    bs["MonthNumber"] = bs.MonthNumber.astype(int)
    valid = ba.LocationID.isin(l.LocationID)
    report.append(f"Budget: {len(ba)} IDs, {int((~valid).sum())} not in Locations (dropped); "
                  f"allocation sums to {bs.Allocation.sum():.2f}.")
    ba = ba[valid]

    # ---- Dim_Date (ends at last sales date, like the DAX version) ----
    d = pd.DataFrame({"Date": pd.date_range("2021-01-01", f.OrderDate.max())})
    d["Year"] = d.Date.dt.year; d["Quarter"] = "Q" + d.Date.dt.quarter.astype(str)
    d["MonthNumber"] = d.Date.dt.month; d["MonthName"] = d.Date.dt.strftime("%B")
    d["MonthShort"] = d.Date.dt.strftime("%b"); d["YearMonth"] = d.Date.dt.strftime("%Y-%m")
    d["Week"] = d.Date.dt.isocalendar().week.astype(int); d["Day"] = d.Date.dt.day

    # ---- Enriched fact for analysis ----
    fx = (f.merge(p, on="ProductID").merge(l, on="LocationID")
           .merge(c, on="CustomerID").merge(s, on="SalespersonID"))
    fx["TotalCost"] = fx.Quantity * fx.UnitCost
    fx["Profit"] = fx.LineSales - fx.TotalCost
    fx["Year"] = fx.OrderDate.dt.year; fx["Month"] = fx.OrderDate.dt.month
    fx["Quarter"] = fx.OrderDate.dt.quarter

    # ---- Fact_Budget: monthly budget per location per year, pro-rated for partial months ----
    last = f.OrderDate.max()
    cal = d.groupby(["Year", "MonthNumber"]).Date.count().rename("DaysElapsed").reset_index()
    cal["DaysInMonth"] = cal.apply(lambda r: pd.Period(f"{int(r.Year)}-{int(r.MonthNumber):02d}").days_in_month, axis=1)
    fb = ba.merge(cal, how="cross").merge(bs[["MonthNumber", "Allocation"]], on="MonthNumber")
    fb["Budget"] = fb.AnnualBudget * fb.Allocation * fb.DaysElapsed / fb.DaysInMonth
    fb = fb[["LocationID", "Year", "MonthNumber", "Budget"]]

    return dict(Fact_Sales=f, Dim_Product=p, Dim_Location=l, Dim_Customer=c, Dim_Salesperson=s,
                Dim_Date=d, Budget_Annual=ba, Budget_Season=bs, Fact_Budget=fb), fx, report
