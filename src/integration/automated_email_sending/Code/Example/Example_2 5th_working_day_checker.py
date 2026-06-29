# Databricks notebook source
import pandas as pd
from datetime import datetime

# Function to calculate the 5th working day of the current month
def get_5th_working_day():
    # Get the current month and year
    now = datetime.now()
    year, month = now.year, now.month

    # Generate the list of all working days (Monday to Friday) in the current month
    first_day = datetime(year, month, 1)
    last_day = pd.to_datetime(f'{year}-{month}-01') + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    
    # Use pandas to generate the working days of the month
    working_days = pd.bdate_range(first_day, last_day)

    # Check if today is the 5th working day
    if len(working_days) >= 5:
        fifth_working_day = working_days[4]  # The 5th working day (index 4)
        return fifth_working_day.date()

    return None

# Get today's date and check if it is the 5th working day
today = datetime.now().date()
fifth_working_day = get_5th_working_day()

if today == fifth_working_day:
    print("Today is the 5th working day. Proceed with the job.")
    try:
        print("Running the next notebook...")
        # Replace with your actual notebook path in Databricks
        dbutils.notebook.run("ccr_email", 0)
    except Exception as e:
        print(f"Error running the notebook: {e}")
else:
    print("Today is not the 5th working day. Exiting.")
