import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- 1. SETTINGS & TIMEZONE ---
IST = pytz.timezone('Asia/Kolkata')
st.set_page_config(page_title="Pocket Survival", page_icon="⚔️", layout="wide")

# --- 2. DATABASE CONNECTION ---
# These must be set in Streamlit Cloud -> Settings -> Secrets
URL = st.secrets.get("SUPABASE_URL", "")
KEY = st.secrets.get("SUPABASE_KEY", "")

if not URL or not KEY:
    st.error("Missing Supabase Secrets! Please add them to Streamlit Settings.")
    st.stop()

@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)

supabase = get_supabase()

# --- 3. AUTHENTICATION ---
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
            except: 
                st.error("Login failed. Check your email or password.")
    with tab2:
        ne = st.text_input("New Email", key="r_email")
        np = st.text_input("New Password", type="password", key="r_pw")
        if st.button("Register"):
            try:
                # Ensure "Confirm Email" is turned OFF in Supabase Auth Settings
                supabase.auth.sign_up({"email": ne, "password": np})
                st.success("Player Registered! Now switch to the 'Login' tab to enter.")
            except Exception as err:
                st.error(f"Error: {err}")

# --- 4. MAIN APP LOGIC ---
if st.session_state.user is None:
    login_ui()
else:
    u_id = st.session_state.user.id
    now = datetime.now(IST)
    current_month_str = now.strftime("%m-%Y") 

    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user.email}**")
        # --- HARDCODED BUDGET ---
        budget = 1000 
        st.metric("Monthly Max HP", f"₹{budget}")
        
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # Fetch User Data
    try:
        res = supabase.table("expenses").select("*").eq("user_id", u_id).execute()
        all_df = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Database Error: {e}")
        all_df = pd.DataFrame()

    # Filter for Current Month Only
    if not all_df.empty:
        # Formats YYYY-MM-DD into MM-YYYY
        all_df['month_check'] = all_df['timestamp'].apply(lambda x: x[5:7] + "-" + x[0:4])
        month_df = all_df[all_df['month_check'] == current_month_str]
    else:
        month_df = pd.DataFrame()

    # Calculations
    total_spent = month_df['amount'].sum() if not month_df.empty else 0
    current_hp = max(0, budget - total_spent)
    overspent = max(0, total_spent - budget)
    hp_percent = int((current_hp / budget) * 100) if budget > 0 else 0

    # --- 5. UI DISPLAY ---
    st.title(f"🕹️ Battle Station: {now.strftime('%B %Y')}")
    
    col1, col2 = st.columns(2)
    col1.metric("Wallet HP", f"₹{current_hp:,.2f}")
    
    if overspent > 0:
        col2.metric("CRITICAL DAMAGE", f"₹{overspent:,.2f}", delta="SYSTEM OVERLOAD", delta_color="inverse")
        st.error(f"⚠️ BUDGET BREACHED: You are over by ₹{overspent:,.2f}!")
    else:
        col2.metric("Monthly Spent", f"₹{total_spent:,.2f}")

    # Health Bar Visual
    st.progress(hp_percent / 100)
    st.divider()

    # Input Form
    with st.form("log_damage", clear_on_submit=True):
        c_item, c_amt = st.columns([3, 1])
        item_in = c_item.text_input("Source of Damage (Expense Name)")
        amt_in = c_amt.number_input("Amount (₹)", min_value=0.0)
        
        if st.form_submit_button("Confirm Damage"):
            if item_in and amt_in > 0:
                # IMPORTANT: Including user_id fixes the RLS Error
                supabase.table("expenses").insert({
                    "user_id": u_id,
                    "item": item_in,
                    "amount": amt_in,
                    "day_name": now.strftime("%A"),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M %p")
                }).execute()
                st.rerun()

    # History Table
    if not month_df.empty:
        st.subheader("🕵️ Monthly Intelligence Logs")
        display_df = month_df[['timestamp', 'item', 'amount']].sort_values(by='timestamp', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No damage taken yet this month. Stay safe!")
