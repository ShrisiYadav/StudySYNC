let currentAdmin = null;
let growthChart = null;

document.addEventListener('DOMContentLoaded', () => {
    const userStr = localStorage.getItem('user');
    if (!userStr) {
        window.location.href = 'auth.html';
        return;
    }
    
    currentAdmin = JSON.parse(userStr);
    if (currentAdmin.role !== 'admin') {
        api.showToast('Access Denied', 'Administrators access privileges only', 'error');
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1500);
        return;
    }
    
    document.getElementById('admin-display-name').textContent = currentAdmin.name;
    
    // Bind search action trigger on Enter key press
    document.getElementById('search-users-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            fetchUsersList();
        }
    });

    // Bind edit profile and reset password submit forms
    document.getElementById('edit-user-form').addEventListener('submit', handleEditUserSubmit);
    document.getElementById('reset-password-form').addEventListener('submit', handleResetPasswordSubmit);

    // Populate data
    refreshAdminDashboard();
});

function refreshAdminDashboard() {
    fetchPlatformMetrics();
    fetchUsersList();
    fetchRecordsAuditList();
}

// Fetch platform statistics
async function fetchPlatformMetrics() {
    try {
        const response = await api.get('/admin/metrics');
        
        // Update widgets
        document.getElementById('stat-total-users').textContent = response.total_users;
        document.getElementById('stat-total-logs').textContent = response.total_logs;
        document.getElementById('stat-steps-count').textContent = response.activity.steps;
        document.getElementById('stat-water-count').textContent = response.activity.water;
        
        // Draw registration growth line chart
        renderGrowthChart(response.growth);
    } catch (error) {
        api.showToast('Metrics Error', 'Failed to retrieve platform analytics', 'error');
    }
}

function renderGrowthChart(growthData) {
    const ctx = document.getElementById('chart-growth').getContext('2d');
    
    if (growthChart) {
        growthChart.destroy();
    }
    
    // Fallback if data is empty
    const labels = growthData.months.length > 0 ? growthData.months : ['No Data'];
    const counts = growthData.counts.length > 0 ? growthData.counts : [0];
    
    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Registered Users',
                data: counts,
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                borderColor: 'rgb(99, 102, 241)',
                borderWidth: 2.5,
                tension: 0.3,
                pointBackgroundColor: 'rgb(99, 102, 241)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0', font: { family: 'Inter', size: 10 } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#a0aec0', font: { family: 'Inter', size: 10 } }
                }
            }
        }
    });
}

// Fetch users directory
async function fetchUsersList() {
    const searchVal = document.getElementById('search-users-input').value;
    const tbody = document.getElementById('users-table-body');
    
    try {
        const response = await api.get(`/admin/users?search=${encodeURIComponent(searchVal)}`);
        tbody.innerHTML = '';
        
        const list = response.users;
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No matching users found</td></tr>';
            return;
        }
        
        list.forEach(user => {
            const statusClass = user.is_active === 1 ? 'active' : 'disabled';
            const statusLabel = user.is_active === 1 ? 'Active' : 'Disabled';
            const toggleIcon = user.is_active === 1 ? '🚫' : '✅';
            const toggleTitle = user.is_active === 1 ? 'Disable Account' : 'Enable Account';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${user.id}</td>
                <td style="font-weight: 500;">${user.name}</td>
                <td>${user.email}</td>
                <td><span class="role-badge ${user.role}">${user.role}</span></td>
                <td><span class="status-badge ${statusClass}">${statusLabel}</span></td>
                <td>
                    <div class="action-btn-group">
                        <button onclick="openEditModal(${user.id}, '${user.name.replace(/'/g, "\\'")}', '${user.email}', ${user.age}, '${user.gender}', '${user.role}')" class="btn-icon" title="Edit Profile">✏️</button>
                        <button onclick="openResetPasswordModal(${user.id}, '${user.name.replace(/'/g, "\\'")}')" class="btn-icon" title="Reset Password">🔑</button>
                        <button onclick="toggleUserStatus(${user.id}, '${user.name.replace(/'/g, "\\'")}', ${user.is_active})" class="btn-icon ${user.is_active === 1 ? 'disable-btn' : 'enable-btn'}" title="${toggleTitle}">
                            ${toggleIcon}
                        </button>
                        <button onclick="confirmDeleteUser(${user.id}, '${user.name.replace(/'/g, "\\'")}')" class="btn-icon" style="color: var(--danger);" title="Delete User Account">
                            🗑️
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error retrieving user directory", error);
    }
}

async function confirmDeleteUser(id, name) {
    if (id === currentAdmin.id) {
        api.showToast('Operation Blocked', 'You cannot delete your own admin account', 'error');
        return;
    }
    
    if (confirm(`Are you absolutely sure you want to delete the user "${name}"?\nAll associated health logs, goals, and credentials will be permanently purged!`)) {
        try {
            await api.delete(`/admin/users/${id}`);
            api.showToast('Account Deleted', `${name}'s account has been successfully removed`, 'success');
            refreshAdminDashboard();
        } catch (error) {
            api.showToast('Delete Error', error.message, 'error');
        }
    }
}

