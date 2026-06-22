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

// ------------- Toast-уведомления -------------
const toastContainer = document.getElementById('toastContainer');

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast--visible'));
    setTimeout(() => {
        toast.classList.remove('toast--visible');
        toast.addEventListener('transitionend', () => toast.remove());
    }, 3000);
}

// ------------- Модалка подтверждения -------------
const confirmModal = document.getElementById('confirmModal');
const confirmMessage = document.getElementById('confirmMessage');
const btnConfirmOk = document.getElementById('btnConfirmOk');
const btnConfirmCancel = document.getElementById('btnConfirmCancel');

function showConfirm(message) {
    return new Promise(resolve => {
        confirmMessage.textContent = message;
        confirmModal.style.display = 'flex';
        const cleanup = (result) => {
            confirmModal.style.display = 'none';
            btnConfirmOk.removeEventListener('click', onOk);
            btnConfirmCancel.removeEventListener('click', onCancel);
            resolve(result);
        };
        const onOk = () => cleanup(true);
        const onCancel = () => cleanup(false);
        btnConfirmOk.addEventListener('click', onOk);
        btnConfirmCancel.addEventListener('click', onCancel);
    });
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
    header.style.display = 'flex';
    tabNav.style.display = 'flex';
    currentUsernameSpan.textContent = currentUser.username;
    switchTab(activeTab);
    if (activeTab === 'workouts') loadWorkouts();
}

