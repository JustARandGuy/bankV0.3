from decimal import Decimal
from os import name
from flask import Flask, render_template, request, redirect, url_for, g
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

#db = mysql.connector.connect(
#    host="localhost",
#    user="root",
#    password="",
#    database="bank",
#    charset='utf8mb4'
#)

def execute_query(query, params=None, dictionary=True):
    
    db = get_db()
    cursor = db.cursor(dictionary=dictionary)
    cursor.execute(query, params or ())
    return cursor.fetchall()

def get_user_info(uid):
    
    query = "SELECT * FROM users WHERE UID=%s"
    result = execute_query(query, (uid,))
    if result:
        return {
            "name": result[0]["name"],
            "surname": result[0]["surname"],
            "birthdate": result[0]["birth_date"],
            "bankdate": result[0]["bank_date"]
        }
    return {}

def get_account_data(query, uid):
    #�������� ������ ������.
    data = execute_query(query, (uid,))
    for account in data:
        for key, value in account.items():
            if isinstance(value, Decimal):  
                account[key] = float(value)
    return data

def get_db():
    
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='bank'
        )
    return g.db

@app.teardown_appcontext
def close_db(exception):
 
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def login():
    print("Accessing login page")  
    return render_template('login.html')


@app.route('/auth', methods=['POST'])
def auth():
    phone = request.form['phone']
    password = request.form['password']
    
    sql = """
    SELECT * FROM users
    WHERE phone_number = %s AND password = %s
    """
    
    try:
        result = execute_query(sql, (phone, password))
        
        if not result:
            return "User not found or invalid credentials", 401  # HTTP 401 Unauthorized
        
        user = result[0]
        UID = user['UID']
        
        a_role = user['role']
        if a_role == "admin":
            return redirect(url_for('adashboard', UID=UID))
        else:
            return redirect(url_for('udashboard', UID=UID))
    
    except Exception as e:
        print(f"Error during authentication: {e}")
        return "An error occurred during authentication. Please try again later.", 500  # HTTP 500 Internal Server Error


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        surname = request.form.get('surname')
        patronymic = request.form.get('patronymic')
        birth_date = request.form.get('birth_date')
        address = request.form.get('address')
        sex = int(request.form.get('sex'))
        email = request.form.get('email')
        bankd = str(request.form.get('bank_day'))
        password = request.form.get('password')

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.callproc('add_user', [phone, name, surname, patronymic, birth_date, address, sex, email, bankd, password])
            db.commit()
            return redirect(url_for('login'))  
        except mysql.connector.Error as err:
            error_message = str(err)
            return render_template('register.html', error=error_message)
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')

@app.route('/admin_dashboard/<int:UID>')
def adashboard(UID):
    db = get_db()

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE UID=%s", (UID,))
    result = cursor.fetchone()
    
    sql = """SELECT ba.accountID, ba.UID, type, balance
FROM bank_accounts AS ba
RIGHT JOIN debits ON ba.accountID = debits.accountID
WHERE ba.status = 1
UNION

SELECT ba.accountID, ba.UID, ba.type, balance
FROM bank_accounts AS ba
RIGHT JOIN deposits ON ba.accountID = deposits.accountID
WHERE ba.status = 1
UNION

SELECT ba.accountID, ba.UID, ba.type, balance
FROM bank_accounts AS ba
RIGHT JOIN saving_accounts AS sa ON ba.accountID = sa.accountID
WHERE ba.status = 1
UNION

SELECT ba.accountID, ba.UID, ba.type, debt
FROM bank_accounts AS ba
RIGHT JOIN credit_card AS cc ON ba.accountID = cc.accountID
WHERE ba.status = 1
UNION

(SELECT ba.accountID, ba.UID, ba.type, debt
FROM bank_accounts AS ba
RIGHT JOIN credit AS cr ON ba.accountID = cr.creditID
WHERE ba.status = 1)

ORDER BY accountID

"""
    accounts = execute_query(sql)
    
    sql = """SELECT UID, phone_number, name, surname, patronymic FROM users """

    users1 = execute_query(sql)
    
    for account in accounts:
        if account['type'] == 1:
            account['type'] = 'Debit'
        elif account['type'] == 3:
            account['type'] = 'Dposit'
        elif account['type'] == 4:
            account['type'] = 'Credit Card'
        elif account['type'] == 5:
            account['type'] = 'Saving Account'
        elif account['type'] == 2:
            account['type'] = 'Credit'
        else:
            account['type'] = 'unknown'

    user_info = get_user_info(UID)


    return render_template('admin_dashboard.html', accounts = accounts, users = users1)

