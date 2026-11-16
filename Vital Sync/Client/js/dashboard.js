// Verify auth state
let currentUser = null;
let charts = {};
let closePanelListener = null;
let currentTrendsDays = 7;

function getLocalDateString() {
    const localDate = new Date();
    const year = localDate.getFullYear();
    const month = String(localDate.getMonth() + 1).padStart(2, '0');
    const day = String(localDate.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const userStr = localStorage.getItem('user');
    if (!userStr) {
        window.location.href = 'auth.html';
        return;
    }
    
    currentUser = JSON.parse(userStr);
    
    // Update headers and admin routes
    document.getElementById('user-display-name').textContent = currentUser.name;
    document.getElementById('greeting-title').textContent = `Hello, ${currentUser.name.split(' ')[0]}`;
    
    const formattedDate = new Date().toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    document.getElementById('current-date-string').textContent = formattedDate;
    
    if (currentUser.role === 'admin') {
        document.getElementById('admin-nav-item').style.display = 'block';
        document.getElementById('admin-banner-btn').style.display = 'inline-flex';
    }
    
    // Default logging dates to today
    const todayStr = getLocalDateString();
    document.getElementById('input-steps-date').value = todayStr;
    document.getElementById('input-water-date').value = todayStr;
    document.getElementById('input-sleep-date').value = todayStr;
    document.getElementById('input-heart-date').value = todayStr;
    
    // Bind form submits
    bindForms();
    
    // Initial fetch logs and charts data
    refreshDashboardData();
    
    // Refresh alerts every 30 seconds
    setInterval(fetchNotifications, 30000);
});

// Logs Tab Switcher
function switchLogTab(e, metric) {
    document.querySelectorAll('.log-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.log-form-container').forEach(form => {
        form.classList.remove('active');
    });
    
    if (e && e.currentTarget) {
        e.currentTarget.classList.add('active');
    }
    document.getElementById(`log-form-${metric}`).classList.add('active');
}

// Notification Drawer Toggle
function toggleNotifications(e) {
    if (e) e.stopPropagation();
    const panel = document.getElementById('notif-panel');
    const bellBtn = document.getElementById('bell-btn');
    const isActive = panel.classList.toggle('active');
    
    if (isActive) {
        if (closePanelListener) {
            document.removeEventListener('click', closePanelListener);
        }
        
        closePanelListener = function(event) {
            if (!panel.contains(event.target) && !bellBtn.contains(event.target)) {
                panel.classList.remove('active');
                document.removeEventListener('click', closePanelListener);
                closePanelListener = null;
            }
        };
        
        document.addEventListener('click', closePanelListener);
    } else {
        if (closePanelListener) {
            document.removeEventListener('click', closePanelListener);
            closePanelListener = null;
        }
    }
}

// Form Bindings
function bindForms() {
    // Steps Form Submit
    document.getElementById('form-steps').addEventListener('submit', async (e) => {
        e.preventDefault();
        const value = document.getElementById('input-steps-value').value;
        const date = document.getElementById('input-steps-date').value;
        await submitMetric('steps', value, date, 'form-steps');
    });

    // Water Form Submit
    document.getElementById('form-water').addEventListener('submit', async (e) => {
        e.preventDefault();
        const value = document.getElementById('input-water-value').value;
        const date = document.getElementById('input-water-date').value;
        await submitMetric('water', value, date, 'form-water');
    });

    // Sleep Form Submit
    document.getElementById('form-sleep').addEventListener('submit', async (e) => {
        e.preventDefault();
        const value = document.getElementById('input-sleep-value').value;
        const date = document.getElementById('input-sleep-date').value;
        await submitMetric('sleep', value, date, 'form-sleep');
    });

    // Heart Rate Form Submit
    document.getElementById('form-heart').addEventListener('submit', async (e) => {
        e.preventDefault();
        const value = document.getElementById('input-heart-value').value;
        const date = document.getElementById('input-heart-date').value;
        await submitMetric('heart_rate', value, date, 'form-heart');
    });
}

// Submit single log to server
async function submitMetric(metricType, value, date, formId) {
    try {
        await api.post('/health/log', { metric_type: metricType, value, date });
        api.showToast('Data Logged', `${metricType.replace('_', ' ').toUpperCase()} recorded successfully`, 'success');
        
        // Reset logging input values but keep date default
        const form = document.getElementById(formId);
        if (form) {
            form.querySelector('input[type="number"]').value = '';
        }
        
        // Refresh all panel logs
        refreshDashboardData();
    } catch (error) {
        api.showToast('Log Error', error.message, 'error');
    }
}

// Quick add helper for water
async function quickLogWater(amount) {
    const todayStr = getLocalDateString();
    try {
        await api.post('/health/log', { metric_type: 'water', value: amount, date: todayStr });
        api.showToast('Hydration Logged', `Added +${amount}ml water`, 'success');
        refreshDashboardData();
    } catch (error) {
        api.showToast('Logging Error', error.message, 'error');
    }
}

