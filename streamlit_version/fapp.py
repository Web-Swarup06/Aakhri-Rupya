import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# --- 1. CONFIGURATION & TIMEZONE ---
IST = pytz.timezone('Asia/Kolkata')
st.set_page_config(page_title="Pocket Survival", page_icon="💀", layout="wide")

CSV_FILE = "expenses_record.csv"

# --- 2. DATA ENGINE (CSV) ---
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["Item", "Amount", "Day", "Full_Timestamp"])

def save_expense(item, amount):
    now = datetime.now(IST)
    new_entry = {
        "Item": [item],
        "Amount": [amount],
        "Day": [now.strftime("%A")],
        "Full_Timestamp": [now.strftime("%Y-%m-%d %I:%M %p")]
    }
    df_new = pd.DataFrame(new_entry)
    if not os.path.exists(CSV_FILE):
        df_new.to_csv(CSV_FILE, index=False)
    else:
        df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🕹️ Game Menu")
    page = st.radio("Go to:", ["Battle Station (Add)", "Intelligence (Logs by Day)"])
    st.markdown("---")
    initial_hp = st.number_input("Monthly HP (Budget ₹)", value=5000, step=500)
    
    if st.button("🗑️ Reset All Progress"):
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            st.rerun()

# --- 4. DATA PROCESSING ---
df = load_data()
total_damage = df['Amount'].sum() if not df.empty else 0

# Survival Logic (No negative balance)
overspend_amt = 0
if total_damage > initial_hp:
    overspend_amt = total_damage - initial_hp
    current_hp = 0
    hp_percent = 0
else:
    current_hp = initial_hp - total_damage
    hp_percent = int((current_hp / initial_hp) * 100)

# --- 5. PAGE: BATTLE STATION ---
if page == "Battle Station (Add)":
    st.title("⚔️ Battle Station")
    
    # HUD Metrics
    col1, col2 = st.columns(2)
    col1.metric("Current HP", f"₹{current_hp:,.2f}")
    
    if overspend_amt > 0:
        col2.metric("Overspent By", f"₹{overspend_amt:,.2f}", delta="-CRITICAL", delta_color="inverse")
        st.error(f"⚠️ SYSTEM BREACH: You have overspent by ₹{overspend_amt:,.2f} beyond your budget!")
    else:
        col2.metric("Total Damage", f"₹{total_damage:,.2f}")

    # Visual HP Bar
    if overspend_amt > 0:
        st.warning("HP DEPLETED: Operating on Overdraft")
        st.progress(0)
    else:
        st.progress(hp_percent / 100)
        st.caption(f"Wallet Integrity: {hp_percent}%")

    st.markdown("---")
    
    # Input Form
    with st.form("input_form", clear_on_submit=True):
        st.subheader("Log New Expense")
        item_name = st.text_input("Source of Damage")
        cost = st.number_input("Amount (₹)", min_value=0.0)
        if st.form_submit_button("Confirm Damage"):
            if item_name and cost > 0:
                save_expense(item_name, cost)
                st.toast(f"Logged {item_name}!", icon="💥")
                st.rerun()

# --- 6. PAGE: INTELLIGENCE (LOGS BY DAY) ---
else:
    st.title("📅 Intelligence Report")
    
    if df.empty:
        st.info("No logs found.")
    else:
        # Grouping by day for selection
        existing_days = df['Day'].unique()
        selected_day = st.sidebar.selectbox("Filter by Day", existing_days)
        
        filtered_df = df[df['Day'] == selected_day]
        
        st.subheader(f"History for {selected_day}")
        
        for _, row in filtered_df.iterrows():
            with st.container():
                c1, c2 = st.columns([3, 1])
                # Extracting time from the timestamp string
                time_val = row['Full_Timestamp'].split(' ', 1)[1]
                c1.markdown(f"**{row['Item']}** \n\n <small>{time_val}</small>", unsafe_allow_html=True)
                c2.markdown(f"### -₹{row['Amount']}")
                st.divider()
        
        day_total = filtered_df['Amount'].sum()
        st.info(f"Total damage on {selected_day}: ₹{day_total:,.2f}")

        # Download option
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("📥 Download Record", csv_data, "expenses.csv", "text/csv")
