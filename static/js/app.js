// ------------- API-хелперы -------------
const API_BASE = '/api';

async function apiGet(url) {
    const res = await fetch(API_BASE + url);
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || `Ошибка ${res.status}`);
    }
    return res.json();
}

async function apiPost(url, data) {
    const res = await fetch(API_BASE + url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Ошибка сервера');
    }
    return res.json();
}

async function apiPut(url, data) {
    const res = await fetch(API_BASE + url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Ошибка сервера');
    }
    return res.json();
}

async function apiDelete(url) {
    const res = await fetch(API_BASE + url, { method: 'DELETE' });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Ошибка сервера');
    }
    return res.json();
}

// ------------- Авторизация -------------
let currentUser = null;
let isLoginMode = true;

const authScreen = document.getElementById('authScreen');
const mainApp = document.getElementById('mainApp');
const header = document.getElementById('header');
const authForm = document.getElementById('authForm');
const authTitle = document.getElementById('authTitle');
const authSubmitBtn = document.getElementById('authSubmitBtn');
const authSwitchText = document.getElementById('authSwitchText');
const btnSwitchAuth = document.getElementById('btnSwitchAuth');
const authError = document.getElementById('authError');
const btnLogout = document.getElementById('btnLogout');
const currentUsernameSpan = document.getElementById('currentUsername');

btnSwitchAuth.addEventListener('click', () => {
    isLoginMode = !isLoginMode;
    if (isLoginMode) {
        authTitle.textContent = 'Вход';
        authSubmitBtn.textContent = 'Войти';
        authSwitchText.textContent = 'Нет аккаунта?';
        btnSwitchAuth.textContent = 'Зарегистрироваться';
    } else {
        authTitle.textContent = 'Регистрация';
        authSubmitBtn.textContent = 'Зарегистрироваться';
        authSwitchText.textContent = 'Уже есть аккаунт?';
        btnSwitchAuth.textContent = 'Войти';
    }
    authError.textContent = '';
});

authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('authUsername').value.trim();
    const password = document.getElementById('authPassword').value.trim();
    const endpoint = isLoginMode ? '/login' : '/register';

    try {
        const data = await apiPost(endpoint, { username, password });
        currentUser = data.user;
        showMainApp();
    } catch (err) {
        authError.textContent = err.message;
    }
});

btnLogout.addEventListener('click', async () => {
    await apiPost('/logout', {});
    currentUser = null;
    showAuthScreen();
});

async function checkSession() {
    try {
        const res = await fetch(API_BASE + '/check-auth');
        const data = await res.json();
        if (data.authenticated) {
            currentUser = data.user;
            showMainApp();
        } else {
            showAuthScreen();
        }
    } catch {
        showAuthScreen();
    }
}

function showMainApp() {
    authScreen.style.display = 'none';
    mainApp.style.display = 'block';
    header.style.display = 'flex';
    currentUsernameSpan.textContent = currentUser.username;
    loadWorkouts(); // Загружаем тренировки
}

function showAuthScreen() {
    authScreen.style.display = 'flex';
    mainApp.style.display = 'none';
    header.style.display = 'none';
}

// ------------- Управление тренировками -------------
const workoutList = document.getElementById('workoutList');
const emptyState = document.getElementById('emptyState');
const btnAddDay = document.getElementById('btnAddDay');

// Модалка дня
const modalOverlay = document.getElementById('modalOverlay');
const modalTitle = document.getElementById('modalTitle');
const modalForm = document.getElementById('modalForm');
const modalDayId = document.getElementById('modalDayId');
const modalDate = document.getElementById('modalDate');
const modalName = document.getElementById('modalName');
const btnModalCancel = document.getElementById('btnModalCancel');

// Модалка упражнения
const exerciseModalOverlay = document.getElementById('exerciseModalOverlay');
const exerciseModalTitle = document.getElementById('exerciseModalTitle');
const exerciseModalForm = document.getElementById('exerciseModalForm');
const exerciseModalDayId = document.getElementById('exerciseModalDayId');
const exerciseModalExerciseId = document.getElementById('exerciseModalExerciseId');
const exerciseModalName = document.getElementById('exerciseModalName');
const setsContainer = document.getElementById('setsContainer');
const btnAddSet = document.getElementById('btnAddSet');
const btnExerciseModalCancel = document.getElementById('btnExerciseModalCancel');

const expandedDays = new Set();

