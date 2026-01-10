import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- CONFIG & TIMEZONE ---
IST = pytz.timezone('Asia/Kolkata')
st.set_page_config(page_title="Pocket Survival", page_icon="⚔️", layout="wide")

# --- DATABASE CONNECTION ---
# These keys should be added to Streamlit Cloud Settings > Secrets
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
        ne = st.text_input("New Email", key="r_email")
        np = st.text_input("New Password", type="password", key="r_pw")
        if st.button("Register"):
            try:
                # Signup works instantly if "Confirm Email" is OFF in Supabase
                supabase.auth.sign_up({"email": ne, "password": np})
                st.success("Player Registered! Now switch to the 'Login' tab.")
            except Exception as err:
                st.error(f"Error: {err}")

# --- MAIN GAME LOGIC ---
if st.session_state.user is None:
    login_ui()
else:
    u_id = st.session_state.user.id
    now = datetime.now(IST)
    current_month_str = now.strftime("%m-%Y") 

    with st.sidebar:
        st.write(f"Player: **{st.session_state.user.email}**")
        # HARDCODED BUDGET: Change 1000 here to change your starting HP
        budget = 1000 
        st.metric("Monthly Max HP", f"₹{budget}")
        
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # 1. Fetch data from Supabase
    res = supabase.table("expenses").select("*").eq("user_id", u_id).execute()
    all_df = pd.DataFrame(res.data)

    # 2. Filter for Current Month
    if not all_df.empty:
        # Extract MM-YYYY from the stored timestamp string (YYYY-MM-DD...)
        all_df['month_check'] = all_df['timestamp'].apply(lambda x: x[5:7] + "-" + x[0:4])
        month_df = all_df[all_df['month_check'] == current_month_str]
    else:
        month_df = pd.DataFrame()

    # 3. HP Calculations
    total_spent = month_df['amount'].sum() if not month_df.empty else 0
    current_hp = max(0, budget - total_spent)
    overspent = max(0, total_spent - budget)
    hp_percent = int((current_hp / budget) * 100) if budget > 0 else 0

    # --- UI DISPLAY ---
    st.title(f"🕹️ Battle Station: {now.strftime('%B %Y')}")
    
    col1, col2 = st.columns(2)
    col1.metric("Wallet HP", f"₹{current_hp:,.2f}")
    
    if overspent > 0:
        col2.metric("CRITICAL DAMAGE", f"₹{overspent:,.2f}", delta="SYSTEM OVERLOAD", delta_color="inverse")
        st.error(f"⚠️ BUDGET BREACHED: You are over by ₹{overspent:,.2f}!")
    else:
        col2.metric("Total Monthly Damage", f"₹{total_spent:,.2f}")

    # Health Bar
    bar_color = "green" if hp_percent > 20 else "red"
    st.progress(hp_percent / 100)
    st.divider()

    # Damage Input Form
    with st.form("log_damage", clear_on_submit=True):
        c_item, c_amt = st.columns([3, 1])
        item_in = c_item.text_input("What hit your wallet? (Item)")
        amt_in = c_amt.number_input("Damage Amount (₹)", min_value=0.0)
        if st.form_submit_button("Confirm Damage"):
            if item_in and amt_in > 0:
                supabase.table("expenses").insert({
                    "user_id": u_id,
                    "item": item_in,
                    "amount": amt_in,
                    "day_name": now.strftime("%A"),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M %p")
                }).execute()
                st.rerun()

    # Intelligence Logs (Monthly Filtered)
    if not month_df.empty:
        st.subheader("🕵️ Monthly Combat Logs")
        display_df = month_df[['timestamp', 'item', 'amount']].sort_values(by='timestamp', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
