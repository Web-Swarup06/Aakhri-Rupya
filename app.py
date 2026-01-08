import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- DATABASE & PATH CONFIGURATION ---
# This ensures the app works on PC and Cloud servers like Render
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'survival.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initial_pocket_money = db.Column(db.Float, default=5000.0)
    current_balance = db.Column(db.Float, default=5000.0)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Database and create default user
with app.app_context():
    db.create_all()
    if not UserProfile.query.first():
        db.session.add(UserProfile(initial_pocket_money=5000.0, current_balance=5000.0))
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def index():
    user = UserProfile.query.first()
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    # Logic for Survival Calculations
    days_in_month = 30
    day_of_month = datetime.now().day
    days_left = max(1, days_in_month - day_of_month)
    
    # How much they can spend per day to last until Day 30
    daily_limit = user.current_balance / days_left
    
    # HP Bar Calculation (Percentage)
    hp_percent = (user.current_balance / user.initial_pocket_money) * 100
    hp_percent = max(0, min(100, hp_percent)) # Keep between 0 and 100
    
    # Pointing to index1.html as requested
    return render_template('index1.html', 
                           user=user, 
                           expenses=expenses, 
                           limit=round(daily_limit, 2), 
                           days_left=days_left,
                           hp_percent=hp_percent)

@app.route('/spend', methods=['POST'])
def spend():
    item = request.form.get('item')
    try:
        amount = float(request.form.get('amount'))
    except (ValueError, TypeError):
        return redirect(url_for('index'))
    
    user = UserProfile.query.first()
    if amount > 0:
        user.current_balance -= amount
        
        new_expense = Expense(item=item, amount=amount)
        db.session.add(new_expense)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    user = UserProfile.query.first()
    user.current_balance = user.initial_pocket_money
    Expense.query.delete() 
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
