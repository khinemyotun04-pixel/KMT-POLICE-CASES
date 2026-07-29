import sqlite3
import pandas as pd
import streamlit as st
import hashlib
import os
from io import BytesIO

# --- Helper functions for user management ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_user(conn, username: str):
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    return cur.fetchone()


def create_admin_if_missing(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        # No users yet — require setup by entering password (handled in app flow)
        return False
    return True


def add_user(conn, username: str, password: str):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, hash_password(password)),
    )
    conn.commit()


# Page Configuration
st.set_page_config(
    page_title="ပ အမှုထဲ မှတ်တမ်းစနစ်",
    page_icon="🇲🇲",
    layout="wide",
)

# Initialize SQLite Database
DB_PATH = "police_cases.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute(
    """
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region TEXT,
        district TEXT,
        township TEXT,
        station TEXT,
        case_no TEXT,
        complainant TEXT,
        defendant TEXT,
        offence TEXT,
        date_time TEXT,
        investigator TEXT,
        status TEXT,
        remarks TEXT
    )
    """
)

c.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """
)
conn.commit()

# --- Authentication / Admin setup flow ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""

st.sidebar.title("Authentication")

# If no admin user exists, ask to set it up
if not create_admin_if_missing(conn):
    st.sidebar.warning("သင့်အတွက် Admin အကောင့် မရှိသေးပါ။ Admin စကားဝှက်သတ်မှတ်ပေးပါ။")
    with st.sidebar.form("setup_admin"):
        admin_username = st.text_input("Admin အမည်", value="admin")
        admin_password = st.text_input("Admin စကားဝှက် (အသစ်)", type="password")
        admin_password_confirm = st.text_input("စကားဝှက် ထပ်မံရေးပါ", type="password")
        setup_btn = st.form_submit_button("Admin စာရင်းသွင်းမည်")
        if setup_btn:
            if not admin_password or admin_password != admin_password_confirm:
                st.sidebar.error("စကားဝှက်မကိုက်ပါ။ ထပ်မံစမ်းကြည့်ပါ။")
            else:
                add_user(conn, admin_username.strip(), admin_password)
                st.sidebar.success("✅ Admin အကောင့်ကို အောင်မြင်စွာ ပြုလုပ်ပြီးပါပြီ။ အကောင့်ဖြင့် ဝင်ရန် စာမျက်နှာကို ပြန်လည် Refresh ပါ။")

# Login form (shows when users exist and not logged in)
if not st.session_state["logged_in"] and create_admin_if_missing(conn):
    with st.sidebar.form("login_form"):
        username = st.text_input("အမည်")
        password = st.text_input("စကားဝှက်", type="password")
        login_btn = st.form_submit_button("ဝင်မည်")
        if login_btn:
            user = get_user(conn, username.strip())
            if user and hash_password(password) == user[2]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username.strip()
                st.sidebar.success(f"ကြိုဆိုပါတယ် — {st.session_state['username']}")
            else:
                st.sidebar.error("အမည် သို့မဟုတ် စကားဝှက် မှားနေပါတယ်။")

# If logged in, show logout button
if st.session_state.get("logged_in"):
    if st.sidebar.button("ထွက်မည်"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.experimental_rerun()

# --- KMT Logo handling ---
st.sidebar.markdown("---")
st.sidebar.subheader("KMT လိုဂို ထည့်ရန်")
logo_file = None
# Allow uploading a logo. If uploaded, show and keep it in session_state (not persisted to repo)
uploaded_logo = st.sidebar.file_uploader("လို့ဂို ဓာတ်ပုံ (.png/.jpg)", type=["png", "jpg", "jpeg"])
if uploaded_logo is not None:
    # store raw bytes in session state so it persists while app runs
    st.session_state["kmt_logo"] = uploaded_logo.read()

# If there's a saved logo in the working directory, use it; otherwise use uploaded one
if os.path.exists("kmt_logo.png"):
    try:
        with open("kmt_logo.png", "rb") as f:
            logo_file = f.read()
    except Exception:
        logo_file = None
elif st.session_state.get("kmt_logo"):
    logo_file = st.session_state.get("kmt_logo")

# Display header with logo (if available)
col_left, col_right = st.columns([1, 6])
with col_left:
    if logo_file:
        st.image(logo_file, width=120)
    else:
        st.markdown("# 🇲🇲 မြန်မာနိုင်ငံရဲတပ်ဖွဲ့")
with col_right:
    if st.session_state.get("logged_in"):
        st.markdown(f"### ကြိုဆိုပါတယ် — {st.session_state['username']}")
    st.markdown("## အမှုတွ�� မှတ်တမ်းစနစ်")

st.markdown("---")

# If not logged in, block access to the rest of the app
if not st.session_state.get("logged_in"):
    st.info("ကျေးဇူးပြု၍ Admin အကောင့်ဖြင့် အရင် ဝင်ပါ။ Sidebar မှာ အကောင့်ဝင်ရန် ဖောင်ရှိပါတယ်။")
    st.stop()

# --- Main app (same functionality as before) ---
menu = ["အမှုအသစ်ထည့်ရန်", "အမှုများကြည့်ရှုရန်/ရှာဖွေရန်", "စာရင်းအင်းအချက်အလက်"]
choice = st.sidebar.selectbox("လုပ်ဆောင်ချက် ရွေးချယ်ရန်", menu)

if choice == "အမှုအသစ်ထည့်ရန်":
    st.subheader("📝 အမှုအသစ် အချက်အလက် မှတ်တမ်းပြုစုခြင်း")
    with st.form("case_form"):
        col1, col2 = st.columns(2)
        with col1:
            region = st.text_input("တိုင်းဒေသကြီး / ပြည်နယ်")
            district = st.text_input("ခရိုင်")
            township = st.text_input("မြို့နယ်")
            station = st.text_input("စခန်း")
            case_no = st.text_input("အမှုအမှတ် / ခုနှစ်")
            complainant = st.text_input("တိုင်တန်းသူ အမည်")
        with col2:
            defendant = st.text_input("တရားခံ အမည်")
            offence = st.text_input("ပုဒ်မ / ပြစ်မှုအမျိုးအစား")
            date_time = st.text_input("ဖြစ်စဉ်နေ့စွဲ နှင့် အချိန်")
            investigator = st.text_input("စစ်ဆေးဆဲ တာဝန်ခံ အရာရှိ")
            status = st.selectbox("အမှုအခြေအနေ", ["စစ်ဆေးဆဲ", "တရားရုံးတင်ပြီး", "အပြီးသတ်ပိတ်သိမ်း"]) 
            remarks = st.text_area("မှတ်ချက်")
        submit_button = st.form_submit_button(label="အချက်အလက် သိမ်းဆည်းမည်")
        if submit_button:
            if station.strip() and case_no.strip():
                c.execute(
                    """
                    INSERT INTO cases (region, district, township, station, case_no, complainant, defendant, offence, date_time, investigator, status, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (region, district, township, station, case_no, complainant, defendant, offence, date_time, investigator, status, remarks),
                )
                conn.commit()
                st.success("✅ အမှုအချက်အလက်များကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")
            else:
                st.warning("⚠️ ကျေးဇူးပြု၍ စခန်းနှင့် အမှုအမှတ်ကို ထည့်သွင်းပေးပါ။")

