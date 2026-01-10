import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- CONFIG & TIMEZONE ---
IST = pytz.timezone('Asia/Kolkata')
st.set_page_config(page_title="Pocket Survival Global", page_icon="⚔️", layout="wide")

# --- DATABASE CONNECTION ---
# Replace with your keys or use st.secrets for deployment
URL = st.secrets.get("SUPABASE_URL", "YOUR_URL_HERE")
KEY = st.secrets.get("SUPABASE_KEY", "YOUR_KEY_HERE")
supabase: Client = create_client(URL, KEY)

# --- AUTHENTICATION LOGIC ---
if "user" not in st.session_state:
    st.session_state.user = None

def login_ui():
    st.title("🛡️ Survival Authentication")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        email = st.text_input("Email", key="l_email")
        pw = st.text_input("Password", type="password", key="l_pw")
        if st.button("Enter Game"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Invalid credentials.")
    with tab2:
        new_email = st.text_input("New Email")
        new_pw = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            supabase.auth.sign_up({"email": new_email, "password": new_pw})
            st.info("Check email for confirmation link!")

# --- MAIN APP ---
if st.session_state.user is None:
    login_ui()
else:
    u_id = st.session_state.user.id
    
    # Sidebar HUD
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state.user.email}**")
        budget = st.number_input("Monthly HP (Budget ₹)", value=5000)
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # Fetch Cloud Data
    res = supabase.table("expenses").select("*").eq("user_id", u_id).execute()
    df = pd.DataFrame(res.data)

    # Damage Logic (No Negative Balance)
    total_spent = df['amount'].sum() if not df.empty else 0
    overspent = max(0, total_spent - budget)
    current_hp = max(0, budget - total_spent)
    hp_percent = int((current_hp / budget) * 100) if budget > 0 else 0

    # Display HUD
    st.title("🕹️ Battle Station")
    c1, c2 = st.columns(2)
    c1.metric("Wallet HP", f"₹{current_hp:,.2f}")
    
    if overspent > 0:
        c2.metric("OVERSPENT BY", f"₹{overspent:,.2f}", delta="-CRITICAL", delta_color="inverse")
        st.error(f"⚠️ SYSTEM BREACH: You are ₹{overspent:,.2f} beyond your budget!")
    else:
        c2.metric("Total Damage Taken", f"₹{total_spent:,.2f}")

    st.progress(hp_percent / 100)
    st.divider()

    # Input Form
    with st.form("damage_log", clear_on_submit=True):
        col_a, col_b = st.columns([3, 1])
        item = col_a.text_input("Source of Damage (Item)")
        amt = col_b.number_input("Amount (₹)", min_value=0.0)
        if st.form_submit_button("Confirm Damage"):
            if item and amt > 0:
                now = datetime.now(IST)
                supabase.table("expenses").insert({
                    "user_id": u_id, "item": item, "amount": amt,
                    "day_name": now.strftime("%A"),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M %p")
                }).execute()
                st.rerun()

    # Intelligence Logs (Daily Filter)
    if not df.empty:
        st.subheader("🕵️ Intelligence Report")
        days = df['day_name'].unique()
        sel_day = st.selectbox("Select Day to Inspect", days)
        filtered = df[df['day_name'] == sel_day]
        st.table(filtered[['timestamp', 'item', 'amount']])
