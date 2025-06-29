import pandas as pd

def summarize_pnl_by_opentime(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates net PnL (ProfitLossAfterSlippage - CommissionFees) for each unique OpenTime.

    Args:
        df (pd.DataFrame): DataFrame containing at least columns 'OpenTime', 'ProfitLossAfterSlippage', and 'CommissionFees'.

    Returns:
        pd.DataFrame: Summary DataFrame with 'OpenTime' and total 'NetPnL'.
    """
    import pytz

    df = df.copy()
    # Keep original OpenTime as string for CET conversion
    df["OpenTime"] = pd.to_datetime(df["OpenTime"], format="%H:%M:%S", errors="coerce").dt.time
    df["ProfitLossAfterSlippage"] = pd.to_numeric(df["ProfitLossAfterSlippage"], errors="coerce")
    df["CommissionFees"] = pd.to_numeric(df["CommissionFees"], errors="coerce")
    df["NetPnL"] = df["ProfitLossAfterSlippage"]*100 - df["CommissionFees"]
    # Convert IsWin to boolean, handling string cases
    df["IsWin"] = df["IsWin"].astype(str).str.lower().map({"true": True, "false": False})

    # --- CET Conversion ---
    # Convert OpenTime (HH:MM:SS) to datetime with arbitrary date and convert to CET
    def convert_to_cet(time_str):
        try:
            naive_dt = pd.to_datetime(f"2000-01-01 {time_str}")
            eastern = pytz.timezone("US/Eastern")
            cet = pytz.timezone("Europe/Prague")
            localized = eastern.localize(naive_dt)
            return localized.astimezone(cet).strftime("%H:%M:%S")
        except:
            return None
    # Create OpenTimeCET column based on original string OpenTime
    # Need to get the string representation of OpenTime for apply
    open_time_strs = df["OpenTime"].astype(str)
    df["OpenTimeCET"] = open_time_strs.apply(convert_to_cet)

    grouped = df.groupby("OpenTime").agg(
        NetPnL=("NetPnL", "sum"),
        Trades=("OpenTime", "count"),
        Wins=("IsWin", "sum"),
        Losses=("IsWin", lambda x: (~x).sum())
    ).reset_index()
    grouped["WinRate"] = ((grouped["Wins"] / grouped["Trades"] * 100).round(2)).astype(str) + "%"

    # Add CET column to grouped by merging unique pairs
    grouped = grouped.merge(
        df[["OpenTime", "OpenTimeCET"]].drop_duplicates(), on="OpenTime", how="left"
    )
    # Reorder columns so OpenTimeCET is next to OpenTime
    cols = list(grouped.columns)
    if "OpenTime" in cols and "OpenTimeCET" in cols:
        cols.insert(cols.index("OpenTime") + 1, cols.pop(cols.index("OpenTimeCET")))
        grouped = grouped[cols]

    # Define starting capital for CAR calculation
    starting_capital = 18000  # user-defined base capital

    # Add Compound Annual Return (CAR) calculation
    if "OpenDate" in df.columns:
        df["OpenDate"] = pd.to_datetime(df["OpenDate"], errors="coerce")
        total_days = df["OpenDate"].dt.date.nunique()

        if total_days > 0:
            end_value = starting_capital + grouped["NetPnL"]
            years = total_days / 252  # Approximate number of years
            grouped["CAR"] = ((end_value / starting_capital) ** (1 / years) - 1) * 100
            grouped["CAR"] = grouped["CAR"].round(2).astype(str) + "%"
        else:
            grouped["CAR"] = "N/A"
    else:
        grouped["CAR"] = "N/A"

    # Max Drawdown calculation per OpenTime group (improved version)
    def compute_max_drawdown(pnls, starting_capital):
        equity_curve = pnls.cumsum() + starting_capital
        running_max = equity_curve.cummax()
        drawdowns = (equity_curve - running_max) / running_max
        return round(drawdowns.min() * 100, 2)

    max_drawdowns = []
    for time in grouped["OpenTime"]:
        pnl_series = df[df["OpenTime"] == time]["NetPnL"]
        if not pnl_series.empty:
            max_dd = compute_max_drawdown(pnl_series.reset_index(drop=True), starting_capital)
            max_drawdowns.append(f"{max_dd}%")
        else:
            max_drawdowns.append("N/A")

    grouped["MaxDrawdown"] = max_drawdowns

    # --- CALMAR ratio calculation ---
    def parse_drawdown(value):
        try:
            return abs(float(value.strip('%')))
        except:
            return None

    calmar_ratios = []
    for car_str, dd_str in zip(grouped["CAR"], grouped["MaxDrawdown"]):
        try:
            car = float(car_str.strip('%'))
            dd = parse_drawdown(dd_str)
            if dd and dd != 0:
                calmar = round(car / dd, 2)
                calmar_ratios.append(calmar)
            else:
                calmar_ratios.append("N/A")
        except:
            calmar_ratios.append("N/A")

    grouped["Calmar"] = calmar_ratios
    return grouped

def summarize_pnl_by_opentime_for_weekday(df: pd.DataFrame, target_weekday: str) -> pd.DataFrame:
    """
    Aggregates net PnL (ProfitLossAfterSlippage - CommissionFees) by open time 
    for a specific weekday.

    Args:
        df (pd.DataFrame): DataFrame containing trading data
        target_weekday (str): Weekday for analysis. Options:
                            - 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
                            - number 0-6 (0=Monday, 6=Sunday)

    Returns:
        pd.DataFrame: Summary table with open times and metrics for the given day.
    """
    import pandas as pd
    import pytz

    df = df.copy()
    
    # Mapping for different weekday input formats
    weekday_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    # Convert target_weekday to number
    if isinstance(target_weekday, str):
        target_weekday = target_weekday.lower()
        if target_weekday in weekday_mapping:
            target_weekday_num = weekday_mapping[target_weekday]
        else:
            raise ValueError(f"Unknown weekday: {target_weekday}. Use: {list(weekday_mapping.keys())} or number 0-6")
    else:
        target_weekday_num = int(target_weekday)
        if target_weekday_num < 0 or target_weekday_num > 6:
            raise ValueError("Weekday number must be between 0-6 (0=Monday, 6=Sunday)")
    
    # Convert columns to proper data types
    df["OpenDate"] = pd.to_datetime(df["OpenDate"], errors="coerce")
    df["OpenTime"] = pd.to_datetime(df["OpenTime"], format="%H:%M:%S", errors="coerce").dt.time
    df["ProfitLossAfterSlippage"] = pd.to_numeric(df["ProfitLossAfterSlippage"], errors="coerce")
    df["CommissionFees"] = pd.to_numeric(df["CommissionFees"], errors="coerce")
    df["NetPnL"] = df["ProfitLossAfterSlippage"] * 100 - df["CommissionFees"]
    
    # Convert IsWin to boolean
    df["IsWin"] = df["IsWin"].astype(str).str.lower().map({"true": True, "false": False})
    
    # Filter by weekday
    df["WeekdayNum"] = df["OpenDate"].dt.dayofweek
    df_filtered = df[df["WeekdayNum"] == target_weekday_num].copy()
    
    if df_filtered.empty:
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return pd.DataFrame()
    
    # --- CET Conversion ---
    def convert_to_cet(time_str):
        try:
            naive_dt = pd.to_datetime(f"2000-01-01 {time_str}")
            eastern = pytz.timezone("US/Eastern")
            cet = pytz.timezone("Europe/Prague")
            localized = eastern.localize(naive_dt)
            return localized.astimezone(cet).strftime("%H:%M:%S")
        except:
            return None
    
    # Create CET column
    open_time_strs = df_filtered["OpenTime"].astype(str)
    df_filtered["OpenTimeCET"] = open_time_strs.apply(convert_to_cet)
    
    # Group by open time
    grouped = df_filtered.groupby("OpenTime").agg(
        NetPnL=("NetPnL", "sum"),
        Trades=("OpenTime", "count"),
        Wins=("IsWin", "sum"),
        Losses=("IsWin", lambda x: (~x).sum())
    ).reset_index()
    
    # Calculate win rate
    grouped["WinRate"] = ((grouped["Wins"] / grouped["Trades"] * 100).round(2)).astype(str) + "%"
    
    # Add CET column
    grouped = grouped.merge(
        df_filtered[["OpenTime", "OpenTimeCET"]].drop_duplicates(), 
        on="OpenTime", 
        how="left"
    )
    
    # Reorder columns
    cols = list(grouped.columns)
    if "OpenTime" in cols and "OpenTimeCET" in cols:
        cols.insert(cols.index("OpenTime") + 1, cols.pop(cols.index("OpenTimeCET")))
        grouped = grouped[cols]
    
    # Define starting capital
    starting_capital = 18000
    
    # Calculate CAR (Compound Annual Return)
    total_days = df_filtered["OpenDate"].dt.date.nunique()
    if total_days > 0:
        years = total_days / 252  # Approximate number of trading days per year
        end_value = starting_capital + grouped["NetPnL"]
        grouped["CAR"] = ((end_value / starting_capital) ** (1 / years) - 1) * 100
        grouped["CAR"] = grouped["CAR"].round(2).astype(str) + "%"
    else:
        grouped["CAR"] = "N/A"
    
    # Calculate maximum drawdown
    def compute_max_drawdown(pnls, starting_capital):
        if pnls.empty:
            return 0
        equity_curve = pnls.cumsum() + starting_capital
        running_max = equity_curve.cummax()
        drawdowns = (equity_curve - running_max) / running_max
        return round(drawdowns.min() * 100, 2)
    
    max_drawdowns = []
    for time in grouped["OpenTime"]:
        pnl_series = df_filtered[df_filtered["OpenTime"] == time]["NetPnL"]
        if not pnl_series.empty:
            max_dd = compute_max_drawdown(pnl_series.reset_index(drop=True), starting_capital)
            max_drawdowns.append(f"{max_dd}%")
        else:
            max_drawdowns.append("N/A")
    
    grouped["MaxDrawdown"] = max_drawdowns
    
    # Calculate CALMAR ratio
    def parse_drawdown(value):
        try:
            return abs(float(value.strip('%')))
        except:
            return None
    
    calmar_ratios = []
    for car_str, dd_str in zip(grouped["CAR"], grouped["MaxDrawdown"]):
        try:
            car = float(car_str.strip('%'))
            dd = parse_drawdown(dd_str)
            if dd and dd != 0:
                calmar = round(car / dd, 2)
                calmar_ratios.append(calmar)
            else:
                calmar_ratios.append("N/A")
        except:
            calmar_ratios.append("N/A")
    
    grouped["Calmar"] = calmar_ratios
    
    # Sort by time
    grouped = grouped.sort_values("OpenTime")
    
    # Add information about analyzed day
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    analyzed_day = weekday_names[target_weekday_num]
    
    return grouped


def analyze_all_weekdays(df: pd.DataFrame) -> pd.DataFrame:
    """
    Helper function to analyze all weekdays at once.
    
    Returns:
        pd.DataFrame: Combined DataFrame with results for all weekdays
    """
    import pandas as pd
    
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    all_results = []
    
    for i, day in enumerate(weekdays):
        # Temporarily suppress output from main function
        import sys
        from io import StringIO
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = summarize_pnl_by_opentime_for_weekday(df, day)
            if not result.empty:
                # Add weekday column
                result = result.copy()
                result['Weekday'] = weekday_names[i]
                result['WeekdayNum'] = i
                all_results.append(result)
        finally:
            sys.stdout = old_stdout
    
    if not all_results:
        return pd.DataFrame()
    
    # Combine all results
    combined_df = pd.concat(all_results, ignore_index=True)
    
    # Reorder columns so weekday is at the beginning
    cols = ['Weekday', 'WeekdayNum'] + [col for col in combined_df.columns if col not in ['Weekday', 'WeekdayNum']]
    combined_df = combined_df[cols]
    
    # Sort by weekday and time
    combined_df = combined_df.sort_values(['WeekdayNum', 'OpenTime'])
    
    return combined_df