import os
import pandas as pd
from analysis import *

DATA_DIR = "data"
OUTPUT_DIR = "output"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_summaries = {}
    all_summaries_days = {}

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            filepath = os.path.join(DATA_DIR, filename)
            print(f"🔍 Loading file: {filename}")
            try:
                df = pd.read_csv(filepath)
                summary = summarize_pnl_by_opentime(df)
                sheet_name = os.path.splitext(filename)[0]
                all_summaries[sheet_name] = summary
                summary_days = analyze_all_weekdays(df)
                sheet_name = os.path.splitext(filename)[0]
                all_summaries_days[sheet_name] = summary_days
            except Exception as e:
                print(f"❌ Error during processing {filename}: {e}")

    output_excel = os.path.join(OUTPUT_DIR, "summary_all.xlsx")
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        for sheet, data in all_summaries.items():
            data.to_excel(writer, sheet_name=sheet[:31], index=False)  # Excel sheet names max 31 chars

    print(f"Summary saved to {output_excel}")

    output_excel = os.path.join(OUTPUT_DIR, "summary_all_days.xlsx")
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        for sheet, data in all_summaries_days.items():
            data.to_excel(writer, sheet_name=sheet[:31], index=False)  # Excel sheet names max 31 chars

    print(f"Summary saved to {output_excel}")

if __name__ == "__main__":
    main()