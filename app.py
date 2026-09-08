import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import json
import time

st.set_page_config(page_title="PharmaSales Tracker Pro", page_icon="💊", layout="wide")

# -----------------------------------------------------------------------------
# গুগল শিট ও স্ক্রিপ্ট কনফিগারেশন (সরাসরি আপনার আসল আইডি সহ)
# -----------------------------------------------------------------------------
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwtsQjARD1Ig8B0BFSoLaNuLi_Je0lw9vdC52vE_f59Ef6143cAGjPlvFGA/exec"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1rhkmYVHJvYIHIISxUDuURb_NZAQHXvyPhaYFcfPb7c8/gviz/tq?tqx=out:csv"

# ১০০ জন ডাক্তারের ডাটাবেস
DOCTOR_LIST = [
    "SUMIT PATRA", "P PANDA", "BIDISHA BAIDYA", "K K GUHA", "TIYASA MONDAL",
    "SOURAV DOLOI", "AKASH SEN", "BIDYUT BANERJEE", "BARUN MANDI", "BANAMALI SAMANTA",
    "S S PRAMANIK", "BIPLAB JANA", "TAPAS MANDAL", "S GHORAI", "A K DOLUI",
    "S BHOWMIK", "M HAZRA", "R GHOSH", "A PAL", "D K DAS", "S K MAITY",
    "P C HAZRA", "N C DAS", "S DEY", "A K RAY", "T K SAHOO", "B MUKHERJEE",
    "S K GHOSH", "P PATRA", "D DOLOI", "A MIDYA", "S SAMANTA", "B DOLOI"
]

STAFF_LIST = ["Sourav", "Susanta", "Sarojit", "New Joining"]
MONTH_LIST = ["APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "JANUARY", "FEBRUARY", "MARCH"]

st.sidebar.title("🔐 Login Portal")
user_role = st.sidebar.radio("Select Portal", ["📲 Field Staff Entry", "📊 Manager / Admin Dashboard"])

# -----------------------------------------------------------------------------
# লাইভ ডেটা পড়ার ফাংশন (gviz রিয়েল-টাইম ইঞ্জিন)
# -----------------------------------------------------------------------------
def get_live_data():
    try:
        fresh_url = f"{GOOGLE_SHEET_CSV_URL}&t={int(time.time())}"
        df = pd.read_csv(fresh_url)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        if "Sale" in df.columns:
            df["Sale"] = pd.to_numeric(df["Sale"], errors="coerce").fillna(0)
        if "Target" in df.columns:
            df["Target"] = pd.to_numeric(df["Target"], errors="coerce").fillna(0)
        return df
    except Exception:
        return pd.DataFrame()

df_live = get_live_data()

# -----------------------------------------------------------------------------
# ১. ফিল্ড স্টাফ এন্ট্রি + লাইভ রিপোর্ট টেবিল
# -----------------------------------------------------------------------------
if user_role == "📲 Field Staff Entry":
    st.title("📲 Field Staff Sales Entry & Live Status")

    col1, col2 = st.columns(2)
    with col1:
        staff_name = st.selectbox("Staff Name (আপনার নাম নির্বাচন করুন)", STAFF_LIST)
        month = st.selectbox("Select Month (মাস)", MONTH_LIST, index=5)
    with col2:
        doctor = st.selectbox("Select Doctor (ডাক্তার নির্বাচন করুন)", DOCTOR_LIST)
        target = st.number_input("Target Potentiality (₹)", min_value=0, step=1000, value=20000)

    sale = st.number_input("Actual Sale Received (₹)", min_value=0, step=500, value=0)

    # ডুপ্লিকেট এন্ট্রি চেকিং
    existing_records = pd.DataFrame()
    if not df_live.empty and "Doctor" in df_live.columns and "Month" in df_live.columns:
        existing_records = df_live[(df_live["Doctor"].astype(str).str.strip().str.upper() == str(doctor).strip().upper()) & 
                                   (df_live["Month"].astype(str).str.strip().str.upper() == str(month).strip().upper())]

    if not existing_records.empty:
        total_prev = existing_records["Sale"].sum()
        staff_prev = ", ".join(existing_records["Staff"].astype(str).unique())
        st.warning(f"⚠️ **সতর্কতা:** এই ডাক্তারের ({doctor}) নামে **{month}** মাসে ইতিমধ্যে **₹{total_prev:,.0f}** সেলস এন্ট্রি জমা আছে (স্টাফ: {staff_prev})।")

    with st.form("staff_entry_form", clear_on_submit=True):
        confirm_duplicate = False
        if not existing_records.empty:
            confirm_duplicate = st.checkbox("হ্যাঁ, আমি নিশ্চিত হয়ে অতিরিক্ত সেলস যোগ করতে চাই")

        submitted = st.form_submit_button("🚀 Submit Sales")

        if submitted:
            if sale <= 0:
                st.error("অনুগ্রহ করে বিক্রয়ের টাকা (Sale Received) সঠিকভাবে লিখুন!")
            elif not existing_records.empty and not confirm_duplicate:
                st.error("⚠️ অতিরিক্ত সেলস দিতে চাইলে উপরের বক্সে টিক চিহ্ন দিয়ে সাবমিট করুন।")
            else:
                payload = {
                    "staff": staff_name,
                    "month": month,
                    "doctor": doctor,
                    "target": target,
                    "sale": sale
                }
                try:
                    res = requests.post(
                        APPS_SCRIPT_URL, 
                        data=json.dumps(payload), 
                        headers={"Content-Type": "application/json"},
                        allow_redirects=True, 
                        timeout=15
                    )
                    st.success(f"✅ সফলভাবে সংরক্ষিত হয়েছে: {doctor} - ₹{sale:,} ({staff_name})")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"সংযোগ সমস্যা: {e}")

    # -------------------------------------------------------------
    # ফিল্ড স্টাফের লাইভ টেবিল (কোন কোন ডাক্তারের সেলস জমা পড়েছে)
    # -------------------------------------------------------------
    st.divider()
    st.subheader(f"📋 {month} মাসে জমা পড়া ডাক্তারদের সেলস রিপোর্ট")

    view_scope = st.radio(
        "কোন রিপোর্টটি দেখতে চান?",
        [f"আমার নিজের এন্ট্রি ({staff_name})", "সব ফিল্ড স্টাফদের সম্মিলিত এন্ট্রি"],
        horizontal=True
    )

    if not df_live.empty and "Month" in df_live.columns:
        if view_scope == f"আমার নিজের এন্ট্রি ({staff_name})":
            display_df = df_live[(df_live["Staff"].astype(str).str.strip().str.upper() == staff_name.strip().upper()) & 
                                 (df_live["Month"].astype(str).str.strip().str.upper() == month.strip().upper())]
        else:
            display_df = df_live[df_live["Month"].astype(str).str.strip().str.upper() == month.strip().upper()]

        if not display_df.empty:
            cols = [c for c in ["Doctor", "Sale", "Target", "Staff", "Timestamp"] if c in display_df.columns]
            st.dataframe(
                display_df[cols].reset_index(drop=True), 
                use_container_width=True,
                height=300
            )

            total_val = display_df["Sale"].sum()
            total_drs = display_df["Doctor"].nunique()
            st.info(f"📊 মোট জমা হওয়া সেলস: **₹{total_val:,.0f}** | মোট ডাক্তার কভার হয়েছে: **{total_drs}** জন")
        else:
            st.caption(f"ℹ️ {month} মাসে এখনও কোনো সেলস রিপোর্ট জমা পড়েনি।")
    else:
        st.caption("ℹ️ ডেটাবেস থেকে ডেটা লোড হচ্ছে অথবা এখনও কোনো এন্ট্রি জমা পড়েনি।")

