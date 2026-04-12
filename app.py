import streamlit as st
import pandas as pd
import time as tm
from streamlit_option_menu import option_menu
from main import dt_time, add_expenses, exp_is_valid, budg_is_valid, add_budget
import altair as alt



#declarations:
EXP_PATH = "data/expenses.csv"
BUDGET_PATH = "data/budget.csv"
#declarations end.



date, time = dt_time()


def get_daily_chart(df):
    daily_sp = df.resample("D", on="date")["item price"].sum()
    end_date = pd.Timestamp.now().normalize()
    start_date = end_date - pd.Timedelta(days=7)
    full_range = pd.date_range(start=start_date, end=end_date, freq="D")
    daily_sp = daily_sp.reindex(full_range, fill_value=0)
    daily_sp.index.name = "date"
    daily_sp = daily_sp.reset_index()
    daily_chart = alt.Chart(daily_sp).mark_line(point=True).encode(
        x=alt.X("date:T", title="Last 7 days", axis=alt.Axis(tickCount="day", format="%b %d")),
        y=alt.Y("item price:Q", title="Expenditure (in ₹)"),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("item price:Q", title="Expenditure (in ₹)")
        ]
    )
    return daily_chart


def get_weekly_chart(df):
    weekly_sp = df.resample("W", on="date")["item price"].sum()
    weekly_sp = weekly_sp.reset_index()
    weekly_chart = alt.Chart(weekly_sp).mark_line(point=True).encode(
        x=alt.X("date:T", title="Weeks"),
        y=alt.Y("item price:Q", title="Expenditure (in ₹)"),
        tooltip=[
            alt.Tooltip("date:T", title="Date (week_till)"),
            alt.Tooltip("item price:Q", title="Expenditure (in ₹)")
        ]
    )
    return weekly_chart


def get_monthly_chart(df):
    monthly_sp = df.resample("ME", on="date")["item price"].sum()
    monthly_sp = monthly_sp.reset_index()
    monthly_chart = alt.Chart(monthly_sp).mark_line(point=True).encode(
        x=alt.X("date:T", timeUnit="yearmonth", title="Month"),
        y=alt.Y("item price:Q", title="Expenditure (in ₹)"),
        tooltip=[
            alt.Tooltip("date:T", timeUnit="yearmonth", title="Month"),
            alt.Tooltip("item price:Q", title="Expenditure (in ₹)")
        ]
    )
    return monthly_chart


def get_category_chart(df):
    category_sp = df.groupby("item category")["item price"].sum()
    category_sp = category_sp.reset_index()
    category_chart = alt.Chart(category_sp).mark_bar().encode(
        x=alt.X("item price:Q", title="Expenditure (in ₹)"),
        y=alt.Y("item category:N", title="Categories", axis=alt.Axis(labelAngle=0)),
        color="item category:N",
        tooltip=[
            alt.Tooltip("item price:Q", title="spending (in ₹)"),
            alt.Tooltip("item category:N", title="Category")
        ]
    )
    return category_chart


def read_budget():
    try:
        budg_df_read = pd.read_csv(BUDGET_PATH)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return "File not found!!!!"
    if not budg_df_read.empty:
        mnth_n_yr = budg_df_read.iloc[-1]["month"]
        budget = budg_df_read.iloc[-1]["budget"]
        return mnth_n_yr, budget
    else:
        return "Empty budget file; add logs."



def categories_list():
    categories = [
        "food",
        "utilities",
        "academics",
        "transport",
        "personal",
        "health",
        "Entertainment",
        "subscriptions",
        "miscellaneous"
    ]
    return categories



