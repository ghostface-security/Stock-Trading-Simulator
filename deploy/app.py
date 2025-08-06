# Import necessary modules
import random
import time
import sqlite3
import os
import secrets
import hashlib
import requests
from flask import Flask, render_template, redirect, url_for, request, session, flash, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
import atexit
from functools import wraps
from datetime import datetime, timedelta
# import logging # Removed: No longer needed for custom logger setup

# --- PATCH 1 & 2: Add secure libraries ---
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect


# Create the Flask application instance
app = Flask(__name__)

# --- Removed: Custom logger configuration for debugging ---
# app.logger.setLevel(logging.INFO)
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# app.logger.addHandler(handler)

# --- Removed: Diagnostic logger message ---
# app.logger.info("--- APP.PY LOGGER CHECK: Flask application started and logger configured. ---")


# A secret key is required for sessions and flash messages
app.secret_key = 'c8f1e2d3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1' # NEW Chosen random secret key

# --- PATCH 4 & FIX: Secure Database File Location with Absolute Path ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/pi/Stock-Trading-Simulator/instance/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- PATCH 1 & 2: Initialize security extensions ---
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)


# --- Stock Market API Configuration ---
STOCK_SYMBOLS = ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'NFLX', 'SBUX', 'NKE', 'KO']
STOCK_NAMES = {
    'AAPL': 'Apple Inc.',
    'GOOG': 'Alphabet Inc.',
    'MSFT': 'Microsoft Corp.',
    'AMZN': 'Amazon.com Inc.',
    'TSLA': 'Tesla, Inc.',
    'NFLX': 'Netflix, Inc.',
    'SBUX': 'Starbucks Corp.',
    'NKE': 'NIKE, Inc.',
    'KO': 'The Coca-Cola Company'
}

# --- Fee Configuration ---
WITHDRAWAL_FEE_RATE = 0.005   # 0.5%
STOCK_BUY_FEE_RATE = 0.01   # 1%
STOCK_SELL_FEE_RATE = 0.01   # 1%
INITIAL_BALANCE = 0   # Initial balance for new users

