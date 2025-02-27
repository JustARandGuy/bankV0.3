// �������� ������ � �������
const expensesBtn = document.getElementById('expenses-btn');
const depositsBtn = document.getElementById('deposits-btn');
const expensesTable = document.getElementById('expenses-table');
const depositsTable = document.getElementById('deposits-table');

// ������� ��� ������������ ����� ���������
function showExpenses() {
    expensesTable.style.display = 'block';
    depositsTable.style.display = 'none';
}

function showDeposits() {
    expensesTable.style.display = 'none';
    depositsTable.style.display = 'block';
}

// ��������� ����������� ������� ��� ������
expensesBtn.addEventListener('click', showExpenses);
depositsBtn.addEventListener('click', showDeposits);

// ���������� ���������� ������� � �������
showDeposits();
