import csv
import re
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd


#declarations:
EXP_PATH = "data/expenses.csv"
BUDGET_PATH = "data/budget.csv"
#declarations end.




def exp_is_valid(string):
    if s := re.fullmatch(r"(?:([A-Za-z_]+), )?([^,]+), ([0-9]+)", string):
        itm_category = s.group(1)
        itm_name = s.group(2)
        itm_price = int(s.group(3))
        if itm_category == None:
            itm_category = "Other"
        return itm_category, itm_name, itm_price
    else:
        return None

def budg_is_valid(string):
    if s := re.fullmatch(r"([0-9]+)", string):
        budget = s.group(1)
        return budget
    else:
        return None


def dt_time():
    #time handling
    dtime_obj = dt.datetime.now(ZoneInfo("Asia/Kolkata"))
    dt_obj = dtime_obj.date()
    date = dt_obj.isoformat()
    tm_obj = dtime_obj.time()
    time = tm_obj.isoformat(timespec='seconds')
    return date, time


def add_expenses(itm_category, itm_name, itm_price, date, time):
    with open(EXP_PATH, "a+") as exp_file:
        writer = csv.writer(exp_file)
        exp_file.seek(0)
        reader = csv.reader(exp_file)
        rows = list(reader)
        sr = 1 #default sr
        if len(rows) == 0:
            writer.writerow(["sr.no", "item category", "item name", "item price", "date", "time"])
        else:
            sr = len(rows)
        writer.writerow([sr, itm_category, itm_name, itm_price, date, time])


def add_budget(budget, mo_date_str, time):
    try:
        budg_df = pd.read_csv(BUDGET_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        budg_df = pd.DataFrame(columns=["budget", "month", "time"])
    if mo_date_str in budg_df["month"].values:
        budg_df.loc[budg_df["month"] == mo_date_str[:7], "budget"] = budget
    else:
        new_row = {"budget": budget, "month": mo_date_str[:7], "time": time}
        budg_df = pd.concat([budg_df, pd.DataFrame([new_row])], ignore_index=True)
    budg_df.to_csv(BUDGET_PATH, index=False)








    