// Fetch relative daily metrics progress
async function refreshDashboardData() {
    await fetchGoalsProgress();
    await fetchNotifications();
    await fetchAnalyticsTrends();
    await fetchReminders();
}

async function fetchGoalsProgress() {
    try {
        const response = await api.get('/goals');
        const goals = response.goals;
        const progress = response.progress;
        
        // Update Steps Card
        document.getElementById('metric-steps-current').textContent = progress.steps.logged;
        document.getElementById('metric-steps-target').textContent = `/ ${goals.steps} steps`;
        document.getElementById('progress-steps').style.width = `${progress.steps.percentage}%`;
        document.getElementById('footer-steps').textContent = `${Math.round(progress.steps.percentage)}% of daily goal reached`;
        document.getElementById('goal-current-steps').textContent = `Current Target: ${goals.steps} steps`;
        
        // Update Water Card
        document.getElementById('metric-water-current').textContent = progress.water.logged;
        document.getElementById('metric-water-target').textContent = `/ ${goals.water} ml`;
        document.getElementById('progress-water').style.width = `${progress.water.percentage}%`;
        document.getElementById('footer-water').textContent = `${Math.round(progress.water.percentage)}% of daily goal reached`;
        document.getElementById('goal-current-water').textContent = `Current Target: ${goals.water} ml`;
        
        // Update Sleep Card
        document.getElementById('metric-sleep-current').textContent = progress.sleep.logged;
        document.getElementById('metric-sleep-target').textContent = `/ ${goals.sleep} hours`;
        document.getElementById('progress-sleep').style.width = `${progress.sleep.percentage}%`;
        document.getElementById('footer-sleep').textContent = `${Math.round(progress.sleep.percentage)}% of daily goal reached`;
        document.getElementById('goal-current-sleep').textContent = `Current Target: ${goals.sleep} hours`;
        
        // Update Pulse Card with last entry
        const pulseHistory = await api.get('/health/history?metric_type=heart_rate');
        const logs = pulseHistory.logs;
        if (logs.length > 0) {
            const lastLog = logs[logs.length - 1];
            document.getElementById('metric-heart-current').textContent = lastLog.bpm;
            document.getElementById('footer-heart').textContent = `Logged at: ${lastLog.logged_at.split(' ')[1]}`;
        } else {
            document.getElementById('metric-heart-current').textContent = '--';
            document.getElementById('footer-heart').textContent = 'No pulse logs registered';
        }
        
    } catch (error) {
        console.error("Error loading daily goals and progress", error);
    }
}

// Adjust daily target settings
async function saveGoal(metric) {
    const input = document.getElementById(`goal-input-${metric}`);
    const targetValue = input.value;
    
    if (!targetValue) {
        api.showToast('Inputs Error', 'Please enter a target value', 'error');
        return;
    }
    
    try {
        await api.post('/goals', { metric_type: metric, target_value: targetValue });
        api.showToast('Goal Configured', `Your daily ${metric} target was updated`, 'success');
        input.value = '';
        refreshDashboardData();
    } catch (error) {
        api.showToast('Goal Configuration Error', error.message, 'error');
    }
}

// Fetch in-app notifications
async function fetchNotifications() {
    try {
        const response = await api.get('/notifications');
        const list = response.notifications;
        const container = document.getElementById('notifications-container');
        const badge = document.getElementById('bell-badge');
        
        container.innerHTML = '';
        
        const unreadCount = list.filter(n => !n.is_read).length;
        if (unreadCount > 0) {
            badge.style.display = 'flex';
            badge.textContent = unreadCount;
        } else {
            badge.style.display = 'none';
        }
        
        if (list.length === 0) {
            container.innerHTML = '<div class="no-notifs">No active notifications</div>';
            return;
        }
        
        list.forEach(notif => {
            const item = document.createElement('div');
            item.className = `notif-item ${notif.is_read ? '' : 'unread'}`;
            item.onclick = () => readNotification(notif.id);
            
            item.innerHTML = `
                <span class="notif-item-title ${notif.type}">${notif.title}</span>
                <span class="notif-item-msg">${notif.message}</span>
                <span class="notif-item-time">${notif.created_at}</span>
            `;
            container.appendChild(item);
        });
    } catch (error) {
        console.error("Error loading notifications list", error);
    }
}

async function readNotification(id) {
    try {
        await api.post(`/notifications/read/${id}`);
        fetchNotifications();
    } catch (error) {
        console.error("Error marking notification as read", error);
    }
}

async function markAllNotificationsRead() {
    try {
        await api.post('/notifications/read');
        api.showToast('Notifications Read', 'All notifications cleared', 'success');
        fetchNotifications();
    } catch (error) {
        api.showToast('Error', error.message, 'error');
    }
}

