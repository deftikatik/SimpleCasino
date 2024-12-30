from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def create_database():
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            balance INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, 1000))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def authenticate_user(username, password):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def get_balance(username):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_balance(username, amount):
    conn = sqlite3.connect('casino.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'username' in session:
        balance = get_balance(session['username'])
        return render_template('dashboard.html', username=session['username'], balance=balance)
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = authenticate_user(username, password)
    if user:
        session['username'] = username
        if username == 'deftikatik':
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    flash('Invalid username or password.')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if register_user(username, password):
            flash('Registration successful. You can now log in.')
            return redirect(url_for('index'))
        flash('Username already exists.')
    return render_template('register.html')

@app.route('/play', methods=['POST'])
def play_roulette():
    if 'username' not in session:
        return redirect(url_for('index'))

    bet_amount = int(request.form['bet_amount'])
    bet_number = int(request.form['bet_number'])
    balance = get_balance(session['username'])

    if bet_amount <= 0 or bet_amount > balance:
        flash('Invalid bet amount.')
        return redirect(url_for('index'))
    if bet_number < 0 or bet_number > 36:
        flash('Invalid number. Choose a number between 0 and 36.')
        return redirect(url_for('index'))

    winning_number = random.randint(0, 36)
    if bet_number == winning_number:
        winnings = bet_amount * 36
        balance += winnings
        flash(f'<div class="win-message">🎉 You won ${winnings}! The winning number was {winning_number}. 🎉</div>')
    else:
        balance -= bet_amount
        flash(f'<div class="lose-message">😞 You lost your bet. The winning number was {winning_number}. 😞</div>')

    update_balance(session['username'], balance)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'username' not in session or session['username'] != 'deftikatik':
        return redirect(url_for('index'))

    if request.method == 'POST':
        target_user = request.form['target_user']
        amount = int(request.form['amount'])
        if get_balance(target_user) is not None:
            new_balance = get_balance(target_user) + amount
            update_balance(target_user, new_balance)
            flash(f'Added {amount} to {target_user}. New balance: {new_balance}')
        else:
            flash('User not found.')

    return render_template('admin.html')

if __name__ == '__main__':
    create_database()
    app.run(debug=True)
