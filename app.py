import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO

# পেজ কনফিগারেশন (মোবাইল ফ্রেন্ডলি ভিউ)
st.set_page_config(page_title="PharmaSales Tracker", page_icon="💊", layout="wide")

# ডেমো ডাক্তার তালিকা (আপনার ১০০ জন ডাক্তারের ডেটাবেস)
DOCTOR_LIST = [
    "SUMIT PATRA", "P PANDA", "BIDISHA BAIDYA", "K K GUHA", 
    "TIYASA MONDAL", "SOURAV DOLOI", "AKASH SEN", "BIDYUT BANERJEE",
    "BARUN MANDI", "BANAMALI SAMANTA", "S S PRAMANIK", "BIPLAB JANA"
]

MONTH_LIST = ["APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER", "JANUARY", "FEBRUARY", "MARCH"]

# সেশন স্টেটে ডেটা স্টোর করা (পরবর্তীতে গুগল শিট বা ডাটাবেসে কানেক্ট করা যাবে)
if "sales_data" not in st.session_state:
    st.session_state.sales_data = []

# সাইডবার লগইন / রোল সিলেকশন
st.sidebar.title("🔐 Login Portal")
user_role = st.sidebar.radio("Select Role", ["Field Staff", "Manager / Admin"])

# -------------------------------------------------------------
# ১. ফিল্ড স্টাফ ইন্টারফেস (Mobile Friendly Form)
# -------------------------------------------------------------
if user_role == "Field Staff":
    st.title("📲 Field Staff Daily Reporting")
    st.write("সহজে ডাক্তারের নাম ও সেলস এন্ট্রি করুন:")

    with st.form("entry_form", clear_on_submit=True):
        staff_name = st.selectbox("Staff Name", ["Staff 1 (Uluberia)", "Staff 2 (Amta)", "Staff 3 (Bagnan)", "Staff 4 (Shyampur)"])
        month = st.selectbox("Select Month", MONTH_LIST, index=5)
        doctor = st.selectbox("Doctor Name", DOCTOR_LIST)
        target = st.number_input("Target Potentiality (₹)", min_value=0, step=1000, value=10000)
        sale = st.number_input("Actual Sale Received (₹)", min_value=0, step=500, value=0)
        remarks = st.text_input("Remarks (Optional)")
        
        submitted = st.form_submit_button("🚀 Submit Sales")
        
        if submitted:
            if sale > 0:
                st.session_state.sales_data.append({
                    "Staff": staff_name,
                    "Month": month,
                    "Doctor": doctor,
                    "Target": target,
                    "Sale": sale,
                    "Remarks": remarks
                })
                st.success(f"সফলভাবে যুক্ত হয়েছে: {doctor} - ₹{sale:,}")
            else:
                st.warning("অনুগ্রহ করে বিক্রয়ের টাকা (Sale Received) লিখুন!")

# -------------------------------------------------------------
# ২. ম্যানেজার / অ্যাডমিন ইন্টারফেস (Auto-Merging & Export)
# -------------------------------------------------------------
else:
    st.title("📊 Manager Dashboard & Master Consolidation")
    
    if len(st.session_state.sales_data) == 0:
        st.info("এখনও কোনো সেলস এন্ট্রি জমা পড়েনি।")
    else:
        df_raw = pd.DataFrame(st.session_state.sales_data)
        
        # ট্যাব ১: লাইভ কাঁচা এন্ট্রি
        tab1, tab2 = st.tabs(["📋 All Staff Live Entries", "🏆 Master Consolidated Report"])
        
        with tab1:
            st.dataframe(df_raw, use_container_width=True)
            
        with tab2:
            st.write("### একই ডাক্তারের একাধিক এন্ট্রি স্বয়ংক্রিয়ভাবে যোগ করা রিপোর্ট:")
            
            # অটোমেটিক ডুপ্লিকেট মার্জিং লজিক
            df_consolidated = df_raw.groupby(["Month", "Doctor"]).agg({
                "Target": "sum",
                "Sale": "sum",
                "Staff": lambda x: ", ".join(x.unique()),
                "Remarks": lambda x: "; ".join([r for r in x if r])
            }).reset_index()
            
            # লাখে রূপান্তর (Lakhs)
            df_consolidated["Sale_in_Lakhs"] = (df_consolidated["Sale"] / 100000).round(2)
            
            st.dataframe(df_consolidated, use_container_width=True)
            
            # এক্সেল এক্সপোর্ট বাটন
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_consolidated.to_excel(writer, index=False, sheet_name="Consolidated_Master")
                df_raw.to_excel(writer, index=False, sheet_name="Raw_Entries")
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Download Master Excel Sheet",
                data=excel_data,
                file_name="Master_Sales_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
