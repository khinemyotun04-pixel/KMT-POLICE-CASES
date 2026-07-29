import sqlite3
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="ပ အမှုထဲ မှတ်တမ်းစနစ်",
    page_icon="🇲🇲",
    layout="wide",
)

# Initialize SQLite Database
conn = sqlite3.connect("police_cases.db", check_same_thread=False)
c = conn.cursor()
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
conn.commit()

# App Header
st.title("🇲🇲 မြန်မာနိုင်ငံရဲတပ်ဖွဲ့ - အမှုတွဲမှတ်တမ်းစနစ်")
st.markdown("---")

# Sidebar Menu
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

# (Optional) Close connection when the app stops - Streamlit apps usually run persistently,
# so we keep the connection open. If you need to close it explicitly, call conn.close().