def app(date, time):

    df = pd.read_csv(EXP_PATH)
    dt_df = df.copy()
    reverse_df = df.copy()
    reverse_df = reverse_df[::-1]
    dt_df["date"] = pd.to_datetime(dt_df["date"])


    daily_chart = get_daily_chart(dt_df)
    weekly_chart = get_weekly_chart(dt_df)
    monthly_chart = get_monthly_chart(dt_df)
    category_chart = get_category_chart(dt_df)


    with st.sidebar:
        selected = option_menu(
                menu_title = "Main Menu",
                options = ["Home", "All expenses", "Budget", "Category spending"]
            )

    if selected == "All expenses":
        st.markdown("## All your expenses are here!")
        st.markdown("""
                    ###### (Tip: You can download as CSV and view in excel. Click top right on chart)

                    ##### Filters
        """)
        exp_df_choice = st.selectbox(
            "Choose a filter:",
            ["All time", "This week"]
        )
        st.subheader("\n")
        st.dataframe(reverse_df, hide_index=True)

    elif selected == "Home":

        st.markdown("""
                    # :red[:material/receipt_long:] :red[XPENSOR]
        """)
        st.subheader("Track all your expenses here!")
        st.subheader("\n")
        col11, col12 = st.columns([2,2])
        with col11:
            if "exp_added" not in st.session_state:
                st.session_state.exp_added = False

            with st.form("Add expense", clear_on_submit=True):

                categories = categories_list()

                expense = st.text_input("Add Expense: ", placeholder="Add expense")

                added = st.form_submit_button("Add")
                if added:
                    if exp_is_valid(expense) != None:
                        itm_category, itm_name, itm_price = exp_is_valid(expense)
                        if not itm_category in categories:
                            st.error("Please enter category name from existing categories")
                            st.stop()
                        add_expenses(itm_category, itm_name, itm_price, date, time)
                        st.session_state.exp_added = True

                    else:
                        msg = st.empty()
                        msg.error("""
                                    Please enter expense in this format:
                                    :blue[category name, item name, price]
                                    dont use comma(,) in item name
                                    (category name is optional; and price without any symbol.)
                                    """)
                        tm.sleep(5)
                        msg.empty()


            if st.session_state.exp_added:
                msg = st.empty()
                msg.success("Expense added successfully!")
                tm.sleep(2)
                msg.empty()
                st.session_state.exp_added = False

        with col12:
            if "budget_added" not in st.session_state:
                st.session_state.budget_added = False

            with st.form("Add Budget", clear_on_submit=True):
                mo_date = st.date_input("Select date for adding budget:")
                mo_date_str = mo_date.strftime("%Y-%m-%d")
                budget = st.text_input("Add Budget:", placeholder="Add Budget in ₹")
                budg_added = st.form_submit_button("Add")
                if budg_added:
                    if budg_is_valid(budget) != None:
                        add_budget(budget, mo_date_str, time)
                        st.session_state.budget_added = True
                    else:
                        msg = st.empty()
                        msg.error('''
                                  Please add budget in :blue[numeric] format only.
                                  ''')
                        tm.sleep(4)
                        msg.empty()

            if st.session_state.budget_added:
                msg = st.empty()
                msg.success("Budget added successfully!")
                tm.sleep(2)
                msg.empty()
                st.session_state.budget_added = False


        st.subheader("\n")
        col21, col22, col23 = st.columns([1,1,1])
        with col21:
            if "daily_default" not in st.session_state:         #to show daily data chart as default
                st.session_state.daily_default = True
            dly_but = st.button("daily expenses")
        if dly_but:                                             #weekly data showing button
            st.session_state.daily_default = True
        if st.session_state.daily_default:
            st.subheader("Daily Expenses:")
            st.altair_chart(daily_chart, use_container_width=True)
            st.session_state.daily_default = False

        with col22:
            wek_but = st.button("weekly expenses")
        if wek_but:
            st.subheader("Weekly Expenses:")
            st.altair_chart(weekly_chart, use_container_width=True)

        with col23:
            mon_but = st.button("monthly expenses")
        if mon_but:
            st.subheader("Monthly Expenses:")
            st.altair_chart(monthly_chart, use_container_width=True)


    elif selected == "Budget":
        st.markdown("## Your Budget:")
        budg_read = read_budget()
        if len(budg_read) == 2:
            st.markdown(f"""\nBudget for month of {budg_read[0]} is:\n #### ₹{budg_read[1]}""")
        if len(budg_read) == 1:
            st.write(budg_read[0])

    elif selected == "Category spending":
        st.subheader("Category wise spending:")
        st.altair_chart(category_chart, use_container_width=True)





app(date, time)





