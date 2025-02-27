// Получаем кнопки и таблицы
const expensesBtn = document.getElementById('expenses-btn');
const depositsBtn = document.getElementById('deposits-btn');
const expensesTable = document.getElementById('expenses-table');
const depositsTable = document.getElementById('deposits-table');

// Функция для переключения между таблицами
function showExpenses() {
    expensesTable.style.display = 'block';
    depositsTable.style.display = 'none';
}

function showDeposits() {
    expensesTable.style.display = 'none';
    depositsTable.style.display = 'block';
}

// Добавляем обработчики событий для кнопок
expensesBtn.addEventListener('click', showExpenses);
depositsBtn.addEventListener('click', showDeposits);

// Изначально показываем таблицу с тратами
showDeposits();