// Форматирование
function formatDate(dateStr) {
    const parts = dateStr.split('-');
    return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr;
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatSets(sets) {
    if (!sets || sets.length === 0) return '';
    return sets.map(s => {
        let part = `${s.reps}`;
        if (s.weight !== null && s.weight !== undefined) part += ` (${s.weight} кг)`;
        if (s.rest_time !== null && s.rest_time !== undefined) {
            const mins = Math.floor(s.rest_time / 60);
            const secs = s.rest_time % 60;
            if (mins > 0) part += ` (${mins} мин ${secs} с)`;
            else part += ` (${secs} с)`;
        }
        return part;
    }).join(', ');
}

// Загрузка списка дней
async function loadWorkouts() {
    try {
        const days = await apiGet('/workouts');
        renderWorkouts(days);
    } catch (err) {
        console.error(err);
        workoutList.innerHTML = '<p style="color:red;text-align:center;">Ошибка загрузки тренировок</p>';
    }
}

function renderWorkouts(days) {
    workoutList.innerHTML = '';
    if (days.length === 0) {
        emptyState.style.display = 'block';
        return;
    }
    emptyState.style.display = 'none';
    days.forEach(day => {
        const card = createWorkoutCard(day);
        workoutList.appendChild(card);
    });
}

function createWorkoutCard(day) {
    const card = document.createElement('div');
    card.className = 'workout-card';
    card.dataset.dayId = day.id;
    if (expandedDays.has(day.id)) card.classList.add('workout-card--expanded');

    card.innerHTML = `
        <div class="workout-card__header">
            <div class="workout-card__info">
                <span class="workout-card__date">${formatDate(day.date)}</span>
                <span class="workout-card__name">${escapeHTML(day.name)}</span>
            </div>
            <div class="workout-card__actions">
                <button class="btn-icon btn-icon--edit" data-action="edit-day">✎</button>
                <button class="btn-icon btn-icon--danger" data-action="delete-day">✕</button>
                <span class="workout-card__expand-icon">▼</span>
            </div>
        </div>
        <div class="workout-card__body">
            <div class="exercises-list">
                ${(day.exercises || []).map(ex => `
                    <div class="exercise-item" data-exercise-id="${ex.id}">
                        <div class="exercise-item__info">
                            <span class="exercise-item__name">${escapeHTML(ex.name)}</span>
                            <span class="exercise-item__sets">${formatSets(ex.sets)}</span>
                        </div>
                        <div class="exercise-item__actions">
                            <button class="btn-icon btn-icon--edit" data-action="edit-exercise" data-exercise-id="${ex.id}">✎</button>
                            <button class="btn-icon btn-icon--danger" data-action="delete-exercise" data-exercise-id="${ex.id}">✕</button>
                        </div>
                    </div>
                `).join('')}
            </div>
            <button class="btn btn--save btn--add-exercise" data-action="add-exercise-btn">+ Добавить упражнение</button>
        </div>
    `;

    // Обработчики внутри карточки
    const headerEl = card.querySelector('.workout-card__header');
    headerEl.addEventListener('click', (e) => {
        if (e.target.closest('[data-action]')) return;
        card.classList.toggle('workout-card--expanded');
        if (card.classList.contains('workout-card--expanded')) {
            expandedDays.add(day.id);
        } else {
            expandedDays.delete(day.id);
        }
    });

    card.querySelector('[data-action="edit-day"]').addEventListener('click', (e) => {
        e.stopPropagation();
        openEditDayModal(day);
    });
    card.querySelector('[data-action="delete-day"]').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteWorkoutDay(day.id);
    });
    card.querySelector('[data-action="add-exercise-btn"]').addEventListener('click', () => {
        openExerciseModal(day.id, null);
    });

    // Кнопки упражнений
    card.querySelectorAll('.exercise-item').forEach(item => {
        const exId = item.dataset.exerciseId;
        item.querySelector('[data-action="edit-exercise"]').addEventListener('click', () => {
            const ex = day.exercises.find(e => e.id === exId);
            if (ex) openExerciseModal(day.id, ex);
        });
        item.querySelector('[data-action="delete-exercise"]').addEventListener('click', () => {
            deleteExercise(day.id, exId);
        });
    });

    return card;
}

// ------------- Модальное окно дня -------------
function openAddDayModal() {
    modalTitle.textContent = 'Новый тренировочный день';
    modalDayId.value = '';
    modalDate.value = '';
    modalName.value = '';
    modalOverlay.style.display = 'flex';
}

function openEditDayModal(day) {
    modalTitle.textContent = 'Редактировать день';
    modalDayId.value = day.id;
    modalDate.value = day.date;
    modalName.value = day.name;
    modalOverlay.style.display = 'flex';
}

