import csv
import sqlite3
import re
import datetime as dt
from zoneinfo import ZoneInfo
import pandas as pd
import os


#declarations:
EXP_PATH = "data/expenses.csv"
BUDGET_PATH = "data/budget.csv"
DATA_PATH = "data/expenses.db"
#declarations end.


def get_db():
    return sqlite3.connect(DATA_PATH)

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget INTEGER NOT NULL,
                month TEXT NOT NULL UNIQUE,
                time TEXT NOT NULL
            )
        """)


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

def dt_parse(str):
    dt_p = dt.datetime.strptime(str, "%Y-%m-%d")
    return dt_p.year, dt_p.month, dt_p.strftime("%B"), dt_p.day


def add_expenses(itm_category, itm_name, itm_price, date, time):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO expenses
            (category, item_name, price, date, time)
            VALUES (?, ?, ?, ?, ?)
        """, (itm_category, itm_name, itm_price, date, time))

    # with open(EXP_PATH, "r") as exp_file:
    #     reader = csv.reader(exp_file)
    #     rows = list(reader)
    
    # sr = len(rows)

    # with open(EXP_PATH, "a", newline="") as exp_file:
    #     writer = csv.writer(exp_file)
    #     if len(rows) == 0:
    #         writer.writerow(["sr.no", "item category", "item name", "item price", "date", "time"])
    #         sr = 1 #default sr
    #     writer.writerow([sr, itm_category, itm_name, itm_price, date, time])


def add_budget(budget, mo_date_str, time):
    mo_key = mo_date_str[:7]
    with get_db() as conn:
            conn.execute("""
                INSERT INTO budgets
                (budget, month, time)
                VALUES (?, ?, ?)
                ON CONFLICT(month) DO UPDATE SET
                budget = excluded.budget, 
                time = excluded.time
            """, (budget, mo_key, time))
    # try:
    #     budg_df = pd.read_csv(BUDGET_PATH)
    # except (FileNotFoundError, pd.errors.EmptyDataError):
    #     budg_df = pd.DataFrame(columns=["budget", "month", "time"])
    # budg_df["budge"] = budgt_df["budget"].astype(str)
    # mo_key = mo_date_str[:7]
    # if mo_key in budg_df["month"].str[:7].values:
    #     budg_df.loc[budg_df["month"].str[:7] == mo_key, "budget"] = budget
    # else:
    #     new_row = {"budget": budget, "month": mo_date_str, "time": time}
    #     budg_df = pd.concat([budg_df, pd.DataFrame([new_row])], ignore_index=True)
    # budg_df.to_csv(BUDGET_PATH, index=False)


def get_expenses():
    with get_db() as conn:
        df = pd.read_sql_query("""
            SELECT
                id,
                category,
                item_name,
                price,
                date,
                time
            FROM expenses
        """, conn)

    return df