# -------------------------------------------------------------
# ২. ম্যানেজার ড্যাশবোর্ড
# -------------------------------------------------------------
else:
    st.title("📊 Manager Master Dashboard")
    admin_pass = st.sidebar.text_input("Admin Password", type="password")

    if admin_pass != "admin123":
        st.warning("🔒 ড্যাশবোর্ড দেখতে অনুগ্রহ করে অ্যাডমিন পাসওয়ার্ড দিন। (ডিফল্ট: admin123)")
    else:
        st.success("স্বাগতম অ্যাডমিন! গুগল শিট থেকে লাইভ ডেটা লোড হচ্ছে...")

        if not df_live.empty:
            tab1, tab2 = st.tabs(["🏆 Consolidated Master Report", "📋 Google Sheet Raw Live Data"])

            with tab1:
                st.subheader("একই ডাক্তারের একাধিক এন্ট্রি স্বয়ংক্রিয়ভাবে যোগ করা মাস্টার হিসাব:")
                
                df_merged = df_live.groupby(["Month", "Doctor"]).agg({
                    "Target": "sum",
                    "Sale": "sum",
                    "Staff": lambda x: ", ".join(x.unique())
                }).reset_index()

                df_merged["Business in Lakhs"] = (df_merged["Sale"] / 100000).round(2)
                st.dataframe(df_merged, use_container_width=True)

                buf = BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    df_merged.to_excel(writer, index=False, sheet_name="Master_Report")
                    df_live.to_excel(writer, index=False, sheet_name="All_Staff_Entries")

                st.download_button(
                    label="📥 Download Master Excel Sheet",
                    data=buf.getvalue(),
                    file_name="Master_Sales_Consolidation.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with tab2:
                st.subheader("গুগল শিটের সমস্ত কাঁচা এন্ট্রি হিস্ট্রি:")
                st.dataframe(df_live, use_container_width=True)
        else:
            st.info("এখনও কোনো সেলস ডেটা জমা পড়েনি।")
