from decimal import Decimal
from os import name
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
    print(cursor.fetchone())
    
    cursor.execute("SELECT UID FROM users WHERE phone_number=%s", (phone,))
    UID1 = cursor.fetchone()[0]  # Извлекаем значение UID

    if user:
        cursor.execute("SELECT role FROM users WHERE phone_number=%s", (phone,))
        a_role = cursor.fetchone()
        print("tyt", a_role)
        if a_role[0] == "admin":
            return redirect(url_for('adashboard', UID=UID1))  # Передаем UID как параметр
        else:
            return redirect(url_for('udashboard', UID=UID1))
    else:
        return "Invalid credentials"

@app.route('/admin_dashboard/<int:UID>')
def adashboard(UID):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE UID=%s", (UID,))
    result = cursor.fetchone()
    
    name = result[2]
    surname = result[3]
    birthdate = result[5]
    bankday = result[11]
    print('Request from users: ', result, '\n')


    return render_template('admin_dashboard.html')

@app.route('/user_dashboard/<int:UID>')
def udashboard(UID):
    db.reconnect(attempts=3, delay=2)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE UID=%s", (UID,))
    result = cursor.fetchone()
    
    name = result[2]
    surname = result[3]
    birthdate = result[5]
    bankday = result[11]
    print('Request from users: ', result, '\n')

    cursor = db.cursor(dictionary=True)
    
    #debits
    cursor.execute("SELECT ba.accountID, balance FROM debits LEFT JOIN bank_accounts AS ba ON debits.accountID = ba.accountID WHERE ba.UID=%s", (UID,))
    result = cursor.fetchall()
    debit_accounts_data = result
    for account in debit_accounts_data:
        account['balance'] = float(account['balance'])  # или str(account['balance'])
    print(debit_accounts_data)

    #deposits
    cursor.execute("SELECT ba.accountID, close_date, percent, balance FROM deposits LEFT JOIN bank_accounts AS ba ON deposits.accountID = ba.accountID WHERE ba.UID=%s", (UID,))
    result = cursor.fetchall()
    deposit_accounts_data = result
    for account in deposit_accounts_data:
        account['balance'] = float(account['balance'])  # или str(account['balance'])
    print(deposit_accounts_data)
    
    #saving
    cursor.execute("SELECT ba.accountID, percent, `limit`, spent_limit, balance FROM saving_accounts AS sa LEFT JOIN bank_accounts AS ba ON sa.accountID = ba.accountID WHERE ba.UID=%s", (UID,))
    result = cursor.fetchall()
    saving_accounts_data = result
    for account in saving_accounts_data:
        account['spent_limit'] = float(account['spent_limit'])
        account['balance'] = float(account['balance'])  # или str(account['balance'])
        account['spent_limit'] = account['limit'] - account['spent_limit']
    print(saving_accounts_data)

    #credit card
    cursor.execute("SELECT ba.accountID, `limit`, debt, balance FROM credit_card AS cc LEFT JOIN bank_accounts AS ba ON cc.accountID = ba.accountID WHERE ba.UID=%s", (UID,))
    result = cursor.fetchall()
    cc_accounts_data = result
    for account in cc_accounts_data:
        account['debt'] = float(account['debt'])
        account['balance'] = float(account['balance'])  # или str(account['balance'])
    print(cc_accounts_data)
    
    #credit
    cursor.execute("SELECT ba.accountID, expire_date, debt FROM credit LEFT JOIN bank_accounts AS ba ON credit.creditID = ba.accountID WHERE ba.UID=%s", (UID,))
    result = cursor.fetchall()
    cc_accounts_data = result
    for account in cc_accounts_data:
        account['debt'] = float(account['debt'])
    print(cc_accounts_data)
    
    #operations
    cursor.execute("SELECT accountID, type, date, summ FROM operations AS op WHERE op.UID=%s ORDER BY date DESC", (UID,))
    result = cursor.fetchall()
    operations_data = result
    for account in operations_data:
        if account['type'] == 1:
            account['type'] = 'deposit'
        else:
            account['type'] = 'withdraw'
        account['summ'] = float(account['summ'])
    #print(operations_data)

    return render_template('user_dashboard.html', debit_accounts=debit_accounts_data, deposit_accounts = deposit_accounts_data, saving_accounts = saving_accounts_data, cc_accounts = cc_accounts_data, operations = operations_data)

@app.route('/execute_transaction', methods=['GET', 'POST'])
def execute_transaction():
    if request.method == 'POST':
        accountID = request.form['accountID']
        transaction_type = request.form['transaction_type']
        amount = request.form['amount']
        print(accountID)

        try:
            cursor = db.cursor()
            # Вызываем хранимую процедуру
            cursor.callproc('add_operation', [int(transaction_type), int(accountID),  Decimal(amount)])
            db.commit()
        except Exception as e:
            db.rollback()
            return f"Error: {str(e)}"
        
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        else:
            return redirect(url_for('/'))  # Если referrer отсутствует
    else:
        return render_template('transaction.html')
    
if __name__ == '__main__':
    app.run(port=5050, debug=False)
