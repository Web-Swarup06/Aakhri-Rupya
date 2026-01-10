# ⚔️ Pocket Survival: Finance Edition
Pocket Survival is a gamified personal finance tracker built with Streamlit and Supabase. Treat your monthly budget like a health bar (HP) and log expenses as "Damage" to your wallet integrity.

# 🎮 Game Features
- Health Bar HUD: Real-time visualization of your remaining budget.
- Global Persistence: Data is stored in a Supabase (PostgreSQL) cloud database, accessible from any device.
- Overspending Alert: If HP hits zero, the app tracks "Critical Damage" (overspending) without showing negative balances.
- Daily Intelligence: Filter and view battle logs (expenses) by the specific day of the week.
- IST 12-Hour Clock: Accurate Indian Standard Time logging using pytz.

# 🛠️ Tech Stack
- Frontend: Streamlit
- Database & Auth: Supabase (PostgreSQL)
- Data Handling: Pandas
- Timezone Management: Pytz

# 🚀 Deployment & Setup
## 1. Prerequisites
- Python 3.8+
- A free Supabase account.

## 2. Database Configuration
`CREATE TABLE expenses (`  
  `id SERIAL PRIMARY KEY,`  
  `user_id UUID REFERENCES auth.users NOT NULL,`  
  `item TEXT,`  
  `amount FLOAT,`  
  `day_name TEXT,`  
  `timestamp TEXT`  
`);`  
Enable Privacy (RLS)  
`ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;`  
`CREATE POLICY "Users can only access their own expenses"`  
`ON expenses FOR ALL USING (auth.uid() = user_id);`

## 3. Local Installation
- Clone the repository:  
   git clone https://github.com/yourusername/pocket-survival.git  
   cd pocket-survival
- Install dependencies:
   pip install -r requirements.txt  
- Setup Secrets: Create a `.streamlit/secrets.toml` file and add your Supabase credentials:  
   SUPABASE_URL = "https://your-project.supabase.co"  
   SUPABASE_KEY = "your-anon-key"
- Run the app:
   streamlit run app.py
