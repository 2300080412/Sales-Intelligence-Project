# Sales Intelligence Project (Power BI kit + Python replica)

Power BI itself does not run in VS Code. This project gives you two things:

1. **`PBI_Kit/`** - what you paste into Power BI Desktop: Power Query M, DAX, theme, build guide and insights.
2. **`src/`** - a Python replica of the same pipeline you can run in VS Code: cleaning, star schema, measures, all 25 answers and an interactive 7-page HTML dashboard.

## Run in VS Code
1. Open this folder (File > Open Folder). Install the Python extension.
2. Terminal > New Terminal, then:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Mac/Linux: source .venv/bin/activate)
   pip install -r requirements.txt
   python src/main.py
   ```
   or press F5 (uses `.vscode/launch.json`).
3. Open `outputs/dashboard.html` in your browser.

Outputs: `outputs/clean/*.csv` (star schema tables, importable into Power BI), `outputs/answers.md` (answers to the management questions), `outputs/dashboard.html`.

## Data caveats (also in PBI_Kit/04_Build_Guide_and_Insights.md)
- 2023 covers only 1 Jan - 15 Mar; YoY is compared like-for-like.
- Budget sheet IDs/names do not match Locations (23 IDs dropped); budget achievement of about 360% is a data issue, confirm with your trainer.
- Only one state (California): use County. Customer names are not unique: use CustomerLabel.
