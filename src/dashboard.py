"""Phase 5-12: interactive multi-page HTML dashboard (plotly). Open outputs/dashboard.html in a browser."""
import pandas as pd, plotly.express as px, plotly.graph_objects as go
from measures import kpis, by, pareto, yoy, budget_vs_actual

TEAL, AMBER, NAVY, RED = "#1D9A8A", "#F2A541", "#1B263B", "#E4572E"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _fig(f, h=380):
    f.update_layout(height=h, margin=dict(l=40, r=20, t=50, b=40), template="plotly_white",
                    title_font=dict(size=15, color=NAVY), font=dict(family="Segoe UI"))
    return f


def build(fx, tables, out):
    k, fb = kpis(fx), tables["Fact_Budget"]
    y = yoy(fx)
    ba = budget_vs_actual(fx, fb)
    ach = ba.Actual.sum() / ba.Budget.sum()
    pages = {}

    # ---- Page 1: Pulse ----
    cards = [("Total Sales", f"${k['Total Sales']/1e6:.2f}M"), ("Gross Profit", f"${k['Gross Profit']/1e6:.2f}M"),
             ("Margin", f"{k['Gross Margin %']:.1%}"), ("Orders", f"{k['Total Orders']:,}"),
             ("Quantity", f"{k['Total Quantity']:,}"), ("Avg Order Value", f"${k['Average Order Value']:,.0f}"),
             ("Budget Achievement*", f"{ach:.0%}"), ("2023 YTD vs 2022", f"{y['2023 YTD vs 2022 same window']:+.1%}")]
    card_html = "".join(f"<div class='card'><span>{a}</span><b>{b}</b></div>" for a, b in cards)
    m = fx.groupby(["Year", "Month"]).LineSales.sum().reset_index()
    m["YM"] = pd.to_datetime(dict(year=m.Year, month=m.Month, day=1))
    m["MA3"] = m.LineSales.rolling(3).mean()
    f1 = go.Figure([go.Scatter(x=m.YM, y=m.LineSales, name="Monthly sales", line=dict(color=TEAL, width=3)),
                    go.Scatter(x=m.YM, y=m.MA3, name="3-mo moving avg", line=dict(color=AMBER, dash="dash"))])
    f1.update_layout(title="Monthly sales (2023 = Jan to mid-Mar only)")
    yr = by(fx, "Year")
    f2 = px.bar(yr, x="Year", y="Sales", text_auto=".3s", color_discrete_sequence=[TEAL], title="Sales by year")
    top = by(fx, "ProductName").head(10).iloc[::-1]
    f3 = px.bar(top, x="Sales", y="ProductName", orientation="h", color="Margin", color_continuous_scale="Tealgrown" if False else "Teal", title="Top 10 products (colour = margin)")
    co = by(fx, "County").head(10).iloc[::-1]
    f4 = px.bar(co, x="Sales", y="County", orientation="h", color_discrete_sequence=[NAVY], title="Top 10 counties (only one state: California)")
    pages["Pulse"] = (card_html + "<p class='note'>*Budget achievement uses the Location-ID join; see README caveat.</p>", [f1, f2, f3, f4])

    # ---- Page 2: Momentum ----
    mm = fx.groupby(["Year", "Month"]).LineSales.sum().reset_index(); mm["M"] = mm.Month.map(lambda i: MONTHS[i - 1])
    g1 = px.line(mm, x="M", y="LineSales", color="Year", markers=True, category_orders={"M": MONTHS}, title="YoY by month")
    q = fx[fx.Year < 2023].groupby(["Year", "Quarter"]).LineSales.sum().reset_index()
    g2 = px.bar(q, x="Quarter", y="LineSales", color=q.Year.astype(str), barmode="group", title="Quarterly sales 2021-22")
    dd = fx.groupby("OrderDate").LineSales.sum().reset_index()
    dd["Roll30"] = dd.LineSales.rolling(30).mean(); dd["Cum"] = dd.LineSales.cumsum()
    thr = 2 * dd.LineSales.mean(); sp = dd[dd.LineSales > thr]
    g3 = go.Figure([go.Scatter(x=dd.OrderDate, y=dd.LineSales, name="Daily", line=dict(color="#98C1D9", width=1)),
                    go.Scatter(x=dd.OrderDate, y=dd.Roll30, name="30-day avg", line=dict(color=NAVY, width=3)),
                    go.Scatter(x=sp.OrderDate, y=sp.LineSales, mode="markers", name="Spike (>2x avg)", marker=dict(color=RED, size=9))])
    g3.update_layout(title="Daily sales with spikes")
    g4 = px.area(dd, x="OrderDate", y="Cum", title="Running total sales", color_discrete_sequence=[TEAL])
    pages["Momentum"] = ("", [g1, g2, g3, g4])

    # ---- Page 3: Product Lab ----
    p = pareto(fx)
    h1 = go.Figure([go.Bar(x=p.ProductName, y=p.Sales, name="Sales", marker_color=TEAL),
                    go.Scatter(x=p.ProductName, y=p.CumShare, name="Cumulative %", yaxis="y2", line=dict(color=AMBER))])
    h1.update_layout(title="Pareto: products vs cumulative sales", yaxis2=dict(overlaying="y", side="right", tickformat=".0%"), xaxis=dict(showticklabels=False))
    h2 = px.scatter(p, x="Sales", y="Profit", size="Qty", color="Margin", hover_name="ProductName", color_continuous_scale="RdYlGn", title="Sales vs Profit (size = qty, colour = margin)")
    low = p[(p.Sales > p.Sales.median()) & (p.Margin < p.Margin.median())].head(10)
    h3 = px.bar(low, x="ProductName", y="Margin", color="Sales", title="High sales but low margin (pricing / cost review)")
    bot = p.tail(10)
    h4 = px.bar(bot, x="ProductName", y="Sales", color_discrete_sequence=[RED], title="Bottom 10 products by sales")
    pages["Product Lab"] = ("", [h1, h2, h3, h4])

    # ---- Page 4: Customers ----
    c = by(fx, "CustomerLabel")
    t10 = c.head(10).iloc[::-1]
    i1 = px.bar(t10, x="Sales", y="CustomerLabel", orientation="h", color="Margin", color_continuous_scale="Teal", title=f"Top 10 customers = {c.head(10).Sales.sum()/c.Sales.sum():.1%} of sales")
    i2 = px.scatter(c, x="Sales", y="Margin", size="Orders", hover_name="CustomerLabel", color_discrete_sequence=[NAVY], title="Customer sales vs margin")
    i3 = px.histogram(c, x="Sales", nbins=30, color_discrete_sequence=[TEAL], title="Customer sales distribution (very even)")
    pages["Customers"] = ("", [i1, i2, i3])

    # ---- Page 5: Sales Team ----
    s = by(fx, "SalespersonName")
    yy = fx[fx.Year < 2023].pivot_table(index="SalespersonName", columns="Year", values="LineSales", aggfunc="sum")
    yy["YoY"] = yy[2022] / yy[2021] - 1; yy = yy.sort_values("YoY").reset_index()
    j1 = px.bar(s.head(15).iloc[::-1], x="Sales", y="SalespersonName", orientation="h", color="Margin", color_continuous_scale="Teal", title="Top 15 salespeople")
    j2 = px.bar(yy, x="SalespersonName", y="YoY", color=yy.YoY > 0, color_discrete_map={True: TEAL, False: RED}, title="YoY 2022 vs 2021 by salesperson").update_layout(showlegend=False, xaxis=dict(showticklabels=False))
    j3 = px.scatter(s, x="Orders", y="Sales", size="Profit", hover_name="SalespersonName", color="Margin", title="Orders vs Sales (size = profit)")
    pages["Sales Team"] = ("", [j1, j2, j3])

    # ---- Page 6: Territory ----
    L = by(fx, ["City", "Latitude", "Longitude", "Population"]).reset_index(drop=True)
    L["SalesPer1K"] = L.Sales / L.Population * 1000
    k1 = px.scatter_geo(L, lat="Latitude", lon="Longitude", size="Sales", color="SalesPer1K", hover_name="City",
                        scope="usa", color_continuous_scale="RdYlGn", title="Sales by city (colour = sales per 1K residents)")
    k1.update_geos(fitbounds="locations")
    k2 = px.scatter(L, x="Population", y="Sales", hover_name="City", log_x=True, trendline="ols" if False else None,
                    color_discrete_sequence=[NAVY], title=f"Sales vs Population (r = {L.Population.corr(L.Sales):.2f})")
    k3 = px.bar(L.head(15).iloc[::-1], x="Sales", y="City", orientation="h", color_discrete_sequence=[TEAL], title="Top 15 locations")
    k4 = px.bar(L.tail(10), x="City", y="Sales", color_discrete_sequence=[RED], title="Bottom 10 locations")
    pages["Territory"] = ("", [k1, k2, k3, k4])

    # ---- Page 7: Target Tracker ----
    lb = ba.groupby("LocationID")[["Actual", "Budget"]].sum().reset_index().merge(tables["Dim_Location"][["LocationID", "City"]])
    lb["Ach"] = lb.Actual / lb.Budget
    lb = lb.sort_values("Ach")
    n1 = go.Figure([go.Bar(x=lb.City, y=lb.Budget, name="Budget", marker_color="#98C1D9"), go.Bar(x=lb.City, y=lb.Actual, name="Actual", marker_color=TEAL)])
    n1.update_layout(barmode="group", title="Actual vs Budget by location (2021+2022)", xaxis=dict(showticklabels=False))
    mv = ba.groupby(["Year", "Month"])[["Actual", "Budget"]].sum().reset_index(); mv["YM"] = pd.to_datetime(dict(year=mv.Year, month=mv.Month, day=1))
    n2 = go.Figure([go.Scatter(x=mv.YM, y=mv.Budget, name="Budget", line=dict(color=AMBER, width=3)), go.Scatter(x=mv.YM, y=mv.Actual, name="Actual", line=dict(color=TEAL, width=3))])
    n2.update_layout(title="Monthly Budget vs Actual (budget follows fixed seasonality)")
    n3 = px.bar(lb.head(15), x="City", y="Ach", color_discrete_sequence=[RED], title="15 lowest budget achievement locations").update_layout(yaxis_tickformat=".0%")
    pages["Target Tracker"] = (f"<p class='note'>Overall achievement {ach:.0%}. Every location exceeds budget, which signals a budget data issue (see README).</p>", [n1, n2, n3])

    # ---- assemble HTML with tabs ----
    tabs, body, first = "", "", True
    for i, (name, (extra, figs)) in enumerate(pages.items()):
        tabs += f"<button onclick=\"show({i})\" id='b{i}' class='{'on' if first else ''}'>{name}</button>"
        charts = "".join(f"<div class='ch'>{_fig(f).to_html(full_html=False, include_plotlyjs=('cdn' if (i, j) != (0, 0) else True))}</div>" for j, f in enumerate(figs))
        body += f"<section id='p{i}' style='display:{'block' if first else 'none'}'><div class='cards'>{extra if extra.startswith('<div') else ''}</div>{'' if extra.startswith('<div') else extra}<div class='grid'>{charts}</div></section>"
        first = False
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Sales Intelligence</title><style>
body{{margin:0;font-family:Segoe UI,Arial;background:#F4F6F8}} header{{background:{NAVY};color:#fff;padding:14px 24px;font-size:20px}}
nav{{display:flex;gap:6px;padding:10px 24px;background:#fff;flex-wrap:wrap}} nav button{{border:0;padding:8px 16px;border-radius:18px;background:#E0E1DD;cursor:pointer}}
nav button.on{{background:{TEAL};color:#fff}} section{{padding:16px 24px}} .cards{{display:flex;gap:12px;flex-wrap:wrap}}
.card{{background:#fff;border-radius:8px;padding:12px 18px;min-width:130px;border-left:5px solid {AMBER}}} .card span{{display:block;color:#415A77;font-size:12px}} .card b{{font-size:24px;color:{NAVY}}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:14px;margin-top:14px}} .ch{{background:#fff;border-radius:8px;padding:6px}} .note{{color:#415A77;font-size:12px}}
</style></head><body><header>Sales Intelligence Dashboard | 2021 to 15-Mar-2023</header><nav>{tabs}</nav>{body}
<script>function show(n){{document.querySelectorAll('section').forEach((s,i)=>s.style.display=i==n?'block':'none');document.querySelectorAll('nav button').forEach((b,i)=>b.className=i==n?'on':'');window.dispatchEvent(new Event('resize'))}}</script></body></html>"""
    out.write_text(html, encoding="utf-8")