function closeDayModal() { modalOverlay.style.display = 'none'; }

async function submitDayForm(e) {
    e.preventDefault();
    const id = modalDayId.value;
    const date = modalDate.value;
    const name = modalName.value.trim();
    if (!date || !name) return;

    try {
        if (id) {
            await apiPut(`/workouts/${id}`, { date, name });
        } else {
            await apiPost('/workouts', { date, name });
        }
        closeDayModal();
        await loadWorkouts();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    }
}

async function deleteWorkoutDay(dayId) {
    if (!confirm('Удалить этот тренировочный день и все его упражнения?')) return;
    try {
        await apiDelete(`/workouts/${dayId}`);
        expandedDays.delete(dayId);
        await loadWorkouts();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    }
}

// ------------- Модальное окно упражнения (с подходами) -------------
function createSetRow(setData = {}) {
    const row = document.createElement('div');
    row.className = 'set-row';
    row.innerHTML = `
        <input type="number" class="reps" placeholder="Повторы" min="1" value="${setData.reps||''}" required>
        <input type="number" class="weight" placeholder="Вес (кг)" step="0.5" value="${setData.weight||''}">
        <input type="number" class="rest" placeholder="Отдых (сек)" min="0" value="${setData.rest_time||''}">
        <button type="button" class="btn-remove-set">✕</button>
    `;
    row.querySelector('.btn-remove-set').addEventListener('click', () => row.remove());
    return row;
}

function openExerciseModal(dayId, exercise = null) {
    exerciseModalDayId.value = dayId;
    setsContainer.innerHTML = '';
    if (exercise) {
        exerciseModalTitle.textContent = 'Редактировать упражнение';
        exerciseModalExerciseId.value = exercise.id;
        exerciseModalName.value = exercise.name;
        exercise.sets.forEach(s => setsContainer.appendChild(createSetRow(s)));
    } else {
        exerciseModalTitle.textContent = 'Новое упражнение';
        exerciseModalExerciseId.value = '';
        exerciseModalName.value = '';
        setsContainer.appendChild(createSetRow());
    }
    exerciseModalOverlay.style.display = 'flex';
}

function closeExerciseModal() {
    exerciseModalOverlay.style.display = 'none';
}

btnAddSet.addEventListener('click', () => {
    setsContainer.appendChild(createSetRow());
});

async function submitExerciseForm(e) {
    e.preventDefault();
    const dayId = exerciseModalDayId.value;
    const exerciseId = exerciseModalExerciseId.value;
    const name = exerciseModalName.value.trim();
    const setRows = [...setsContainer.querySelectorAll('.set-row')];
    const sets = [];
    for (let row of setRows) {
        const reps = parseInt(row.querySelector('.reps').value);
        if (isNaN(reps) || reps < 1) {
            alert('Каждый подход должен содержать количество повторов (целое число ≥ 1)');
            return;
        }
        const weightVal = row.querySelector('.weight').value.trim();
        const weight = weightVal ? parseFloat(weightVal) : null;
        const restVal = row.querySelector('.rest').value.trim();
        const rest_time = restVal ? parseInt(restVal) : null;
        sets.push({ reps, weight, rest_time });
    }
    if (sets.length === 0) {
        alert('Добавьте хотя бы один подход');
        return;
    }

    try {
        if (exerciseId) {
            await apiPut(`/workouts/${dayId}/exercises/${exerciseId}`, { name, sets });
        } else {
            await apiPost(`/workouts/${dayId}/exercises`, { name, sets });
        }
        closeExerciseModal();
        await loadWorkouts();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    }
}

async function deleteExercise(dayId, exerciseId) {
    if (!confirm('Удалить упражнение?')) return;
    try {
        await apiDelete(`/workouts/${dayId}/exercises/${exerciseId}`);
        await loadWorkouts();
    } catch (err) {
        alert('Ошибка: ' + err.message);
    }
}

// ------------- Привязка глобальных событий -------------
btnAddDay.addEventListener('click', openAddDayModal);
btnModalCancel.addEventListener('click', closeDayModal);
modalForm.addEventListener('submit', submitDayForm);
modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeDayModal(); });
btnExerciseModalCancel.addEventListener('click', closeExerciseModal);
exerciseModalForm.addEventListener('submit', submitExerciseForm);
exerciseModalOverlay.addEventListener('click', (e) => { if (e.target === exerciseModalOverlay) closeExerciseModal(); });

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDayModal();
        closeExerciseModal();
    }
});

// ------------- Старт -------------
checkSession();