@app.route('/add_account', methods=['POST'])
def add_account():
    db = get_db()
    cursor = db.cursor()
    account_type = request.form.get('account_type')  # Получение выбранного типа аккаунта
    
    
    if account_type == '1':
        user_id = int(request.form.get('user_id'))
        cursor.callproc('add_debit', [user_id, 1])

        print(user_id)
        
    elif account_type == '2':
        user_id = request.form.get('user_id')
        amount = request.form.get('deposit_amount')
        period = request.form.get('deposit_period')
        percent = request.form.get('deposit_percent')
        cursor.callproc('add_deposit', [user_id, amount, period, percent, 1])
    
    elif account_type == '3':
        user_id = request.form.get('user_id')
        percent = request.form.get('percent')
        cursor.callproc('add_saving_account', [user_id, percent, 1])
    
    elif account_type == '4':
        user_id = request.form.get('user_id')
        percent = request.form.get('percent')
        limit = request.form.get('limit')
        cursor.callproc('add_credit_card', [user_id, percent, limit])
    
    elif account_type == '5':
        user_id = request.form.get('user_id')
        amount = request.form.get('amount')
        period = request.form.get('period')
        percent = request.form.get('percent')
        cursor.callproc('add_credit', [user_id, amount, percent, period])
    
    else:
        return "Invalid option selected", 400
    
    db.commit()
    
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('/'))  # ���� referrer �����������

@app.route('/delete_account/<int:AID>', methods=['POST'])
def delete_account(AID):
    
    db = get_db()
    cursor = db.cursor()

    try:
        
        cursor.callproc('close_account', [AID])
        db.commit()
        message = "Account successfully deleted!"
        status = "success"
    except Error as e:
        if e.errno == 1644:  
            message = "Cannot delete debit account: Account is not empty or other restriction."
        else:
            message = f"An unexpected error occurred: {e.msg}"
        status = "error"
        db.rollback()

    db.commit()
    
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    else:
        return redirect(url_for('/'))  # ���� referrer �����������

@app.route('/user_dashboard/<int:UID>')
def udashboard(UID):
    db = get_db()

    user_info = get_user_info(UID)
    
    debit_accounts_query = """
        SELECT ba.accountID, balance
        FROM debits
        LEFT JOIN bank_accounts AS ba ON debits.accountID = ba.accountID
        WHERE ba.UID=%s
    """
    deposit_accounts_query = """
        SELECT ba.accountID, close_date, percent, balance
        FROM deposits
        LEFT JOIN bank_accounts AS ba ON deposits.accountID = ba.accountID
        WHERE ba.UID=%s
    """
    saving_accounts_query = """
        SELECT ba.accountID, percent, `limit`, spent_limit, balance
        FROM saving_accounts AS sa
        LEFT JOIN bank_accounts AS ba ON sa.accountID = ba.accountID
        WHERE ba.UID=%s
    """
    credit_card_query = """
        SELECT ba.accountID, `limit`, debt, balance
        FROM credit_card AS cc
        LEFT JOIN bank_accounts AS ba ON cc.accountID = ba.accountID
        WHERE ba.UID=%s
    """
    operations_query = """
        SELECT accountID, type, date, summ
        FROM operations AS op
        WHERE op.UID=%s
        ORDER BY date DESC
    """
    
    credit_query = """
        SELECT creditID, expire_date, debt
        FROM credit
        LEFT JOIN bank_accounts AS ba ON credit.creditID = ba.accountID
        WHERE ba.UID=%s
    """

    debit_accounts = get_account_data(debit_accounts_query, UID)
    deposit_accounts = get_account_data(deposit_accounts_query, UID)
    saving_accounts = get_account_data(saving_accounts_query, UID)
    credit_cards = get_account_data(credit_card_query, UID)
    credit_accounts = get_account_data(credit_query, UID)
    operations = get_account_data(operations_query, UID)
    
    for operation in operations:
        if operation['type'] == 1:
            operation['type'] = 'Deposit'
        else:
            operation['type'] = 'Withdraw'
            

    return render_template(
        'user_dashboard.html',
        user_info=user_info,
        debit_accounts=debit_accounts,
        deposit_accounts=deposit_accounts,
        saving_accounts=saving_accounts,
        cc_accounts = credit_cards,
        credit_accounts = credit_accounts,
        operations=operations
    )