# --- Database Models ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    transactions = db.relationship('Transaction', backref='user', lazy=True)
    portfolio = db.relationship('StockHolding', backref='user', lazy=True)
    password_reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy=True)
    wallet = db.relationship('UserWallet', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        try:
            if bcrypt.check_password_hash(self.password_hash, password):
                return True
        except ValueError:
            old_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if old_hash == self.password_hash:
                self.set_password(password)
                db.session.add(self)
                db.session.commit()
                # app.logger.info(f"User '{self.username}' password migrated to bcrypt.") # Removed debug log
                return True
        return False

class UserWallet(db.Model):
    __tablename__ = 'user_wallets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.00)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class StockHolding(db.Model):
    __tablename__ = 'stock_holdings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cost_basis = db.Column(db.Float, nullable=False)

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

class StockPrice(db.Model):
    __tablename__ = 'stock_prices'
    symbol = db.Column(db.String(10), primary_key=True)
    price = db.Column(db.Float, nullable=False)

stock_prices = {}
global_exchange_user_id = None

def fetch_and_update_stock_prices():
    global stock_prices
    with app.app_context():
        for symbol in STOCK_SYMBOLS:
            stock_record = StockPrice.query.filter_by(symbol=symbol).first()
            if stock_record:
                current_price = stock_record.price
                change_percent = random.uniform(-0.02, 0.02)
                new_price = current_price * (1 + change_percent)
                new_price = round(max(1.0, new_price), 2)
                stock_record.price = new_price
            else:
                new_price = round(random.uniform(50.0, 200.0), 2)
                new_stock_price = StockPrice(symbol=symbol, price=new_price)
                db.session.add(new_stock_price)
            stock_prices[symbol] = new_price
        db.session.commit()

def initialize_stock_prices():
    global stock_prices
    with app.app_context():
        prices_exist = StockPrice.query.first()
        if not prices_exist:
            for symbol in STOCK_SYMBOLS:
                new_price = round(random.uniform(50.0, 200.0), 2)
                new_stock_price = StockPrice(symbol=symbol, price=new_price)
                db.session.add(new_stock_price)
            db.session.commit()
        stock_records = StockPrice.query.all()
        stock_prices = {record.symbol: record.price for record in stock_records}
    # app.logger.info(f"Stock prices initialized from DB: {stock_prices}") # Removed debug log

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
        g.user_wallet = None
    else:
        g.user = User.query.get(user_id)
        if g.user:
            g.user_wallet = UserWallet.query.filter_by(user_id=g.user.id).first()
            if not g.user_wallet:
                g.user_wallet = UserWallet(user_id=g.user.id, balance=INITIAL_BALANCE)
                db.session.add(g.user_wallet)
                db.session.commit()
        else:
            session.clear()
            g.user = None
            g.user_wallet = None

def get_global_exchange_user():
    global global_exchange_user_id
    with app.app_context():
        if global_exchange_user_id:
            return User.query.get(global_exchange_user_id)
        
        global_exchange_user = User.query.filter_by(username='Global_Exchange').first()
        if not global_exchange_user:
            global_exchange_user = User(username='Global_Exchange', password_hash='NO_LOGIN')
            db.session.add(global_exchange_user)
            db.session.commit()
            
            exchange_wallet = UserWallet(user_id=global_exchange_user.id, balance=0.0)
            db.session.add(exchange_wallet)
            db.session.commit()

        global_exchange_user_id = global_exchange_user.id
        return global_exchange_user

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('banking_dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            new_wallet = UserWallet(user_id=new_user.id, balance=INITIAL_BALANCE)
            db.session.add(new_wallet)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('banking_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        
        # --- Removed debug log ---
        if user:
            # app.logger.info(f"DEBUG: User '{username}' found for password reset.")
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            PasswordResetToken.query.filter_by(user_id=user.id).delete()
            
            new_token = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
            db.session.add(new_token)
            db.session.commit()
            
            flash('A password reset link has been generated. Please check your console/logs for the link.', 'info')
            # app.logger.info(f"Password reset link for user '{user.username}': {url_for('reset_password', token=token, _external=True)}") # Removed debug log
        else:
            # app.logger.info(f"DEBUG: User '{username}' NOT found for password reset.") # Removed debug log
            flash('No account found with that username.', 'error')
            
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or reset_token.expires_at < datetime.utcnow():
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(reset_token.user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_password = request.form['new_password']
        user.set_password(new_password)
        
        db.session.delete(reset_token)
        db.session.commit()
        
        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/banking_dashboard')
@login_required
def banking_dashboard():
    user = g.user
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.timestamp.desc()).limit(10).all()
    return render_template('banking_dashboard.html', user=user, user_wallet=g.user_wallet, transactions=transactions)

@app.route('/deposit', methods=['POST'])
@login_required
def deposit():
    try:
        amount = float(request.form['amount'])
    except (ValueError, KeyError):
        flash('Invalid amount.', 'error')
        return redirect(url_for('banking_dashboard'))

    if amount <= 0:
        flash('Deposit amount must be positive.', 'error')
    else:
        g.user_wallet.balance += amount
        
        exchange_user = get_global_exchange_user()
        exchange_wallet = UserWallet.query.filter_by(user_id=exchange_user.id).first()
        exchange_wallet.balance += amount
        
        new_transaction = Transaction(
            user_id=g.user.id,
            transaction_type='Deposit',
            amount=amount
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash(f'Successfully deposited ${amount:.2f}.', 'success')

    return redirect(url_for('banking_dashboard'))

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    try:
        amount = float(request.form['amount'])
    except (ValueError, KeyError):
        flash('Invalid amount.', 'error')
        return redirect(url_for('banking_dashboard'))

    if amount <= 0:
        flash('Invalid withdrawal amount.', 'error')
        return redirect(url_for('banking_dashboard'))

    fee = round(amount * WITHDRAWAL_FEE_RATE, 2)
    total_debit = amount + fee
    
    if g.user_wallet.balance < total_debit:
        flash(f'Insufficient funds to cover withdrawal and fee (${fee:.2f}).', 'error')
    else:
        g.user_wallet.balance -= total_debit
        
        exchange_user = get_global_exchange_user()
        exchange_wallet = UserWallet.query.filter_by(user_id=exchange_user.id).first()
        exchange_wallet.balance -= amount
        
        user_transaction = Transaction(
            user_id=g.user.id,
            transaction_type='Withdrawal',
            amount=-amount
        )
        db.session.add(user_transaction)
        
        fee_transaction = Transaction(
            user_id=exchange_user.id,
            transaction_type='Fee Collected',
            amount=fee
        )
        db.session.add(fee_transaction)
        
        db.session.commit()
        flash(f'Successfully withdrew ${amount:.2f} (Fee: ${fee:.2f}).', 'success')

    return redirect(url_for('banking_dashboard'))

@app.route('/transfer', methods=['POST'])
@login_required
def transfer():
    try:
        amount = float(request.form['amount'])
        recipient_username = request.form['recipient']
    except (ValueError, KeyError):
        flash('Invalid amount or recipient.', 'error')
        return redirect(url_for('banking_dashboard'))

    recipient = User.query.filter_by(username=recipient_username).first()
    
    if not recipient:
        flash('Recipient not found.', 'error')
    elif amount <= 0 or g.user_wallet.balance < amount:
        flash('Invalid transfer amount or insufficient funds.', 'error')
    else:
        recipient_wallet = UserWallet.query.filter_by(user_id=recipient.id).first()
        if not recipient_wallet:
            flash('Recipient wallet not found. Please contact support.', 'error')
            return redirect(url_for('banking_dashboard'))
        
        g.user_wallet.balance -= amount
        recipient_wallet.balance += amount
        
        sender_transaction = Transaction(
            user_id=g.user.id,
            transaction_type=f'Transfer Out to {recipient_username}',
            amount=-amount
        )
        recipient_transaction = Transaction(
            user_id=recipient.id,
            transaction_type=f'Transfer In from {g.user.username}',
            amount=amount
        )
        db.session.add(sender_transaction)
        db.session.add(recipient_transaction)
        
        db.session.commit()
        flash(f'Successfully transferred ${amount:.2f} to {recipient_username}.', 'success')

    return redirect(url_for('banking_dashboard'))

@app.route('/stock_dashboard')
@login_required
def stock_dashboard():
    user = g.user
    portfolio = StockHolding.query.filter_by(user_id=user.id).all()
    return render_template('stock_dashboard.html', user=user, user_wallet=g.user_wallet, market_prices=stock_prices, portfolio=portfolio, stock_names=STOCK_NAMES)

@app.route('/buy_stock', methods=['POST'])
@login_required
def buy_stock():
    try:
        symbol = request.form['symbol']
        quantity = int(request.form['quantity'])
    except (ValueError, KeyError):
        flash('Invalid stock or quantity.', 'error')
        return redirect(url_for('stock_dashboard'))

    current_price = stock_prices.get(symbol)
    if not current_price or quantity <= 0:
        flash('Invalid stock or quantity.', 'error')
        return redirect(url_for('stock_dashboard'))

    total_cost = current_price * quantity
    fee = round(total_cost * STOCK_BUY_FEE_RATE, 2)
    total_debit = total_cost + fee

    if g.user_wallet.balance < total_debit:
        flash(f'Insufficient funds to buy {quantity} shares of {symbol} (Total cost: ${total_cost:.2f}, Fee: ${fee:.2f}).', 'error')
    else:
        g.user_wallet.balance -= total_debit

        exchange_user = get_global_exchange_user()
        exchange_wallet = UserWallet.query.filter_by(user_id=exchange_user.id).first()
        exchange_wallet.balance += fee
        exchange_wallet.balance -= total_cost
        
        holding = StockHolding.query.filter_by(user_id=g.user.id, symbol=symbol).first()
        if holding:
            new_quantity = holding.quantity + quantity
            new_cost_basis = ((holding.cost_basis * holding.quantity) + total_cost) / new_quantity
            holding.quantity = new_quantity
            holding.cost_basis = new_cost_basis
        else:
            new_holding = StockHolding(user_id=g.user.id, symbol=symbol, quantity=quantity, cost_basis=current_price)
            db.session.add(new_holding)
        
        new_transaction = Transaction(user_id=g.user.id, transaction_type=f'Buy {quantity} shares of {symbol}', amount=-total_cost)
        db.session.add(new_transaction)
        
        fee_transaction = Transaction(user_id=exchange_user.id, transaction_type=f'Fee collected from {g.user.username} for Buy {symbol}', amount=fee)
        db.session.add(fee_transaction)
        
        db.session.commit()
        flash(f'Successfully bought {quantity} shares of {symbol} for ${total_cost:.2f} (Fee: ${fee:.2f}).', 'success')
    
    return redirect(url_for('stock_dashboard'))

@app.route('/sell_stock', methods=['POST'])
@login_required
def sell_stock():
    try:
        symbol = request.form['symbol']
        quantity = int(request.form['quantity'])
    except (ValueError, KeyError):
        flash('Invalid stock or quantity.', 'error')
        return redirect(url_for('stock_dashboard'))

    current_price = stock_prices.get(symbol)
    if not current_price or quantity <= 0:
        flash('Invalid stock or quantity.', 'error')
        return redirect(url_for('stock_dashboard'))
    
    holding = StockHolding.query.filter_by(user_id=g.user.id, symbol=symbol).first()
    if not holding or holding.quantity < quantity:
        flash('Not enough shares to sell.', 'error')
        return redirect(url_for('stock_dashboard'))

    total_sale = current_price * quantity
    cost_of_sold_shares = holding.cost_basis * quantity
    
    profit_loss = total_sale - cost_of_sold_shares
    
    fee = 0
    if profit_loss > 0:
        fee = round(total_sale * STOCK_SELL_FEE_RATE, 2)
    
    net_profit = total_sale - fee

    g.user_wallet.balance += net_profit

    exchange_user = get_global_exchange_user()
    exchange_wallet = UserWallet.query.filter_by(user_id=exchange_user.id).first()
    exchange_wallet.balance -= total_sale
    if fee > 0:
        exchange_wallet.balance += fee

    holding.quantity -= quantity
    if holding.quantity == 0:
        db.session.delete(holding)
    
    new_transaction = Transaction(user_id=g.user.id, transaction_type=f'Sell {quantity} shares of {symbol}', amount=net_profit)
    db.session.add(new_transaction)
    
    if fee > 0:
        fee_transaction = Transaction(user_id=exchange_user.id, transaction_type=f'Fee collected from {g.user.username} for Sell {symbol}', amount=fee)
        db.session.add(fee_transaction)

    db.session.commit()
    
    if fee > 0:
        flash(f'Successfully sold {quantity} shares of {symbol} for a profit of ${profit_loss:.2f} (Fee: ${fee:.2f}, Net: ${net_profit:.2f}).', 'success')
    else:
        flash(f'Successfully sold {quantity} shares of {symbol} for a loss of ${abs(profit_loss):.2f}. No fee was charged.', 'success')
    
    return redirect(url_for('stock_dashboard'))

@app.route('/get_stock_prices')
def get_stock_prices():
    return jsonify(stock_prices)

@app.route('/confirm_delete')
@login_required
def confirm_delete():
    return render_template('confirm_delete.html')

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = g.user
    user_id = user.id
    
    StockHolding.query.filter_by(user_id=user_id).delete()
    Transaction.query.filter_by(user_id=user_id).delete()
    PasswordResetToken.query.filter_by(user_id=user_id).delete()
    UserWallet.query.filter_by(user_id=user_id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    session.pop('user_id', None)
    
    flash('Your account has been successfully deleted.', 'success')
    return redirect(url_for('login'))

# Removed: Temporary debug route to list all users
# @app.route('/debug_users')
# def debug_users():
#     users = User.query.all()
#     user_list = [user.username for user in users]
#     return render_template('debug_users.html', users=user_list)


# Run the app if this file is executed directly
if __name__ == '__main__':
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created.")
        
        print("Initializing stock prices...")
        initialize_stock_prices()
        print("Stock prices initialized.")
        
        print("Ensuring Global Exchange account exists...")
        get_global_exchange_user()
        print("Global Exchange account ready.")
        
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=fetch_and_update_stock_prices, trigger='interval', seconds=60)
    scheduler.start()

    atexit.register(lambda: scheduler.shutdown())

    print("Starting Flask application...")
    app.run(debug=False, port=5000, use_reloader=False)
