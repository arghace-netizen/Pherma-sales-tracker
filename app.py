import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import json

st.set_page_config(page_title="PharmaSales Tracker Pro", page_icon="💊", layout="wide")

# -----------------------------------------------------------------------------
# আপনার লিঙ্ক দুটি এখানে কোটেশনের ভেতরে বসান:
# -----------------------------------------------------------------------------
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxtvGD6H1ig0URXF1alcnN6l_JcHNhxBcbzsOBJem_YFZNC3TN0imHKIf61_m_V71KK6w/exec"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1rhkmYVHJVyiHIISxUDuURb_NZAQHXvyPhaYFcfPb72k/export?format=csv"

# ১০০ জন ডাক্তারের ডাটাবেস
DOCTOR_LIST = [
    "SUMIT PATRA", "P PANDA", "BIDISHA BAIDYA", "K K GUHA", "TIYASA MONDAL",
    "SOURAV DOLOI", "AKASH SEN", "BIDYUT BANERJEE", "BARUN MANDI", "BANAMALI SAMANTA",
    "S S PRAMANIK", "BIPLAB JANA", "TAPAS MANDAL", "S GHORAI", "A K DOLUI",
    "S BHOWMIK", "M HAZRA", "R GHOSH", "A PAL", "D K DAS", "S K MAITY",
    "P C HAZRA", "N C DAS", "S DEY", "A K RAY", "T K SAHOO", "B MUKHERJEE",
    "S K GHOSH", "P PATRA", "D DOLOI", "A MIDYA", "S SAMANTA", "B DOLOI"
]

MONTH_LIST = ["APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "JANUARY", "FEBRUARY", "MARCH"]

# সাইডবার পোর্টাল
st.sidebar.title("🔐 Login Portal")
user_role = st.sidebar.radio("Select Portal", ["📲 Field Staff Entry", "📊 Manager / Admin Dashboard"])

# -----------------------------------------------------------------------------
# ১. ফিল্ড স্টাফ এন্ট্রি (Google Sheet-এ স্থায়ীভাবে সেভ হবে)
# -----------------------------------------------------------------------------
if user_role == "📲 Field Staff Entry":
    st.title("📲 Field Staff Sales Entry")
    st.write("সহজে ডাক্তারের নাম ও সেলস সিলেক্ট করে সাবমিট করুন:")

    with st.form("staff_entry_form", clear_on_submit=True):
        staff_name = st.selectbox("Staff Name", [
            "Staff 1 (Uluberia Area)",
            "Staff 2 (Amta Area)",
            "Staff 3 (Bagnan Area)",
            "Staff 4 (Shyampur Area)"
        ])
        month = st.selectbox("Select Month", MONTH_LIST, index=5)
        doctor = st.selectbox("Select Doctor", DOCTOR_LIST)
        target = st.number_input("Target Potentiality (₹)", min_value=0, step=1000, value=20000)
        sale = st.number_input("Actual Sale Received (₹)", min_value=0, step=500, value=0)

        submitted = st.form_submit_button("🚀 Submit Sales")

        if submitted:
            if sale > 0:
                payload = {
                    "staff": staff_name,
                    "month": month,
                    "doctor": doctor,
                    "target": target,
                    "sale": sale
                }
                try:
                    res = requests.post(APPS_SCRIPT_URL, data=json.dumps(payload), timeout=15)
                    if res.status_code == 200:
                        st.success(f"✅ গুগলে স্থায়ীভাবে সেভ হয়েছে: {doctor} - ₹{sale:,}")
                    else:
                        st.warning("⚠️ তথ্য পাঠানো হয়েছে, তবে সার্ভার রেসপন্স চেক করুন।")
                except Exception as e:
                    st.error(f"সংযোগ ত্রুটি: {e}")
            else:
                st.warning("অনুগ্রহ করে বিক্রয়ের টাকা (Sale Received) লিখুন!")

# -----------------------------------------------------------------------------
# ২. ম্যানেজার ড্যাশবোর্ড (অটো-মার্জিং ও এক্সেল ডাউনলোড)
# -----------------------------------------------------------------------------
else:
    st.title("📊 Manager Master Dashboard")
    admin_pass = st.sidebar.text_input("Admin Password", type="password")

    if admin_pass != "admin123":
        st.warning("🔒 ড্যাশবোর্ড দেখতে অনুগ্রহ করে অ্যাডমিন পাসওয়ার্ড দিন। (ডিফল্ট: admin123)")
    else:
        st.success("স্বাগতম অ্যাডমিন! গুগল শিট থেকে লাইভ ডেটা লোড হচ্ছে...")

        try:
            df = pd.read_csv(GOOGLE_SHEET_CSV_URL)
            df["Sale"] = pd.to_numeric(df["Sale"], errors="coerce").fillna(0)
            df["Target"] = pd.to_numeric(df["Target"], errors="coerce").fillna(0)

            tab1, tab2 = st.tabs(["🏆 Consolidated Master Report", "📋 Google Sheet Raw Live Data"])

            with tab1:
                st.subheader("একই ডাক্তারের একাধিক এন্ট্রি স্বয়ংক্রিয়ভাবে যোগ করা হিসাব:")
                
                df_merged = df.groupby(["Month", "Doctor"]).agg({
                    "Target": "sum",
                    "Sale": "sum",
                    "Staff": lambda x: ", ".join(x.unique())
                }).reset_index()

                # লাখে রূপান্তর
                df_merged["Business in Lakhs"] = (df_merged["Sale"] / 100000).round(2)

                st.dataframe(df_merged, use_container_width=True)

                # এক্সেল ফাইল ডাউনলোড
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    df_merged.to_excel(writer, index=False, sheet_name="Master_Report")
                    df.to_excel(writer, index=False, sheet_name="All_Staff_Entries")

                st.download_button(
                    label="📥 Download Master Excel Sheet",
                    data=buf.getvalue(),
                    file_name="Master_Sales_Consolidation.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with tab2:
                st.subheader("গুগল শিটের লাইভ কাঁচা এন্ট্রি:")
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.info("এখনও কোনো সেলস ডেটা জমা পড়েনি অথবা ডেটা রিড করা যাচ্ছে না।")