// Get history trends and render charts
async function fetchAnalyticsTrends() {
    try {
        const response = await api.get(`/analytics/trends?days=${currentTrendsDays}`);
        renderTrendsCharts(response);
    } catch (error) {
        console.error("Error loading analytics trends", error);
    }
}

// Change trends display range (7 or 30 days) and update charts
async function changeTrendsRange(days) {
    if (days !== 7 && days !== 30) return;
    
    currentTrendsDays = days;
    
    // Toggle active classes on buttons
    document.getElementById('toggle-days-7').classList.toggle('active', days === 7);
    document.getElementById('toggle-days-30').classList.toggle('active', days === 30);
    
    // Fetch and re-render charts
    await fetchAnalyticsTrends();
}

function renderTrendsCharts(data) {
    const dates = data.dates;
    
    const chartConfigs = {
        grid: {
            color: 'rgba(255, 255, 255, 0.05)'
        },
        ticks: {
            color: '#a0aec0',
            font: { family: 'Inter', size: 10 }
        }
    };
    
    // Steps Chart (Bar)
    createOrUpdateChart('chart-steps', 'bar', {
        labels: dates,
        datasets: [{
            label: 'Steps Walked',
            data: data.steps,
            backgroundColor: 'rgba(16, 185, 129, 0.3)',
            borderColor: 'rgb(16, 185, 129)',
            borderWidth: 1.5,
            borderRadius: 6
        }]
    }, 'Steps count', chartConfigs);

    // Water Chart (Bar)
    createOrUpdateChart('chart-water', 'bar', {
        labels: dates,
        datasets: [{
            label: 'Water (ml)',
            data: data.water,
            backgroundColor: 'rgba(14, 165, 233, 0.3)',
            borderColor: 'rgb(14, 165, 233)',
            borderWidth: 1.5,
            borderRadius: 6
        }]
    }, 'Water volume (ml)', chartConfigs);

    // Sleep Chart (Bar/Line)
    createOrUpdateChart('chart-sleep', 'bar', {
        labels: dates,
        datasets: [{
            label: 'Sleep hours',
            data: data.sleep,
            backgroundColor: 'rgba(139, 92, 246, 0.3)',
            borderColor: 'rgb(139, 92, 246)',
            borderWidth: 1.5,
            borderRadius: 6
        }]
    }, 'Sleep (hrs)', chartConfigs);

    // Heart Rate Chart (Line)
    createOrUpdateChart('chart-heart', 'line', {
        labels: dates,
        datasets: [{
            label: 'Pulse BPM (Avg)',
            data: data.heart_rate,
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderColor: 'rgb(239, 68, 68)',
            borderWidth: 2,
            tension: 0.35,
            pointBackgroundColor: 'rgb(239, 68, 68)',
            fill: true
        }]
    }, 'Pulse (BPM)', chartConfigs);
}

function createOrUpdateChart(canvasId, type, data, ylabel, styleConfigs) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Destroy previous Chart instance to resolve canvas overlap glitches
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    charts[canvasId] = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: styleConfigs.grid,
                    ticks: styleConfigs.ticks
                },
                y: {
                    grid: styleConfigs.grid,
                    ticks: styleConfigs.ticks,
                    title: {
                        display: true,
                        text: ylabel,
                        color: '#718096',
                        font: { family: 'Inter', size: 11, weight: 'medium' }
                    }
                }
            }
        }
    });
}

// User Sign Out action
async function handleLogout() {
    try {
        await api.post('/auth/logout');
    } catch (e) {
        console.error("Error reporting logout to server", e);
    }
    
    // Clear state
    api.setAuthToken(null);
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

async function fetchReminders() {
    try {
        const response = await api.get('/notifications/reminders');
        const list = response.reminders;
        const panel = document.getElementById('reminders-panel');
        
        panel.innerHTML = '';
        
        // Hide panel if no reminders are active
        if (list.length === 0) {
            panel.style.display = 'none';
            return;
        }
        
        panel.style.display = 'flex';
        
        list.forEach(reminder => {
            const card = document.createElement('div');
            card.className = `reminder-card ${reminder.severity}`;
            
            // Map icons for visual flare
            const icon = reminder.type === 'water' ? '💧' :
                         reminder.type === 'activity' ? '👣' : '🌙';
                         
            card.innerHTML = `
                <div class="reminder-content">
                    <span class="reminder-title">${icon} ${reminder.title}</span>
                    <span class="reminder-text">${reminder.message}</span>
                </div>
                <button class="reminder-close-btn" onclick="dismissReminder(this)">&times;</button>
            `;
            panel.appendChild(card);
        });
    } catch (error) {
        console.error("Error loading reminder cards", error);
    }
}

function dismissReminder(button) {
    const card = button.closest('.reminder-card');
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            card.remove();
            const panel = document.getElementById('reminders-panel');
            if (panel && panel.children.length === 0) {
                panel.style.display = 'none';
            }
        }, 300);
    }
}
