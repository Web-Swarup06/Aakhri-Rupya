import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client

# --- 1. SETTINGS & TIMEZONE ---
IST = pytz.timezone('Asia/Kolkata')
st.set_page_config(page_title="Pocket Survival", page_icon="⚔️", layout="wide")

# --- 2. DATABASE CONNECTION ---
URL = st.secrets.get("SUPABASE_URL", "")
KEY = st.secrets.get("SUPABASE_KEY", "")

@st.cache_resource
def get_supabase():
    return create_client(URL, KEY)

supabase = get_supabase()

# --- 3. UPDATED AUTHENTICATION ---
if "user" not in st.session_state:
    st.session_state.user = None

def login_ui():
    st.title("🛡️ Survival Login")
    tab1, tab2 = st.tabs(["Login", "Create Player"])
    
    with tab1:
        e = st.text_input("Email", key="l_email")
        p = st.text_input("Password", type="password", key="l_pw")
        if st.button("Enter Game"):
            # Use a placeholder to prevent "Double Messages"
            msg = st.empty() 
            try:
                res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                if res.user:
                    st.session_state.user = res.user
                    msg.success("Identity Verified! Entering...")
                    st.rerun() # Clean jump to main app
            except:
                msg.error("Invalid Credentials.")

    with tab2:
        ne = st.text_input("New Email", key="r_email")
        np = st.text_input("New Password", type="password", key="r_pw")
        if st.button("Register"):
            try:
                supabase.auth.sign_up({"email": ne, "password": np})
                st.success("Account Created! You can now Login.")
            except Exception as err:
                st.error(f"Error: {err}")

# --- 4. MAIN APP ---
if st.session_state.user is None:
    login_ui()
else:
    u_id = st.session_state.user.id
    now = datetime.now(IST)
    current_month_str = now.strftime("%m-%Y") 

    # --- SIDEBAR HUD ---
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user.email}**")
        
        # Adding a 'key' helps Streamlit remember this value during the session
        budget = st.number_input("Monthly HP (Budget ₹)", value=1000, key="monthly_budget_input")
        
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    # --- THE REST OF YOUR FETCH & MATH CODE REMAINS THE SAME ---

    # Fetch Data
    res = supabase.table("expenses").select("*").eq("user_id", u_id).execute()
    all_df = pd.DataFrame(res.data)

    if not all_df.empty:
        all_df['month_check'] = all_df['timestamp'].apply(lambda x: x[5:7] + "-" + x[0:4])
        month_df = all_df[all_df['month_check'] == current_month_str]
    else:
        month_df = pd.DataFrame()

    # Math
    total_spent = month_df['amount'].sum() if not month_df.empty else 0
    current_hp = max(0, budget - total_spent)
    overspent = max(0, total_spent - budget)
    hp_percent = int((current_hp / budget) * 100) if budget > 0 else 0

    # UI
    st.title(f"🕹️ Battle Station: {now.strftime('%B %Y')}")
    c1, c2 = st.columns(2)
    c1.metric("Wallet HP", f"₹{current_hp:,.2f}")
    
    if overspent > 0:
        c2.metric("OVERSPENT", f"₹{overspent:,.2f}", delta="-CRITICAL", delta_color="inverse")
    else:
        c2.metric("Monthly Spent", f"₹{total_spent:,.2f}")

    st.progress(hp_percent / 100)
    st.divider()

    with st.form("log_damage", clear_on_submit=True):
        c_item, c_amt = st.columns([3, 1])
        item_in = c_item.text_input("Item Name")
        amt_in = c_amt.number_input("Amount (₹)", min_value=0.0)
        if st.form_submit_button("Confirm Damage"):
            if item_in and amt_in > 0:
                supabase.table("expenses").insert({
                    "user_id": u_id, "item": item_in, "amount": amt_in,
                    "day_name": now.strftime("%A"),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M %p")
                }).execute()
                st.rerun()

    if not month_df.empty:
        st.dataframe(month_df[['timestamp', 'item', 'amount']].sort_values(by='timestamp', ascending=False), use_container_width=True, hide_index=True)