function showAuthScreen() {
    authScreen.style.display = 'flex';
    mainApp.style.display = 'none';
    nutritionApp.style.display = 'none';
    bmiApp.style.display = 'none';
    header.style.display = 'none';
    tabNav.style.display = 'none';
    nutritionLoaded = false;
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
const modalNotes = document.getElementById('modalNotes');
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
const exerciseModalDesc = document.getElementById('exerciseModalDesc');

const expandedDays = new Set();
let allWorkouts = [];
let personalRecords = {};  // { 'Жим лёжа': 100, ... }

// ------------- Форматирование -------------
function formatDate(dateStr) {
    const parts = dateStr.split('-');
    return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr;
}

function formatMonthYear(dateStr) {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleString('ru', { month: 'long', year: 'numeric' });
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatSets(sets, exerciseName) {
    if (!sets || sets.length === 0) return '';
    return sets.map(s => {
        let part = `${s.reps}`;
        const isPR = s.weight !== null && s.weight !== undefined &&
            personalRecords[exerciseName] !== undefined &&
            s.weight >= personalRecords[exerciseName];
        if (s.weight !== null && s.weight !== undefined) {
            part += ` (${s.weight} кг${isPR ? ' 🏆' : ''})`;
        }
        if (s.rest_time !== null && s.rest_time !== undefined) {
            const mins = Math.floor(s.rest_time / 60);
            const secs = s.rest_time % 60;
            part += mins > 0 ? ` (${mins} мин ${secs} с)` : ` (${secs} с)`;
        }
        return part;
    }).join(', ');
}

function buildPersonalRecords(workouts) {
    const records = {};
    workouts.forEach(day => {
        (day.exercises || []).forEach(ex => {
            (ex.sets || []).forEach(s => {
                if (s.weight !== null && s.weight !== undefined) {
                    if (records[ex.name] === undefined || s.weight > records[ex.name]) {
                        records[ex.name] = s.weight;
                    }
                }
            });
        });
    });
    return records;
}

// ------------- Фильтры -------------
const filterSearch = document.getElementById('filterSearch');
const filterDateFrom = document.getElementById('filterDateFrom');
const filterDateTo = document.getElementById('filterDateTo');
const btnFilterReset = document.getElementById('btnFilterReset');

function applyFilters() {
    const query = filterSearch.value.trim().toLowerCase();
    const from = filterDateFrom.value;
    const to = filterDateTo.value;
    const filtered = allWorkouts.filter(day => {
        if (query && !day.name.toLowerCase().includes(query)) return false;
        if (from && day.date < from) return false;
        if (to && day.date > to) return false;
        return true;
    });
    renderWorkouts(filtered);
}

filterSearch.addEventListener('input', applyFilters);
filterDateFrom.addEventListener('change', applyFilters);
filterDateTo.addEventListener('change', applyFilters);
btnFilterReset.addEventListener('click', () => {
    filterSearch.value = '';
    filterDateFrom.value = '';
    filterDateTo.value = '';
    renderWorkouts(allWorkouts);
});

// ------------- Загрузка тренировок -------------
async function loadWorkouts() {
    try {
        allWorkouts = await apiGet('/workouts');
        personalRecords = buildPersonalRecords(allWorkouts);
        applyFilters();
    } catch (err) {
        console.error(err);
        workoutList.innerHTML = '<p style="color:red;text-align:center;">Ошибка загрузки тренировок</p>';
    }
}

// ------------- Группировка по месяцам -------------
function renderWorkouts(days) {
    workoutList.innerHTML = '';
    if (days.length === 0) {
        emptyState.style.display = 'block';
        return;
    }
    emptyState.style.display = 'none';

    const groups = {};
    days.forEach(day => {
        const key = day.date.slice(0, 7); // YYYY-MM
        if (!groups[key]) groups[key] = [];
        groups[key].push(day);
    });

    Object.keys(groups).sort((a, b) => b.localeCompare(a)).forEach(key => {
        const monthDays = groups[key];
        const header = document.createElement('div');
        header.className = 'month-group';
        const totalSets = monthDays.reduce((acc, d) =>
            acc + d.exercises.reduce((a, e) => a + e.sets.length, 0), 0);
        header.innerHTML = `
            <span class="month-group__label">${formatMonthYear(key + '-01')}</span>
            <span class="month-group__meta">${monthDays.length} тр. · ${totalSets} подходов</span>
        `;
        workoutList.appendChild(header);
        monthDays.forEach(day => workoutList.appendChild(createWorkoutCard(day)));
    });
}

// ------------- Карточка тренировки -------------
function createWorkoutCard(day) {
    const card = document.createElement('div');
    card.className = 'workout-card';
    card.dataset.dayId = day.id;
    if (expandedDays.has(day.id)) card.classList.add('workout-card--expanded');

    const exerciseCount = (day.exercises || []).length;
    const setCount = (day.exercises || []).reduce((a, e) => a + e.sets.length, 0);
    const summary = exerciseCount > 0 ? `${exerciseCount} упр. · ${setCount} подх.` : 'Нет упражнений';

    card.innerHTML = `
        <div class="workout-card__header">
            <div class="workout-card__info">
                <span class="workout-card__date">${formatDate(day.date)}</span>
                <div class="workout-card__title-block">
                    <span class="workout-card__name">${escapeHTML(day.name)}</span>
                    <span class="workout-card__summary">${summary}</span>
                    ${day.notes ? `<span class="workout-card__notes">${escapeHTML(day.notes)}</span>` : ''}
                </div>
            </div>
            <div class="workout-card__actions">
                <button class="btn-icon btn-icon--copy" data-action="copy-day" title="Скопировать на сегодня">⧉</button>
                <button class="btn-icon btn-icon--edit" data-action="edit-day" title="Редактировать">✎</button>
                <button class="btn-icon btn-icon--danger" data-action="delete-day" title="Удалить">✕</button>
                <span class="workout-card__expand-icon">▼</span>
            </div>
        </div>
        <div class="workout-card__body">
            <div class="exercises-list">
                ${(day.exercises || []).map(ex => `
                    <div class="exercise-item" data-exercise-id="${ex.id}">
                        <div class="exercise-item__order">
                            <button class="btn-icon btn-icon--order" data-action="move-up" data-exercise-id="${ex.id}" title="Вверх">▲</button>
                            <button class="btn-icon btn-icon--order" data-action="move-down" data-exercise-id="${ex.id}" title="Вниз">▼</button>
                        </div>
                        <div class="exercise-item__info">
                            <span class="exercise-item__name">${escapeHTML(ex.name)}</span>
                            ${ex.description ? `<span class="exercise-item__desc">${escapeHTML(ex.description)}</span>` : ''}
                            <span class="exercise-item__sets">${formatSets(ex.sets, ex.name)}</span>
                        </div>
                        <div class="exercise-item__actions">
                            <button class="btn-icon btn-icon--edit" data-action="edit-exercise" data-exercise-id="${ex.id}" title="Редактировать">✎</button>
                            <button class="btn-icon btn-icon--danger" data-action="delete-exercise" data-exercise-id="${ex.id}" title="Удалить">✕</button>
                        </div>
                    </div>
                `).join('')}
            </div>
            <button class="btn btn--save btn--add-exercise" data-action="add-exercise-btn">+ Добавить упражнение</button>
        </div>
    `;

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

    card.querySelector('[data-action="copy-day"]').addEventListener('click', (e) => {
        e.stopPropagation();
        copyWorkoutDay(day.id);
    });
    card.querySelector('[data-action="edit-day"]').addEventListener('click', (e) => {
        e.stopPropagation();
        openEditDayModal(day);
    });
    card.querySelector('[data-action="delete-day"]').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteWorkoutDay(day.id, day.name);
    });
    card.querySelector('[data-action="add-exercise-btn"]').addEventListener('click', () => {
        openExerciseModal(day.id, null);
    });

    card.querySelectorAll('.exercise-item').forEach(item => {
        const exId = item.dataset.exerciseId;
        item.querySelector('[data-action="edit-exercise"]').addEventListener('click', () => {
            const ex = day.exercises.find(e => e.id === exId);
            if (ex) openExerciseModal(day.id, ex);
        });
        item.querySelector('[data-action="delete-exercise"]').addEventListener('click', () => {
            deleteExercise(day.id, exId);
        });
        item.querySelector('[data-action="move-up"]').addEventListener('click', () => {
            moveExercise(day, exId, -1);
        });
        item.querySelector('[data-action="move-down"]').addEventListener('click', () => {
            moveExercise(day, exId, 1);
        });
    });

    return card;
}

