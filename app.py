import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- CONFIG & TIMEZONE ---
IST = pytz.timezone('Asia/Kolkata')
st.set_page_config(page_title="Pocket Survival", page_icon="⚔️", layout="wide")

# --- DATABASE CONNECTION ---
# When you deploy, these will be pulled from Streamlit Cloud "Secrets"
URL = st.secrets.get("SUPABASE_URL", "YOUR_URL_HERE")
KEY = st.secrets.get("SUPABASE_KEY", "YOUR_KEY_HERE")
supabase: Client = create_client(URL, KEY)

# --- AUTHENTICATION ---
if "user" not in st.session_state:
    st.session_state.user = None

def login_ui():
    st.title("🛡️ Survival Login")
    tab1, tab2 = st.tabs(["Login", "Create Player"])
    with tab1:
        e = st.text_input("Email", key="l_email")
        p = st.text_input("Password", type="password", key="l_pw")
        if st.button("Enter Game"):
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Login failed. Check credentials.")
    with tab2:
        ne = st.text_input("New Email")
        np = st.text_input("New Password", type="password")
        if st.button("Register"):
            supabase.auth.sign_up({"email": ne, "password": np})
            st.info("Check your email for the confirmation link!")

# --- MAIN APP LOGIC ---
if st.session_state.user is None:
    login_ui()
else:
    u_id = st.session_state.user.id
    now = datetime.now(IST)
    current_month_str = now.strftime("%m-%Y") # e.g., "01-2026"

    with st.sidebar:
        st.write(f"Player: **{st.session_state.user.email}**")
        budget = st.number_input("Monthly HP (Budget ₹)", value=5000)
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # 1. Fetch ALL user data
    res = supabase.table("expenses").select("*").eq("user_id", u_id).execute()
    all_df = pd.DataFrame(res.data)

    # 2. Filter for CURRENT MONTH ONLY
    if not all_df.empty:
        # We look at the 'timestamp' column which we save as 'YYYY-MM-DD...'
        all_df['month_check'] = all_df['timestamp'].apply(lambda x: x[5:7] + "-" + x[0:4])
        month_df = all_df[all_df['month_check'] == current_month_str]
    else:
        month_df = pd.DataFrame()

    # 3. Calculations
    total_spent = month_df['amount'].sum() if not month_df.empty else 0
    current_hp = max(0, budget - total_spent)
    overspent = max(0, total_spent - budget)
    hp_percent = int((current_hp / budget) * 100) if budget > 0 else 0

    # --- UI DISPLAY ---
    st.title(f"🕹️ Battle Station: {now.strftime('%B %Y')}")
    
    c1, c2 = st.columns(2)
    c1.metric("Current HP", f"₹{current_hp:,.2f}")
    
    if overspent > 0:
        c2.metric("CRITICAL DAMAGE", f"₹{overspent:,.2f}", delta="SYSTEM OVERLOAD", delta_color="inverse")
        st.error(f"🛑 Budget Breached! You are ₹{overspent:,.2f} over the limit.")
    else:
        c2.metric("Monthly Spending", f"₹{total_spent:,.2f}")

    st.progress(hp_percent / 100)
    st.divider()

    # Input Form
    with st.form("damage_form", clear_on_submit=True):
        col_item, col_amt = st.columns([3, 1])
        item_input = col_item.text_input("Expense Description")
        amt_input = col_amt.number_input("Amount (₹)", min_value=0.0)
        if st.form_submit_button("Log Damage"):
            if item_input and amt_input > 0:
                supabase.table("expenses").insert({
                    "user_id": u_id,
                    "item": item_input,
                    "amount": amt_input,
                    "day_name": now.strftime("%A"),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M %p")
                }).execute()
                st.rerun()

    # Daily Log View
    if not month_df.empty:
        st.subheader("🕵️ Monthly Intelligence")
        # Just show the most recent items first
        st.dataframe(month_df[['timestamp', 'item', 'amount']].sort_values(by='timestamp', ascending=False), use_container_width=True)
