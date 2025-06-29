# MEIC Best Entry Analysis

A Python tool for analyzing optimal entry times for MEIC trades based on BYOB (Build Your Own Backtester) data.

## Overview

This program processes CSV exports from BYOB to identify the best entry times for MEIC trading. It generates two Excel files:

- **Daily results**: Performance breakdown by individual days
- **Aggregated data**: Summary statistics by entry time

## Output Files

The analysis produces two Excel files in the `output` folder:

- `summary_all_days.xlsx` - Daily performance breakdown
- `summary_all.xlsx` - Aggregated entry time analysis

## Usage Instructions

### 1. Export Data from BYOB

- Configure your entry/exit parameters in BYOB
- Select "all time entries" and "all days"
- Run the backtest
- Click "Export Trades" to download the CSV file

### 2. Prepare CSV Files

- Name your CSV files descriptively (e.g., `1_1_24_180cred.csv`)
- **Note**: The filename becomes the Excel sheet name, so keep it concise
- You can process multiple CSV files in one run

### 3. File Organization

- Create a `data` folder in your project directory
- Place all CSV files in the `data` folder

### 4. Run Analysis

```bash
python main.py
```

### 5. View Results

- Check the `output` folder for generated Excel files
- `summary_all_days.xlsx` contains per-day results
- `summary_all.xlsx` contains aggregated entry time data

## Requirements

- Python 3.x
- Required packages (install via pip):
  - pandas
  - openpyxl

## File Structure

```
project-folder/
├── main.py
├── data/
│   ├── your_file1.csv
│   ├── your_file2.csv
│   └── ...
└── output/
    ├── summary_all_days.xlsx
    └── summary_all.xlsx
```

## Tips

- Use descriptive but concise CSV filenames as they become sheet names in Excel
- Process multiple strategies by including multiple CSV files in the `data` folder
- Ensure your BYOB exports include all necessary trade data for accurate analysis