@app.route('/execute_transaction', methods=['GET', 'POST'])
def execute_transaction():
    if request.method == 'POST':
        accountID = request.form['accountID']
        transaction_type = request.form['transaction_type']
        amount = request.form['amount']
        print(accountID)

        try:
            cursor = db.cursor()
            # �������� �������� ���������
            cursor.callproc('add_operation', [int(transaction_type), int(accountID),  Decimal(amount)])
            db.commit()
        except Exception as e:
            db.rollback()
            return f"Error: {str(e)}"
        
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        else:
            return redirect(url_for('/'))  # ���� referrer �����������
    else:
        return render_template('transaction.html')
    
@app.route('/user_dashboard/accounts/<int:AID>')
def accounts(AID):
    #���������� ���� �����������
    
    sql= """SELECT type FROM bank_accounts WHERE accountID = %s"""
    acc_type = execute_query(sql, (AID,))

    if acc_type == 1:
        return redirect(url_for('debit_account', AID=AID))
    elif acc_type == 2:
        return redirect(url_for('deposit_account', AID=AID))
    elif acc_type == 3:
        return redirect(url_for('saving_account', AID=AID))
    elif acc_type == 4:
        return redirect(url_for('cc_account', AID=AID))
    elif acc_type == 5:
        return redirect(url_for('credit_account', AID=AID))
    else:
        print("account type not found", AID, ' ', acc_type)
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        else:
            return redirect(url_for('/'))
        
    return 0

@app.route('/user_dashboard/accounts/debit/<int:AID>')
def debit_account(AID):
    
    sql = """SELECT * FROM debits WHERE accountID = %s LIMIT 1"""
    data = execute_query(sql, (AID,))
    
    
    balance = float(data[0]['balance'])
    sql = """SELECT summ, date FROM operations WHERE accountID = %s AND type = 1"""
    deposit_operations = execute_query(sql, (AID,))
    sql = """SELECT summ, date FROM operations WHERE accountID = %s AND type = 2"""
    withdraw_operations = execute_query(sql, (AID,))

    return render_template('debit.html', balance = balance, deposit_operations = deposit_operations, withdraw_operations = withdraw_operations)

@app.route('/user_dashboard/accounts/deposit/<int:AID>')
def deposit_account(AID):
    return 0

@app.route('/user_dashboard/accounts/saving/<int:AID>')
def saving_account(AID):
    return 0

@app.route('/user_dashboard/accounts/creditcard/<int:AID>')
def cc_account(AID):
    return 0

@app.route('/user_dashboard/accounts/credit/<int:AID>')
def credit_account(AID):
    return 0

@app.route('/user_dashboard/payments')
def payments(AID):
    return 0


if __name__ == '__main__':
    app.run(port=5050, debug=False)
