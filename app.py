import streamlit as st
import pandas as pd
import time as tm
from streamlit_option_menu import option_menu
from main import dt_time, add_expenses, exp_is_valid, budg_is_valid, add_budget, dt_parse, get_expenses, get_db
import altair as alt
import base64



#declarations:
EXP_PATH = "data/expenses.csv"
BUDGET_PATH = "data/budget.csv"
#declarations end.

date, time = dt_time()

# UI customization | sidebar, app design | @AI usage
def sidebar_bg(image_path):
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{
            background-image: url("data:image/png;base64,{data}");
            background-size: cover;
            background-position: center;
        }}
        </style>
    """, unsafe_allow_html=True)

sidebar_bg("data/1.jpg")
# sidebar design end.


def get_daily_chart(df):
    daily_sp = df.resample("D", on="date")["price"].sum()
    end_date = pd.Timestamp.now().normalize()
    start_date = end_date - pd.Timedelta(days=7)
    full_range = pd.date_range(start=start_date, end=end_date, freq="D")
    daily_sp = daily_sp.reindex(full_range, fill_value=0)
    daily_sp.index.name = "date"
    daily_sp = daily_sp.reset_index()
    daily_chart = alt.Chart(daily_sp).mark_line(point=True).encode(
        x=alt.X("date:T", title="Last 7 days", axis=alt.Axis(tickCount="day", format="%b %d")),
        y=alt.Y("price:Q", title="Expenditure (in ₹)"),
        tooltip=[
            alt.Tooltip("date:T", title="Date"),
            alt.Tooltip("price:Q", title="Expenditure (in ₹)")
        ]
    )
    return daily_chart


def get_weekly_chart(df):
    weekly_sp = df.resample("W", on="date")["price"].sum()
    weekly_sp = weekly_sp.reset_index()
    weekly_chart = alt.Chart(weekly_sp).mark_line(point=True).encode(
        x=alt.X("date:T", title="Weeks"),
        y=alt.Y("price:Q", title="Expenditure (in ₹)"),
        tooltip=[
            alt.Tooltip("date:T", title="Date (week_till)"),
            alt.Tooltip("price:Q", title="Expenditure (in ₹)")
        ]
    )
    return weekly_chart


def get_monthly_chart(df):
    monthly_sp = df.resample("ME", on="date")["price"].sum()
    monthly_sp = monthly_sp.reset_index()
    monthly_chart = alt.Chart(monthly_sp).mark_line(point=True).encode(
        x=alt.X("date:T", timeUnit="yearmonth", title="Month"),
        y=alt.Y("price:Q", title="Expenditure (in ₹)"),
        tooltip=[
            alt.Tooltip("date:T", timeUnit="yearmonth", title="Month"),
            alt.Tooltip("price:Q", title="Expenditure (in ₹)")
        ]
    )
    return monthly_chart, monthly_sp


def get_category_chart(df):
    category_sp = df.groupby("category")["price"].sum()
    category_sp = category_sp.reset_index()
    category_chart = alt.Chart(category_sp).mark_bar().encode(
        x=alt.X("price:Q", title="Expenditure (in ₹)"),
        y=alt.Y("category:N", title="Categories", axis=alt.Axis(labelAngle=0)),
        color="category:N",
        tooltip=[
            alt.Tooltip("price:Q", title="spending (in ₹)"),
            alt.Tooltip("category:N", title="Category")
        ]
    )
    return category_chart, category_sp


def get_spsplit_donutchart(category_chart):
    category_sp = category_chart[1]
    category_sp["percent"] = category_sp["price"] / category_sp["price"].sum()
    donutchart = alt.Chart(category_sp).mark_arc(innerRadius=80, outerRadius=150).encode(
        theta=alt.Theta("price:Q"),
        color=alt.Color("category:N"),
        tooltip=[
            alt.Tooltip("category:N", title="Category"),
            alt.Tooltip("price:Q", title="spending (in ₹)"),
            alt.Tooltip("percent:Q", title="Percentage", format=".1%")
        ]
    )
    return donutchart



def read_budget():
    date, time = dt_time()
    current_month = date[:7]

    with get_db() as conn:
        row = conn.execute("""
            SELECT month, budget
            FROM budgets
            WHERE month = ?
        """, (current_month,)).fetchone()

    if row is None:
        return None, None

    mnth_n_yr = f"{row[0]}-01"
    budget = row[1]

    # mnth_n_yr is full date str: e.g 2025-03-01
    return mnth_n_yr, budget



def categories_list():
    categories = [
        "food",
        "utilities",
        "academics",
        "transport",
        "personal",
        "health",
        "entertainment",
        "subscriptions",
        "miscellaneous"
    ]
    return categories



# Main app code starts here:
def app(date, time):   

    df = get_expenses()
    df["date"] = pd.to_datetime(df["date"])
    dt_df = df.copy()  # dataframe copied for datetime manipulation
    reverse_df = df.copy()[::-1]
    dt_df["date"] = pd.to_datetime(dt_df["date"])


    daily_chart = get_daily_chart(dt_df)
    weekly_chart = get_weekly_chart(dt_df)
    monthly_chart = get_monthly_chart(dt_df)
    category_chart = get_category_chart(dt_df)
    donutchart = get_spsplit_donutchart(category_chart)

    st.markdown("""
        <style>
        .stApp {
            background-color: #0c0c0c;
            background-image: radial-gradient(#3a3a3c 1px, transparent 1px);
            background-size: 24px 24px;
        }
        </style>
    """, unsafe_allow_html=True)
    

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
        exp_df_choice = st.selectbox(                   # in development phase!
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
                                    :blue[category name, item_name, price]
                                    dont use comma(,) in item_name
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
            if "daily_default" not in st.session_state:         # to show daily data chart as default
                st.session_state.daily_default = True
            dly_but = st.button("daily expenses")
        if dly_but:                                             # weekly data showing button
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
            st.altair_chart(monthly_chart[0], use_container_width=True)


    elif selected == "Budget":
        st.markdown("# Your Budget:")
        budg_read = read_budget()
        if budg_read[0] is not None:
            budg_read_month_name = dt_parse(budg_read[0])[2]
            budg_read_yr = dt_parse(budg_read[0])[0]
            
            st.markdown(f"""\n ### Budget for month of {budg_read_month_name} {budg_read_yr} is:   ₹{budg_read[1]}""")
        
            monthly_sp_1 = get_monthly_chart(dt_df)[1]           # This is aggregate of spending in a month i.e monthly_sp, rebranded as monthly_sp_1

            monthly_sp_1["date"] = monthly_sp_1["date"].astype(str).str[:7]
            monthly_sp_1 = monthly_sp_1.set_index("date")

            total_sp_of_budg_mo = monthly_sp_1.loc[budg_read[0][:7]]["price"]          # Total spending of latest month of which budget added
            total_sp_of_budg_mo = int(total_sp_of_budg_mo)
            budget_of_mo = int(budg_read[1])

            perc_spent = int((total_sp_of_budg_mo/budget_of_mo)*100)
            status_text = f"You have spent {perc_spent}% of your budget."
            st.subheader("\n")
            prog_bar = st.progress(perc_spent, text=status_text)

            st.subheader("\n")
            category_sp_1 = get_category_chart(dt_df)[1]
            catgry_row = category_sp_1.loc[category_sp_1["price"].idxmax()]
            max_spent_catgry_sp = catgry_row["price"]                        # Actual spending on "max spent category"
            max_spent_catgry_nm = catgry_row["category"]
            st.text(f"The categoty on which you have spent the most of your budget is: '{max_spent_catgry_nm}' (₹{max_spent_catgry_sp})")

        else:
            st.write("No budget set for current month.")
        

    elif selected == "Category spending":
        st.subheader("Category wise spending:")
        st.altair_chart(category_chart[0], use_container_width=True)
        st.subheader("\n")
        st.subheader("Spending split: ")
        st.altair_chart(donutchart, use_container_width=True)




app(date, time)





