
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Подключение к базе данных
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="bank",
    charset='utf8mb4'
)

@app.route('/')
def login():
    print("Accessing login page")  # Для проверки
    return render_template('login.html')



@app.route('/auth', methods=['POST'])
def auth():
    phone = request.form['phone']
    password = request.form['password']

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE phone_number=%s AND password=%s", (phone, password))
    user = cursor.fetchone()

    if user:
        return redirect(url_for('dashboard'))
    else:
        return "Invalid credentials"

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(port=5050, debug=False)
