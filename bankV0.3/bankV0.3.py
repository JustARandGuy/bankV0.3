from decimal import Decimal
from os import name
from flask import Flask, render_template, request, redirect, url_for, g
import mysql.connector

app = Flask(__name__)

# ����������� � ���� ������
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="bank",
    charset='utf8mb4'
)

def execute_query(query, params=None, dictionary=True):
    #������� ��� ���������� SQL-������� � �������������� ����������� �����������
    db = get_db()
    cursor = db.cursor(dictionary=dictionary)
    cursor.execute(query, params or ())
    return cursor.fetchall()

def get_user_info(uid):
    #������� ��������� ���� � ������������
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
            if isinstance(value, Decimal):  # ���� ������������ ��� Decimal
                account[key] = float(value)
    return data

def get_db():
    #������������� ��� ���������� ������������ ����������� � ���� ������
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
    #��������� ����������� � ���� ������ ����� ��������� �������
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def login():
    print("Accessing login page")  # ��� ��������
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
    UID1 = cursor.fetchone()[0]  # ��������� �������� UID

    if user:
        cursor.execute("SELECT role FROM users WHERE phone_number=%s", (phone,))
        a_role = cursor.fetchone()
        print("tyt", a_role)
        if a_role[0] == "admin":
            return redirect(url_for('adashboard', UID=UID1))  # �������� UID ��� ��������
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
