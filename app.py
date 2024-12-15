from flask import Flask, render_template, request, redirect, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            balance REAL DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payer TEXT NOT NULL,
            amount REAL NOT NULL,
            shared_by TEXT NOT NULL
        )''')
        conn.commit()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-participant', methods=['GET', 'POST'])
def add_participant():
    if request.method == 'POST':
        name = request.form['name']
        with sqlite3.connect(DATABASE) as conn:
            try:
                conn.execute("INSERT INTO participants (name) VALUES (?)", (name,))
                conn.commit()
                return jsonify({"message": f"Participant {name} added successfully."})
            except sqlite3.IntegrityError:
                return jsonify({"error": f"Participant {name} already exists."}), 400
    return render_template('add_participant.html')
@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'GET':
        return render_template('add_expense.html')
    elif request.method == 'POST':
        payer = request.form['payer']
        amount = float(request.form['amount'])
        shared_by = request.form['shared_by'].split(',')

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM participants WHERE name = ?", (payer,))
            if not cursor.fetchone():
                return "Payer does not exist. Please add the participant first.", 400
            
            for person in shared_by:
                cursor.execute("SELECT name FROM participants WHERE name = ?", (person.strip(),))
                if not cursor.fetchone():
                    return f"Participant {person.strip()} does not exist.", 400

            amount_per_person = amount / len(shared_by)
            cursor.execute("UPDATE participants SET balance = balance + ? WHERE name = ?", (amount, payer))
            for person in shared_by:
                cursor.execute("UPDATE participants SET balance = balance - ? WHERE name = ?", (amount_per_person, person.strip()))
            cursor.execute("INSERT INTO expenses (payer, amount, shared_by) VALUES (?, ?, ?)",
                           (payer, amount, ','.join(shared_by)))
            conn.commit()

        return redirect('/')
@app.route('/view-balances')
def view_balances():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, balance FROM participants")
        balances = cursor.fetchall()
    return jsonify(balances)

@app.route('/settle-expenses')
def settle_expenses():
    # Logic for settling expenses
    return jsonify({"message": "Settlement completed."})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)