// Fetch general logs audit trail
async function fetchRecordsAuditList() {
    const tbody = document.getElementById('records-table-body');
    
    try {
        const response = await api.get('/admin/records');
        tbody.innerHTML = '';
        
        const list = response.records;
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No records registered on platform</td></tr>';
            return;
        }
        
        list.forEach(record => {
            const unit = record.metric_type === 'steps' ? ' steps' :
                         record.metric_type === 'water' ? ' ml' :
                         record.metric_type === 'sleep' ? ' hrs' : ' bpm';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div style="font-weight: 500;">${record.user_name}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${record.user_email}</div>
                </td>
                <td><span class="metric-badge ${record.metric_type}">${record.metric_type.replace('_', ' ')}</span></td>
                <td style="font-family: var(--font-heading); font-weight: 600;">${record.value}${unit}</td>
                <td>${record.log_date}</td>
                <td>
                    <button onclick="confirmDeleteRecord(${record.id}, '${record.metric_type}')" class="action-delete-btn" title="Delete Log Record">
                        🗑️
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error("Error loading records audit trail", error);
    }
}

async function confirmDeleteRecord(id, metricType) {
    if (confirm(`Delete this health entry record?`)) {
        try {
            await api.delete(`/admin/records/${id}?metric_type=${metricType}`);
            api.showToast('Record Purged', 'Record successfully removed', 'success');
            refreshAdminDashboard();
        } catch (error) {
            api.showToast('Purge Error', error.message, 'error');
        }
    }
}

// User Sign Out action
async function handleLogout() {
    try {
        await api.post('/auth/logout');
    } catch (e) {
        console.error("Error logging out", e);
    }
    api.setAuthToken(null);
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// Modal dialog wrappers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function openEditModal(id, name, email, age, gender, role) {
    document.getElementById('edit-user-id').value = id;
    document.getElementById('edit-user-name').value = name;
    document.getElementById('edit-user-email').value = email;
    document.getElementById('edit-user-age').value = age;
    document.getElementById('edit-user-gender').value = gender;
    document.getElementById('edit-user-role').value = role;
    openModal('edit-user-modal');
}

async function handleEditUserSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('edit-user-id').value;
    const name = document.getElementById('edit-user-name').value;
    const email = document.getElementById('edit-user-email').value;
    const age = document.getElementById('edit-user-age').value;
    const gender = document.getElementById('edit-user-gender').value;
    const role = document.getElementById('edit-user-role').value;

    try {
        const response = await apiRequest(`/admin/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ name, email, age, gender, role })
        });
        
        api.showToast('Profile Updated', 'User details updated successfully', 'success');
        closeModal('edit-user-modal');
        
        // If editing current admin, update local storage
        if (parseInt(id) === currentAdmin.id) {
            currentAdmin.name = name;
            currentAdmin.email = email;
            currentAdmin.role = role;
            localStorage.setItem('user', JSON.stringify(currentAdmin));
            document.getElementById('admin-display-name').textContent = name;
        }

        refreshAdminDashboard();
    } catch (error) {
        api.showToast('Update Error', error.message, 'error');
    }
}

function openResetPasswordModal(id, name) {
    document.getElementById('reset-pass-user-id').value = id;
    document.getElementById('reset-pass-name').value = name;
    document.getElementById('reset-pass-value').value = '';
    openModal('reset-password-modal');
}

async function handleResetPasswordSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('reset-pass-user-id').value;
    const password = document.getElementById('reset-pass-value').value;

    if (password.length < 8) {
        api.showToast('Validation Error', 'Password must be at least 8 characters long', 'error');
        return;
    }

    try {
        await api.post(`/admin/users/${id}/reset-password`, { password });
        api.showToast('Password Reset', 'User password updated successfully', 'success');
        closeModal('reset-password-modal');
        refreshAdminDashboard();
    } catch (error) {
        api.showToast('Reset Error', error.message, 'error');
    }
}

async function toggleUserStatus(id, name, isActive) {
    if (id === currentAdmin.id) {
        api.showToast('Operation Blocked', 'You cannot disable your own admin account', 'error');
        return;
    }

    const actionText = isActive === 1 ? 'disable' : 'enable';
    if (confirm(`Are you sure you want to ${actionText} the user "${name}"?`)) {
        try {
            const response = await api.post(`/admin/users/${id}/toggle-status`);
            api.showToast('Status Updated', response.message, 'success');
            refreshAdminDashboard();
        } catch (error) {
            api.showToast('Status Toggle Error', error.message, 'error');
        }
    }
}