async function copyWorkoutDay(dayId) {
    try {
        await apiPost(`/workouts/${dayId}/copy`, {});
        await loadWorkouts();
        showToast('Тренировка скопирована на сегодня');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

// ------------- Модальное окно дня -------------
function openAddDayModal() {
    modalTitle.textContent = 'Новый тренировочный день';
    modalDayId.value = '';
    modalDate.value = new Date().toISOString().split('T')[0];
    modalName.value = '';
    modalNotes.value = '';
    modalOverlay.style.display = 'flex';
}

function openEditDayModal(day) {
    modalTitle.textContent = 'Редактировать день';
    modalDayId.value = day.id;
    modalDate.value = day.date;
    modalName.value = day.name;
    modalNotes.value = day.notes || '';
    modalOverlay.style.display = 'flex';
}

function closeDayModal() { modalOverlay.style.display = 'none'; }

async function submitDayForm(e) {
    e.preventDefault();
    const id = modalDayId.value;
    const date = modalDate.value;
    const name = modalName.value.trim();
    const notes = modalNotes.value.trim();
    if (!date || !name) return;
    try {
        if (id) {
            await apiPut(`/workouts/${id}`, { date, name, notes });
        } else {
            await apiPost('/workouts', { date, name, notes });
        }
        closeDayModal();
        await loadWorkouts();
        showToast(id ? 'День обновлён' : 'Тренировка добавлена');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function deleteWorkoutDay(dayId, dayName) {
    const ok = await showConfirm(`Удалить тренировку «${dayName}» и все её упражнения?`);
    if (!ok) return;
    try {
        await apiDelete(`/workouts/${dayId}`);
        expandedDays.delete(dayId);
        await loadWorkouts();
        showToast('Тренировка удалена');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

// ------------- Модальное окно упражнения -------------
function createSetRow(setData = {}) {
    const row = document.createElement('div');
    row.className = 'set-row';
    row.innerHTML = `
        <input type="number" class="reps" placeholder="Повторы" min="1" value="${setData.reps || ''}" required>
        <input type="number" class="weight" placeholder="Вес (кг)" step="0.5" value="${setData.weight || ''}">
        <input type="number" class="rest" placeholder="Отдых (сек)" min="0" value="${setData.rest_time || ''}">
        <button type="button" class="btn-remove-set" title="Удалить подход">✕</button>
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
        exerciseModalDesc.value = exercise.description || '';
        exercise.sets.forEach(s => setsContainer.appendChild(createSetRow(s)));
    } else {
        exerciseModalTitle.textContent = 'Новое упражнение';
        exerciseModalExerciseId.value = '';
        exerciseModalName.value = '';
        exerciseModalDesc.value = '';
        setsContainer.appendChild(createSetRow());
    }
    exerciseModalOverlay.style.display = 'flex';
}

function closeExerciseModal() { exerciseModalOverlay.style.display = 'none'; }

btnAddSet.addEventListener('click', () => setsContainer.appendChild(createSetRow()));

async function submitExerciseForm(e) {
    e.preventDefault();
    const dayId = exerciseModalDayId.value;
    const exerciseId = exerciseModalExerciseId.value;
    const name = exerciseModalName.value.trim();
    const description = exerciseModalDesc.value.trim();
    const setRows = [...setsContainer.querySelectorAll('.set-row')];
    const sets = [];
    for (let row of setRows) {
        const reps = parseInt(row.querySelector('.reps').value);
        if (isNaN(reps) || reps < 1) {
            showToast('Каждый подход должен содержать количество повторов (≥ 1)', 'error');
            return;
        }
        const weightVal = row.querySelector('.weight').value.trim();
        const weight = weightVal ? parseFloat(weightVal) : null;
        const restVal = row.querySelector('.rest').value.trim();
        const rest_time = restVal ? parseInt(restVal) : null;
        sets.push({ reps, weight, rest_time });
    }
    if (sets.length === 0) {
        showToast('Добавьте хотя бы один подход', 'error');
        return;
    }
    try {
        if (exerciseId) {
            await apiPut(`/workouts/${dayId}/exercises/${exerciseId}`, { name, description: description || null, sets });
        } else {
            await apiPost(`/workouts/${dayId}/exercises`, { name, description: description || null, sets });
        }
        closeExerciseModal();
        await loadWorkouts();
        showToast(exerciseId ? 'Упражнение обновлено' : 'Упражнение добавлено');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function deleteExercise(dayId, exerciseId) {
    const ok = await showConfirm('Удалить упражнение?');
    if (!ok) return;
    try {
        await apiDelete(`/workouts/${dayId}/exercises/${exerciseId}`);
        await loadWorkouts();
        showToast('Упражнение удалено');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
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
        confirmModal.style.display = 'none';
        document.getElementById('profileModalOverlay').style.display = 'none';
        document.getElementById('foodModalOverlay').style.display = 'none';
        document.getElementById('mealTypeModalOverlay').style.display = 'none';
    }
});

// ------------- Перемещение упражнений -------------
async function moveExercise(day, exerciseId, direction) {
    const exercises = day.exercises;
    const idx = exercises.findIndex(e => e.id === exerciseId);
    const newIdx = idx + direction;
    if (newIdx < 0 || newIdx >= exercises.length) return;
    [exercises[idx], exercises[newIdx]] = [exercises[newIdx], exercises[idx]];
    try {
        await apiPut(`/workouts/${day.id}/exercises/reorder`, { exercise_ids: exercises.map(e => e.id) });
        await loadWorkouts();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

// ------------- Шаблоны -------------
const templatesModalOverlay = document.getElementById('templatesModalOverlay');
const templatesList = document.getElementById('templatesList');
const templateSourceSelect = document.getElementById('templateSourceSelect');
const templateNameInput = document.getElementById('templateNameInput');
const btnSaveTemplate = document.getElementById('btnSaveTemplate');
const btnTemplates = document.getElementById('btnTemplates');
const btnTemplatesClose = document.getElementById('btnTemplatesClose');

btnTemplates.addEventListener('click', openTemplatesModal);
btnTemplatesClose.addEventListener('click', () => { templatesModalOverlay.style.display = 'none'; });
templatesModalOverlay.addEventListener('click', (e) => { if (e.target === templatesModalOverlay) templatesModalOverlay.style.display = 'none'; });

async function openTemplatesModal() {
    templatesModalOverlay.style.display = 'flex';
    templateSourceSelect.innerHTML = '<option value="">— выберите день —</option>';
    allWorkouts.forEach(day => {
        const opt = document.createElement('option');
        opt.value = day.id;
        opt.textContent = `${formatDate(day.date)} — ${day.name}`;
        templateSourceSelect.appendChild(opt);
    });
    await loadTemplatesList();
}

async function loadTemplatesList() {
    try {
        const templates = await apiGet('/templates');
        if (templates.length === 0) {
            templatesList.innerHTML = '<p style="color:#888;text-align:center;">Нет сохранённых шаблонов.</p>';
            return;
        }
        templatesList.innerHTML = '';
        templates.forEach(tmpl => {
            const item = document.createElement('div');
            item.className = 'template-item';
            item.innerHTML = `
                <div class="template-item__info">
                    <span class="template-item__name">${escapeHTML(tmpl.name)}</span>
                    <span class="template-item__meta">${tmpl.exercises.length} упр.</span>
                </div>
                <div class="template-item__actions">
                    <button class="btn btn--save btn--sm" data-tmpl-use="${tmpl.id}">Создать тренировку</button>
                    <button class="btn-icon btn-icon--danger" data-tmpl-del="${tmpl.id}">✕</button>
                </div>
            `;
            item.querySelector(`[data-tmpl-use="${tmpl.id}"]`).addEventListener('click', () => useTemplate(tmpl.id, tmpl.name));
            item.querySelector(`[data-tmpl-del="${tmpl.id}"]`).addEventListener('click', () => deleteTemplate(tmpl.id, tmpl.name));
            templatesList.appendChild(item);
        });
    } catch (err) {
        templatesList.innerHTML = `<p style="color:red;">Ошибка: ${err.message}</p>`;
    }
}

btnSaveTemplate.addEventListener('click', async () => {
    const dayId = templateSourceSelect.value;
    const name = templateNameInput.value.trim();
    if (!dayId) { showToast('Выберите тренировочный день', 'error'); return; }
    if (!name) { showToast('Введите название шаблона', 'error'); return; }
    const day = allWorkouts.find(d => d.id === dayId);
    if (!day) return;
    try {
        await apiPost('/templates', { name, exercises: day.exercises });
        templateNameInput.value = '';
        await loadTemplatesList();
        showToast('Шаблон сохранён');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
});

async function useTemplate(templateId, templateName) {
    const today = new Date().toISOString().split('T')[0];
    try {
        await apiPost(`/templates/${templateId}/use`, { date: today });
        await loadWorkouts();
        templatesModalOverlay.style.display = 'none';
        showToast(`Тренировка «${templateName}» создана`);
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

async function deleteTemplate(templateId, templateName) {
    const ok = await showConfirm(`Удалить шаблон «${templateName}»?`);
    if (!ok) return;
    try {
        await apiDelete(`/templates/${templateId}`);
        await loadTemplatesList();
        showToast('Шаблон удалён');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}

// ------------- Статистика -------------
const statsModalOverlay = document.getElementById('statsModalOverlay');
const statsExerciseSelect = document.getElementById('statsExerciseSelect');
const statsEmpty = document.getElementById('statsEmpty');
const btnStatsClose = document.getElementById('btnStatsClose');
const btnStats = document.getElementById('btnStats');
let statsChart = null;

btnStats.addEventListener('click', openStatsModal);
btnStatsClose.addEventListener('click', () => { statsModalOverlay.style.display = 'none'; });
statsModalOverlay.addEventListener('click', (e) => { if (e.target === statsModalOverlay) statsModalOverlay.style.display = 'none'; });

statsExerciseSelect.addEventListener('change', renderStatsChart);
document.querySelectorAll('input[name="statsMetric"]').forEach(r => r.addEventListener('change', renderStatsChart));

async function openStatsModal() {
    statsModalOverlay.style.display = 'flex';
    try {
        const names = await apiGet('/stats/exercises');
        statsExerciseSelect.innerHTML = '<option value="">— выберите упражнение —</option>';
        names.forEach(name => {
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name + (personalRecords[name] !== undefined ? ` (рекорд: ${personalRecords[name]} кг)` : '');
            statsExerciseSelect.appendChild(opt);
        });
        statsEmpty.style.display = names.length === 0 ? 'block' : 'none';
        if (statsChart) { statsChart.destroy(); statsChart = null; }
    } catch (err) {
        showToast('Ошибка загрузки упражнений: ' + err.message, 'error');
    }
}

async function renderStatsChart() {
    const name = statsExerciseSelect.value;
    const metric = document.querySelector('input[name="statsMetric"]:checked').value;
    const metricLabels = { max_weight: 'Макс. вес (кг)', total_volume: 'Объём (кг×повт)', total_reps: 'Повторения' };
    if (!name) return;
    try {
        const data = await apiGet(`/stats/progress?exercise=${encodeURIComponent(name)}`);
        if (statsChart) { statsChart.destroy(); statsChart = null; }
        if (data.length === 0) { statsEmpty.style.display = 'block'; return; }
        statsEmpty.style.display = 'none';
        const labels = data.map(d => formatDate(d.date));
        const values = data.map(d => d[metric] ?? 0);
        const ctx = document.getElementById('statsChart').getContext('2d');
        statsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: metricLabels[metric],
                    data: values,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76,175,80,0.1)',
                    tension: 0.3,
                    pointRadius: 5,
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: false } },
            }
        });
    } catch (err) {
        showToast('Ошибка загрузки статистики: ' + err.message, 'error');
    }
}

// ------------- Экспорт CSV -------------
document.getElementById('btnExport').addEventListener('click', () => {
    window.location.href = API_BASE + '/export';
});

// ------------- Tab-навигация -------------
const tabNav = document.getElementById('tabNav');
const nutritionApp = document.getElementById('nutritionApp');
let activeTab = 'workouts';
let nutritionLoaded = false;

tabNav.querySelectorAll('.tab-nav__btn').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

const bmiApp = document.getElementById('bmiApp');

function switchTab(tab) {
    activeTab = tab;
    tabNav.querySelectorAll('.tab-nav__btn').forEach(b => {
        b.classList.toggle('tab-nav__btn--active', b.dataset.tab === tab);
    });
    mainApp.style.display = tab === 'workouts' ? 'block' : 'none';
    nutritionApp.style.display = tab === 'nutrition' ? 'block' : 'none';
    bmiApp.style.display = tab === 'bmi' ? 'block' : 'none';
    if (tab === 'nutrition' && !nutritionLoaded) {
        nutritionLoaded = true;
        loadNutritionData();
    }
    if (tab === 'bmi' && nutritionProfile) {
        document.getElementById('bmiWeight').value = nutritionProfile.weight;
        document.getElementById('bmiHeight').value = nutritionProfile.height;
    }
}

// ------------- Питание: профиль и калькулятор -------------
let nutritionProfile = null;
let currentNutritionDay = null;
let nutritionTargets = null;
let selectedNutritionDate = new Date().toISOString().split('T')[0];

const nutritionSetup = document.getElementById('nutritionSetup');
const nutritionDashboard = document.getElementById('nutritionDashboard');
const nutritionTargetsEl = document.getElementById('nutritionTargets');
const mealsSection = document.getElementById('mealsSection');
const mealsEmpty = document.getElementById('mealsEmpty');
const profileModalOverlay = document.getElementById('profileModalOverlay');
const profileForm = document.getElementById('profileForm');

document.getElementById('btnSetupProfile').addEventListener('click', () => openProfileModal());

document.getElementById('btnDatePrev').addEventListener('click', () => {
    const d = new Date(selectedNutritionDate);
    d.setDate(d.getDate() - 1);
    selectedNutritionDate = d.toISOString().split('T')[0];
    loadNutritionData();
});
document.getElementById('btnDateNext').addEventListener('click', () => {
    const d = new Date(selectedNutritionDate);
    d.setDate(d.getDate() + 1);
    selectedNutritionDate = d.toISOString().split('T')[0];
    loadNutritionData();
});
document.getElementById('btnDateToday').addEventListener('click', () => {
    selectedNutritionDate = new Date().toISOString().split('T')[0];
    loadNutritionData();
});
document.getElementById('btnProfileCancel').addEventListener('click', () => { profileModalOverlay.style.display = 'none'; });
profileModalOverlay.addEventListener('click', (e) => { if (e.target === profileModalOverlay) profileModalOverlay.style.display = 'none'; });

function openProfileModal() {
    if (nutritionProfile) {
        document.querySelector(`input[name="profileSex"][value="${nutritionProfile.sex}"]`).checked = true;
        document.getElementById('profileWeight').value = nutritionProfile.weight;
        document.getElementById('profileHeight').value = nutritionProfile.height;
        document.getElementById('profileAge').value = nutritionProfile.age;
        document.getElementById('profileActivity').value = nutritionProfile.activity_level;
        document.querySelector(`input[name="profileGoal"][value="${nutritionProfile.goal}"]`).checked = true;
    }
    profileModalOverlay.style.display = 'flex';
}

profileForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        sex: document.querySelector('input[name="profileSex"]:checked').value,
        weight: parseFloat(document.getElementById('profileWeight').value),
        height: parseFloat(document.getElementById('profileHeight').value),
        age: parseInt(document.getElementById('profileAge').value),
        activity_level: parseFloat(document.getElementById('profileActivity').value),
        goal: document.querySelector('input[name="profileGoal"]:checked').value,
    };
    try {
        const res = await apiPost('/nutrition/profile', data);
        nutritionProfile = res.profile;
        profileModalOverlay.style.display = 'none';
        showToast('Параметры сохранены');
        await loadNutritionData();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
});

// ------------- Питание: загрузка данных и дашборд -------------
const MEAL_LABELS = { breakfast: 'Завтрак', lunch: 'Обед', dinner: 'Ужин', snack: 'Перекус' };

async function loadNutritionData() {
    try {
        const profileRes = await apiGet('/nutrition/profile');
        nutritionProfile = profileRes.profile;

        if (!nutritionProfile) {
            nutritionSetup.style.display = 'block';
            nutritionDashboard.style.display = 'none';
            return;
        }

        nutritionSetup.style.display = 'none';
        nutritionDashboard.style.display = 'block';

        const todayRes = await apiGet(`/nutrition/today?date=${selectedNutritionDate}`);
        currentNutritionDay = todayRes.day;
        nutritionTargets = todayRes.targets;

        const dateLabel = document.getElementById('currentDateLabel');
        const isToday = selectedNutritionDate === new Date().toISOString().split('T')[0];
        dateLabel.textContent = isToday ? 'Сегодня' : formatDate(selectedNutritionDate);

        renderNutritionDashboard();
    } catch (err) {
        console.error(err);
        showToast('Ошибка загрузки питания', 'error');
    }
}

function renderNutritionDashboard() {
    if (!currentNutritionDay || !nutritionTargets) return;

    const d = currentNutritionDay;
    const t = nutritionTargets;
    const calPct = Math.min(100, Math.round(d.total_calories / t.goal_calories * 100));
    const proPct = Math.min(100, Math.round(d.total_protein / t.protein_grams * 100));
    const fatPct = Math.min(100, Math.round(d.total_fat / t.fat_grams * 100));
    const carbPct = Math.min(100, Math.round(d.total_carbs / t.carb_grams * 100));
    const calRemain = Math.round(t.goal_calories - d.total_calories);
    const calOver = d.total_calories > t.goal_calories;
    const proOver = d.total_protein > t.protein_grams;
    const fatOver = d.total_fat > t.fat_grams;
    const carbOver = d.total_carbs > t.carb_grams;

    nutritionTargetsEl.innerHTML = `
        <div class="nutrition-targets__header">
            <span class="nutrition-targets__title ${calOver ? 'text--danger' : ''}">Сегодня: ${calRemain > 0 ? 'осталось ' + calRemain + ' ккал' : 'превышение на ' + Math.abs(calRemain) + ' ккал!'}</span>
            <button class="nutrition-targets__edit" id="btnEditProfile">Параметры</button>
        </div>
        <div class="progress-row">
            <div class="progress-row__label">
                <span>Калории</span>
                <strong class="${calOver ? 'text--danger' : ''}">${Math.round(d.total_calories)} / ${t.goal_calories} ккал</strong>
            </div>
            <div class="progress-bar">
                <div class="progress-bar__fill ${calOver ? 'progress-bar__fill--over' : 'progress-bar__fill--cal'}" style="width:${Math.min(calPct, 100)}%"></div>
            </div>
        </div>
        ${calOver ? '<p class="nutrition-warning">Дневная норма калорий превышена!</p>' : ''}
        <div class="macro-grid">
            <div class="progress-row">
                <div class="progress-row__label">
                    <span>Белки</span>
                    <strong class="${proOver ? 'text--danger' : ''}">${Math.round(d.total_protein)} / ${t.protein_grams} г</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-bar__fill ${proOver ? 'progress-bar__fill--over' : 'progress-bar__fill--pro'}" style="width:${Math.min(proPct, 100)}%"></div>
                </div>
            </div>
            <div class="progress-row">
                <div class="progress-row__label">
                    <span>Жиры</span>
                    <strong class="${fatOver ? 'text--danger' : ''}">${Math.round(d.total_fat)} / ${t.fat_grams} г</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-bar__fill ${fatOver ? 'progress-bar__fill--over' : 'progress-bar__fill--fat'}" style="width:${Math.min(fatPct, 100)}%"></div>
                </div>
            </div>
            <div class="progress-row">
                <div class="progress-row__label">
                    <span>Углеводы</span>
                    <strong class="${carbOver ? 'text--danger' : ''}">${Math.round(d.total_carbs)} / ${t.carb_grams} г</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-bar__fill ${carbOver ? 'progress-bar__fill--over' : 'progress-bar__fill--carb'}" style="width:${Math.min(carbPct, 100)}%"></div>
                </div>
            </div>
        </div>
    `;
    nutritionTargetsEl.querySelector('#btnEditProfile').addEventListener('click', openProfileModal);

    renderMeals();
}

// ------------- Питание: приёмы пищи -------------
const mealTypeModalOverlay = document.getElementById('mealTypeModalOverlay');

document.getElementById('btnAddMeal').addEventListener('click', () => { mealTypeModalOverlay.style.display = 'flex'; });
document.getElementById('btnMealTypeCancel').addEventListener('click', () => { mealTypeModalOverlay.style.display = 'none'; });
mealTypeModalOverlay.addEventListener('click', (e) => { if (e.target === mealTypeModalOverlay) mealTypeModalOverlay.style.display = 'none'; });

mealTypeModalOverlay.querySelectorAll('[data-type]').forEach(btn => {
    btn.addEventListener('click', async () => {
        mealTypeModalOverlay.style.display = 'none';
        try {
            await apiPost(`/nutrition/days/${currentNutritionDay.id}/meals`, { meal_type: btn.dataset.type });
            await loadNutritionData();
            showToast(`${MEAL_LABELS[btn.dataset.type]} добавлен`);
        } catch (err) {
            showToast('Ошибка: ' + err.message, 'error');
        }
    });
});

function renderMeals() {
    const meals = currentNutritionDay.meals || [];
    mealsSection.innerHTML = '';
    mealsEmpty.style.display = meals.length === 0 ? 'block' : 'none';

    meals.forEach(meal => {
        const card = document.createElement('div');
        card.className = 'meal-card meal-card--expanded';
        const foods = meal.food_items || [];
        const kcalSum = Math.round(meal.total_calories);

        card.innerHTML = `
            <div class="meal-card__header">
                <div class="meal-card__info">
                    <span class="meal-card__type meal-card__type--${meal.meal_type}">${MEAL_LABELS[meal.meal_type] || meal.meal_type}</span>
                    <span class="meal-card__summary">${kcalSum} ккал · ${foods.length} продукт.</span>
                </div>
                <div class="meal-card__actions">
                    <button class="btn-icon btn-icon--danger" data-action="del-meal" title="Удалить">✕</button>
                    <span class="meal-card__expand">▼</span>
                </div>
            </div>
            <div class="meal-card__body">
                <div class="food-list">
                    ${foods.map(f => `
                        <div class="food-item" data-food-id="${f.id}">
                            <div class="food-item__info">
                                <span class="food-item__name">${escapeHTML(f.name)} · ${f.weight_grams}г</span>
                                <span class="food-item__macros">${f.actual_calories} ккал · Б ${f.actual_protein} · Ж ${f.actual_fat} · У ${f.actual_carbs}</span>
                            </div>
                            <div class="food-item__actions">
                                <button class="btn-icon btn-icon--edit" data-action="edit-food" data-food-id="${f.id}" title="Редактировать">✎</button>
                                <button class="btn-icon btn-icon--danger" data-action="del-food" data-food-id="${f.id}" title="Удалить">✕</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <button class="btn--add-food" data-action="add-food">+ Добавить продукт</button>
            </div>
        `;

        const header = card.querySelector('.meal-card__header');
        header.addEventListener('click', (e) => {
            if (e.target.closest('[data-action]')) return;
            card.classList.toggle('meal-card--expanded');
        });

        card.querySelector('[data-action="del-meal"]').addEventListener('click', async (e) => {
            e.stopPropagation();
            const ok = await showConfirm(`Удалить ${MEAL_LABELS[meal.meal_type]}?`);
            if (!ok) return;
            try {
                await apiDelete(`/nutrition/days/${currentNutritionDay.id}/meals/${meal.id}`);
                await loadNutritionData();
                showToast('Приём пищи удалён');
            } catch (err) { showToast('Ошибка: ' + err.message, 'error'); }
        });

        card.querySelector('[data-action="add-food"]').addEventListener('click', () => openFoodModal(meal.id));

        card.querySelectorAll('[data-action="edit-food"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const f = foods.find(x => x.id === btn.dataset.foodId);
                if (f) openFoodModal(meal.id, f);
            });
        });

        card.querySelectorAll('[data-action="del-food"]').forEach(btn => {
            btn.addEventListener('click', async () => {
                const ok = await showConfirm('Удалить продукт?');
                if (!ok) return;
                try {
                    await apiDelete(`/nutrition/meals/${meal.id}/foods/${btn.dataset.foodId}`);
                    await loadNutritionData();
                    showToast('Продукт удалён');
                } catch (err) { showToast('Ошибка: ' + err.message, 'error'); }
            });
        });

        mealsSection.appendChild(card);
    });
}

// ------------- Питание: продукты (CRUD) -------------
const foodModalOverlay = document.getElementById('foodModalOverlay');
const foodForm = document.getElementById('foodForm');

document.getElementById('btnFoodCancel').addEventListener('click', () => { foodModalOverlay.style.display = 'none'; });
foodModalOverlay.addEventListener('click', (e) => { if (e.target === foodModalOverlay) foodModalOverlay.style.display = 'none'; });

function openFoodModal(mealId, food = null) {
    document.getElementById('foodMealId').value = mealId;
    document.getElementById('foodItemId').value = food ? food.id : '';
    document.getElementById('foodModalTitle').textContent = food ? 'Редактировать продукт' : 'Добавить продукт';
    document.getElementById('foodName').value = food ? food.name : '';
    document.getElementById('foodWeight').value = food ? food.weight_grams : '';
    document.getElementById('foodCal').value = food ? food.calories_per_100g : '';
    document.getElementById('foodPro').value = food ? food.protein_per_100g : '';
    document.getElementById('foodFat').value = food ? food.fat_per_100g : '';
    document.getElementById('foodCarb').value = food ? food.carbs_per_100g : '';
    foodModalOverlay.style.display = 'flex';
}

foodForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const mealId = document.getElementById('foodMealId').value;
    const foodId = document.getElementById('foodItemId').value;
    const data = {
        name: document.getElementById('foodName').value.trim(),
        weight_grams: parseFloat(document.getElementById('foodWeight').value),
        calories_per_100g: parseFloat(document.getElementById('foodCal').value),
        protein_per_100g: parseFloat(document.getElementById('foodPro').value),
        fat_per_100g: parseFloat(document.getElementById('foodFat').value),
        carbs_per_100g: parseFloat(document.getElementById('foodCarb').value),
    };
    try {
        if (foodId) {
            await apiPut(`/nutrition/meals/${mealId}/foods/${foodId}`, data);
        } else {
            await apiPost(`/nutrition/meals/${mealId}/foods`, data);
        }
        foodModalOverlay.style.display = 'none';
        await loadNutritionData();
        showToast(foodId ? 'Продукт обновлён' : 'Продукт добавлен');
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
});

// ------------- ИМТ (индекс массы тела) -------------
document.getElementById('bmiForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const weight = parseFloat(document.getElementById('bmiWeight').value);
    const heightCm = parseFloat(document.getElementById('bmiHeight').value);
    const heightM = heightCm / 100;
    const bmi = weight / (heightM * heightM);
    const bmiRound = Math.round(bmi * 10) / 10;

    let label, color;
    if (bmi < 18.5) { label = 'Дефицит массы тела'; color = '#1565c0'; }
    else if (bmi < 25) { label = 'Нормальный вес'; color = '#2e7d32'; }
    else if (bmi < 30) { label = 'Избыточный вес'; color = '#e65100'; }
    else { label = 'Ожирение'; color = '#c62828'; }

    document.getElementById('bmiValue').textContent = bmiRound;
    document.getElementById('bmiValue').style.color = color;
    document.getElementById('bmiLabel').textContent = label;
    document.getElementById('bmiLabel').style.color = color;

    const markerPct = Math.max(0, Math.min(100, (bmi - 16) / (40 - 16) * 100));
    document.getElementById('bmiMarker').style.left = `calc(${markerPct}% - 2px)`;
    document.getElementById('bmiResult').style.display = 'block';
});

// ------------- PWA Service Worker -------------
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}

// ------------- Старт -------------
checkSession();
