let selectedGender = '';

function switchTab(tab) {
    const loginSection = document.getElementById('login-section');
    const registerSection = document.getElementById('register-section');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    if (tab === 'login') {
        loginSection.classList.add('active');
        registerSection.classList.remove('active');
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
    } else {
        loginSection.classList.remove('active');
        registerSection.classList.add('active');
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
    }
}

function selectGender(gender) {
    selectedGender = gender;
    document.getElementById('reg-gender').value = gender;
    
    document.querySelectorAll('.gender-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`gender-${gender}`).classList.add('active');
}

document.addEventListener('DOMContentLoaded', () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            window.location.href = user.role === 'admin' ? 'admin.html' : 'dashboard.html';
        } catch (e) {
            localStorage.removeItem('user');
        }
    }
});

// Login Form submission
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await api.post('/auth/login', { email, password });
        api.showToast('Login Success', 'Welcome back!', 'success');
        
        // Save auth details
        api.setAuthToken(response.token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        setTimeout(() => {
            window.location.href = response.user.role === 'admin' ? 'admin.html' : 'dashboard.html';
        }, 800);
    } catch (error) {
        api.showToast('Login Failed', error.message, 'error');
    }
});

// Registration Form submission
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const age = document.getElementById('reg-age').value;
    const gender = document.getElementById('reg-gender').value;

    if (!gender) {
        api.showToast('Validation Error', 'Please select a gender option', 'error');
        return;
    }

    if (password.length < 8) {
        api.showToast('Validation Error', 'Password must be at least 8 characters long', 'error');
        return;
    }

    try {
        await api.post('/auth/register', { name, email, password, age, gender });
        api.showToast('Registration Successful', 'Account created! Please login now.', 'success');
        
        // Reset and redirect to login panel
        document.getElementById('register-form').reset();
        selectedGender = '';
        document.querySelectorAll('.gender-btn').forEach(btn => btn.classList.remove('active'));
        
        setTimeout(() => {
            switchTab('login');
        }, 1500);
    } catch (error) {
        api.showToast('Registration Failed', error.message, 'error');
    }
});
