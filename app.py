from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# --- DATABASE CONFIG ---
# This creates a file named survival.db in your folder
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'survival.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    initial_pocket_money = db.Column(db.Float, default=5000.0)
    current_balance = db.Column(db.Float, default=5000.0)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Create the database
with app.app_context():
    db.create_all()
    # Initialize a user if none exists
    if not UserProfile.query.first():
        db.session.add(UserProfile())
        db.session.commit()

# --- ROUTES ---
@app.route('/')
def index():
    user = UserProfile.query.first()
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    # Logic for Survival
    days_in_month = 30
    day_of_month = datetime.now().day
    days_left = max(1, days_in_month - day_of_month)
    
    daily_limit = user.current_balance / days_left
    hp_percent = (user.current_balance / user.initial_pocket_money) * 100
    
    return render_template('index1.html', 
                           user=user, 
                           expenses=expenses, 
                           limit=round(daily_limit, 2), 
                           days_left=days_left,
                           hp_percent=hp_percent)

@app.route('/spend', methods=['POST'])
def spend():
    item = request.form.get('item')
    amount = float(request.form.get('amount'))
    
    user = UserProfile.query.first()
    if amount > 0:
        # Update Balance
        user.current_balance -= amount
        # Save Expense
        new_expense = Expense(item=item, amount=amount)
        db.session.add(new_expense)
        db.session.commit()
        
    return redirect(url_for('index'))

@app.route('/reset')
def reset():
    # Helper to restart the month
    user = UserProfile.query.first()
    user.current_balance = user.initial_pocket_money
    Expense.query.delete()
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