elif choice == "အမှုများကြည့်ရှုရန်/ရှာဖွေရန်":
    st.subheader("🔍 အမှုတွဲများ ရှာဖွေစစ်ဆေးခြင်း")
    search_query = st.text_input("စခန်းအမည် (သို့) အမှုအမှတ် ဖြင့် ရှာရန်")
    if search_query and search_query.strip():
        sql = "SELECT * FROM cases WHERE station LIKE ? OR case_no LIKE ? ORDER BY id DESC"
        params = (f"%{search_query.strip()}%", f"%{search_query.strip()}%")
        df = pd.read_sql(sql, conn, params=params)
    else:
        df = pd.read_sql("SELECT * FROM cases ORDER BY id DESC", conn)

    if df.empty:
        st.info("ပြသရန် အချက်အလက် မရှိသေးပါ။")
    else:
        st.dataframe(df, use_container_width=True)
        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="CSV အဖြစ်ဒေါင်းလုတ်မည်",
            data=csv,
            file_name="police_cases.csv",
            mime="text/csv",
        )

elif choice == "စာရင်းအင်းအချက်အလက်":
    st.subheader("📊 အမှုအခြေအနေ စာရင်းအင်းများ")
    df_stats = pd.read_sql("SELECT status, count(*) as count FROM cases GROUP BY status", conn)
    if not df_stats.empty:
        df_stats = df_stats.set_index("status")
        st.bar_chart(df_stats)
        st.table(df_stats)
    else:
        st.info("ပြသရန် အချက်အလက် မရှိသေးပါ။")

# Note: We keep the DB connection open for the lifetime of the app. If you need explicit close, call conn.close().
