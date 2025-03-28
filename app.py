import sqlite3
import datetime
import pandas as pd
from time import sleep
import streamlit as st
from typing import Tuple
import plotly.express as px


st.set_page_config(
    page_title="Swarajya : Food Event",
    # page_icon="🍽️",
    page_icon="./Swarajya_logo_bg_sq.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.logo("./Swarajya_logo_bg_sq.png")
st.title(":orange[Swarajya] - :red[Entry Management] 🍽️")
# st.title(":orange[Swarajya] - :blue[Entry Management] 🍽️")

# ------------------------------------------------------------------------------
# Globals:
# ------------------------------------------------------------------------------

if "query" not in st.session_state:
    st.session_state.query = ""

if "data" not in st.session_state:
    st.session_state.data = None

if "last_fetched" not in st.session_state:
    st.session_state.last_fetched = datetime.datetime.now()

if "filtered_data" not in st.session_state:
    st.session_state.filtered_data = None

if "all_cols" not in st.session_state:
    st.session_state.all_cols = [
        'reg', 'name', 'email', 'phone', 'gender', 'status', 'timestamp', 'search_str']

if "visible_cols" not in st.session_state:
    st.session_state.visible_cols = [
        'Reg. No.', 'Name', 'Email Id', 'Phone No.', 'Gender', 'Status', 'Timestamp']


# ------------------------------------------------------------------------------
# Helper Functions:
# ------------------------------------------------------------------------------

def get_all_data(get_headers: bool = False):
    """Load all the entries from the database."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data")

    data = cursor.fetchall()
    headers = None
    if get_headers:
        headers = [description[0] for description in cursor.description]

    conn.close()
    return data, headers


def update_entry(reg_no: str, to_mark: bool = False) -> Tuple[bool, str]:
    """Update the entry in the database."""

    with database_operation_progress.container(border=True):
        with st.spinner("Updating database entry..."):
            info = f"Marking **{reg_no}** as {'**Entered**' if to_mark else '**Not Entered**'}..."
            st.info(info, icon="🔄")

            sleep(1)
            success = 0

            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                new_status = 1 if to_mark else 0

                if new_status == 1:
                    # Set status to 1 and update timestamp to current time
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(
                        "UPDATE data SET status = ?, timestamp = ? WHERE reg = ?",
                        (new_status, timestamp, reg_no)
                    )
                else:
                    # Set status to 0 and clear the timestamp
                    cursor.execute(
                        "UPDATE data SET status = ?, timestamp = NULL WHERE reg = ?",
                        (new_status, reg_no)
                    )
                conn.commit()

                # Check if any row was updated
                success = cursor.rowcount

            except sqlite3.Error as e:
                # return False, f"Error updating entry: {e}"
                st.toast(f"Error updating entry: {e}", icon="⚠️")

            finally:
                conn.close()
                # st.toast("Done", icon="😇")

            if success > 0:
                st.toast(f"Updated {success} entries successfully.", icon="✅")
                st.session_state.query = ""
                # return True, f"Updated {success} entries successfully."

            else:
                st.toast(f"No ({success}) entries updated.", icon="⚠️")
                # return False, f"No ({success}) entries updated."


def clear_input():
    st.session_state['query'] = ""
    st.session_state.filtered_data = None
    st.session_state.data = load_data()


# fetch data every time the page is loaded with cache for 2 seconds:
@st.cache_data(ttl=2)
def load_data():
    data, headers = get_all_data(get_headers=True)
    df = pd.DataFrame(data, columns=headers)
    df['status'] = df['status'].astype(bool)
    df.sort_values(by=['status', 'reg'], ascending=True, inplace=True)
    df.reset_index(drop=True, inplace=True)

    st.session_state.last_fetched = datetime.datetime.now()
    # st.session_state.last_fetched = datetime.datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")
    return df


# ------------------------------------------------------------------------------
# Page rerun render:
# ------------------------------------------------------------------------------
# Load data on each page load / rerun:
st.session_state.data = load_data()

# Search bar:
st.subheader(":green[Search :]")
a, b = st.columns([1, 15])
clear_btn = a.button(' ', icon="❌", type='secondary', on_click=clear_input)

# Since i have 'query' as key, st will by def save the input in st.session_state['query'] only
var_name_does_not_matter = b.text_input(
    "Search by name or registration number:",
    placeholder="Search by name or registration number, press Enter to search",
    # value=st.session_state.query,
    label_visibility='collapsed',
    help="Search by name or registration number",
    key="query"
)

# ------------------------------------------------------------------------------
# Sidebar dashboard:
# ------------------------------------------------------------------------------

st.sidebar.title("🔢 :blue[Count :]")

# if st.sidebar.button("Refresh Data", type="secondary", icon="🔄"):
#     st.session_state.data = load_data()

boys_yes, boys_no, girls_yes, girls_no = 0, 0, 0, 0

for _, person in st.session_state.data.iterrows():
    if person['gender'] == "F":
        if person['status'] == True:
            girls_yes += 1
        else:
            girls_no += 1

    else:
        if person['status'] == True:
            boys_yes += 1
        else:
            boys_no += 1

st.sidebar.dataframe(
    pd.DataFrame.from_dict(
        data={
            "Boys": {"Yes": boys_yes, "No": boys_no},
            "Girls": {"Yes": girls_yes, "No": girls_no},
            "Total": {"Yes": boys_yes + girls_yes,  "No": boys_no + girls_no}
        }, orient="index"
    )
)

# Footfall Trend (Boys vs Girls):
if st.sidebar.button("Show Footfall Trend", type="primary", icon="📈"):
    with st.container(border=True):
        st.subheader("📈 :green[Footfall Trend :]")
        df = st.session_state.data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df_sorted = df.dropna(subset=["timestamp"]).sort_values("timestamp")

        if not df_sorted.empty:
            df_sorted["cumulative_count"] = df_sorted.groupby("gender")[
                "status"].cumsum()

            fig_line = px.line(
                df_sorted, x="timestamp", y="cumulative_count",
                color="gender", labels={"cumulative_count": "Cumulative Count", "timestamp": "Time"},
                # title="Footfall Trend (Boys vs Girls)",
                markers=True
            )

            st.plotly_chart(
                # st.sidebar.plotly_chart(
                fig_line,
                # use_container_width=True,
                config={"displayModeBar": False}
            )


# ------------------------------------------------------------------------------
# On-going operation progress:
# ------------------------------------------------------------------------------

database_operation_progress = st.empty()

# ------------------------------------------------------------------------------
# Filter data based on the search query:
# ------------------------------------------------------------------------------

# Find if input query exists in the df['search_str'] column:
if st.session_state.query:
    st.session_state.filtered_data = st.session_state.data[
        st.session_state.data['search_str'].str.contains(
            st.session_state.query, case=False)
    ]
    st.session_state.filtered_data.drop(columns=['search_str'], inplace=True)

    if st.session_state.filtered_data.empty:
        st.session_state.filtered_data = None
        st.info("No results found for the search query.", icon="🙅‍♂️")

else:
    st.session_state.filtered_data = None


# If some data is filtered, show the options:
if st.session_state.filtered_data is not None:
    # st.subheader(":green[Filtered Data :]")
    with st.container(border=True):
        # Title Row:
        sizes = [7, 10, 20, 8, 5, 10]
        # sizes = 6
        cols = st.columns(sizes)
        for col, header in zip(cols, st.session_state.visible_cols[:-1]):
            with col:
                st.text(header)

        # Data Rows:
        for entry in st.session_state.filtered_data.iterrows():
            cols = st.columns(sizes, vertical_alignment='center')
            visible_cols = st.session_state.visible_cols
            for col, header, value in zip(cols, visible_cols, entry[1]):
                with col:
                    if header == "Status":
                        if not value:
                            st.button(
                                label="Mark Entry", key=f"entry_{entry[0]}",
                                help="Mark entry as done", type="primary",
                                on_click=update_entry,
                                args=(str(entry[1]['reg']), True,),
                            )
                        else:
                            st.button(
                                label="Unmark Entry", key=f"entry_{entry[0]}",
                                help="Mark entry as not done", type="secondary",
                                on_click=update_entry,
                                args=(str(entry[1]['reg']), False),
                            )
                    elif header == 'Timestamp':
                        pass
                    else:
                        st.write(value)

        # st.dataframe(
        #     st.session_state.filtered_data,
        #     use_container_width=True,
        #     hide_index=True,
        #     on_select='rerun',
        #     selection_mode='single-row'
        # )

# ------------------------------------------------------------------------------
# Show all the entries:
# ------------------------------------------------------------------------------

# Show the data in a table with last fetched time:
a, b = st.columns([15, 7], vertical_alignment='bottom')

a.subheader(":green[Data :]")

last_fetched = st.session_state.last_fetched.strftime("%d-%m-%Y %I:%M:%S %p")
b.write(f'Last Fetched : `{last_fetched}`')
# gap = (datetime.datetime.now() - st.session_state.last_fetched).total_seconds()
# b.write(f'Last Fetched : `{last_fetched}` ({int(gap)} sec ago)')

show_data = st.session_state.data.copy()
# show_data.drop(columns=['search_str', 'timestamp'], inplace=True)
show_data.drop(columns=['search_str'], inplace=True)
show_data.columns = st.session_state.visible_cols

st.dataframe(
    show_data,
    # st.session_state.data,
    # column_order=['reg', 'name', 'gender', 'email', 'phone', 'status'],
    use_container_width=True,
    hide_index=True,
)
# st.table(data=show_data)
