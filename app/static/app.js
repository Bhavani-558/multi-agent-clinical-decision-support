/**
 * MultiAgent CDSS — Single Page Application (SPA) Controller
 * Manages Real Doctor Authentication, Account Registration, Session Token Storage,
 * 401 Interceptors, Dynamic Patient Form Building, and 7-Section Clinical Report Rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    const TOKEN_KEY = 'cdss_session_token';
    const DOCTOR_KEY = 'cdss_doctor_info';

    // State Management
    const state = {
        currentScreen: 'screen-login',
        doctorInfo: JSON.parse(sessionStorage.getItem(DOCTOR_KEY) || 'null'),
        sessionToken: sessionStorage.getItem(TOKEN_KEY) || null,
        diseases: [],
        selectedDisease: null,
        currentReport: null,
        patientDetails: { patient_id: '', patient_name: '' },
        currentPatientFeatures: null,
        whatIfOriginalFeatures: null,
        historyItems: [],
        selectedHistoryItem: null
    };

    // DOM References
    const screens = {
        login: document.getElementById('screen-login'),
        register: document.getElementById('screen-register'),
        dashboard: document.getElementById('screen-dashboard'),
        patientForm: document.getElementById('screen-patient-form'),
        results: document.getElementById('screen-results'),
        history: document.getElementById('screen-history')
    };

    const userProfileEl = document.getElementById('user-profile');
    const userAvatarEl = document.getElementById('user-avatar');
    const navDoctorNameEl = document.getElementById('nav-doctor-name');
    const navDoctorRoleEl = document.getElementById('nav-doctor-role');

    // Dynamic Doctor Avatar Helper based on Gender & Name
    function getDoctorAvatarEmoji(doc) {
        if (!doc) return '👨‍⚕️';

        const g = (doc.gender || doc.sex || doc.doctor_gender || '').toString().toLowerCase().trim();
        if (g.startsWith('f') || g === 'woman' || g === 'female_doctor') {
            return '👩‍⚕️';
        }
        if (g.startsWith('m') || g === 'man' || g === 'male_doctor') {
            return '👨‍⚕️';
        }

        const nameStr = (doc.doctor_name || doc.username || doc.doctor_id || '').toLowerCase();

        if (/\b(ms|mrs|miss|lady|madam)\b/.test(nameStr)) {
            return '👩‍⚕️';
        }
        if (/\b(mr|sir)\b/.test(nameStr)) {
            return '👨‍⚕️';
        }

        const femaleNames = new Set([
            'sarah', 'alexandra', 'mary', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan',
            'jessica', 'karen', 'nancy', 'lisa', 'betty', 'margaret', 'sandra', 'ashley',
            'kimberly', 'emily', 'donna', 'michelle', 'carol', 'amanda', 'melissa', 'deborah',
            'stephanie', 'rebecca', 'sharon', 'laura', 'cynthia', 'kathleen', 'amy', 'shirley',
            'angela', 'helen', 'anna', 'brenda', 'pamela', 'nicole', 'samantha', 'katherine',
            'christine', 'debra', 'rachel', 'carolyn', 'janet', 'catherine', 'maria', 'heather',
            'diane', 'virginia', 'julie', 'joyce', 'victoria', 'olivia', 'kelly', 'christina',
            'lauren', 'joan', 'evelyn', 'judith', 'megan', 'cheryl', 'andrea', 'hannah',
            'martha', 'jacqueline', 'frances', 'gloria', 'ann', 'teresa', 'kathryn', 'sara',
            'janice', 'jean', 'alice', 'madison', 'dora', 'priya', 'anita', 'sunita', 'pooja',
            'sneha', 'swati', 'neha', 'divya', 'kavita', 'deepa', 'meena', 'radha', 'shweta',
            'monica', 'sonia', 'nisha', 'riya', 'shruti', 'tanvi', 'aditi', 'aarti', 'archana',
            'florence', 'clara', 'rosalind', 'marie', 'grace', 'diana', 'sophia', 'isabella',
            'ava', 'mia', 'evelyn', 'harper', 'camila', 'gianna', 'abigail', 'ella', 'charlotte'
        ]);

        const cleanTokens = nameStr.replace(/dr\.?|md|phd|prof\.?/gi, '').trim().split(/[\s,._]+/);
        for (const token of cleanTokens) {
            if (token && femaleNames.has(token)) {
                return '👩‍⚕️';
            }
        }

        return '👨‍⚕️';
    }

    function updateUserProfileUI(doc) {
        if (!doc) return;
        if (navDoctorNameEl) navDoctorNameEl.textContent = doc.doctor_name || 'Physician';
        if (navDoctorRoleEl) navDoctorRoleEl.textContent = doc.specialty || 'Clinical Specialist';
        if (userAvatarEl) userAvatarEl.textContent = getDoctorAvatarEmoji(doc);
        const homeDocEl = document.getElementById('home-doctor-display-name');
        if (homeDocEl) homeDocEl.textContent = doc.doctor_name || 'Bhavani Chegondi';
        if (mainPersistentNav) mainPersistentNav.classList.remove('hidden');
        if (typeof updateDoctorHistoryHeader === 'function') {
            updateDoctorHistoryHeader();
        }
    }

    // Auth DOM Elements
    const loginForm = document.getElementById('login-form');
    const loginAlert = document.getElementById('login-alert');
    const loginSuccess = document.getElementById('login-success');
    const btnGotoRegister = document.getElementById('btn-goto-register');

    const registerForm = document.getElementById('register-form');
    const registerAlert = document.getElementById('register-alert');
    const btnGotoLogin = document.getElementById('btn-goto-login');

    const diseaseGrid = document.getElementById('disease-grid');
    const diseaseSearchInput = document.getElementById('disease-search');

    // Persistent Main Navigation Elements
    const mainPersistentNav = document.getElementById('main-persistent-nav');
    const navBtnHome = document.getElementById('nav-btn-home');
    const navBtnPatientData = document.getElementById('nav-btn-patient-data') || document.getElementById('navBtnPatientData');
    const navBtnAnalysis = document.getElementById('nav-btn-analysis');
    const navBtnReports = document.getElementById('nav-btn-reports');
    const navBtnHistory = document.getElementById('nav-btn-history');

    const btnBackToDash = document.getElementById('btn-back-to-dash');
    const btnBackToForm = document.getElementById('btn-back-to-form');
    const btnBackToHistory = document.getElementById('btn-back-to-history');
    const btnOpenHome = document.getElementById('btn-open-home');
    const btnHomeHeroPatientDetails = document.getElementById('btn-home-hero-patient-details');
    const btnHomeQuickstartPatientDetails = document.getElementById('btn-home-quickstart-patient-details');
    const btnOpenPatientDetails = document.getElementById('btn-open-patient-details');
    const btnBackToDashboard = document.getElementById('btn-back-to-dashboard');
    const btnLogout = document.getElementById('btn-logout');
    const btnLoadDemo = document.getElementById('btn-load-demo');
    const btnClearFields = document.getElementById('btn-clear-fields');
    const btnLoadDataset = document.getElementById('btn-load-dataset');
    const modalLoadDataset = document.getElementById('modal-load-dataset');
    const btnCloseDatasetModal = document.getElementById('btn-close-dataset-modal');
    const btnCancelDatasetModal = document.getElementById('btn-cancel-dataset-modal');
    const btnConfirmLoadDataset = document.getElementById('btn-confirm-load-dataset');
    const formLoadDatasetRow = document.getElementById('form-load-dataset-row');
    const datasetModalError = document.getElementById('dataset-modal-error');
    const datasetRowInput = document.getElementById('dataset-row-input');
    const datasetRowHint = document.getElementById('dataset-row-hint');
    const datasetLoadedBanner = document.getElementById('dataset-loaded-banner');
    const patientAnalysisForm = document.getElementById('patient-analysis-form');
    const patientDetailsForm = document.getElementById('patient-details-form');
    const patientHistoryBtn = document.getElementById('btn-open-history');
    const btnHistoryBackToDiseases = document.getElementById('btn-history-back-to-diseases');
    const tabDoctorHistory = document.getElementById('tab-doctor-history');
    const tabPatientHistory = document.getElementById('tab-patient-history');
    const viewDoctorHistory = document.getElementById('view-doctor-history');
    const viewPatientHistory = document.getElementById('view-patient-history');
    const patientHistorySelect = document.getElementById('patient-history-select');
    const patientSummaryBanner = document.getElementById('patient-summary-banner');
    const patientHistoryList = document.getElementById('patient-history-list');
    const historySearchInput = document.getElementById('history-search');
    const historyList = document.getElementById('history-list');
    const patientHistoryDetail = document.getElementById('patient-history-detail');
    const btnClearHistory = document.getElementById('btn-clear-history');
    const modalClearHistory = document.getElementById('modal-clear-history');
    const btnCloseClearHistoryModal = document.getElementById('btn-close-clear-history-modal');
    const btnCancelClearHistory = document.getElementById('btn-cancel-clear-history');
    const btnConfirmClearHistory = document.getElementById('btn-confirm-clear-history');
    const clearHistoryModalNotice = document.getElementById('clear-history-modal-notice');

    const formDiseaseTitle = document.getElementById('form-disease-title');
    const formDiseaseDesc = document.getElementById('form-disease-desc');
    const formDiseaseIcon = document.getElementById('form-disease-icon');
    const formBreadcrumbDisease = document.getElementById('form-breadcrumb-disease');
    const patientFieldsContainer = document.getElementById('patient-fields-container');
    const reportContainer = document.getElementById('report-container');

    // Clean SVG Icons for Password Visibility Toggle
    const eyeOpenSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
    const eyeOffSvg = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

    // Password Visibility Toggle Attachment Helper
    function setupPasswordToggle(btnId, inputId) {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        if (!btn || !input) return;

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const isPass = input.type === 'password';
            input.type = isPass ? 'text' : 'password';

            btn.innerHTML = isPass ? eyeOffSvg : eyeOpenSvg;
            btn.setAttribute('aria-pressed', isPass ? 'true' : 'false');
            btn.setAttribute('aria-label', isPass ? 'Hide password' : 'Show password');
        });
    }

    // Attach toggles to all password fields
    setupPasswordToggle('btn-toggle-password', 'login-pass');
    setupPasswordToggle('btn-toggle-reg-pass', 'reg-pass');
    setupPasswordToggle('btn-toggle-reg-confirm', 'reg-confirm-pass');

    // Global delegation fallback for password eye buttons
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-toggle-pass');
        if (btn) {
            e.preventDefault();
            e.stopPropagation();
            const wrapper = btn.closest('.password-input-wrapper');
            if (wrapper) {
                const input = wrapper.querySelector('input');
                if (input) {
                    const isPass = input.type === 'password';
                    input.type = isPass ? 'text' : 'password';
                    btn.innerHTML = isPass ? eyeOffSvg : eyeOpenSvg;
                }
            }
        }
    });

    // Active Highlight Controller for Persistent Main Navigation
    function updatePersistentNavActive(screenName) {
        const allNavBtns = [navBtnHome, navBtnPatientData, navBtnAnalysis, navBtnReports, navBtnHistory];
        allNavBtns.forEach(btn => btn?.classList.remove('active'));

        if (screenName === 'screen-home') {
            navBtnHome?.classList.add('active');
        } else if (screenName === 'screen-patient-details' || screenName === 'screen-dashboard') {
            // Patient Data & Disease Selection both highlight Patient Data
            navBtnPatientData?.classList.add('active');
        } else if (screenName === 'screen-patient-form') {
            navBtnAnalysis?.classList.add('active');
        } else if (screenName === 'screen-results') {
            navBtnReports?.classList.add('active');
        } else if (screenName === 'screen-history') {
            navBtnHistory?.classList.add('active');
        }
    }

    // Navigation Router
    function navigateTo(screenName) {
        hideAlerts();
        const screenIds = ['screen-login', 'screen-register', 'screen-home', 'screen-dashboard', 'screen-patient-details', 'screen-patient-form', 'screen-results', 'screen-history'];
        screenIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (id === screenName) {
                    el.classList.remove('hidden');
                    el.classList.add('active');
                } else {
                    el.classList.add('hidden');
                    el.classList.remove('active');
                }
            }
        });
        state.currentScreen = screenName;
        updatePersistentNavActive(screenName);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Navigation Switchers
    if (btnGotoRegister) {
        btnGotoRegister.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo('screen-register');
        });
    }

    if (btnGotoLogin) {
        btnGotoLogin.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo('screen-login');
        });
    }

    // Authenticated API Helper (Attaches Authorization Header & Handles 401s)
    async function apiFetch(endpoint, options = {}) {
        const headers = options.headers || {};
        if (state.sessionToken) {
            headers['Authorization'] = `Bearer ${state.sessionToken}`;
        }
        options.headers = headers;

        const res = await fetch(endpoint, options);
        if (res.status === 401) {
            handleUnauthorized();
            throw new Error("Session expired or unauthorized. Please sign in again.");
        }
        return res;
    }

    function handleUnauthorized() {
        state.sessionToken = null;
        state.doctorInfo = null;
        sessionStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(DOCTOR_KEY);
        userProfileEl.classList.add('hidden');
        if (mainPersistentNav) mainPersistentNav.classList.add('hidden');
        showLoginAlert("Session expired or unauthorized. Please sign in.");
        navigateTo('screen-login');
    }

    function showLoginAlert(msg) {
        if (loginAlert) {
            loginAlert.textContent = msg;
            loginAlert.classList.remove('hidden');
        }
    }

    function showLoginSuccess(msg) {
        if (loginSuccess) {
            loginSuccess.textContent = msg;
            loginSuccess.classList.remove('hidden');
        }
    }

    function showRegisterAlert(msg) {
        if (registerAlert) {
            registerAlert.textContent = msg;
            registerAlert.classList.remove('hidden');
        }
    }

    function hideAlerts() {
        if (loginAlert) { loginAlert.textContent = ''; loginAlert.classList.add('hidden'); }
        if (loginSuccess) { loginSuccess.textContent = ''; loginSuccess.classList.add('hidden'); }
        if (registerAlert) { registerAlert.textContent = ''; registerAlert.classList.add('hidden'); }
    }

    // Initialize UI state: show login screen unless active token exists
    if (state.sessionToken && state.doctorInfo) {
        updateUserProfileUI(state.doctorInfo);
        userProfileEl.classList.remove('hidden');
        if (mainPersistentNav) mainPersistentNav.classList.remove('hidden');
        loadDiseases();
        navigateTo('screen-home');
    } else {
        userProfileEl.classList.add('hidden');
        if (mainPersistentNav) mainPersistentNav.classList.add('hidden');
        hideAlerts();
        navigateTo('screen-login');
    }

    // --- SCREEN 1: REAL DOCTOR LOGIN HANDLER ---
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlerts();

        const doctorId = document.getElementById('login-id').value.trim();
        const password = document.getElementById('login-pass').value;

        if (!doctorId || !password) {
            showLoginAlert("Please enter both Doctor ID/email and password.");
            return;
        }

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doctor_id: doctorId, password: password })
            });

            const data = await res.json();

            if (res.status === 200 && data.status === 'success' && data.doctor) {
                state.sessionToken = data.session_token;
                state.doctorInfo = data.doctor;
                sessionStorage.setItem(TOKEN_KEY, data.session_token);
                sessionStorage.setItem(DOCTOR_KEY, JSON.stringify(data.doctor));

                updateUserProfileUI(data.doctor);
                userProfileEl.classList.remove('hidden');
                if (mainPersistentNav) mainPersistentNav.classList.remove('hidden');

                // Clear input fields for security
                document.getElementById('login-pass').value = '';

                // Load diseases schema in background and navigate to Home Page
                loadDiseases();
                navigateTo('screen-home');
            } else {
                showLoginAlert(data.detail || "Invalid Doctor ID/email or password.");
            }
        } catch (err) {
            showLoginAlert("Invalid Doctor ID/email or password.");
        }
    });

    // --- SCREEN 1B: DOCTOR ACCOUNT REGISTRATION HANDLER ---
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAlerts();

            const docName = document.getElementById('reg-name').value.trim();
            const docEmail = document.getElementById('reg-email').value.trim();
            const docSpecialty = document.getElementById('reg-specialty').value.trim();
            const regGenderEl = document.getElementById('reg-gender');
            const docGender = regGenderEl ? regGenderEl.value : 'male';
            const password = document.getElementById('reg-pass').value;
            const confirmPass = document.getElementById('reg-confirm-pass').value;

            if (!docName || !docEmail || !docSpecialty || !password || !confirmPass) {
                showRegisterAlert("All required fields must be completed.");
                return;
            }

            if (password !== confirmPass) {
                showRegisterAlert("Password and Confirm Password do not match.");
                return;
            }

            if (password.length < 8) {
                showRegisterAlert("Password must be at least 8 characters long.");
                return;
            }

            try {
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        doctor_id: docEmail,
                        doctor_name: docName,
                        specialty: docSpecialty,
                        gender: docGender,
                        password: password
                    })
                });

                const data = await res.json();

                if (res.status === 200 && data.status === 'success') {
                    // Registration successful -> Reset reg form, show success message on login screen, pre-fill email
                    document.getElementById('reg-pass').value = '';
                    document.getElementById('reg-confirm-pass').value = '';
                    document.getElementById('login-id').value = docEmail;

                    showLoginSuccess("Doctor account created successfully. Please sign in.");
                    navigateTo('screen-login');
                } else {
                    showRegisterAlert(data.detail || "Registration failed. Please check your entries.");
                }
            } catch (err) {
                showRegisterAlert("An error occurred during registration. Please try again.");
            }
        });
    }

    // --- PASSWORD VISIBILITY TOGGLE HANDLERS ---
    window.togglePasswordVisibility = function (inputId, btnEl) {
        const input = document.getElementById(inputId);
        if (!input) return;
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';

        if (btnEl) {
            btnEl.innerHTML = isPassword
                ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                   </svg>`
                : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                   </svg>`;
        }
    };

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-toggle-pass');
        if (btn) {
            e.preventDefault();
            e.stopPropagation();
            const wrapper = btn.closest('.password-input-wrapper');
            if (wrapper) {
                const input = wrapper.querySelector('input');
                if (input) {
                    window.togglePasswordVisibility(input.id, btn);
                }
            }
        }
    });

    // Logout Handler (Server-Side Revocation)
    btnLogout.addEventListener('click', async () => {
        if (state.sessionToken) {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${state.sessionToken}`
                    },
                    body: JSON.stringify({ session_token: state.sessionToken })
                });
            } catch (err) {
                // Ignore logout network errors
            }
        }
        handleUnauthorized();
    });

    // Professional Pure White Vector Medical Icons for 10 Diseases
    const MEDICAL_ICONS_SVG = {
        'anemia': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 2.5C12 2.5 5 11 5 15.5C5 19.09 7.91 22 11.5 22C15.09 22 18 19.09 18 15.5C18 11 12 2.5 12 2.5Z"/><ellipse cx="11.5" cy="15.5" rx="3.5" ry="2.2" stroke-width="1.2" opacity="0.85"/></svg>`,
        'B_cancer': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 3C8 3 5 7 5 11C5 14.5 8 18 12 22C16 18 19 14.5 19 11C19 7 16 3 12 3Z" opacity="0.35"/><path d="M7 19C9.5 16.5 12 11 12 4C12 4 14.5 11 17 19"/><path d="M8.5 10C10.5 12.5 13.5 12.5 15.5 10"/></svg>`,
        'Chronic_liver': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M4 8C3.5 11 4 17 7 19C10 21 16 21 19.5 18C21 16.5 21.5 13 20 10C18.5 7 14 5 9 5.5C6 5.8 4.5 6.5 4 8Z"/><path d="M10 6C12 9 13 14 11 19" stroke-width="1.2" opacity="0.75"/><circle cx="15" cy="12" r="1.5" fill="#ffffff"/></svg>`,
        'diabetes': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C12 2 6 9 6 13C6 16.31 8.69 19 12 19C15.31 19 18 16.31 18 13C18 9 12 2 12 2Z" opacity="0.35"/><path d="M3 13H7L9 9L12 17L15 11L17 13H21"/></svg>`,
        'heart_disease': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 21.35L10.55 20.03C5.4 15.36 2 12.27 2 8.5C2 5.41 4.42 3 7.5 3C9.24 3 10.91 3.81 12 5.08C13.09 3.81 14.76 3 16.5 3C19.58 3 22 5.41 22 8.5C22 12.27 18.6 15.36 13.45 20.03L12 21.35Z" opacity="0.35"/><path d="M3.5 12H7L9 7L12 17L14.5 10L16.5 14H20.5"/></svg>`,
        'Hepatitis': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="7" opacity="0.35"/><circle cx="12" cy="12" r="3"/><path d="M12 2V5M12 19V22M2 12H5M19 12H22M4.93 4.93L7.05 7.05M16.95 16.95L19.07 19.07M4.93 19.07L7.05 16.95M16.95 7.05L19.07 4.93"/></svg>`,
        'Kidney': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M7.5 4C4.5 6 3 9.5 4 14C5 18.5 8.5 20.5 11 19.5C12.5 18.8 11.5 15.5 10 14C8.5 12.5 8.5 9 10 7C11 5.5 10 4 7.5 4Z"/><path d="M16.5 4C19.5 6 21 9.5 20 14C19 18.5 15.5 20.5 13 19.5C11.5 18.8 12.5 15.5 14 14C15.5 12.5 15.5 9 14 7C13 5.5 14 4 16.5 4Z"/></svg>`,
        'lung_cancer': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 4V11M12 11L8 14M12 11L16 14"/><path d="M10 9C7 9.5 4.5 12 4 15.5C3.5 19 6.5 21 9 20.5C11 20.1 11.5 17 11 14.5C10.6 12.5 10.5 10.5 10 9Z" opacity="0.35"/><path d="M14 9C17 9.5 19.5 12 20 15.5C20.5 19 17.5 21 15 20.5C13 20.1 12.5 17 13 14.5C13.4 12.5 13.5 10.5 14 9Z" opacity="0.35"/></svg>`,
        'Parkinsons': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 4C8 4 5 7 5 11C5 13.5 6.5 15.5 8.5 17L9 20H15L15.5 17C17.5 15.5 19 13.5 19 11C19 7 16 4 12 4Z" opacity="0.35"/><path d="M12 7V11M9.5 9.5L14.5 14.5M14.5 9.5L9.5 14.5"/><circle cx="12" cy="12" r="1.5" fill="#ffffff"/></svg>`,
        'Stroke': `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg"><path d="M12 3C7.58 3 4 6.58 4 11C4 13.8 5.44 16.27 7.64 17.72L8.5 21H15.5L16.36 17.72C18.56 16.27 20 13.8 20 11C20 6.58 16.42 3 12 3Z" opacity="0.35"/><path d="M13 7L8.5 13H12.5L11 18L15.5 12H11.5L13 7Z"/></svg>`
    };

    function getDiseaseSVGIcon(diseaseId, fallbackIcon = '🩺') {
        return MEDICAL_ICONS_SVG[diseaseId] || fallbackIcon;
    }

    function updatePatientDetailsState() {
        const patientIdEl = document.getElementById('patient-id');
        const patientNameEl = document.getElementById('patient-name');
        if (patientIdEl) patientIdEl.value = state.patientDetails.patient_id || '';
        if (patientNameEl) patientNameEl.value = state.patientDetails.patient_name || '';
        validatePatientDetails();
    }

    function validatePatientDetails() {
        const patientId = document.getElementById('patient-id')?.value?.trim() || state.patientDetails.patient_id?.trim() || '';
        const patientName = document.getElementById('patient-name')?.value?.trim() || state.patientDetails.patient_name?.trim() || '';
        const isValid = patientId.length > 0 && patientName.length > 0;
        const diseaseCard = document.getElementById('disease-screen-continue');
        if (diseaseCard) {
            diseaseCard.disabled = !isValid;
            diseaseCard.style.opacity = isValid ? '1' : '0.5';
            diseaseCard.title = isValid ? 'Continue to disease selection' : 'Enter Patient ID and Patient Name to continue';
        }
        return isValid;
    }

    function showPatientDetailError(message) {
        const alert = document.getElementById('patient-detail-alert');
        if (alert) {
            alert.textContent = message;
            alert.classList.remove('hidden');
        }
    }

    function hidePatientDetailError() {
        const alert = document.getElementById('patient-detail-alert');
        if (alert) {
            alert.textContent = '';
            alert.classList.add('hidden');
        }
    }

    if (patientDetailsForm) {
        patientDetailsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const patientId = document.getElementById('patient-id').value.trim();
            const patientName = document.getElementById('patient-name').value.trim();
            if (!patientId || !patientName) {
                showPatientDetailError('Patient ID and Patient Name are required.');
                return;
            }
            if (!patientId.trim() || !patientName.trim()) {
                showPatientDetailError('Whitespace-only Patient ID or Patient Name is not allowed.');
                return;
            }
            state.patientDetails = { patient_id: patientId, patient_name: patientName };
            hidePatientDetailError();
            navigateTo('screen-dashboard');
        });
    }

    if (patientDetailsForm) {
        patientDetailsForm.addEventListener('input', validatePatientDetails);
    }

    async function loadDiseases() {
        try {
            const res = await apiFetch('/api/diseases');
            const data = await res.json();
            if (data.status === 'success') {
                state.diseases = data.diseases;
                renderDiseaseGrid(state.diseases);
            }
        } catch (err) {
            diseaseGrid.innerHTML = `<div class="error-msg">Error loading diseases: ${err.message}</div>`;
        }
    }

    function renderDiseaseGrid(diseaseList) {
        diseaseGrid.innerHTML = '';
        diseaseList.forEach(d => {
            const card = document.createElement('div');
            card.className = 'disease-card';
            const iconSvg = getDiseaseSVGIcon(d.id, d.icon);
            card.innerHTML = `
                <div class="card-top">
                    <span class="card-icon">${iconSvg}</span>
                    <span class="card-cat">${d.category}</span>
                </div>
                <h3>${d.title}</h3>
                <p>${d.description}</p>
                <div class="card-footer">
                    <span>${d.total_features} Parameters</span>
                </div>
            `;
            card.addEventListener('click', () => selectDisease(d));
            diseaseGrid.appendChild(card);
        });
    }

    function filterDiseases(query) {
        const cleanQuery = (query || '').toLowerCase().trim();
        const filtered = state.diseases.filter(d =>
            d.title.toLowerCase().includes(cleanQuery) ||
            d.description.toLowerCase().includes(cleanQuery) ||
            d.category.toLowerCase().includes(cleanQuery)
        );
        renderDiseaseGrid(filtered);
    }

    if (diseaseSearchInput) {
        diseaseSearchInput.addEventListener('input', (e) => {
            filterDiseases(e.target.value);
        });

        diseaseSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (validatePatientDetails()) {
                    navigateTo('screen-dashboard');
                } else {
                    navigateTo('screen-patient-details');
                }
            }
        });
    }

    function getCleanDiseaseName(diseaseObj) {
        if (!diseaseObj) return '';
        const rawTitle = diseaseObj.title || diseaseObj.name || '';
        return rawTitle
            .replace(/\s+(Risk\s+Assessment|Classification|Evaluation|Assessment|Risk)$/i, '')
            .trim();
    }

    // --- SCREEN 3: SELECT DISEASE & BUILD CLEAN FORM ---
    function selectDisease(diseaseObj) {
        if (!validatePatientDetails()) {
            showPatientDetailError('Enter Patient ID and Patient Name before selecting a disease.');
            navigateTo('screen-patient-details');
            return;
        }
        state.selectedDisease = diseaseObj;
        formDiseaseTitle.textContent = "Disease Parameters";
        if (formDiseaseDesc) formDiseaseDesc.textContent = "";
        formDiseaseIcon.innerHTML = getDiseaseSVGIcon(diseaseObj.id, diseaseObj.icon);
        formBreadcrumbDisease.textContent = getCleanDiseaseName(diseaseObj);

        hideDatasetBanner();
        renderPatientFields(diseaseObj.features, false);
        navigateTo('screen-patient-form');
    }

    function renderPatientFields(features, fillDemo = false) {
        patientFieldsContainer.innerHTML = '';
        const demoData = state.selectedDisease.demo_patient || {};

        features.forEach(feat => {
            const formGroup = document.createElement('div');
            formGroup.className = 'form-group';

            const label = document.createElement('label');
            label.htmlFor = `input-${feat.name}`;
            label.textContent = feat.label;
            formGroup.appendChild(label);

            let inputEl;
            const val = fillDemo ? (demoData[feat.name] !== undefined ? demoData[feat.name] : '') : '';

            if (feat.type === 'categorical' && feat.options && feat.options.length > 0) {
                inputEl = document.createElement('select');
                inputEl.id = `input-${feat.name}`;
                inputEl.name = feat.name;
                inputEl.required = true;

                const defaultOpt = document.createElement('option');
                defaultOpt.value = '';
                defaultOpt.textContent = `-- Select ${feat.label} --`;
                inputEl.appendChild(defaultOpt);

                feat.options.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    if (fillDemo && String(val) === String(opt.value)) {
                        option.selected = true;
                    }
                    inputEl.appendChild(option);
                });
            } else {
                inputEl = document.createElement('input');
                inputEl.type = 'number';
                inputEl.step = 'any';
                inputEl.id = `input-${feat.name}`;
                inputEl.name = feat.name;
                inputEl.placeholder = feat.placeholder || `Enter ${feat.label}`;
                inputEl.value = val;
                inputEl.required = true;
            }

            formGroup.appendChild(inputEl);
            patientFieldsContainer.appendChild(formGroup);
        });
    }

    btnLoadDemo.addEventListener('click', () => {
        hideDatasetBanner();
        if (state.selectedDisease) {
            renderPatientFields(state.selectedDisease.features, true);
        }
    });

    btnClearFields.addEventListener('click', () => {
        hideDatasetBanner();
        if (state.selectedDisease) {
            renderPatientFields(state.selectedDisease.features, false);
        }
    });

    // ============================================================
    // COMPACT LOAD DATASET ROW MODAL CONTROLLER
    // ============================================================
    const datasetInfoCache = {};

    function hideDatasetBanner() {
        if (datasetLoadedBanner) {
            datasetLoadedBanner.innerHTML = '';
            datasetLoadedBanner.classList.add('hidden');
        }
    }

    function showDatasetSuccessBanner(rowNum) {
        if (!datasetLoadedBanner) return;
        datasetLoadedBanner.innerHTML = `
            <div class="banner-text">
                <span>✓</span>
                <span><strong>Clinical Record ${escapeHtml(rowNum)} loaded successfully.</strong></span>
            </div>
        `;
        datasetLoadedBanner.classList.remove('hidden');

        const clearBtn = document.getElementById('btn-banner-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                hideDatasetBanner();
                if (state.selectedDisease) {
                    renderPatientFields(state.selectedDisease.features, false);
                }
            });
        }
    }

    function showDatasetModalError(msg) {
        if (datasetModalError) {
            datasetModalError.textContent = msg;
            datasetModalError.classList.remove('hidden');
        }
    }

    function hideDatasetModalError() {
        if (datasetModalError) {
            datasetModalError.textContent = '';
            datasetModalError.classList.add('hidden');
        }
    }

    function openDatasetModal() {
        if (!state.selectedDisease) return;

        hideDatasetModalError();
        if (datasetRowInput) {
            datasetRowInput.value = '';
        }
        if (datasetRowHint) {
            datasetRowHint.textContent = '';
        }

        if (modalLoadDataset) {
            modalLoadDataset.classList.remove('hidden');
        }

        if (datasetRowInput) {
            datasetRowInput.focus();
        }
    }

    function closeDatasetModal() {
        hideDatasetModalError();
        if (modalLoadDataset) {
            modalLoadDataset.classList.add('hidden');
        }
    }

    async function handleDatasetRowSubmit(e) {
        if (e) e.preventDefault();
        hideDatasetModalError();

        if (!state.selectedDisease) {
            showDatasetModalError('Please select a disease first.');
            return;
        }

        const diseaseId = state.selectedDisease.id;
        const diseaseName = getCleanDiseaseName(state.selectedDisease) || 'selected disease';
        const rawVal = datasetRowInput ? datasetRowInput.value.trim() : '';

        // 1. Reject empty input
        if (!rawVal) {
            showDatasetModalError('Please enter a dataset row number.');
            if (datasetRowInput) datasetRowInput.focus();
            return;
        }

        // 2. Reject non-numeric row numbers
        if (!/^\d+$/.test(rawVal)) {
            showDatasetModalError('Please enter a valid numeric row number.');
            if (datasetRowInput) datasetRowInput.focus();
            return;
        }

        const rowNum = parseInt(rawVal, 10);

        // 3. Reject row number less than 1
        if (rowNum < 1) {
            showDatasetModalError('Row number must be at least 1.');
            if (datasetRowInput) datasetRowInput.focus();
            return;
        }

        if (btnConfirmLoadDataset) {
            btnConfirmLoadDataset.disabled = true;
            btnConfirmLoadDataset.textContent = 'Loading...';
        }

        try {
            const res = await apiFetch(`/api/dataset/${encodeURIComponent(diseaseId)}/load-row/${rowNum}`);
            const json = await res.json().catch(() => ({}));

            if (!res.ok || json.status !== 'success') {
                let errorMsg = json.detail || json.message || '';
                // Meaningful error: "Dataset not found for [Disease Name]." rather than generic "Not Found"
                if (!errorMsg || errorMsg === 'Not Found' || errorMsg.toLowerCase().includes('not found')) {
                    errorMsg = `Dataset not found for ${diseaseName}.`;
                }
                // Meaningful error: "Row number cannot exceed [N] for this dataset."
                showDatasetModalError(errorMsg);
                if (datasetRowInput) datasetRowInput.focus();
                return;
            }

            const rowData = json.data;
            const features = rowData.features || {};

            // 4. Map retrieved row values into EXISTING patient input fields
            for (let [featName, val] of Object.entries(features)) {
                const inputEl = document.getElementById(`input-${featName}`);
                if (!inputEl) continue;

                if (inputEl.tagName.toLowerCase() === 'select') {
                    let matched = false;
                    for (let opt of inputEl.options) {
                        if (String(opt.value).toLowerCase() === String(val).toLowerCase()) {
                            opt.selected = true;
                            matched = true;
                            break;
                        }
                    }
                    if (!matched && inputEl.options.length > 0) {
                        inputEl.value = val;
                    }
                } else {
                    inputEl.value = val;
                }

                inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                inputEl.dispatchEvent(new Event('change', { bubbles: true }));
            }

            // 5. Close modal and show success message
            closeDatasetModal();
            showDatasetSuccessBanner(rowNum);

        } catch (err) {
            const msg = err.message || '';
            if (msg.includes('Not Found') || msg === 'Not Found') {
                showDatasetModalError(`Dataset not found for ${diseaseName}.`);
            } else {
                showDatasetModalError(msg || `Failed to load row ${rowNum}.`);
            }
        } finally {
            if (btnConfirmLoadDataset) {
                btnConfirmLoadDataset.disabled = false;
                btnConfirmLoadDataset.innerHTML = '<span>LOAD RECORD</span>';
            }
        }
    }

    // Modal event bindings
    if (btnLoadDataset) btnLoadDataset.addEventListener('click', openDatasetModal);
    if (btnCloseDatasetModal) btnCloseDatasetModal.addEventListener('click', closeDatasetModal);
    if (btnCancelDatasetModal) btnCancelDatasetModal.addEventListener('click', closeDatasetModal);
    if (formLoadDatasetRow) formLoadDatasetRow.addEventListener('submit', handleDatasetRowSubmit);

    if (modalLoadDataset) {
        modalLoadDataset.addEventListener('click', (e) => {
            if (e.target === modalLoadDataset) {
                closeDatasetModal();
            }
        });
    }


    // Persistent Main Navigation Click Listeners
    if (navBtnHome) {
        navBtnHome.addEventListener('click', () => {
            navigateTo('screen-home');
        });
    }

    if (navBtnPatientData) {
        navBtnPatientData.addEventListener('click', () => {
            updatePatientDetailsState();
            navigateTo('screen-patient-details');
        });
    }

    if (navBtnAnalysis) {
        navBtnAnalysis.addEventListener('click', () => {
            if (state.selectedDisease) {
                navigateTo('screen-patient-form');
            } else if (validatePatientDetails()) {
                navigateTo('screen-dashboard');
            } else {
                updatePatientDetailsState();
                navigateTo('screen-patient-details');
            }
        });
    }

    if (navBtnReports) {
        navBtnReports.addEventListener('click', () => {
            if (state.currentReport) {
                navigateTo('screen-results');
            } else if (state.selectedDisease) {
                navigateTo('screen-patient-form');
            } else {
                updatePatientDetailsState();
                navigateTo('screen-patient-details');
            }
        });
    }

    if (navBtnHistory) {
        navBtnHistory.addEventListener('click', async () => {
            await loadHistory();
            switchHistoryTab('doctor');
            navigateTo('screen-history');
        });
    }

    if (btnBackToDash) btnBackToDash.addEventListener('click', () => navigateTo('screen-dashboard'));
    if (btnBackToForm) btnBackToForm.addEventListener('click', () => navigateTo('screen-patient-form'));
    if (btnBackToDashboard) btnBackToDashboard.addEventListener('click', () => navigateTo('screen-home'));
    if (btnBackToHistory) btnBackToHistory.addEventListener('click', () => navigateTo('screen-history'));
    if (btnHistoryBackToDiseases) btnHistoryBackToDiseases.addEventListener('click', () => navigateTo('screen-dashboard'));
    if (btnOpenHome) btnOpenHome.addEventListener('click', () => navigateTo('screen-home'));
    if (btnHomeHeroPatientDetails) btnHomeHeroPatientDetails.addEventListener('click', () => {
        updatePatientDetailsState();
        navigateTo('screen-patient-details');
    });
    if (btnHomeQuickstartPatientDetails) btnHomeQuickstartPatientDetails.addEventListener('click', () => {
        updatePatientDetailsState();
        navigateTo('screen-patient-details');
    });
    if (btnOpenPatientDetails) btnOpenPatientDetails.addEventListener('click', () => {
        updatePatientDetailsState();
        navigateTo('screen-patient-details');
    });
    document.querySelector('.brand')?.addEventListener('click', () => {
        if (state.sessionToken) navigateTo('screen-home');
    });

    if (tabDoctorHistory) tabDoctorHistory.addEventListener('click', () => switchHistoryTab('doctor'));
    if (tabPatientHistory) tabPatientHistory.addEventListener('click', () => switchHistoryTab('patient'));

    function switchHistoryTab(tabName) {
        state.activeHistoryTab = tabName;
        if (tabName === 'doctor') {
            tabDoctorHistory?.classList.add('active');
            tabPatientHistory?.classList.remove('active');
            viewDoctorHistory?.classList.add('active');
            viewDoctorHistory?.classList.remove('hidden');
            viewPatientHistory?.classList.remove('active');
            viewPatientHistory?.classList.add('hidden');
            renderDoctorHistoryList();
        } else {
            tabPatientHistory?.classList.add('active');
            tabDoctorHistory?.classList.remove('active');
            viewPatientHistory?.classList.add('active');
            viewPatientHistory?.classList.remove('hidden');
            viewDoctorHistory?.classList.remove('active');
            viewDoctorHistory?.classList.add('hidden');
            populatePatientSelector();
            if (state.selectedPatientId) {
                renderPatientHistory(state.selectedPatientId);
            } else {
                renderPatientHistoryEmpty();
            }
        }
    }

    if (patientHistoryBtn) patientHistoryBtn.addEventListener('click', async () => {
        await loadHistory();
        switchHistoryTab('doctor');
        navigateTo('screen-history');
    });

    // Clear History Modal Handlers
    function openClearHistoryModal() {
        if (clearHistoryModalNotice) {
            clearHistoryModalNotice.textContent = '';
            clearHistoryModalNotice.classList.add('hidden');
        }
        if (modalClearHistory) {
            modalClearHistory.classList.remove('hidden');
        }
    }

    function closeClearHistoryModal() {
        if (clearHistoryModalNotice) {
            clearHistoryModalNotice.textContent = '';
            clearHistoryModalNotice.classList.add('hidden');
        }
        if (modalClearHistory) {
            modalClearHistory.classList.add('hidden');
        }
    }

    if (btnClearHistory) {
        btnClearHistory.addEventListener('click', openClearHistoryModal);
    }
    if (btnCloseClearHistoryModal) {
        btnCloseClearHistoryModal.addEventListener('click', closeClearHistoryModal);
    }
    if (btnCancelClearHistory) {
        btnCancelClearHistory.addEventListener('click', closeClearHistoryModal);
    }
    if (modalClearHistory) {
        modalClearHistory.addEventListener('click', (e) => {
            if (e.target === modalClearHistory) {
                closeClearHistoryModal();
            }
        });
    }
    if (btnConfirmClearHistory) {
        btnConfirmClearHistory.addEventListener('click', async () => {
            try {
                const res = await apiFetch('/api/history', { method: 'DELETE' });
                if (res.ok) {
                    const data = await res.json().catch(() => ({}));
                    if (data.status === 'success') {
                        state.historyItems = [];
                        closeClearHistoryModal();
                        await loadHistory();
                        return;
                    }
                }
                if (clearHistoryModalNotice) {
                    clearHistoryModalNotice.textContent = 'The existing backend does not currently provide a clear-history operation. History records remain unchanged.';
                    clearHistoryModalNotice.classList.remove('hidden');
                }
            } catch (err) {
                if (clearHistoryModalNotice) {
                    clearHistoryModalNotice.textContent = 'The existing backend does not currently provide a clear-history operation. History records remain unchanged.';
                    clearHistoryModalNotice.classList.remove('hidden');
                }
            }
        });
    }

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatDiseaseName(slug) {
        if (!slug) return 'Clinical Disease';
        const found = (state.diseases || []).find(d => d.id === slug);
        if (found && found.name) return found.name;
        return slug.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }

    function formatHistoryDate(isoString) {
        if (!isoString) return 'N/A';
        try {
            const d = new Date(isoString);
            if (isNaN(d.getTime())) return isoString;
            const day = d.getDate();
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const month = monthNames[d.getMonth()];
            const year = d.getFullYear();
            let hours = d.getHours();
            const minutes = d.getMinutes().toString().padStart(2, '0');
            const ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            hours = hours ? hours : 12;
            return `${day} ${month} ${year}, ${hours}:${minutes} ${ampm}`;
        } catch {
            return isoString;
        }
    }

    function getDoctorDisplayName(docName) {
        let name = (docName || state.doctorInfo?.doctor_name || state.doctorInfo?.username || 'Physician').trim();
        if (!name.toLowerCase().startsWith('dr.') && !name.toLowerCase().startsWith('dr ')) {
            name = 'Dr. ' + name;
        }
        return name;
    }

    function updateDoctorHistoryHeader() {
        const doc = state.doctorInfo;
        const nameEl = document.getElementById('history-doctor-name');
        const specEl = document.getElementById('history-doctor-specialty');
        const avatarEl = document.getElementById('history-doctor-avatar');
        const patientsCountEl = document.getElementById('stat-patients-count');
        const analysesCountEl = document.getElementById('stat-analyses-count');
        const subSummaryEl = document.getElementById('history-sub-summary');

        if (nameEl) nameEl.textContent = getDoctorDisplayName(doc?.doctor_name);
        if (specEl) specEl.textContent = doc?.specialty || 'Clinical Specialist';
        if (avatarEl) avatarEl.textContent = getDoctorAvatarEmoji(doc);

        const totalAnalyses = state.historyItems.length;
        const uniquePatients = new Set(
            state.historyItems
                .map(i => (i.patient_id || '').trim().toLowerCase())
                .filter(Boolean)
        ).size;

        if (patientsCountEl) patientsCountEl.textContent = uniquePatients;
        if (analysesCountEl) analysesCountEl.textContent = totalAnalyses;
        if (subSummaryEl) {
            subSummaryEl.textContent = `Displaying ${totalAnalyses} saved ${totalAnalyses === 1 ? 'evaluation' : 'evaluations'} across ${uniquePatients} unique ${uniquePatients === 1 ? 'patient' : 'patients'}.`;
        }
    }

    async function loadHistory() {
        try {
            const res = await apiFetch('/api/history');
            const data = await res.json();
            if (data.status === 'success') {
                state.historyItems = data.items || [];
                updateDoctorHistoryHeader();
                populatePatientSelector();
                if (state.activeHistoryTab === 'patient' && state.selectedPatientId) {
                    renderPatientHistory(state.selectedPatientId);
                } else {
                    renderDoctorHistoryList();
                }
            }
        } catch (err) {
            if (historyList) {
                historyList.innerHTML = `<div class="error-msg">Unable to load history: ${escapeHtml(err.message)}</div>`;
            }
        }
    }

    function renderDoctorHistoryList() {
        if (!historyList) return;
        updateDoctorHistoryHeader();

        const query = (historySearchInput?.value || '').trim().toLowerCase();
        const filtered = state.historyItems.filter(item => {
            const patientId = (item.patient_id || '').toLowerCase();
            const patientName = (item.patient_name || '').toLowerCase();
            return !query || patientId.includes(query) || patientName.includes(query);
        });

        if (!filtered.length) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state-icon">📋</span>
                    <h3>No diagnostic analyses found</h3>
                    <p>No prior analyses match your search criteria. Try adjusting the search query.</p>
                </div>`;
            return;
        }

        historyList.innerHTML = filtered.map(item => {
            const pred = item.prediction || 'Unknown';
            const predLower = pred.toLowerCase();
            const isPresence = predLower.includes('presence') || predLower.includes('high');
            const isAbsence = predLower.includes('absence') || predLower.includes('low');
            const predClass = isPresence ? 'pred-presence' : isAbsence ? 'pred-absence' : 'pred-unknown';
            const predIcon = isPresence ? '⚠️' : isAbsence ? '✅' : 'ℹ️';

            const probText = item.model_probability != null
                ? (Number(item.model_probability) <= 1 ? (item.model_probability * 100).toFixed(1) + '%' : Number(item.model_probability).toFixed(1) + '%')
                : 'N/A';
            const formattedDate = formatHistoryDate(item.analysis_timestamp);
            const evalDoctorName = getDoctorDisplayName(item.doctor_name);

            return `
                <div class="history-card" data-id="${item.id}">
                    <div class="history-card-header">
                        <div class="history-patient-info">
                            <div class="history-patient-avatar">👤</div>
                            <div class="history-patient-meta">
                                <span class="history-patient-name">${escapeHtml(item.patient_name || 'Anonymous Patient')}</span>
                                <span class="history-patient-id-badge">ID: ${escapeHtml(item.patient_id || 'N/A')}</span>
                            </div>
                        </div>
                        <div class="history-doctor-attribution">
                            <span>👨‍⚕️ Evaluated by ${escapeHtml(evalDoctorName)}</span>
                        </div>
                    </div>
                    <div class="history-card-grid">
                        <div class="history-grid-col-left">
                            <div class="clinical-field-row">
                                <span class="field-icon">🩺</span>
                                <span class="field-label">Target Disease:</span>
                                <span class="field-value highlight">${escapeHtml(formatDiseaseName(item.disease))}</span>
                            </div>
                            <div class="clinical-field-row">
                                <span class="field-icon">📈</span>
                                <span class="field-label">Model Confidence:</span>
                                <span class="field-value">${probText}</span>
                            </div>
                            <div class="clinical-field-row">
                                <span class="field-icon">📅</span>
                                <span class="field-label">Analysis Date:</span>
                                <span class="field-value timestamp">${formattedDate}</span>
                            </div>
                        </div>
                        <div class="history-grid-col-right">
                            <div class="prediction-status-box ${predClass}">
                                <div class="prediction-box-title">Diagnostic Prediction</div>
                                <div class="prediction-status-badge">
                                    <span class="pred-symbol">${predIcon}</span>
                                    <span class="pred-text">${escapeHtml(pred)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="history-card-footer">
                        <button type="button" class="btn btn-primary btn-sm btn-view-report" data-id="${item.id}">
                            <span>📊 View Full Report →</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        historyList.querySelectorAll('.btn-view-report').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = Number(btn.dataset.id);
                await fetchAndOpenReport(id);
            });
        });
    }

    function populatePatientSelector() {
        if (!patientHistorySelect) return;
        const currentVal = state.selectedPatientId || patientHistorySelect.value;
        const patientMap = new Map();
        (state.historyItems || []).forEach(item => {
            if (item.patient_id && !patientMap.has(item.patient_id)) {
                patientMap.set(item.patient_id, {
                    id: item.patient_id,
                    name: item.patient_name || item.patient_id,
                    count: 0
                });
            }
            if (item.patient_id && patientMap.has(item.patient_id)) {
                patientMap.get(item.patient_id).count++;
            }
        });

        const sortedPatients = Array.from(patientMap.values()).sort((a, b) => a.name.localeCompare(b.name));

        patientHistorySelect.innerHTML = '<option value="">-- Choose Patient --</option>' +
            sortedPatients.map(p => `
                <option value="${escapeHtml(p.id)}" ${p.id === currentVal ? 'selected' : ''}>
                    ${escapeHtml(p.name)} (${escapeHtml(p.id)}) — ${p.count} ${p.count === 1 ? 'analysis' : 'analyses'}
                </option>
            `).join('');
    }

    async function selectPatientInHistory(patientId) {
        state.selectedPatientId = patientId;
        switchHistoryTab('patient');
        if (patientHistorySelect) {
            patientHistorySelect.value = patientId;
        }
        await renderPatientHistory(patientId);
    }

    if (patientHistorySelect) {
        patientHistorySelect.addEventListener('change', async (e) => {
            const patientId = e.target.value;
            state.selectedPatientId = patientId;
            await renderPatientHistory(patientId);
        });
    }

    function renderPatientHistoryEmpty() {
        if (patientSummaryBanner) {
            patientSummaryBanner.classList.add('hidden');
            patientSummaryBanner.innerHTML = '';
        }
        if (patientHistoryList) {
            patientHistoryList.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state-icon">👤</span>
                    <h3>Select a patient to view longitudinal history</h3>
                    <p>Choose a patient from the dropdown above, or click "View Patient History" on any card in the Doctor History view to inspect their chronological diagnostic progression.</p>
                </div>`;
        }
    }

    async function renderPatientHistory(patientId) {
        if (!patientId) {
            renderPatientHistoryEmpty();
            return;
        }

        let records = [];
        try {
            const res = await apiFetch(`/api/history/patient/${encodeURIComponent(patientId)}`);
            const data = await res.json();
            if (data.status === 'success' && Array.isArray(data.items)) {
                records = data.items;
            }
        } catch (err) {
            records = state.historyItems.filter(i => (i.patient_id || '').toLowerCase() === patientId.toLowerCase());
        }

        if (!records.length) {
            records = state.historyItems.filter(i => (i.patient_id || '').toLowerCase() === patientId.toLowerCase());
        }

        // Chronological order: earliest first (Analysis #1, #2, etc.)
        const chronologicalRecords = [...records].sort((a, b) => {
            const tA = new Date(a.analysis_timestamp).getTime() || 0;
            const tB = new Date(b.analysis_timestamp).getTime() || 0;
            return tA - tB;
        });

        const patientName = chronologicalRecords[0]?.patient_name || patientId;

        // Render Patient Summary Banner
        if (patientSummaryBanner) {
            patientSummaryBanner.classList.remove('hidden');
            patientSummaryBanner.innerHTML = `
                <div class="patient-summary-left">
                    <div class="history-patient-avatar">👤</div>
                    <div class="patient-summary-details">
                        <h3>${escapeHtml(patientName)}</h3>
                        <span class="patient-summary-id">Patient Identifier: <strong>${escapeHtml(patientId)}</strong></span>
                    </div>
                </div>
                <div class="patient-summary-stats">
                    <div class="patient-stat-pill">
                        <span>Total Analyses:</span>
                        <strong>${chronologicalRecords.length}</strong>
                    </div>
                    <div class="patient-stat-pill">
                        <span>Timeline:</span>
                        <strong>Chronological</strong>
                    </div>
                </div>
            `;
        }

        if (patientHistoryList) {
            if (!chronologicalRecords.length) {
                patientHistoryList.innerHTML = `
                    <div class="empty-state">
                        <span class="empty-state-icon">📁</span>
                        <h3>No records found for this patient</h3>
                        <p>No prior analyses were found for patient ID ${escapeHtml(patientId)}.</p>
                    </div>`;
                return;
            }

            patientHistoryList.innerHTML = chronologicalRecords.map((item, idx) => {
                const pred = item.prediction || 'Unknown';
                const predLower = pred.toLowerCase();
                const isPresence = predLower.includes('presence') || predLower.includes('high');
                const isAbsence = predLower.includes('absence') || predLower.includes('low');
                const predClass = isPresence ? 'pred-presence' : isAbsence ? 'pred-absence' : 'pred-unknown';
                const predIcon = isPresence ? '⚠️' : isAbsence ? '✅' : 'ℹ️';

                const probText = item.model_probability != null
                    ? (Number(item.model_probability) <= 1 ? (item.model_probability * 100).toFixed(1) + '%' : Number(item.model_probability).toFixed(1) + '%')
                    : 'N/A';
                const formattedDate = formatHistoryDate(item.analysis_timestamp);
                const seqNumber = idx + 1;
                const seqTag = idx === 0 ? `Analysis #${seqNumber} (Baseline)` :
                    idx === chronologicalRecords.length - 1 ? `Analysis #${seqNumber} (Latest)` :
                        `Analysis #${seqNumber}`;
                const evalDoctorName = getDoctorDisplayName(item.doctor_name);

                return `
                    <div class="history-card" data-id="${item.id}">
                        <div class="history-card-header">
                            <div class="history-patient-info">
                                <span class="history-timeline-badge">${seqTag}</span>
                                <span class="history-patient-id-badge">ID: ${escapeHtml(item.patient_id)}</span>
                            </div>
                            <div class="history-doctor-attribution">
                                <span>👨‍⚕️ Evaluated by ${escapeHtml(evalDoctorName)}</span>
                            </div>
                        </div>
                        <div class="history-card-grid">
                            <div class="history-grid-col-left">
                                <div class="clinical-field-row">
                                    <span class="field-icon">🩺</span>
                                    <span class="field-label">Target Disease:</span>
                                    <span class="field-value highlight">${escapeHtml(formatDiseaseName(item.disease))}</span>
                                </div>
                                <div class="clinical-field-row">
                                    <span class="field-icon">📈</span>
                                    <span class="field-label">Model Confidence:</span>
                                    <span class="field-value">${probText}</span>
                                </div>
                                <div class="clinical-field-row">
                                    <span class="field-icon">📅</span>
                                    <span class="field-label">Analysis Date:</span>
                                    <span class="field-value timestamp">${formattedDate}</span>
                                </div>
                            </div>
                            <div class="history-grid-col-right">
                                <div class="prediction-status-box ${predClass}">
                                    <div class="prediction-box-title">Diagnostic Prediction</div>
                                    <div class="prediction-status-badge">
                                        <span class="pred-symbol">${predIcon}</span>
                                        <span class="pred-text">${escapeHtml(pred)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="history-card-footer">
                            <button type="button" class="btn btn-primary btn-sm btn-view-report" data-id="${item.id}">
                                <span>📊 View Full Report →</span>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            patientHistoryList.querySelectorAll('.btn-view-report').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    const id = Number(btn.dataset.id);
                    await fetchAndOpenReport(id);
                });
            });
        }
    }

    async function fetchAndOpenReport(id) {
        let item = state.historyItems.find(entry => entry.id === id);
        if (!item || !item.report_data) {
            try {
                const res = await apiFetch(`/api/history/${id}`);
                const data = await res.json();
                if (data.status === 'success' && data.item) {
                    item = data.item;
                }
            } catch (err) {
                console.error("Failed to load saved report:", err);
            }
        }
        if (item && item.report_data) {
            state.selectedHistoryItem = item;
            openSavedReport(item);
        } else {
            alert("Unable to open the requested saved report.");
        }
    }

    function openSavedReport(item) {
        if (!item || !item.report_data) {
            if (patientHistoryDetail) {
                patientHistoryDetail.classList.remove('hidden');
                patientHistoryDetail.innerHTML = '<div class="alert-danger">Saved report payload was not found.</div>';
            }
            return;
        }

        const report = item.report_data;
        if (item.patient_id && !report.patient_id) report.patient_id = item.patient_id;
        if (item.patient_name && !report.patient_name) report.patient_name = item.patient_name;
        if (item.trust_confidence_data && !report.trust_confidence_data) {
            report.trust_confidence_data = item.trust_confidence_data;
        }
        if (item.clinical_input_data) {
            state.currentPatientFeatures = typeof item.clinical_input_data === 'string'
                ? JSON.parse(item.clinical_input_data)
                : { ...item.clinical_input_data };
        }
        state.currentReport = report;
        renderReportResults(report, true);
        navigateTo('screen-results');
    }

    if (historySearchInput) {
        historySearchInput.addEventListener('input', renderDoctorHistoryList);
    }

    // --- SCREEN 4: SUBMIT FORM & RENDER RESULTS (PROTECTED ROUTE) ---
    patientAnalysisForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(patientAnalysisForm);
        const patientFeatures = {};

        for (let [key, val] of formData.entries()) {
            if (!isNaN(val) && val.trim() !== '') {
                patientFeatures[key] = parseFloat(val);
            } else {
                patientFeatures[key] = val;
            }
        }

        if (!state.patientDetails.patient_id || !state.patientDetails.patient_name) {
            showPatientDetailError('Patient ID and Patient Name are required before analysis.');
            navigateTo('screen-patient-details');
            return;
        }

        navigateTo('screen-results');
        reportContainer.innerHTML = '<div class="loading-spinner">Analyzing Patient Data...</div>';
        state.currentPatientFeatures = { ...patientFeatures };

        try {
            const res = await apiFetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    disease: state.selectedDisease.id,
                    patient_features: patientFeatures,
                    patient_metadata: {
                        patient_id: state.patientDetails.patient_id,
                        patient_name: state.patientDetails.patient_name,
                        target_disease: state.selectedDisease.id
                    }
                })
            });

            const data = await res.json();
            if (data.status === 'success') {
                state.currentReport = data.report;
                state.currentPatientFeatures = data.patient_features || patientFeatures;
                renderReportResults(data.report);
            } else {
                reportContainer.innerHTML = `<div class="error-msg">Pipeline Error: ${data.detail}</div>`;
            }
        } catch (err) {
            reportContainer.innerHTML = `<div class="error-msg">Analysis Request Failed: ${err.message}</div>`;
        }
    });

    function ensureEvidenceStylesInjected() {
        if (document.getElementById('injected-cdss-evidence-styles')) return;
        const style = document.createElement('style');
        style.id = 'injected-cdss-evidence-styles';
        style.textContent = `
            .evidence-comparison-container {
                display: flex !important;
                flex-direction: column !important;
                gap: 20px !important;
                width: 100% !important;
                margin-top: 14px !important;
                box-sizing: border-box !important;
            }
            .evidence-cards-row {
                display: grid !important;
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
                gap: 20px !important;
                width: 100% !important;
                align-items: stretch !important;
                box-sizing: border-box !important;
            }
            .evidence-card {
                background: rgba(15, 23, 42, 0.85) !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                border-radius: 14px !important;
                padding: 24px !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-start !important;
                height: 100% !important;
                min-height: 220px !important;
                box-sizing: border-box !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                position: relative !important;
                overflow: hidden !important;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            .evidence-card:hover {
                transform: translateY(-3px) !important;
                border-color: rgba(0, 242, 254, 0.35) !important;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 242, 254, 0.15) !important;
                background: rgba(28, 39, 66, 0.90) !important;
            }
            .btn-toggle-evidence-details,
            .evidence-details-toggle {
                display: inline-flex !important;
                align-items: center !important;
                gap: 8px !important;
                background: rgba(15, 23, 42, 0.75) !important;
                border: 1px solid rgba(0, 242, 254, 0.35) !important;
                color: #00f2fe !important;
                padding: 10px 20px !important;
                border-radius: 20px !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 0.88rem !important;
                font-weight: 600 !important;
                cursor: pointer !important;
                transition: all 0.25s ease !important;
                align-self: flex-start !important;
                box-shadow: 0 0 15px rgba(0, 242, 254, 0.15) !important;
                outline: none !important;
                text-decoration: none !important;
            }
            .btn-toggle-evidence-details:hover,
            .evidence-details-toggle:hover {
                background: rgba(0, 242, 254, 0.12) !important;
                border-color: #00f2fe !important;
                color: #ffffff !important;
                box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
            }
            .btn-toggle-evidence-details.active,
            .evidence-details-toggle.active {
                background: rgba(0, 242, 254, 0.2) !important;
                border-color: #00f2fe !important;
                color: #ffffff !important;
            }
            .evidence-technical-drawer.hidden {
                display: none !important;
            }
            .trust-accordion-container {
                display: flex !important;
                flex-direction: column !important;
                gap: 14px !important;
                width: 100% !important;
                margin-top: 16px !important;
                box-sizing: border-box !important;
            }
            .trust-accordion-item {
                background: rgba(15, 23, 42, 0.85) !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                border-radius: 14px !important;
                overflow: hidden !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .trust-accordion-item:hover {
                border-color: rgba(0, 242, 254, 0.4) !important;
                box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45), 0 0 15px rgba(0, 242, 254, 0.12) !important;
                background: rgba(24, 34, 58, 0.90) !important;
            }
            .trust-accordion-item.active {
                border-color: rgba(0, 242, 254, 0.55) !important;
                box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 242, 254, 0.18) !important;
                background: rgba(18, 26, 45, 0.95) !important;
            }
            .trust-accordion-header {
                width: 100% !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                padding: 18px 24px !important;
                background: transparent !important;
                border: none !important;
                color: #f1f5f9 !important;
                font-family: 'Outfit', sans-serif !important;
                font-size: 1.08rem !important;
                font-weight: 700 !important;
                cursor: pointer !important;
                text-align: left !important;
                transition: background 0.2s ease, color 0.2s ease !important;
                box-sizing: border-box !important;
                outline: none !important;
            }
            .trust-accordion-header:hover {
                color: #00f2fe !important;
            }
            .trust-accordion-item.active .trust-accordion-header {
                border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
                color: #00f2fe !important;
            }
            .accordion-title-group {
                display: flex !important;
                align-items: center !important;
                gap: 12px !important;
            }
            .accordion-icon {
                font-size: 1.35rem !important;
                line-height: 1 !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            .accordion-title {
                color: inherit !important;
                letter-spacing: 0.3px !important;
            }
            .accordion-indicator {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 32px !important;
                height: 32px !important;
                border-radius: 50% !important;
                background: rgba(255, 255, 255, 0.06) !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                color: #00f2fe !important;
                font-size: 1.3rem !important;
                font-weight: 700 !important;
                line-height: 1 !important;
                transition: all 0.25s ease !important;
                user-select: none !important;
                flex-shrink: 0 !important;
            }
            .trust-accordion-header:hover .accordion-indicator {
                background: rgba(0, 242, 254, 0.15) !important;
                border-color: #00f2fe !important;
                box-shadow: 0 0 10px rgba(0, 242, 254, 0.3) !important;
            }
            .trust-accordion-item.active .accordion-indicator {
                background: rgba(0, 242, 254, 0.25) !important;
                border-color: #00f2fe !important;
                color: #ffffff !important;
                box-shadow: 0 0 12px rgba(0, 242, 254, 0.35) !important;
            }
            .trust-accordion-collapse {
                max-height: 0;
                overflow: hidden;
                opacity: 0;
                transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease;
                box-sizing: border-box;
            }
            .trust-accordion-item.active .trust-accordion-collapse {
                opacity: 1;
            }
            .trust-accordion-body {
                padding: 22px 24px 24px 24px !important;
                background: rgba(11, 15, 25, 0.65) !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 16px !important;
                box-sizing: border-box !important;
            }
            .trust-status-badge {
                display: inline-flex !important;
                align-items: center !important;
                gap: 8px !important;
                padding: 6px 16px !important;
                border-radius: 20px !important;
                font-size: 0.85rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.8px !important;
                text-transform: uppercase !important;
                align-self: flex-start !important;
            }
            .trust-status-badge.status-conflict {
                background: rgba(239, 68, 68, 0.18) !important;
                color: #fca5a5 !important;
                border: 1px solid rgba(239, 68, 68, 0.45) !important;
            }
            .trust-status-badge.status-aligned {
                background: rgba(16, 185, 129, 0.18) !important;
                color: #6ee7b7 !important;
                border: 1px solid rgba(16, 185, 129, 0.45) !important;
            }
            .trust-status-badge.status-neutral {
                background: rgba(148, 163, 184, 0.18) !important;
                color: #cbd5e1 !important;
                border: 1px solid rgba(148, 163, 184, 0.4) !important;
            }
            .trust-counts-grid {
                display: grid !important;
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
                gap: 12px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .trust-count-pill {
                background: rgba(15, 23, 42, 0.8) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 10px !important;
                padding: 12px 16px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                box-sizing: border-box !important;
            }
            .trust-count-pill .count-pill-label {
                font-size: 0.85rem !important;
                color: #94a3b8 !important;
                font-weight: 600 !important;
            }
            .trust-count-pill .count-pill-value {
                font-family: 'Outfit', sans-serif !important;
                font-size: 1.4rem !important;
                font-weight: 800 !important;
            }
            .trust-count-pill.pill-supporting {
                border-left: 4px solid #10b981 !important;
            }
            .trust-count-pill.pill-supporting .count-pill-value {
                color: #10b981 !important;
            }
            .trust-count-pill.pill-conflicting {
                border-left: 4px solid #ef4444 !important;
            }
            .trust-count-pill.pill-conflicting .count-pill-value {
                color: #ef4444 !important;
            }
            .trust-count-pill.pill-neutral {
                border-left: 4px solid #94a3b8 !important;
            }
            .trust-count-pill.pill-neutral .count-pill-value {
                color: #94a3b8 !important;
            }
            .trust-explanation-box {
                background: rgba(0, 0, 0, 0.25) !important;
                border-left: 3px solid #00f2fe !important;
                border-radius: 0 8px 8px 0 !important;
                padding: 10px 14px !important;
                margin-top: 2px !important;
            }
            .trust-explanation-text {
                font-size: 0.9rem !important;
                line-height: 1.5 !important;
                color: #f1f5f9 !important;
                font-style: italic !important;
                margin: 0 !important;
            }
            .trust-mini-label {
                font-size: 0.76rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.9px !important;
                color: #94a3b8 !important;
                margin-bottom: 4px !important;
            }
            .trust-hero-val {
                font-family: 'Outfit', sans-serif !important;
                font-size: 2rem !important;
                font-weight: 800 !important;
                line-height: 1.2 !important;
                letter-spacing: -0.5px !important;
            }
            .trust-hero-val.consensus-contradictory {
                color: #f59e0b !important;
            }
            .trust-hero-val.consensus-high {
                color: #10b981 !important;
            }
            .trust-hero-val.consensus-moderate {
                color: #00f2fe !important;
            }
            .trust-hero-val.consensus-low {
                color: #ef4444 !important;
            }
            /* --- 5-Tier Consensus Analysis Status Indicators --- */
            .consensus-levels-wrapper {
                display: flex !important;
                flex-direction: column !important;
                gap: 10px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .consensus-levels-grid {
                display: grid !important;
                grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
                gap: 10px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            @media (max-width: 992px) {
                .consensus-levels-grid {
                    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)) !important;
                }
            }
            .consensus-level-card {
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                padding: 14px 10px !important;
                border-radius: 10px !important;
                min-height: 74px !important;
                box-sizing: border-box !important;
                cursor: default !important;
                user-select: none !important;
                transition: all 0.25s ease !important;
            }
            .consensus-card-header {
                display: flex !important;
                align-items: center !important;
                gap: 6px !important;
                margin-bottom: 6px !important;
            }
            .consensus-status-dot {
                width: 7px !important;
                height: 7px !important;
                border-radius: 50% !important;
                display: inline-block !important;
                flex-shrink: 0 !important;
            }
            .consensus-status-badge {
                font-size: 0.68rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.6px !important;
                text-transform: uppercase !important;
                padding: 2px 7px !important;
                border-radius: 4px !important;
                line-height: 1 !important;
            }
            .consensus-level-title {
                font-family: 'Outfit', sans-serif !important;
                font-size: 0.78rem !important;
                letter-spacing: 0.5px !important;
                line-height: 1.25 !important;
                text-transform: uppercase !important;
            }
            .consensus-level-card.inactive {
                background: rgba(15, 23, 42, 0.55) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                box-shadow: none !important;
                opacity: 0.55 !important;
            }
            .consensus-level-card.inactive .consensus-status-dot {
                background: #475569 !important;
                box-shadow: none !important;
            }
            .consensus-level-card.inactive .consensus-status-badge {
                color: #64748b !important;
                background: rgba(255, 255, 255, 0.03) !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                font-weight: 600 !important;
            }
            .consensus-level-card.inactive .consensus-level-title {
                color: #64748b !important;
                font-weight: 600 !important;
            }
            .consensus-level-card.tier-emerald.active {
                background: rgba(16, 185, 129, 0.16) !important;
                border: 1.5px solid #10b981 !important;
                box-shadow: 0 0 16px rgba(16, 185, 129, 0.3), inset 0 0 12px rgba(16, 185, 129, 0.08) !important;
                opacity: 1 !important;
            }
            .consensus-level-card.tier-emerald.active .consensus-status-dot {
                background: #10b981 !important;
                box-shadow: 0 0 8px #10b981, 0 0 12px rgba(16, 185, 129, 0.6) !important;
            }
            .consensus-level-card.tier-emerald.active .consensus-status-badge {
                color: #34d399 !important;
                background: rgba(16, 185, 129, 0.22) !important;
                border: 1px solid rgba(16, 185, 129, 0.45) !important;
            }
            .consensus-level-card.tier-emerald.active .consensus-level-title {
                color: #34d399 !important;
                font-weight: 700 !important;
                text-shadow: 0 0 10px rgba(16, 185, 129, 0.35) !important;
            }
            .consensus-level-card.tier-cyan.active {
                background: rgba(0, 242, 254, 0.16) !important;
                border: 1.5px solid #00f2fe !important;
                box-shadow: 0 0 16px rgba(0, 242, 254, 0.3), inset 0 0 12px rgba(0, 242, 254, 0.08) !important;
                opacity: 1 !important;
            }
            .consensus-level-card.tier-cyan.active .consensus-status-dot {
                background: #00f2fe !important;
                box-shadow: 0 0 8px #00f2fe, 0 0 12px rgba(0, 242, 254, 0.6) !important;
            }
            .consensus-level-card.tier-cyan.active .consensus-status-badge {
                color: #00f2fe !important;
                background: rgba(0, 242, 254, 0.22) !important;
                border: 1px solid rgba(0, 242, 254, 0.45) !important;
            }
            .consensus-level-card.tier-cyan.active .consensus-level-title {
                color: #00f2fe !important;
                font-weight: 700 !important;
                text-shadow: 0 0 10px rgba(0, 242, 254, 0.35) !important;
            }
            .consensus-level-card.tier-amber.active {
                background: rgba(245, 158, 11, 0.16) !important;
                border: 1.5px solid #f59e0b !important;
                box-shadow: 0 0 16px rgba(245, 158, 11, 0.3), inset 0 0 12px rgba(245, 158, 11, 0.08) !important;
                opacity: 1 !important;
            }
            .consensus-level-card.tier-amber.active .consensus-status-dot {
                background: #f59e0b !important;
                box-shadow: 0 0 8px #f59e0b, 0 0 12px rgba(245, 158, 11, 0.6) !important;
            }
            .consensus-level-card.tier-amber.active .consensus-status-badge {
                color: #fbbf24 !important;
                background: rgba(245, 158, 11, 0.22) !important;
                border: 1px solid rgba(245, 158, 11, 0.45) !important;
            }
            .consensus-level-card.tier-amber.active .consensus-level-title {
                color: #fbbf24 !important;
                font-weight: 700 !important;
                text-shadow: 0 0 10px rgba(245, 158, 11, 0.35) !important;
            }
            .trust-hero-val.trust-score-hero {
                color: #00f2fe !important;
                text-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
            }
            .trust-metric-callout {
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                font-size: 1rem !important;
                color: #cbd5e1 !important;
            }
            .trust-metric-callout .callout-label {
                font-weight: 600 !important;
                color: #94a3b8 !important;
            }
            .trust-metric-callout .callout-value {
                font-family: 'Outfit', sans-serif !important;
                font-weight: 800 !important;
                color: #f1f5f9 !important;
                font-size: 1.25rem !important;
            }
            .trust-components-section {
                display: flex !important;
                flex-direction: column !important;
                gap: 10px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .trust-components-title {
                font-size: 0.76rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.8px !important;
                color: #64748b !important;
            }
            .trust-components-grid {
                display: grid !important;
                grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
                gap: 12px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .trust-component-card {
                background: rgba(15, 23, 42, 0.8) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 10px !important;
                padding: 12px 14px !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 4px !important;
                box-sizing: border-box !important;
                transition: transform 0.2s ease, border-color 0.2s ease !important;
            }
            .trust-component-card:hover {
                transform: translateY(-2px) !important;
                border-color: rgba(0, 242, 254, 0.3) !important;
            }
            .component-card-top {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 6px !important;
            }
            .component-name {
                font-size: 0.74rem !important;
                font-weight: 600 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                color: #94a3b8 !important;
            }
            .component-weight {
                font-size: 0.72rem !important;
                font-weight: 700 !important;
                color: #00f2fe !important;
                background: rgba(0, 242, 254, 0.12) !important;
                padding: 1px 6px !important;
                border-radius: 8px !important;
            }
            .component-value {
                font-family: 'Outfit', sans-serif !important;
                font-size: 1.35rem !important;
                font-weight: 800 !important;
                color: #f1f5f9 !important;
                line-height: 1.2 !important;
                margin: 2px 0 !important;
            }
            .component-desc {
                font-size: 0.74rem !important;
                color: #64748b !important;
            }
            .trust-fused-row {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 10px !important;
                padding-top: 4px !important;
                border-top: 1px solid rgba(255, 255, 255, 0.06) !important;
            }
            .fused-chip {
                background: rgba(15, 23, 42, 0.6) !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                border-radius: 8px !important;
                padding: 6px 12px !important;
                font-size: 0.8rem !important;
                display: inline-flex !important;
                align-items: center !important;
                gap: 6px !important;
            }
            .fused-chip .chip-label {
                color: #64748b !important;
                font-weight: 500 !important;
            }
            .fused-chip .chip-val {
                color: #f1f5f9 !important;
                font-weight: 700 !important;
            }
            .interpretation-subsections-container {
                display: flex !important;
                flex-direction: column !important;
                gap: 20px !important;
                width: 100% !important;
                margin-top: 16px !important;
                box-sizing: border-box !important;
            }
            .interpretation-subsection {
                background: rgba(15, 23, 42, 0.85) !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                border-radius: 14px !important;
                padding: 22px 24px !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                box-sizing: border-box !important;
                width: 100% !important;
                transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
            }
            .interpretation-subsection:hover {
                border-color: rgba(0, 242, 254, 0.35) !important;
                box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45), 0 0 15px rgba(0, 242, 254, 0.1) !important;
            }
            .interpretation-subheading {
                display: flex !important;
                align-items: center !important;
                gap: 10px !important;
                padding-bottom: 12px !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
                margin-bottom: 16px !important;
            }
            .interpretation-subheading .subheading-icon {
                font-size: 1.3rem !important;
                line-height: 1 !important;
            }
            .interpretation-subheading .subheading-text {
                font-family: 'Outfit', sans-serif !important;
                font-size: 1.05rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px !important;
                color: #f1f5f9 !important;
                text-transform: uppercase !important;
            }
            .interpretation-prediction-grid {
                display: flex !important;
                flex-direction: column !important;
                gap: 10px !important;
            }
            .interpretation-data-row {
                display: flex !important;
                align-items: baseline !important;
                gap: 10px !important;
                font-size: 0.98rem !important;
                color: #cbd5e1 !important;
            }
            .interpretation-data-row .data-label {
                font-weight: 600 !important;
                color: #94a3b8 !important;
                min-width: 110px !important;
            }
            .interpretation-data-row .data-value {
                font-weight: 700 !important;
                color: #f1f5f9 !important;
                font-size: 1.05rem !important;
            }
            .interpretation-data-row .data-value.prediction-val {
                color: #00f2fe !important;
                font-size: 1.15rem !important;
            }
            .interpretation-data-row .data-value.probability-val {
                font-family: 'Outfit', sans-serif !important;
                color: #f1f5f9 !important;
                font-size: 1.25rem !important;
            }
            .interpretation-data-row .data-value.risk-val {
                padding: 2px 10px !important;
                border-radius: 12px !important;
                font-size: 0.85rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                display: inline-block !important;
            }
            .interpretation-data-row .data-value.risk-val.risk-high {
                background: rgba(239, 68, 68, 0.18) !important;
                color: #fca5a5 !important;
                border: 1px solid rgba(239, 68, 68, 0.4) !important;
            }
            .interpretation-data-row .data-value.risk-val.risk-low {
                background: rgba(16, 185, 129, 0.18) !important;
                color: #6ee7b7 !important;
                border: 1px solid rgba(16, 185, 129, 0.4) !important;
            }
            .shap-features-container {
                display: flex !important;
                flex-direction: column !important;
                gap: 14px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .shap-feature-block {
                background: rgba(11, 15, 25, 0.65) !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-left: 4px solid #00f2fe !important;
                border-radius: 10px !important;
                padding: 14px 18px !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 6px !important;
                box-sizing: border-box !important;
                transition: transform 0.2s ease, border-color 0.2s ease !important;
            }
            .shap-feature-block:hover {
                transform: translateX(3px) !important;
                border-color: rgba(0, 242, 254, 0.35) !important;
            }
            .shap-feature-block.impact-increase-border {
                border-left-color: #ef4444 !important;
            }
            .shap-feature-block.impact-decrease-border {
                border-left-color: #10b981 !important;
            }
            .shap-field-line {
                display: flex !important;
                align-items: baseline !important;
                gap: 8px !important;
                font-size: 0.92rem !important;
                line-height: 1.4 !important;
            }
            .shap-field-label {
                font-weight: 600 !important;
                color: #94a3b8 !important;
                min-width: 100px !important;
                flex-shrink: 0 !important;
            }
            .shap-field-value {
                color: #f1f5f9 !important;
                font-weight: 500 !important;
            }
            .shap-field-value.feature-name {
                font-family: 'Outfit', sans-serif !important;
                font-size: 1.05rem !important;
                font-weight: 700 !important;
                color: #ffffff !important;
            }
            .shap-field-value.shap-val {
                font-family: 'Outfit', sans-serif !important;
                font-weight: 800 !important;
                color: #00f2fe !important;
                font-size: 0.98rem !important;
            }
            .shap-field-value.impact-val {
                font-weight: 700 !important;
            }
            .shap-field-value.impact-val.impact-increase {
                color: #f87171 !important;
            }
            .shap-field-value.impact-val.impact-decrease {
                color: #34d399 !important;
            }
            .shap-field-line.explanation-line {
                margin-top: 2px !important;
                padding-top: 4px !important;
                border-top: 1px dashed rgba(255, 255, 255, 0.06) !important;
            }
            .shap-field-value.explanation-text {
                color: #cbd5e1 !important;
                font-style: italic !important;
                line-height: 1.5 !important;
            }
            .final-system-decision-card {
                background: rgba(11, 15, 25, 0.85) !important;
                border: 1px solid rgba(255, 255, 255, 0.14) !important;
                border-radius: 14px !important;
                padding: 30px 34px !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 16px !important;
                box-sizing: border-box !important;
            }
            .final-system-decision-card.decision-card-not-detected {
                border-left: 5px solid #10b981 !important;
                box-shadow: 0 6px 28px rgba(0, 0, 0, 0.45), 0 0 20px rgba(16, 185, 129, 0.1) !important;
            }
            .final-system-decision-card.decision-card-detected {
                border-left: 5px solid #ef4444 !important;
                box-shadow: 0 6px 28px rgba(0, 0, 0, 0.45), 0 0 20px rgba(239, 68, 68, 0.1) !important;
            }
            .llm-clinical-explanation-section {
                display: flex !important;
                flex-direction: column !important;
                gap: 16px !important;
                padding-top: 0 !important;
                border-top: none !important;
                margin-top: 0 !important;
                width: 100% !important;
            }
            .llm-explanation-title {
                font-family: 'Outfit', sans-serif !important;
                font-size: 1.35rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.6px !important;
                color: #ffffff !important;
                display: flex !important;
                align-items: center !important;
                gap: 10px !important;
            }
            .llm-explanation-paragraph {
                font-size: 1.15rem !important;
                line-height: 1.85 !important;
                color: #f1f5f9 !important;
                background: rgba(15, 23, 42, 0.7) !important;
                border: 1px solid rgba(0, 242, 254, 0.22) !important;
                border-left: 4px solid #00f2fe !important;
                border-radius: 10px !important;
                padding: 24px 28px !important;
                margin: 0 !important;
                text-align: left !important;
                letter-spacing: 0.2px !important;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 4px 20px rgba(0, 0, 0, 0.3) !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 16px !important;
            }
            .llm-explanation-p {
                margin: 0 !important;
                padding: 0 !important;
                line-height: 1.85 !important;
                color: #f1f5f9 !important;
            }
            .download-options-grid {
                display: grid !important;
                grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
                gap: 16px !important;
                margin-top: 18px !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .download-card-btn {
                display: flex !important;
                align-items: center !important;
                gap: 14px !important;
                background: rgba(15, 23, 42, 0.75) !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                border-radius: 12px !important;
                padding: 18px 20px !important;
                color: #f1f5f9 !important;
                cursor: pointer !important;
                text-align: left !important;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
                outline: none !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }
            .download-card-btn:hover {
                background: rgba(15, 23, 42, 0.95) !important;
                border-color: rgba(0, 242, 254, 0.45) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), 0 0 16px rgba(0, 242, 254, 0.15) !important;
            }
            .download-card-icon {
                font-size: 1.6rem !important;
                line-height: 1 !important;
                flex-shrink: 0 !important;
            }
            .download-card-title {
                font-family: 'Outfit', sans-serif !important;
                font-size: 0.96rem !important;
                font-weight: 700 !important;
                color: #f1f5f9 !important;
                letter-spacing: -0.2px !important;
            }
            @media (max-width: 768px) {
                .evidence-cards-row {
                    grid-template-columns: 1fr !important;
                    gap: 16px !important;
                }
                .trust-counts-grid {
                    grid-template-columns: 1fr !important;
                }
                .trust-components-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
                }
                .download-options-grid {
                    grid-template-columns: 1fr !important;
                }
                .trust-accordion-header {
                    padding: 14px 18px !important;
                    font-size: 0.98rem !important;
                }
                .trust-accordion-body {
                    padding: 16px 18px !important;
                }
                .trust-hero-val {
                    font-size: 1.6rem !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
    ensureEvidenceStylesInjected();

    function generateDynamicClinicalInterpretation(params) {
        const {
            diseaseName = 'Disease',
            isDetected = false,
            detectionStatus = 'NOT DETECTED',
            probFormatted = '0.00%',
            cleanRiskTier = 'Low Risk',
            shapFeatures = [],
            mappedNode = 'Disease',
            totalTriples = 0,
            supportingEvidence = 0,
            conflictingEvidence = 0,
            neutralEvidence = 0,
            consensusLevel = 'MODERATE_CONSENSUS',
            trustScore = null,
            fusedConfidence = null,
            hasConflictingSignals = false,
            counterfactualData = null
        } = params || {};

        const diseasePhrase = String(diseaseName || 'the target condition').toLowerCase().trim();

        // 1. System Prediction & Main Influencing Factors (Questions A & B)
        const predLead = isDetected
            ? `The assessment indicates an elevated predicted likelihood of ${diseasePhrase} based on the evaluated clinical parameters, with an estimated model probability of ${probFormatted} (${cleanRiskTier || 'High Risk'}).`
            : `The assessment indicates a low predicted likelihood of ${diseasePhrase} based on the evaluated clinical parameters, with an estimated model probability of ${probFormatted} (${cleanRiskTier || 'Low Risk'}).`;

        let factorLead = '';
        const incList = shapFeatures.filter(f => f.impact && f.impact.toLowerCase().includes('increase')).map(f => f.feature);
        const decList = shapFeatures.filter(f => f.impact && f.impact.toLowerCase().includes('decrease')).map(f => f.feature);
        const allNames = shapFeatures.map(f => f.feature);

        if (incList.length > 0 && decList.length > 0) {
            factorLead = `The primary clinical factors influencing this prediction include ${allNames.join(', ')}, with ${incList.join(', ')} contributing toward higher risk and ${decList.join(', ')} contributing toward lower risk.`;
        } else if (incList.length > 0) {
            factorLead = `The primary clinical factors influencing this prediction include ${incList.join(', ')}, all contributing toward higher risk.`;
        } else if (decList.length > 0) {
            factorLead = `The primary clinical factors contributing to this prediction include ${decList.join(', ')}, all contributing toward lower risk.`;
        } else {
            factorLead = `Feature attribution analysis evaluated input parameters without individual dominant directional drivers.`;
        }
        const paragraph1 = `${predLead} ${factorLead}`;

        // 2. Biomedical Evidence & Consistency/Contradiction Analysis (Questions C & D, Requirements 11, 12, 13, 14)
        let paragraph2 = '';
        const isInsufficientEv = (totalTriples === 0) || (consensusLevel && consensusLevel.toUpperCase().includes('INSUFFICIENT')) || (supportingEvidence === 0 && conflictingEvidence === 0);
        const isStronglySupportingEv = supportingEvidence > 0 && conflictingEvidence === 0 && !hasConflictingSignals;
        const isMixedEv = supportingEvidence > 0 && conflictingEvidence > 0;

        if (hasConflictingSignals || isMixedEv) {
            paragraph2 = `Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '${mappedNode}' identified ${totalTriples} evidence relationships, comprising ${supportingEvidence} supporting, ${conflictingEvidence} conflicting, and ${neutralEvidence} neutral items. The presence of both supporting and conflicting signals indicates that the available biomedical evidence is not fully consistent with the model prediction. Because divergent evidence items were identified across the knowledge graph, the system incorporates this disagreement directly into the evidence-aware evaluation to inform clinical review.`;
        } else if (isInsufficientEv) {
            paragraph2 = `Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '${mappedNode}' indicates that available biomedical evidence is limited (${totalTriples} evidence items retrieved). The system explicitly notes that current biomedical literature in the knowledge graph provides insufficient data to independently confirm or refute the prediction, underscoring the need for careful clinical assessment.`;
        } else if (isStronglySupportingEv) {
            paragraph2 = `Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '${mappedNode}' identified ${totalTriples} evidence relationships (${supportingEvidence} supporting, 0 conflicting, and ${neutralEvidence} neutral items). The available biomedical evidence aligns with the model prediction, reinforcing the pathophysiological consistency of the evaluated clinical parameters.`;
        } else {
            paragraph2 = `Biomedical evidence retrieved from the PrimeKG knowledge graph mapped to '${mappedNode}' identified ${totalTriples} evidence relationships (${supportingEvidence} supporting, ${conflictingEvidence} conflicting, and ${neutralEvidence} neutral items), providing contextual literature grounding for the clinical evaluation.`;
        }

        // 3. Trust/Consensus Analysis, Decision Fusion & Overall Interpretation (Questions E & F)
        const consensusDisplay = (consensusLevel || 'MODERATE_CONSENSUS').replace(/_/g, ' ');
        const trustScoreFormatted = (trustScore !== undefined && trustScore !== null) ? Number(trustScore).toFixed(4) : 'N/A';
        const fusedConfFormatted = (fusedConfidence !== undefined && fusedConfidence !== null) ? Number(fusedConfidence).toFixed(4) : 'N/A';

        let cfText = '';
        if (counterfactualData && Array.isArray(counterfactualData.modified_features) && counterfactualData.modified_features.length > 0) {
            const modNames = counterfactualData.modified_features.map(m => m.label || m.feature).join(', ');
            const origP = counterfactualData.original?.probability_formatted || '';
            const simP = counterfactualData.counterfactual?.probability_formatted || '';
            if (origP && simP) {
                cfText = ` In counterfactual simulation, adjusting ${modNames} altered the estimated probability from ${origP} to ${simP}, demonstrating sensitivity to actionable clinical target adjustments.`;
            }
        }

        const paragraph3 = `Multi-source consensus evaluation established a ${consensusDisplay} classification with an overall system trust score of ${trustScoreFormatted} and a fused confidence score of ${fusedConfFormatted}.${cfText} Overall, the system considers the available evidence and model output together to provide an evidence-aware decision-support interpretation. This result is intended strictly to assist the physician and should be interpreted alongside comprehensive clinical judgment.`;

        return {
            paragraph1,
            paragraph2,
            paragraph3,
            paragraphs: [paragraph1, paragraph2, paragraph3],
            fullText: `${paragraph1}\n\n${paragraph2}\n\n${paragraph3}`
        };
    }
    window.generateDynamicClinicalInterpretation = generateDynamicClinicalInterpretation;

    function renderReportResults(report, isSaved = false) {
        ensureEvidenceStylesInjected();
        if (isSaved) {
            if (btnBackToHistory) btnBackToHistory.classList.remove('hidden');
            if (btnBackToForm) btnBackToForm.classList.add('hidden');
        } else {
            if (btnBackToHistory) btnBackToHistory.classList.add('hidden');
            if (btnBackToForm) btnBackToForm.classList.remove('hidden');
        }

        const sections = report.sections || [];
        const metadata = report.patient_metadata || {};
        const isCapped = report.is_capped_by_contradiction || report.contradiction_flag_raised;

        function formatShapFeatureName(name) {
            if (!name) return 'Feature';
            return String(name).replace(/_+/g, ' ').trim();
        }

        function getTop5ShapFeatures(rep) {
            let list = [];
            const kf = (rep.sections || []).find(s => s.section_id === 'key_factors');
            if (Array.isArray(kf?.items) && kf.items.length > 0) {
                list = [...kf.items];
            } else if (Array.isArray(rep.shap_summary?.top_attributions) && rep.shap_summary.top_attributions.length > 0) {
                list = [...rep.shap_summary.top_attributions];
            } else if (Array.isArray(rep.shap_data?.top_attributions) && rep.shap_data.top_attributions.length > 0) {
                list = [...rep.shap_data.top_attributions];
            } else if (Array.isArray(rep.shap_explanation?.top_attributions) && rep.shap_explanation.top_attributions.length > 0) {
                list = [...rep.shap_explanation.top_attributions];
            } else if (Array.isArray(rep.all_attributions) && rep.all_attributions.length > 0) {
                list = [...rep.all_attributions];
            }

            list.sort((a, b) => {
                const valA = Math.abs(parseFloat(a.shap_value ?? a.attribution_value ?? 0) || 0);
                const valB = Math.abs(parseFloat(b.shap_value ?? b.attribution_value ?? 0) || 0);
                return valB - valA;
            });

            return list.slice(0, 5);
        }

        const sharedTop5ShapFeatures = getTop5ShapFeatures(report);

        let html = '';

        sections.forEach(sec => {
            const id = sec.section_id;
            const title = sec.title;
            const text = sec.summary_text;
            const metrics = sec.metrics || {};

            if (id === 'prediction' || id === 'disease_prediction') {
                const badgeClass = (metrics.risk_tier === 'HIGH_RISK') ? 'increases_risk' : 'decreases_risk';
                const predClass = metrics.predicted_class;
                let clinicalResult = 'Absence';
                if (predClass !== undefined && predClass !== null) {
                    clinicalResult = (predClass == 1 || predClass === '1') ? 'Presence' : 'Absence';
                } else if (metrics.risk_tier) {
                    clinicalResult = (metrics.risk_tier === 'HIGH_RISK') ? 'Presence' : 'Absence';
                } else if (metrics.predicted_result) {
                    const resStr = String(metrics.predicted_result).toLowerCase();
                    clinicalResult = (resStr === '1' || resStr === 'presence' || resStr === 'high_risk' || resStr === 'disease' || resStr === 'positive') ? 'Presence' : 'Absence';
                }

                const currentPatientId = report.patient_id
                    || metadata.patient_id
                    || report.json_payload?.patient_id
                    || report.json_payload?.patient_metadata?.patient_id
                    || (isSaved ? state.selectedHistoryItem?.patient_id : null)
                    || state.patientDetails?.patient_id
                    || state.selectedHistoryItem?.patient_id
                    || '1';

                const currentPatientName = report.patient_name
                    || metadata.patient_name
                    || report.json_payload?.patient_name
                    || report.json_payload?.patient_metadata?.patient_name
                    || (isSaved ? state.selectedHistoryItem?.patient_name : null)
                    || state.patientDetails?.patient_name
                    || state.selectedHistoryItem?.patient_name
                    || 'Patient';

                html += `
                    <div class="report-section">
                        <div class="section-header-row">
                            <h3 class="section-title">🩺 DISEASE PREDICTION</h3>
                            <span class="impact-badge ${badgeClass}">${metrics.risk_tier || 'EVALUATED'}</span>
                        </div>
                        <div class="prediction-highlight-box">
                            <div class="summary-patient-meta">
                                <div class="patient-meta-line">
                                    <span class="patient-meta-label">Patient ID:</span>
                                    <span class="patient-meta-value">${escapeHtml(currentPatientId)}</span>
                                </div>
                                <div class="patient-meta-line">
                                    <span class="patient-meta-label">Patient Name:</span>
                                    <span class="patient-meta-value">${escapeHtml(currentPatientName)}</span>
                                </div>
                            </div>
                            <div class="summary-metrics-grid">
                                <div class="summary-metric-item">
                                    <div class="metric-number">${escapeHtml(metrics.disease || state.selectedDisease?.id || 'disease')}</div>
                                    <div class="metric-label">Disease Target</div>
                                </div>
                                <div class="summary-metric-item">
                                    <div class="metric-number">${escapeHtml(clinicalResult)}</div>
                                    <div class="metric-label">Clinical Result</div>
                                </div>
                                <div class="summary-metric-item">
                                    <div class="metric-number">${escapeHtml(metrics.model_probability || 'N/A')}</div>
                                    <div class="metric-label">Model Probability</div>
                                </div>
                            </div>
                        </div>
                        <div class="prediction-whatif-cta">
                            <div>
                                <strong style="color: #00f2fe; font-size: 0.88rem; display: block;">Simulate Clinical Variations</strong>
                                <span class="whatif-cta-hint">Evaluate how altering clinical lab values affects disease probability</span>
                            </div>
                            <button type="button" class="btn btn-whatif btn-trigger-whatif" id="btn-section-whatif">
                                <span class="btn-whatif-icon">🔄</span>
                                <span>What-If Analysis</span>
                            </button>
                        </div>
                    </div>
                `;
            } else if (id === 'key_factors') {
                const items = sharedTop5ShapFeatures.length > 0 ? sharedTop5ShapFeatures : (sec.items || []).slice(0, 5);
                let tableRows = '';
                items.forEach(attr => {
                    const rawImpact = String(attr.impact_direction || 'neutral').toLowerCase().replace(/_/g, ' ');
                    const shapNum = parseFloat(attr.shap_value ?? attr.attribution_value ?? 0);
                    const isDecrease = rawImpact.includes('decrease') || shapNum < 0;
                    const impactClass = isDecrease ? 'decreases_risk' : (rawImpact.includes('increase') || shapNum > 0 ? 'increases_risk' : 'neutral');
                    const impactLabel = isDecrease ? 'Decreases risk' : (impactClass === 'increases_risk' ? 'Increases risk' : (attr.impact_direction || 'Neutral'));
                    const cleanName = formatShapFeatureName(attr.feature_name);
                    const rawVal = attr.raw_value !== undefined ? attr.raw_value : (attr.feature_value !== undefined ? attr.feature_value : 'N/A');
                    const riskDirection = isDecrease ? 'Lower risk' : 'Higher risk';

                    tableRows += `
                        <tr>
                            <td><strong>${escapeHtml(cleanName)}</strong></td>
                            <td><span class="impact-badge ${impactClass}">${escapeHtml(impactLabel)}</span></td>
                            <td>${riskDirection} · Patient value: ${escapeHtml(rawVal)}</td>
                        </tr>
                    `;
                });

                html += `
                    <div class="report-section key-factors-section">
                        <h3 class="section-title key-factors-title" style="justify-content: flex-start !important; text-align: left !important; width: 100% !important;">🔍 KEY RISK FACTORS</h3>
                        <p class="key-factors-subtitle" style="text-align: left !important; margin: 0 0 16px 0 !important;">These are the main factors influencing the predicted disease risk.</p>
                        <div class="shap-table-container" style="width: 100% !important; display: flex !important; justify-content: center !important; overflow-x: auto !important; margin: 16px auto 0 auto !important;">
                            <table class="shap-table" style="width: 100% !important; margin: 0 auto !important;">
                                <thead>
                                    <tr>
                                        <th>RISK FACTOR</th>
                                        <th>EFFECT ON RISK</th>
                                        <th>PATIENT VALUE</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${tableRows || '<tr><td colspan="3">No risk factors identified.</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            } else if (id === 'biomedical_evidence') {
                const totalTriples = metrics.total_evidence_triples ?? metrics.total_triples_found ?? metrics.total_triples ?? 0;
                const sup = metrics.supporting_evidence ?? metrics.supporting_count ?? 0;
                const conf = metrics.conflicting_evidence ?? metrics.conflicting_count ?? 0;
                const neu = metrics.neutral_evidence ?? metrics.neutral_count ?? 0;

                html += `
                    <div class="report-section">
                        <h3 class="section-title">🧬 BIOMEDICAL EVIDENCE (PRIMEKG)</h3>
                        <p>Retrieved biomedical evidence from the PrimeKG knowledge graph for the selected disease.</p>
                        <div class="evidence-counts-grid">
                            <div class="count-card">
                                <div class="metric-number">${totalTriples}</div>
                                <div class="metric-label">Total Evidence</div>
                            </div>
                            <div class="count-card">
                                <div class="metric-number" style="color: var(--accent-green);">${sup}</div>
                                <div class="metric-label">Supporting</div>
                            </div>
                            <div class="count-card">
                                <div class="metric-number" style="color: var(--accent-red);">${conf}</div>
                                <div class="metric-label">Conflicting</div>
                            </div>
                            <div class="count-card">
                                <div class="metric-number" style="color: var(--text-secondary);">${neu}</div>
                                <div class="metric-label">Neutral</div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (id === 'evidence_comparison') {
                const predSec = sections.find(s => s.section_id === 'prediction' || s.section_id === 'disease_prediction');
                const bioSec = sections.find(s => s.section_id === 'biomedical_evidence');
                const predMetrics = predSec?.metrics || {};
                const bioMetrics = bioSec?.metrics || {};

                // --- CARD 1: Model Prediction ---
                let probVal = predMetrics.model_probability;
                if (probVal == null && text) {
                    const match = text.match(/risk probability of\s+([0-9.]+[%]?)/i);
                    if (match) probVal = match[1];
                }
                let probFormatted = 'N/A';
                if (probVal != null) {
                    if (typeof probVal === 'number') {
                        probFormatted = (probVal <= 1 ? (probVal * 100).toFixed(2) : probVal.toFixed(2)) + '%';
                    } else {
                        const s = String(probVal).trim();
                        probFormatted = s.endsWith('%') ? s : s + '%';
                    }
                }

                let clinicalResult = 'Absence';
                if (predMetrics.predicted_class !== undefined && predMetrics.predicted_class !== null) {
                    clinicalResult = (predMetrics.predicted_class == 1 || predMetrics.predicted_class === '1') ? 'Presence' : 'Absence';
                } else if (predMetrics.predicted_result) {
                    const rawVal = String(predMetrics.predicted_result).trim().toLowerCase();
                    if (rawVal === 'notckd' || rawVal === '0' || rawVal === 'absence' || rawVal === 'negative' || rawVal === 'benign') {
                        clinicalResult = 'Absence';
                    } else if (rawVal === 'ckd' || rawVal === '1' || rawVal === 'presence' || rawVal === 'positive' || rawVal === 'malignant') {
                        clinicalResult = 'Presence';
                    } else {
                        clinicalResult = String(predMetrics.predicted_result).trim();
                    }
                } else if (predMetrics.risk_tier) {
                    clinicalResult = (predMetrics.risk_tier === 'HIGH_RISK') ? 'Presence' : 'Absence';
                }

                let riskTierStr = predMetrics.risk_tier ? String(predMetrics.risk_tier).replace(/_/g, ' ') : '';
                if (!riskTierStr && text) {
                    const match = text.match(/\(([A-Za-z0-9_]+)\s*\/\s*([A-Za-z0-9_]+)\)/);
                    if (match) {
                        if (!clinicalResult) clinicalResult = match[1];
                        riskTierStr = match[2].replace(/_/g, ' ');
                    }
                }
                const cleanRiskTier = riskTierStr
                    ? riskTierStr.toLowerCase().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
                    : (clinicalResult === 'Presence' ? 'High Risk' : 'Low Risk');
                const tierClass = cleanRiskTier.toLowerCase().includes('high') ? 'tier-high' : 'tier-low';

                // --- CARD 2: Biomedical Evidence ---
                let findingsCount = metrics.biomedical_graph_triples_count ?? bioMetrics.total_evidence_triples ?? bioMetrics.total_triples_found;
                if (findingsCount == null && text) {
                    const match = text.match(/([0-9]+)\s+total graph evidence triples/i);
                    if (match) findingsCount = parseInt(match[1], 10);
                }
                if (findingsCount == null) findingsCount = 0;
                const card2Value = `${findingsCount} ${findingsCount === 1 ? 'Finding' : 'Findings'}`;
                const card2Subtitle = 'Knowledge Graph';

                // --- CARD 3: Evidence Agreement ---
                let supCount = metrics.supporting_evidence_count ?? metrics.supporting_signals ?? bioMetrics.supporting_evidence ?? bioMetrics.supporting_count ?? 0;
                let confCount = metrics.conflicting_evidence_count ?? metrics.conflicting_signals ?? bioMetrics.conflicting_evidence ?? bioMetrics.conflicting_count ?? 0;
                let neuCount = metrics.neutral_evidence_count ?? metrics.neutral_signals ?? bioMetrics.neutral_evidence ?? bioMetrics.neutral_count ?? 0;
                let shapCount = metrics.shap_attribution_count ?? 0;
                let totalSignals = metrics.total_combined_signals ?? (supCount + confCount + neuCount);

                if (supCount === 0 && confCount === 0 && text) {
                    const match = text.match(/\(([0-9]+)\s+supporting,\s*([0-9]+)\s+conflicting,\s*([0-9]+)\s+neutral\)/i);
                    if (match) {
                        supCount = parseInt(match[1], 10);
                        confCount = parseInt(match[2], 10);
                        neuCount = parseInt(match[3], 10);
                    }
                    const sigMatch = text.match(/([0-9]+)\s+total signals evaluated/i);
                    if (sigMatch) totalSignals = parseInt(sigMatch[1], 10);
                    const shapMatch = text.match(/([0-9]+)\s+SHAP feature attributions/i);
                    if (shapMatch) shapCount = parseInt(shapMatch[1], 10);
                }

                const decisionClassification = report.decision_classification || metrics.decision_classification || '';
                const consensusLevel = report.consensus_level || report.trust_confidence_data?.consensus_level || '';

                const isInsufficient = (
                    decisionClassification === 'INSUFFICIENT_EVIDENCE' ||
                    consensusLevel === 'INSUFFICIENT_EVIDENCE' ||
                    (supCount === 0 && confCount === 0)
                );

                let agreementLabel = 'SUPPORTING';
                let badgeClass = 'badge-aligned badge-supporting';
                let cardAgreementClass = 'agreement-aligned';
                let evidenceLineText = 'Supporting';
                let conclusionText = 'Biomedical evidence supports the model prediction.';
                let conclusionClass = 'conclusion-aligned conclusion-supporting';
                let card3BorderShadow = 'border: 1px solid rgba(16, 185, 129, 0.45) !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 15px rgba(16, 185, 129, 0.1) !important;';
                let badgeInlineStyle = 'background: rgba(16, 185, 129, 0.18) !important; color: #6ee7b7 !important; border: 1px solid rgba(16, 185, 129, 0.45) !important;';
                let conclusionBorderColor = '#10b981';

                if (isInsufficient) {
                    agreementLabel = 'LIMITED / INSUFFICIENT';
                    badgeClass = 'badge-neutral badge-insufficient';
                    cardAgreementClass = 'agreement-neutral';
                    evidenceLineText = 'Limited/Insufficient';
                    conclusionText = 'Available biomedical evidence is insufficient to establish strong agreement.';
                    conclusionClass = 'conclusion-neutral conclusion-insufficient';
                    card3BorderShadow = 'border: 1px solid rgba(148, 163, 184, 0.35) !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;';
                    badgeInlineStyle = 'background: rgba(148, 163, 184, 0.18) !important; color: #cbd5e1 !important; border: 1px solid rgba(148, 163, 184, 0.4) !important;';
                    conclusionBorderColor = '#64748b';
                } else if (confCount > 0 && supCount > 0) {
                    agreementLabel = 'MIXED';
                    badgeClass = 'badge-mixed';
                    cardAgreementClass = 'agreement-mixed';
                    evidenceLineText = 'Supporting + Conflicting';
                    conclusionText = 'Biomedical evidence partially conflicts with the model prediction.';
                    conclusionClass = 'conclusion-mixed';
                    card3BorderShadow = 'border: 1px solid rgba(245, 158, 11, 0.45) !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 15px rgba(245, 158, 11, 0.1) !important;';
                    badgeInlineStyle = 'background: rgba(245, 158, 11, 0.18) !important; color: #fbbf24 !important; border: 1px solid rgba(245, 158, 11, 0.45) !important;';
                    conclusionBorderColor = '#f59e0b';
                } else if (confCount > 0 && supCount === 0) {
                    agreementLabel = 'CONFLICTING';
                    badgeClass = 'badge-conflicting';
                    cardAgreementClass = 'agreement-conflicting';
                    evidenceLineText = 'Conflicting';
                    conclusionText = 'Biomedical evidence conflicts with the model prediction.';
                    conclusionClass = 'conclusion-conflicting';
                    card3BorderShadow = 'border: 1px solid rgba(239, 68, 68, 0.45) !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 15px rgba(239, 68, 68, 0.1) !important;';
                    badgeInlineStyle = 'background: rgba(239, 68, 68, 0.18) !important; color: #fca5a5 !important; border: 1px solid rgba(239, 68, 68, 0.45) !important;';
                    conclusionBorderColor = '#ef4444';
                } else {
                    // supCount > 0 && confCount === 0
                    agreementLabel = 'SUPPORTING';
                    badgeClass = 'badge-aligned badge-supporting';
                    cardAgreementClass = 'agreement-aligned';
                    evidenceLineText = 'Supporting';
                    conclusionText = 'Biomedical evidence supports the model prediction.';
                    conclusionClass = 'conclusion-aligned conclusion-supporting';
                    card3BorderShadow = 'border: 1px solid rgba(16, 185, 129, 0.45) !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 15px rgba(16, 185, 129, 0.1) !important;';
                    badgeInlineStyle = 'background: rgba(16, 185, 129, 0.18) !important; color: #6ee7b7 !important; border: 1px solid rgba(16, 185, 129, 0.45) !important;';
                    conclusionBorderColor = '#10b981';
                }

                // Resolve disease name dynamically from existing report / state / metrics
                let resolvedDiseaseName = predMetrics.disease_display_name
                    || report.disease_name
                    || state.selectedDisease?.name
                    || (predMetrics.disease ? formatDiseaseName(predMetrics.disease) : null)
                    || (report.disease ? formatDiseaseName(report.disease) : null)
                    || (metadata.disease ? formatDiseaseName(metadata.disease) : null)
                    || (state.selectedDisease?.id ? formatDiseaseName(state.selectedDisease.id) : null)
                    || 'Clinical Disease';

                if (resolvedDiseaseName.includes('_')) {
                    resolvedDiseaseName = formatDiseaseName(resolvedDiseaseName);
                }

                // Resolve prediction / risk tier dynamically
                let predictionVal = cleanRiskTier;
                if (!predictionVal || predictionVal.toLowerCase() === 'evaluated') {
                    predictionVal = (clinicalResult === 'Presence' ? 'High Risk' : 'Low Risk');
                }
                const modelLineText = `${resolvedDiseaseName} / ${predictionVal}`;

                // --- Contradiction Alert & Safety Constraint (inside expandable section only) ---
                let contradictionNoticeHtml = '';
                if (confCount > 0 && supCount > 0) {
                    contradictionNoticeHtml = `
                        <div class="evidence-notice-box" style="background: rgba(245, 158, 11, 0.12) !important; border: 1px solid rgba(245, 158, 11, 0.4) !important; border-radius: 8px !important; padding: 12px 16px !important; box-sizing: border-box !important;">
                            <div class="notice-title" style="font-size: 0.95rem !important; font-weight: 700 !important; color: #fbbf24 !important; margin-bottom: 4px !important; display: flex !important; align-items: center !important; gap: 6px !important;">⚠️ Evidence is mixed</div>
                            <p class="notice-text" style="font-size: 0.86rem !important; color: #f1f5f9 !important; margin: 0 !important; line-height: 1.5 !important;">Some evidence supports the model prediction while other evidence conflicts with it.</p>
                        </div>
                    `;
                } else if (confCount > 0 && supCount === 0) {
                    contradictionNoticeHtml = `
                        <div class="evidence-notice-box" style="background: rgba(239, 68, 68, 0.12) !important; border: 1px solid rgba(239, 68, 68, 0.4) !important; border-radius: 8px !important; padding: 12px 16px !important; box-sizing: border-box !important;">
                            <div class="notice-title" style="font-size: 0.95rem !important; font-weight: 700 !important; color: #fca5a5 !important; margin-bottom: 4px !important; display: flex !important; align-items: center !important; gap: 6px !important;">⚠️ Contradictory evidence detected</div>
                            <p class="notice-text" style="font-size: 0.86rem !important; color: #f1f5f9 !important; margin: 0 !important; line-height: 1.5 !important;">Biomedical evidence directly conflicts with the model prediction.</p>
                        </div>
                    `;
                }

                // Visible red/pink "Safety constraint active..." banner removed from Evidence view
                // Underlying safety constraint logic remains active
                let safetyConstraintHtml = '';

                html += `
                    <div class="report-section">
                        <h3 class="section-title">⚖️ EVIDENCE & PREDICTION COMPARISON</h3>
                        <div class="evidence-comparison-container" style="display: flex !important; flex-direction: column !important; gap: 20px !important; width: 100% !important; margin-top: 14px !important; box-sizing: border-box !important;">
                            <div class="evidence-cards-row" style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; width: 100%; align-items: stretch; box-sizing: border-box;">
                                <!-- CARD 1: MODEL PREDICTION -->
                                <div class="evidence-card" style="background: rgba(15, 23, 42, 0.85) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; border-radius: 14px !important; padding: 24px !important; min-height: 220px !important; box-sizing: border-box !important; display: flex !important; flex-direction: column !important; justify-content: flex-start !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; position: relative !important; overflow: hidden !important;">
                                    <div class="evidence-card-header" style="display: flex !important; align-items: center !important; gap: 10px !important; padding-bottom: 12px !important; border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important; margin-bottom: 16px !important;">
                                        <span class="evidence-card-icon" style="font-size: 1.4rem !important; line-height: 1 !important;">🧠</span>
                                        <span class="evidence-card-title" style="font-size: 0.8rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.9px !important; color: #94a3b8 !important;">MODEL PREDICTION</span>
                                    </div>
                                    <div class="evidence-card-body" style="flex: 1 !important; display: flex !important; flex-direction: column !important; justify-content: center !important; gap: 6px !important;">
                                        <div class="evidence-primary-value" style="font-family: 'Outfit', sans-serif !important; font-size: 2.2rem !important; font-weight: 800 !important; color: #f1f5f9 !important; line-height: 1.15 !important; letter-spacing: -0.5px !important;">${probFormatted}</div>
                                        <div class="evidence-main-label" style="font-family: 'Outfit', sans-serif !important; font-size: 1.25rem !important; font-weight: 700 !important; color: #00f2fe !important; line-height: 1.2 !important;">${escapeHtml(clinicalResult)}</div>
                                        <div class="evidence-tier-pill ${tierClass}" style="display: inline-block !important; align-self: flex-start !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; padding: 3px 10px !important; border-radius: 12px !important; margin-top: 4px !important; ${cleanRiskTier.toLowerCase().includes('high') ? 'background: rgba(239, 68, 68, 0.15) !important; color: #fca5a5 !important; border: 1px solid rgba(239, 68, 68, 0.35) !important;' : 'background: rgba(16, 185, 129, 0.15) !important; color: #6ee7b7 !important; border: 1px solid rgba(16, 185, 129, 0.35) !important;'}">${escapeHtml(cleanRiskTier)}</div>
                                    </div>
                                </div>

                                <!-- CARD 2: BIOMEDICAL EVIDENCE -->
                                <div class="evidence-card" style="background: rgba(15, 23, 42, 0.85) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; border-radius: 14px !important; padding: 24px !important; min-height: 220px !important; box-sizing: border-box !important; display: flex !important; flex-direction: column !important; justify-content: flex-start !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; position: relative !important; overflow: hidden !important;">
                                    <div class="evidence-card-header" style="display: flex !important; align-items: center !important; gap: 10px !important; padding-bottom: 12px !important; border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important; margin-bottom: 16px !important;">
                                        <span class="evidence-card-icon" style="font-size: 1.4rem !important; line-height: 1 !important;">🧬</span>
                                        <span class="evidence-card-title" style="font-size: 0.8rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.9px !important; color: #94a3b8 !important;">BIOMEDICAL EVIDENCE</span>
                                    </div>
                                    <div class="evidence-card-body" style="flex: 1 !important; display: flex !important; flex-direction: column !important; justify-content: center !important; gap: 6px !important;">
                                        <div class="evidence-primary-value" style="font-family: 'Outfit', sans-serif !important; font-size: 2.2rem !important; font-weight: 800 !important; color: #f1f5f9 !important; line-height: 1.15 !important; letter-spacing: -0.5px !important;">${escapeHtml(card2Value)}</div>
                                        <div class="evidence-subtitle" style="font-size: 0.92rem !important; color: #94a3b8 !important; font-weight: 500 !important;">${escapeHtml(card2Subtitle)}</div>
                                    </div>
                                </div>

                                <!-- CARD 3: EVIDENCE AGREEMENT -->
                                <div class="evidence-card agreement-card ${cardAgreementClass}" style="background: rgba(15, 23, 42, 0.85) !important; ${card3BorderShadow} border-radius: 14px !important; padding: 24px !important; min-height: 220px !important; box-sizing: border-box !important; display: flex !important; flex-direction: column !important; justify-content: flex-start !important; backdrop-filter: blur(12px) !important; -webkit-backdrop-filter: blur(12px) !important; position: relative !important; overflow: hidden !important;">
                                    <div class="evidence-card-header" style="display: flex !important; align-items: center !important; gap: 10px !important; padding-bottom: 12px !important; border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important; margin-bottom: 16px !important;">
                                        <span class="evidence-card-icon" style="font-size: 1.4rem !important; line-height: 1 !important;">⚖️</span>
                                        <span class="evidence-card-title" style="font-size: 0.8rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.9px !important; color: #94a3b8 !important;">EVIDENCE AGREEMENT</span>
                                    </div>
                                    <div class="evidence-card-body" style="flex: 1 !important; display: flex !important; flex-direction: column !important; justify-content: center !important; gap: 6px !important;">
                                        <div class="agreement-badge-wrapper" style="margin-bottom: 6px !important;">
                                            <span class="agreement-badge ${badgeClass}" style="display: inline-block !important; align-self: flex-start !important; font-size: 0.85rem !important; font-weight: 800 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; padding: 4px 14px !important; border-radius: 14px !important; ${badgeInlineStyle}">${escapeHtml(agreementLabel)}</span>
                                        </div>
                                        <div class="agreement-comparison-lines" style="display: flex !important; flex-direction: column !important; gap: 5px !important; margin-bottom: 8px !important;">
                                            <div class="agreement-line" style="font-size: 0.86rem !important; color: #94a3b8 !important; line-height: 1.4 !important;"><span class="line-label" style="color: #64748b !important; font-weight: 500 !important; margin-right: 4px !important;">Model:</span> <strong style="color: #f1f5f9 !important; font-weight: 600 !important;">${escapeHtml(modelLineText)}</strong></div>
                                            <div class="agreement-line" style="font-size: 0.86rem !important; color: #94a3b8 !important; line-height: 1.4 !important;"><span class="line-label" style="color: #64748b !important; font-weight: 500 !important; margin-right: 4px !important;">Evidence:</span> <strong style="color: #f1f5f9 !important; font-weight: 600 !important;">${escapeHtml(evidenceLineText)}</strong></div>
                                        </div>
                                        <div class="agreement-conclusion ${conclusionClass}" style="font-size: 0.84rem !important; line-height: 1.45 !important; color: #f1f5f9 !important; background: rgba(0, 0, 0, 0.25) !important; border-left: 3px solid ${conclusionBorderColor} !important; padding: 8px 12px !important; border-radius: 0 6px 6px 0 !important; margin-top: 4px !important; font-style: italic !important;">"${escapeHtml(conclusionText)}"</div>
                                    </div>
                                </div>
                            </div>

                            <!-- COLLAPSIBLE TECHNICAL DETAILS -->
                            <div class="evidence-details-container" style="display: flex !important; flex-direction: column !important; gap: 12px !important; margin-top: 6px !important;">
                                <button type="button" class="btn-toggle-evidence-details evidence-details-toggle" id="btn-toggle-evidence-details" aria-expanded="false" style="display: inline-flex !important; align-items: center !important; gap: 8px !important; background: rgba(15, 23, 42, 0.75) !important; border: 1px solid rgba(0, 242, 254, 0.35) !important; color: #00f2fe !important; padding: 10px 20px !important; border-radius: 20px !important; font-family: 'Inter', sans-serif !important; font-size: 0.88rem !important; font-weight: 600 !important; cursor: pointer !important; transition: all 0.25s ease !important; align-self: flex-start !important; box-shadow: 0 0 15px rgba(0, 242, 254, 0.15) !important; outline: none !important; text-decoration: none !important;">
                                    <span class="toggle-icon" style="font-size: 0.75rem !important;">▼</span>
                                    <span class="toggle-text">View Evidence Details</span>
                                </button>
                                <div id="evidence-technical-drawer" class="evidence-technical-drawer hidden" style="display: none; background: rgba(11, 15, 25, 0.85) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; border-radius: 14px !important; padding: 20px !important; flex-direction: column !important; gap: 16px !important; width: 100% !important; box-sizing: border-box !important;">
                                    <div class="technical-metrics-grid" style="display: grid !important; grid-template-columns: repeat(4, minmax(0, 1fr)) !important; gap: 12px !important; width: 100% !important; box-sizing: border-box !important;">
                                        <div class="technical-metric-item" style="background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 8px !important; padding: 12px 14px !important; display: flex !important; flex-direction: column !important; gap: 4px !important; text-align: center !important; box-sizing: border-box !important;">
                                            <span class="tech-label" style="font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.6px !important; color: #64748b !important; font-weight: 600 !important;">Supporting</span>
                                            <span class="tech-value" style="font-size: 1.35rem !important; font-weight: 800 !important; font-family: 'Outfit', sans-serif !important; color: #10b981 !important;">${supCount}</span>
                                        </div>
                                        <div class="technical-metric-item" style="background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 8px !important; padding: 12px 14px !important; display: flex !important; flex-direction: column !important; gap: 4px !important; text-align: center !important; box-sizing: border-box !important;">
                                            <span class="tech-label" style="font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.6px !important; color: #64748b !important; font-weight: 600 !important;">Conflicting</span>
                                            <span class="tech-value" style="font-size: 1.35rem !important; font-weight: 800 !important; font-family: 'Outfit', sans-serif !important; color: #ef4444 !important;">${confCount}</span>
                                        </div>
                                        <div class="technical-metric-item" style="background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 8px !important; padding: 12px 14px !important; display: flex !important; flex-direction: column !important; gap: 4px !important; text-align: center !important; box-sizing: border-box !important;">
                                            <span class="tech-label" style="font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.6px !important; color: #64748b !important; font-weight: 600 !important;">Neutral</span>
                                            <span class="tech-value" style="font-size: 1.35rem !important; font-weight: 800 !important; font-family: 'Outfit', sans-serif !important; color: #94a3b8 !important;">${neuCount}</span>
                                        </div>
                                        <div class="technical-metric-item" style="background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 8px !important; padding: 12px 14px !important; display: flex !important; flex-direction: column !important; gap: 4px !important; text-align: center !important; box-sizing: border-box !important;">
                                            <span class="tech-label" style="font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.6px !important; color: #64748b !important; font-weight: 600 !important;">Total Signals</span>
                                            <span class="tech-value" style="font-size: 1.35rem !important; font-weight: 800 !important; font-family: 'Outfit', sans-serif !important; color: #00f2fe !important;">${totalSignals}</span>
                                        </div>
                                    </div>

                                    ${contradictionNoticeHtml}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (id === 'trust_confidence' || id === 'trust_and_confidence') {
                const ecSec = sections.find(s => s.section_id === 'evidence_comparison');
                const bioSec = sections.find(s => s.section_id === 'biomedical_evidence');
                const predSec = sections.find(s => s.section_id === 'prediction' || s.section_id === 'disease_prediction');
                const ecMetrics = ecSec?.metrics || {};
                const bioMetrics = bioSec?.metrics || {};
                const predMetrics = predSec?.metrics || {};

                const tcSummary = report.trust_confidence_data?.trust_and_consensus_summary ||
                    state.selectedHistoryItem?.trust_confidence_data?.trust_and_consensus_summary ||
                    state.currentReport?.trust_confidence_data?.trust_and_consensus_summary || {};

                // --- 1. Contradiction Analysis Data ---
                let supCount = ecMetrics.supporting_evidence_count ?? bioMetrics.supporting_evidence ?? bioMetrics.supporting_count ?? 0;
                let confCount = ecMetrics.conflicting_evidence_count ?? bioMetrics.conflicting_evidence ?? bioMetrics.conflicting_count ?? 0;
                let neuCount = ecMetrics.neutral_evidence_count ?? bioMetrics.neutral_evidence ?? bioMetrics.neutral_count ?? 0;

                if (supCount === 0 && confCount === 0 && ecSec?.summary_text) {
                    const match = ecSec.summary_text.match(/\(([0-9]+)\s+supporting,\s*([0-9]+)\s+conflicting,\s*([0-9]+)\s+neutral\)/i);
                    if (match) {
                        supCount = parseInt(match[1], 10);
                        confCount = parseInt(match[2], 10);
                        neuCount = parseInt(match[3], 10);
                    }
                }

                const hasConflict = isCapped ||
                    ecMetrics.alignment_status === 'CONTRADICTION_DETECTED' ||
                    ecMetrics.decision_classification === 'CONTRADICTION_FLAG' ||
                    confCount > 0;

                let contradictionStatusText = 'CONFLICT DETECTED';
                let contradictionStatusClass = 'status-conflict';
                let contradictionStatusIcon = '⚠️';
                let contradictionExplanation = 'Evidence contains both supporting and conflicting signals.';

                if (!hasConflict && supCount > 0) {
                    contradictionStatusText = 'ALIGNED';
                    contradictionStatusClass = 'status-aligned';
                    contradictionStatusIcon = '✅';
                    contradictionExplanation = 'All biomedical evidence signals support the model prediction without contradiction.';
                } else if (!hasConflict && supCount === 0 && confCount === 0) {
                    contradictionStatusText = 'NEUTRAL';
                    contradictionStatusClass = 'status-neutral';
                    contradictionStatusIcon = '⚖️';
                    contradictionExplanation = 'Evidence signals show a neutral baseline with no contradictory findings.';
                } else if (confCount > 0 && supCount === 0) {
                    contradictionStatusText = 'CONFLICT DETECTED';
                    contradictionStatusClass = 'status-conflict';
                    contradictionStatusIcon = '⚠️';
                    contradictionExplanation = 'Evidence directly conflicts with the model prediction.';
                } else {
                    contradictionStatusText = 'CONFLICT DETECTED';
                    contradictionStatusClass = 'status-conflict';
                    contradictionStatusIcon = '⚠️';
                    contradictionExplanation = 'Evidence contains both supporting and conflicting signals.';
                }

                // --- 2. Consensus Analysis Data ---
                const rawConsensusLvl = metrics.consensus_level || tcSummary.consensus_level || report.consensus_level || '';
                const normalizedCurrentLevel = String(rawConsensusLvl).trim().replace(/\s+/g, '_').toUpperCase();

                // Exactly five backend consensus levels with their required display names and color tiers:
                // 1. STRONG_CONSENSUS -> emerald green
                // 2. MODERATE_CONSENSUS -> cyan
                // 3. WEAK_CONSENSUS -> cyan
                // 4. CONTRADICTORY_CONSENSUS -> amber
                // 5. INSUFFICIENT_EVIDENCE -> cyan
                const CONSENSUS_LEVEL_CONFIG = [
                    { key: 'STRONG_CONSENSUS', label: 'STRONG CONSENSUS', tier: 'emerald', hex: '#10b981', lightHex: '#34d399', rgb: '16, 185, 129' },
                    { key: 'MODERATE_CONSENSUS', label: 'MODERATE CONSENSUS', tier: 'cyan', hex: '#00f2fe', lightHex: '#00f2fe', rgb: '0, 242, 254' },
                    { key: 'WEAK_CONSENSUS', label: 'WEAK CONSENSUS', tier: 'cyan', hex: '#00f2fe', lightHex: '#00f2fe', rgb: '0, 242, 254' },
                    { key: 'CONTRADICTORY_CONSENSUS', label: 'CONTRADICTORY CONSENSUS', tier: 'amber', hex: '#f59e0b', lightHex: '#fbbf24', rgb: '245, 158, 11' },
                    { key: 'INSUFFICIENT_EVIDENCE', label: 'INSUFFICIENT EVIDENCE', tier: 'cyan', hex: '#00f2fe', lightHex: '#00f2fe', rgb: '0, 242, 254' }
                ];

                const consensusLevelsHtml = CONSENSUS_LEVEL_CONFIG.map(cfg => {
                    const isActive = (
                        normalizedCurrentLevel === cfg.key ||
                        (cfg.key.endsWith('_CONSENSUS') && normalizedCurrentLevel === cfg.key.replace('_CONSENSUS', '')) ||
                        (cfg.key === 'INSUFFICIENT_EVIDENCE' && (normalizedCurrentLevel === 'INSUFFICIENT' || normalizedCurrentLevel === 'INSUFFICIENT_EVIDENCE'))
                    );

                    if (isActive) {
                        return `
                            <div class="consensus-level-card tier-${cfg.tier} active" data-consensus-level="${cfg.key}" role="status" aria-current="true" style="background: rgba(${cfg.rgb}, 0.16) !important; border: 1.5px solid ${cfg.hex} !important; box-shadow: 0 0 16px rgba(${cfg.rgb}, 0.3), inset 0 0 12px rgba(${cfg.rgb}, 0.08) !important; opacity: 1 !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; text-align: center !important; padding: 14px 10px !important; border-radius: 10px !important; min-height: 74px !important; box-sizing: border-box !important; cursor: default !important; user-select: none !important;">
                                <div class="consensus-card-header" style="display: flex !important; align-items: center !important; gap: 6px !important; margin-bottom: 6px !important;">
                                    <span class="consensus-status-dot" style="width: 7px !important; height: 7px !important; border-radius: 50% !important; background: ${cfg.hex} !important; box-shadow: 0 0 8px ${cfg.hex}, 0 0 12px rgba(${cfg.rgb}, 0.6) !important; display: inline-block !important;"></span>
                                    <span class="consensus-status-badge" style="font-size: 0.68rem !important; font-weight: 700 !important; letter-spacing: 0.6px !important; text-transform: uppercase !important; padding: 2px 7px !important; border-radius: 4px !important; line-height: 1 !important; color: ${cfg.lightHex} !important; background: rgba(${cfg.rgb}, 0.22) !important; border: 1px solid rgba(${cfg.rgb}, 0.45) !important;">ACTIVE</span>
                                </div>
                                <div class="consensus-level-title" style="font-family: 'Outfit', sans-serif !important; font-size: 0.78rem !important; font-weight: 700 !important; letter-spacing: 0.5px !important; line-height: 1.25 !important; text-transform: uppercase !important; color: ${cfg.lightHex} !important; text-shadow: 0 0 10px rgba(${cfg.rgb}, 0.35) !important;">${cfg.label}</div>
                            </div>
                        `;
                    } else {
                        return `
                            <div class="consensus-level-card tier-${cfg.tier} inactive" data-consensus-level="${cfg.key}" role="status" aria-current="false" style="background: rgba(15, 23, 42, 0.55) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; box-shadow: none !important; opacity: 0.55 !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; text-align: center !important; padding: 14px 10px !important; border-radius: 10px !important; min-height: 74px !important; box-sizing: border-box !important; cursor: default !important; user-select: none !important;">
                                <div class="consensus-card-header" style="display: flex !important; align-items: center !important; gap: 6px !important; margin-bottom: 6px !important;">
                                    <span class="consensus-status-dot" style="width: 7px !important; height: 7px !important; border-radius: 50% !important; background: #475569 !important; box-shadow: none !important; display: inline-block !important;"></span>
                                    <span class="consensus-status-badge" style="font-size: 0.68rem !important; font-weight: 600 !important; letter-spacing: 0.6px !important; text-transform: uppercase !important; padding: 2px 7px !important; border-radius: 4px !important; line-height: 1 !important; color: #64748b !important; background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.06) !important;">INACTIVE</span>
                                </div>
                                <div class="consensus-level-title" style="font-family: 'Outfit', sans-serif !important; font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: 0.5px !important; line-height: 1.25 !important; text-transform: uppercase !important; color: #64748b !important;">${cfg.label}</div>
                            </div>
                        `;
                    }
                }).join('');

                let consensusScoreVal = metrics.consensus_score ?? tcSummary.consensus_score;
                if (consensusScoreVal == null && text) {
                    const match = text.match(/Score:\s*([0-9.]+)/i);
                    if (match) consensusScoreVal = parseFloat(match[1]);
                }
                const consensusScoreFormatted = (consensusScoreVal !== undefined && consensusScoreVal !== null && !isNaN(consensusScoreVal))
                    ? Number(consensusScoreVal).toFixed(4)
                    : (consensusScoreVal || 'N/A');

                const consensusExplanationText = metrics.consensus_explanation || tcSummary.consensus_explanation || metrics.explanation || tcSummary.explanation || 'Overall agreement among available evidence signals.';

                // --- 3. Trust Score Data ---
                let overallTrustVal = metrics.trust_score ?? tcSummary.overall_trust_score ?? report.overall_trust_score;
                if (overallTrustVal == null && text) {
                    const match = text.match(/Trust Score:\s*\*?\*?\s*([0-9.]+)/i);
                    if (match) overallTrustVal = parseFloat(match[1]);
                }
                const overallTrustFormatted = (overallTrustVal !== undefined && overallTrustVal !== null && !isNaN(overallTrustVal))
                    ? Number(overallTrustVal).toFixed(4)
                    : (overallTrustVal || 'N/A');

                const formatFactor = (v) => {
                    if (v === undefined || v === null || isNaN(v)) return 'N/A';
                    return Number(v).toFixed(4);
                };

                const confFactor = tcSummary.confidence_factor ?? (predMetrics.model_decisiveness_factor !== undefined ? predMetrics.model_decisiveness_factor : 0.0938);
                const shapFactor = tcSummary.shap_alignment_factor ?? 0.4000;
                const graphFactor = tcSummary.graph_evidence_factor ?? 1.0000;
                const consFactor = tcSummary.evidence_consistency_factor ?? (metrics.consensus_score ?? 0.3810);

                const weights = tcSummary.weights_used || {
                    confidence_factor: 0.30,
                    shap_alignment_factor: 0.25,
                    graph_evidence_factor: 0.25,
                    evidence_consistency_factor: 0.20
                };

                const confWeight = weights.confidence_factor != null ? (weights.confidence_factor <= 1 ? (weights.confidence_factor * 100).toFixed(0) + '%' : weights.confidence_factor + '%') : '30%';
                const shapWeight = weights.shap_alignment_factor != null ? (weights.shap_alignment_factor <= 1 ? (weights.shap_alignment_factor * 100).toFixed(0) + '%' : weights.shap_alignment_factor + '%') : '25%';
                const graphWeight = weights.graph_evidence_factor != null ? (weights.graph_evidence_factor <= 1 ? (weights.graph_evidence_factor * 100).toFixed(0) + '%' : weights.graph_evidence_factor + '%') : '25%';
                const consWeight = weights.evidence_consistency_factor != null ? (weights.evidence_consistency_factor <= 1 ? (weights.evidence_consistency_factor * 100).toFixed(0) + '%' : weights.evidence_consistency_factor + '%') : '20%';

                const trustCompVal = metrics.trust_component ?? (metrics.trust_score ? (metrics.trust_score * 0.4).toFixed(4) : null);
                const consCompVal = metrics.consensus_component ?? (consensusScoreVal ? (consensusScoreVal * 0.35).toFixed(4) : null);
                const fusedConfVal = metrics.fused_confidence_score ?? metrics.overall_fused_score ?? report.fused_confidence_score;

                let fusedSummaryHtml = '';
                if (trustCompVal != null || consCompVal != null || fusedConfVal != null) {
                    fusedSummaryHtml = `
                        <div class="trust-fused-row">
                            ${trustCompVal != null ? `
                                <div class="fused-chip">
                                    <span class="chip-label">Trust Component:</span>
                                    <span class="chip-val">${formatFactor(trustCompVal)}</span>
                                </div>
                            ` : ''}
                            ${consCompVal != null ? `
                                <div class="fused-chip">
                                    <span class="chip-label">Consensus Component:</span>
                                    <span class="chip-val">${formatFactor(consCompVal)}</span>
                                </div>
                            ` : ''}
                            ${fusedConfVal != null ? `
                                <div class="fused-chip">
                                    <span class="chip-label">Fused Confidence:</span>
                                    <span class="chip-val" style="color: #00f2fe;">${formatFactor(fusedConfVal)}</span>
                                </div>
                            ` : ''}
                            ${isCapped ? `
                                <div class="fused-chip" style="border-color: rgba(239, 68, 68, 0.35); background: rgba(239, 68, 68, 0.1);">
                                    <span class="chip-label" style="color: #fca5a5;">🛡️ Safety Cap:</span>
                                    <span class="chip-val" style="color: #fca5a5;">0.50 Capped</span>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }

                html += `
                    <div class="report-section trust-analysis-section">
                        <h3 class="section-title">🛡️ TRUST ANALYSIS</h3>
                        <div class="trust-accordion-container">
                            <!-- BAR 1: Contradiction Analysis -->
                            <div class="trust-accordion-item" data-accordion="contradiction">
                                <button type="button" class="trust-accordion-header" id="header-contradiction-analysis" aria-expanded="false" aria-controls="content-contradiction-analysis">
                                    <div class="accordion-title-group">
                                        <span class="accordion-icon">⚠️</span>
                                        <span class="accordion-title">Contradiction Analysis</span>
                                    </div>
                                    <span class="accordion-indicator">+</span>
                                </button>
                                <div class="trust-accordion-collapse" id="content-contradiction-analysis" role="region" aria-labelledby="header-contradiction-analysis">
                                    <div class="trust-accordion-body">
                                        <div class="trust-status-badge ${contradictionStatusClass}">
                                            <span class="badge-icon">${contradictionStatusIcon}</span>
                                            <span class="badge-text">${contradictionStatusText}</span>
                                        </div>
                                        <div class="trust-counts-grid">
                                            <div class="trust-count-pill pill-supporting">
                                                <span class="count-pill-label">Supporting:</span>
                                                <span class="count-pill-value">${supCount}</span>
                                            </div>
                                            <div class="trust-count-pill pill-conflicting">
                                                <span class="count-pill-label">Conflicting:</span>
                                                <span class="count-pill-value">${confCount}</span>
                                            </div>
                                            <div class="trust-count-pill pill-neutral">
                                                <span class="count-pill-label">Neutral:</span>
                                                <span class="count-pill-value">${neuCount}</span>
                                            </div>
                                        </div>
                                        <div class="trust-explanation-box">
                                            <p class="trust-explanation-text">"${escapeHtml(contradictionExplanation)}"</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- BAR 2: Consensus Analysis -->
                            <div class="trust-accordion-item" data-accordion="consensus">
                                <button type="button" class="trust-accordion-header" id="header-consensus-analysis" aria-expanded="false" aria-controls="content-consensus-analysis">
                                    <div class="accordion-title-group">
                                        <span class="accordion-icon">🤝</span>
                                        <span class="accordion-title">Consensus Analysis</span>
                                    </div>
                                    <span class="accordion-indicator">+</span>
                                </button>
                                <div class="trust-accordion-collapse" id="content-consensus-analysis" role="region" aria-labelledby="header-consensus-analysis">
                                    <div class="trust-accordion-body">
                                        <div class="consensus-levels-wrapper" style="display: flex !important; flex-direction: column !important; gap: 10px !important; width: 100% !important; box-sizing: border-box !important;">
                                            <div class="trust-mini-label" style="font-size: 0.76rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.9px !important; color: #94a3b8 !important;">CONSENSUS LEVEL (5-TIER EVALUATION)</div>
                                            <div class="consensus-levels-grid" style="display: grid !important; grid-template-columns: repeat(5, minmax(0, 1fr)) !important; gap: 10px !important; width: 100% !important; box-sizing: border-box !important;">
                                                ${consensusLevelsHtml}
                                            </div>
                                        </div>
                                        <div class="trust-metric-callout" style="display: flex !important; align-items: center !important; gap: 8px !important; font-size: 1rem !important; color: #cbd5e1 !important; margin-top: 4px !important;">
                                            <span class="callout-label" style="font-weight: 600 !important; color: #94a3b8 !important;">Consensus Score:</span>
                                            <span class="callout-value" style="font-family: 'Outfit', sans-serif !important; font-weight: 800 !important; color: #f1f5f9 !important; font-size: 1.25rem !important;">${consensusScoreFormatted}</span>
                                        </div>
                                        <div class="trust-explanation-box" style="background: rgba(0, 0, 0, 0.25) !important; border-left: 3px solid #00f2fe !important; border-radius: 0 8px 8px 0 !important; padding: 10px 14px !important; margin-top: 2px !important;">
                                            <p class="trust-explanation-text" style="font-size: 0.9rem !important; line-height: 1.5 !important; color: #f1f5f9 !important; font-style: italic !important; margin: 0 !important;">"${escapeHtml(consensusExplanationText)}"</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- BAR 3: Trust Score -->
                            <div class="trust-accordion-item" data-accordion="trust">
                                <button type="button" class="trust-accordion-header" id="header-trust-score" aria-expanded="false" aria-controls="content-trust-score">
                                    <div class="accordion-title-group">
                                        <span class="accordion-icon">🛡️</span>
                                        <span class="accordion-title">Trust Score</span>
                                    </div>
                                    <span class="accordion-indicator">+</span>
                                </button>
                                <div class="trust-accordion-collapse" id="content-trust-score" role="region" aria-labelledby="header-trust-score">
                                    <div class="trust-accordion-body">
                                        <div class="trust-score-hero-block">
                                            <div class="trust-mini-label">OVERALL TRUST</div>
                                            <div class="trust-hero-val trust-score-hero">${overallTrustFormatted}</div>
                                        </div>
                                        <div class="trust-components-section">
                                            <div class="trust-components-title">TRUST COMPONENTS & WEIGHTS</div>
                                            <div class="trust-components-grid">
                                                <div class="trust-component-card">
                                                    <div class="component-card-top">
                                                        <span class="component-name">Confidence Factor</span>
                                                        <span class="component-weight">${confWeight}</span>
                                                    </div>
                                                    <div class="component-value">${formatFactor(confFactor)}</div>
                                                    <div class="component-desc">Model Decisiveness</div>
                                                </div>
                                                <div class="trust-component-card">
                                                    <div class="component-card-top">
                                                        <span class="component-name">SHAP Alignment</span>
                                                        <span class="component-weight">${shapWeight}</span>
                                                    </div>
                                                    <div class="component-value">${formatFactor(shapFactor)}</div>
                                                    <div class="component-desc">Feature Attribution</div>
                                                </div>
                                                <div class="trust-component-card">
                                                    <div class="component-card-top">
                                                        <span class="component-name">Graph Evidence</span>
                                                        <span class="component-weight">${graphWeight}</span>
                                                    </div>
                                                    <div class="component-value">${formatFactor(graphFactor)}</div>
                                                    <div class="component-desc">PrimeKG Triples</div>
                                                </div>
                                                <div class="trust-component-card">
                                                    <div class="component-card-top">
                                                        <span class="component-name">Evidence Consistency</span>
                                                        <span class="component-weight">${consWeight}</span>
                                                    </div>
                                                    <div class="component-value">${formatFactor(consFactor)}</div>
                                                    <div class="component-desc">Signal Concordance</div>
                                                </div>
                                            </div>
                                        </div>
                                        ${fusedSummaryHtml}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (id === 'interpretation' || id === 'final_interpretation') {
                const predSec = sections.find(s => s.section_id === 'prediction' || s.section_id === 'disease_prediction');
                const predMetrics = predSec?.metrics || {};

                // --- 1. MODEL PREDICTION DATA ---
                let clinicalResult = 'Absence';
                if (predMetrics.predicted_class !== undefined && predMetrics.predicted_class !== null) {
                    clinicalResult = (predMetrics.predicted_class == 1 || predMetrics.predicted_class === '1') ? 'Presence' : 'Absence';
                } else if (predMetrics.predicted_result) {
                    clinicalResult = String(predMetrics.predicted_result).trim();
                } else if (predMetrics.risk_tier) {
                    clinicalResult = (predMetrics.risk_tier === 'HIGH_RISK') ? 'Presence' : 'Absence';
                }

                let probVal = predMetrics.model_probability;
                let probFormatted = 'N/A';
                if (probVal != null) {
                    if (typeof probVal === 'number') {
                        probFormatted = (probVal <= 1 ? (probVal * 100).toFixed(2) : probVal.toFixed(2)) + '%';
                    } else {
                        const s = String(probVal).trim();
                        probFormatted = s.endsWith('%') ? s : s + '%';
                    }
                }

                let riskTierStr = predMetrics.risk_tier ? String(predMetrics.risk_tier).replace(/_/g, ' ') : '';
                const cleanRiskTier = riskTierStr
                    ? riskTierStr.toLowerCase().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
                    : (clinicalResult === 'Presence' ? 'High Risk' : 'Low Risk');

                // --- 2. SHAP EXPLANATION DATA ---
                const keyFactorsSec = sections.find(s => s.section_id === 'key_factors');
                const keyFactorsItems = keyFactorsSec?.items || [];
                const llmExplanationText = report.llm_explanation || null;

                // Build lookup map for LLM explanations and detailed values
                const llmFeatureMap = new Map();
                const parsedLlmRows = [];

                if (llmExplanationText && llmExplanationText !== "LLM explanation unavailable.") {
                    const lines = llmExplanationText.split('\n');
                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (!trimmed.startsWith('|')) continue;
                        const rawCols = trimmed.split('|').map(c => c.trim());
                        const cols = rawCols.filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
                        if (cols.length < 5) continue;
                        if (cols[0].toLowerCase().includes('rank') || cols[0].includes('---') || cols[1].includes('---')) continue;

                        const clean = (s) => s.replace(/\*\*/g, '').replace(/ /g, ' ').replace(/‑/g, '-').trim();

                        const featureCol = clean(cols[1]);
                        const shapCol = clean(cols[2]);
                        const impactCol = clean(cols[3]);
                        const explCol = clean(cols[4]);

                        let featureName = featureCol;
                        let rawValue = 'N/A';
                        if (featureCol.includes('=')) {
                            const parts = featureCol.split('=');
                            featureName = parts[0].trim();
                            rawValue = parts.slice(1).join('=').trim();
                        }

                        let cleanFeatureName = formatShapFeatureName(featureName);
                        const normKey = featureName.toLowerCase().replace(/[^a-z0-9]/g, '');

                        const rowData = {
                            feature: cleanFeatureName,
                            rawValue: rawValue,
                            shapValue: shapCol,
                            impact: impactCol,
                            explanation: explCol
                        };

                        parsedLlmRows.push(rowData);
                        if (!llmFeatureMap.has(normKey)) {
                            llmFeatureMap.set(normKey, rowData);
                        }
                    }
                }

                // Construct shapFeatures strictly driven by the authoritative Top 5 patient-specific SHAP ranking
                const shapFeatures = [];
                const targetTop5 = (sharedTop5ShapFeatures.length > 0 ? sharedTop5ShapFeatures : (Array.isArray(keyFactorsItems) ? keyFactorsItems : [])).slice(0, 5);

                if (targetTop5.length > 0) {
                    targetTop5.forEach(item => {
                        const fRawName = item.feature_name || item.name || 'Unknown';
                        const cleanFeatureName = formatShapFeatureName(fRawName);
                        const normKey = String(fRawName).toLowerCase().replace(/[^a-z0-9]/g, '');

                        const valNum = parseFloat(item.shap_value ?? item.attribution_value ?? 0) || 0;
                        const valStr = (valNum >= 0 ? '+' : '') + valNum.toFixed(4);

                        const rawImpact = String(item.impact_direction || (valNum >= 0 ? 'increases_risk' : 'decreases_risk')).replace(/_/g, ' ');
                        const impactStr = rawImpact.toLowerCase().includes('increase') ? 'Increases risk' :
                            rawImpact.toLowerCase().includes('decrease') ? 'Decreases risk' : rawImpact;

                        let rawValue = item.raw_value !== undefined ? String(item.raw_value) : (item.feature_value !== undefined ? String(item.feature_value) : 'N/A');
                        let explanation = `Feature attribution indicates ${impactStr.toLowerCase()} for ${cleanFeatureName}.`;
                        let displayShap = valStr;
                        let displayImpact = impactStr;

                        const matchedLlm = llmFeatureMap.get(normKey);
                        if (matchedLlm) {
                            if (matchedLlm.explanation) explanation = matchedLlm.explanation;
                            if (matchedLlm.rawValue && matchedLlm.rawValue !== 'N/A') rawValue = matchedLlm.rawValue;
                            if (matchedLlm.impact) displayImpact = matchedLlm.impact;
                            if (matchedLlm.shapValue) displayShap = matchedLlm.shapValue;
                        }

                        shapFeatures.push({
                            feature: cleanFeatureName,
                            rawValue: rawValue,
                            shapValue: displayShap,
                            impact: displayImpact,
                            explanation: explanation
                        });
                    });
                } else if (parsedLlmRows.length > 0) {
                    // Fallback only if sharedTop5ShapFeatures was empty: strictly limit to Top 5
                    parsedLlmRows.slice(0, 5).forEach(row => {
                        shapFeatures.push(row);
                    });
                }

                // Hard limit: Exactly at most 5 cards rendered
                const finalShapCards = shapFeatures.slice(0, 5);

                let shapBlocksHtml = '';
                finalShapCards.forEach(f => {
                    const isIncrease = f.impact.toLowerCase().includes('increase');
                    const borderClass = isIncrease ? 'impact-increase-border' : 'impact-decrease-border';
                    const impactClass = isIncrease ? 'impact-increase' : 'impact-decrease';

                    shapBlocksHtml += `
                        <div class="shap-feature-block ${borderClass}">
                            <div class="shap-field-line">
                                <span class="shap-field-label">Feature:</span>
                                <span class="shap-field-value feature-name">${escapeHtml(f.feature)}</span>
                            </div>
                            <div class="shap-field-line">
                                <span class="shap-field-label">Raw Value:</span>
                                <span class="shap-field-value">${escapeHtml(f.rawValue)}</span>
                            </div>
                            <div class="shap-field-line">
                                <span class="shap-field-label">SHAP Value:</span>
                                <span class="shap-field-value shap-val">${escapeHtml(f.shapValue)}</span>
                            </div>
                            <div class="shap-field-line">
                                <span class="shap-field-label">Impact:</span>
                                <span class="shap-field-value impact-val ${impactClass}">${escapeHtml(f.impact)}</span>
                            </div>
                            <div class="shap-field-line explanation-line">
                                <span class="shap-field-label">Explanation:</span>
                                <span class="shap-field-value explanation-text">${escapeHtml(f.explanation)}</span>
                            </div>
                        </div>
                    `;
                });

                // --- 3. FINAL SYSTEM DECISION ---
                let rawDiseaseSlug = report.disease || metadata.disease || predMetrics.disease || state.selectedDisease?.id || '';
                let diseaseName = '';
                if (state.selectedDisease?.name) {
                    diseaseName = state.selectedDisease.name;
                } else if (report.disease_name) {
                    diseaseName = report.disease_name;
                } else if (rawDiseaseSlug) {
                    diseaseName = typeof formatDiseaseName === 'function' ? formatDiseaseName(rawDiseaseSlug) : rawDiseaseSlug.replace(/_/g, ' ');
                } else {
                    diseaseName = 'Disease';
                }
                const diseaseDisplayName = diseaseName.toUpperCase();

                let isDetected = false;
                const resLower = String(predMetrics.predicted_result || clinicalResult || '').toLowerCase().trim();
                const tierUpper = String(predMetrics.risk_tier || '').toUpperCase().trim();

                if (resLower === 'presence' || resLower === 'positive' || resLower === 'detected' || resLower === 'malignant' || resLower === 'die') {
                    isDetected = true;
                } else if (resLower === 'absence' || resLower === 'negative' || resLower === 'not detected' || resLower === 'benign' || resLower === 'live') {
                    isDetected = false;
                } else if (tierUpper === 'HIGH_RISK') {
                    isDetected = true;
                } else if (tierUpper === 'LOW_RISK') {
                    isDetected = false;
                } else if (predMetrics.predicted_class !== undefined && predMetrics.predicted_class !== null) {
                    isDetected = (predMetrics.predicted_class == 1 || predMetrics.predicted_class === '1');
                } else if (clinicalResult) {
                    isDetected = String(clinicalResult).toLowerCase().includes('presen') || String(clinicalResult).toLowerCase().includes('high');
                }
                const detectionStatus = isDetected ? 'DETECTED' : 'NOT DETECTED';

                const riskTierUpper = (predMetrics.risk_tier ? String(predMetrics.risk_tier).replace(/_/g, ' ') : (isDetected ? 'HIGH RISK' : 'LOW RISK')).toUpperCase();

                // --- PATIENT-SPECIFIC DYNAMIC CLINICAL INTERPRETATION ---
                const secEvidence = sections.find(s => s.section_id === 'biomedical_evidence' || s.section_id === 'evidence');
                const secComparison = sections.find(s => s.section_id === 'evidence_comparison' || s.section_id === 'comparison');
                const secTrust = sections.find(s => s.section_id === 'trust_metrics' || s.section_id === 'trust');

                const mappedNode = secEvidence?.metrics?.mapped_graph_node || rawDiseaseSlug || diseaseName;
                const totalTriples = secEvidence?.metrics?.total_evidence_triples ?? 0;
                const supportingEvidence = secEvidence?.metrics?.supporting_evidence ?? secComparison?.metrics?.supporting_signals ?? 0;
                const conflictingEvidence = secEvidence?.metrics?.conflicting_evidence ?? secComparison?.metrics?.conflicting_signals ?? 0;
                const neutralEvidence = secEvidence?.metrics?.neutral_evidence ?? secComparison?.metrics?.neutral_signals ?? 0;

                const consensusLevelVal = secTrust?.metrics?.consensus_level || report.consensus_level || '';
                const trustScoreVal = secTrust?.metrics?.trust_score ?? report.overall_trust_score;
                const fusedConfVal = secTrust?.metrics?.fused_confidence_score ?? report.fused_confidence_score;

                const hasConflictingSignals = Boolean(isCapped || conflictingEvidence > 0 || (secComparison?.metrics?.conflicting_signals > 0) || (consensusLevelVal && consensusLevelVal.toUpperCase().includes('CONTRADICT')));

                const clinicalInterpretation = generateDynamicClinicalInterpretation({
                    diseaseName: diseaseDisplayName,
                    isDetected: isDetected,
                    detectionStatus: detectionStatus,
                    probFormatted: probFormatted,
                    cleanRiskTier: cleanRiskTier,
                    shapFeatures: finalShapCards,
                    mappedNode: mappedNode,
                    totalTriples: totalTriples,
                    supportingEvidence: supportingEvidence,
                    conflictingEvidence: conflictingEvidence,
                    neutralEvidence: neutralEvidence,
                    consensusLevel: consensusLevelVal,
                    trustScore: trustScoreVal,
                    fusedConfidence: fusedConfVal,
                    hasConflictingSignals: hasConflictingSignals,
                    counterfactualData: state.latestWhatIfData || report.counterfactual || null
                });

                html += `
                    <div class="report-section final-interpretation-section">
                        <h3 class="section-title">📄 FINAL DECISION-SUPPORT INTERPRETATION</h3>
                        <div class="interpretation-subsections-container">
                            <!-- SUBSECTION 1: MODEL PREDICTION -->
                            <div class="interpretation-subsection">
                                <div class="interpretation-subheading">
                                    <span class="subheading-icon">🧠</span>
                                    <span class="subheading-text">MODEL PREDICTION</span>
                                </div>
                                <div class="interpretation-prediction-grid">
                                    <div class="interpretation-data-row">
                                        <span class="data-label">Classification:</span>
                                        <span class="data-value prediction-val">${escapeHtml(detectionStatus)}</span>
                                    </div>
                                    <div class="interpretation-data-row">
                                        <span class="data-label">Probability:</span>
                                        <span class="data-value probability-val">${escapeHtml(probFormatted)}</span>
                                    </div>
                                    <div class="interpretation-data-row">
                                        <span class="data-label">Risk Level:</span>
                                        <span class="data-value risk-val ${cleanRiskTier.toLowerCase().includes('high') ? 'risk-high' : 'risk-low'}">${escapeHtml(cleanRiskTier)}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- SUBSECTION 2: SHAP EXPLANATION -->
                            <div class="interpretation-subsection">
                                <div class="interpretation-subheading">
                                    <span class="subheading-icon">🔍</span>
                                    <span class="subheading-text">SHAP EXPLANATION</span>
                                </div>
                                <div class="shap-features-container">
                                    ${shapBlocksHtml || '<p style="color: var(--text-muted); font-style: italic;">No SHAP feature explanations available.</p>'}
                                </div>
                            </div>

                            <!-- SUBSECTION 3: FINAL SYSTEM DECISION -->
                            <div class="interpretation-subsection final-decision-subsection">
                                <div class="interpretation-subheading">
                                    <span class="subheading-icon">📋</span>
                                    <span class="subheading-text">FINAL SYSTEM DECISION</span>
                                </div>
                                <div class="final-system-decision-card ${isDetected ? 'decision-card-detected' : 'decision-card-not-detected'}">
                                    <div class="llm-clinical-explanation-section">
                                        <div class="llm-explanation-title">🧠 CLINICAL INTERPRETATION</div>
                                        <div class="llm-explanation-paragraph">
                                            <p class="llm-explanation-p">${escapeHtml(clinicalInterpretation.paragraph1)}</p>
                                            <p class="llm-explanation-p">${escapeHtml(clinicalInterpretation.paragraph2)}</p>
                                            <p class="llm-explanation-p">${escapeHtml(clinicalInterpretation.paragraph3)}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (id === 'download_disclaimer' || id === 'export_and_disclaimer') {
                html += `
                    <div class="report-section download-report-section">
                        <h3 class="section-title">📥 DOWNLOAD REPORT</h3>
                        <div class="download-options-grid">
                            <button type="button" class="download-card-btn" id="btn-download-pdf">
                                <span class="download-card-icon">📄</span>
                                <span class="download-card-title">Download Clinical Report (PDF)</span>
                            </button>
                            <button type="button" class="download-card-btn" id="btn-download-json">
                                <span class="download-card-icon">🧾</span>
                                <span class="download-card-title">Download Structured Report (JSON)</span>
                            </button>
                            <button type="button" class="download-card-btn" id="btn-download-markdown">
                                <span class="download-card-icon">📝</span>
                                <span class="download-card-title">Download Report (Markdown)</span>
                            </button>
                        </div>
                    </div>
                `;
            }
        });

        reportContainer.innerHTML = html;

        const btnSectionWhatIf = reportContainer.querySelector('#btn-section-whatif');
        if (btnSectionWhatIf) {
            btnSectionWhatIf.addEventListener('click', () => {
                openWhatIfModal();
            });
        }
        if (btnOpenWhatIf) {
            btnOpenWhatIf.onclick = () => {
                openWhatIfModal();
            };
        }

        const btnToggleEvidence = reportContainer.querySelector('#btn-toggle-evidence-details');
        const evidenceDrawer = reportContainer.querySelector('#evidence-technical-drawer');
        if (btnToggleEvidence && evidenceDrawer) {
            btnToggleEvidence.addEventListener('click', () => {
                const isHidden = evidenceDrawer.classList.contains('hidden') || evidenceDrawer.style.display === 'none';
                if (isHidden) {
                    evidenceDrawer.classList.remove('hidden');
                    evidenceDrawer.style.display = 'flex';
                    btnToggleEvidence.classList.add('active');
                    btnToggleEvidence.setAttribute('aria-expanded', 'true');
                    btnToggleEvidence.style.background = 'rgba(0, 242, 254, 0.2)';
                    btnToggleEvidence.style.borderColor = '#00f2fe';
                    const icon = btnToggleEvidence.querySelector('.toggle-icon');
                    const textSpan = btnToggleEvidence.querySelector('.toggle-text');
                    if (icon) icon.textContent = '▲';
                    if (textSpan) textSpan.textContent = 'Hide Evidence Details';
                } else {
                    evidenceDrawer.classList.add('hidden');
                    evidenceDrawer.style.display = 'none';
                    btnToggleEvidence.classList.remove('active');
                    btnToggleEvidence.setAttribute('aria-expanded', 'false');
                    btnToggleEvidence.style.background = 'rgba(15, 23, 42, 0.75)';
                    btnToggleEvidence.style.borderColor = 'rgba(0, 242, 254, 0.35)';
                    const icon = btnToggleEvidence.querySelector('.toggle-icon');
                    const textSpan = btnToggleEvidence.querySelector('.toggle-text');
                    if (icon) icon.textContent = '▼';
                    if (textSpan) textSpan.textContent = 'View Evidence Details';
                }
            });
        }

        // --- WIRE UP TRUST ANALYSIS ACCORDION ---
        const accordionItems = reportContainer.querySelectorAll('.trust-accordion-item');
        accordionItems.forEach(item => {
            const header = item.querySelector('.trust-accordion-header');
            const collapse = item.querySelector('.trust-accordion-collapse');
            const indicator = item.querySelector('.accordion-indicator');

            if (header && collapse) {
                header.addEventListener('click', () => {
                    const isOpen = item.classList.contains('active');

                    // Close all items first (exclusive accordion behavior)
                    accordionItems.forEach(otherItem => {
                        otherItem.classList.remove('active');
                        const otherHeader = otherItem.querySelector('.trust-accordion-header');
                        const otherCollapse = otherItem.querySelector('.trust-accordion-collapse');
                        const otherIndicator = otherItem.querySelector('.accordion-indicator');
                        if (otherHeader) otherHeader.setAttribute('aria-expanded', 'false');
                        if (otherCollapse) {
                            otherCollapse.style.maxHeight = '0px';
                            otherCollapse.style.opacity = '0';
                        }
                        if (otherIndicator) otherIndicator.textContent = '+';
                    });

                    // If previously closed, expand this item
                    if (!isOpen) {
                        item.classList.add('active');
                        header.setAttribute('aria-expanded', 'true');
                        collapse.style.maxHeight = (collapse.scrollHeight + 60) + 'px';
                        collapse.style.opacity = '1';
                        if (indicator) indicator.textContent = '−';
                    }
                });
            }
        });

        function generatePdfBlob(title, text) {
            // Strip raw markdown artifacts if present
            const cleanedText = (text || '')
                .replace(/\*\*/g, '')
                .replace(/^---$/gm, '')
                .replace(/\| --- \|.*$/gm, '')
                .replace(/\\([()])/g, '$1');
            const rawLines = cleanedText.split('\n');
            const maxLines = 46;
            const pages = [];
            let cur = [];
            for (let l of rawLines) {
                l = l.replace(/\r/g, '');
                while (l.length > 80) {
                    cur.push(l.slice(0, 80));
                    l = l.slice(80);
                    if (cur.length >= maxLines) { pages.push(cur); cur = []; }
                }
                cur.push(l);
                if (cur.length >= maxLines) { pages.push(cur); cur = []; }
            }
            if (cur.length > 0 || pages.length === 0) pages.push(cur);

            let objIndex = 3;
            const pageObjIds = [];
            const contentObjIds = [];
            const contentStreams = [];

            pages.forEach((pLines, pIdx) => {
                const pObjId = objIndex++;
                const cObjId = objIndex++;
                pageObjIds.push(pObjId);
                contentObjIds.push(cObjId);

                let stream = 'BT\n/F1 9 Tf\n45 750 Td\n14 TL\n';
                if (pIdx === 0 && title) {
                    stream += '/F2 13 Tf\n(' + title.replace(/([\\()])/g, '\\\\$1') + ') Tj\nT*\n/F1 9 Tf\n';
                }
                pLines.forEach(line => {
                    const asciiLine = line.replace(/[^\x20-\x7E]/g, ' ');
                    const escaped = asciiLine.replace(/([\\()])/g, '\\\\$1');
                    stream += '(' + escaped + ') Tj\nT*\n';
                });
                stream += 'ET';
                contentStreams.push(stream);
            });

            const fontObj1 = objIndex++;
            const fontObj2 = objIndex++;

            let out = '%PDF-1.4\n';
            const offsets = [];

            function addObj(id, content) {
                offsets[id] = new TextEncoder().encode(out).length;
                out += id + ' 0 obj\n' + content + '\nendobj\n';
            }

            addObj(1, '<< /Type /Catalog /Pages 2 0 R >>');
            addObj(2, '<< /Type /Pages /Kids [' + pageObjIds.map(id => id + ' 0 R').join(' ') + '] /Count ' + pages.length + ' >>');

            pageObjIds.forEach((pId, idx) => {
                const cId = contentObjIds[idx];
                addObj(pId, '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ' + fontObj1 + ' 0 R /F2 ' + fontObj2 + ' 0 R >> >> /Contents ' + cId + ' 0 R >>');
            });

            contentObjIds.forEach((cId, idx) => {
                const stream = contentStreams[idx];
                const len = new TextEncoder().encode(stream).length;
                addObj(cId, '<< /Length ' + len + ' >>\nstream\n' + stream + '\nendstream');
            });

            addObj(fontObj1, '<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>');
            addObj(fontObj2, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>');

            const xrefOffset = new TextEncoder().encode(out).length;
            out += 'xref\n0 ' + (objIndex) + '\n0000000000 65535 f \n';
            for (let i = 1; i < objIndex; i++) {
                const off = String(offsets[i] || 0).padStart(10, '0');
                out += off + ' 00000 n \n';
            }
            out += 'trailer\n<< /Size ' + objIndex + ' /Root 1 0 R >>\nstartxref\n' + xrefOffset + '\n%%EOF';
            return new Blob([new TextEncoder().encode(out)], { type: 'application/pdf' });
        }

        const diseaseCode = report.disease || state.selectedDisease?.id || 'disease';
        const patId = metadata.patient_id || 'PATIENT';

        // 1. PDF Download Button
        const btnDownloadPdf = document.getElementById('btn-download-pdf');
        if (btnDownloadPdf) {
            btnDownloadPdf.addEventListener('click', async () => {
                const reportContent = report.text_report || report.markdown_report || '';
                try {
                    const res = await apiFetch('/api/export-pdf', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            markdown_report: reportContent,
                            patient_id: patId,
                            disease: diseaseCode,
                            format: 'pdf'
                        })
                    });
                    if (!res.ok) {
                        throw new Error(`Server returned ${res.status}`);
                    }
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Clinical_Report_${diseaseCode}_${patId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } catch (err) {
                    console.warn('Backend PDF export failed, falling back to client-side renderer:', err);
                    try {
                        const diseaseName = (report.disease_name || state.selectedDisease?.name || diseaseCode).toUpperCase();
                        const pdfBlob = generatePdfBlob(`CLINICAL REPORT: ${diseaseName}`, reportContent);
                        const url = window.URL.createObjectURL(pdfBlob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `Clinical_Report_${diseaseCode}_${patId}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                    } catch (fallbackErr) {
                        alert('PDF download error: ' + fallbackErr.message);
                    }
                }
            });
        }

        // 2. JSON Download Button
        const btnDownloadJson = document.getElementById('btn-download-json');
        if (btnDownloadJson) {
            btnDownloadJson.addEventListener('click', () => {
                try {
                    const payload = report.json_payload || report;
                    const jsonStr = JSON.stringify(payload, null, 2);
                    const blob = new Blob([jsonStr], { type: 'application/json;charset=utf-8' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Structured_Report_${diseaseCode}_${patId}.json`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } catch (err) {
                    alert('JSON download error: ' + err.message);
                }
            });
        }

        // 3. Markdown Download Button
        const btnDownloadMarkdown = document.getElementById('btn-download-markdown') || document.getElementById('btn-download-report');
        if (btnDownloadMarkdown) {
            btnDownloadMarkdown.addEventListener('click', async () => {
                try {
                    const res = await apiFetch('/api/export-report', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            markdown_report: report.markdown_report,
                            patient_id: patId,
                            disease: diseaseCode
                        })
                    });
                    const blob = await res.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Clinical_Report_${diseaseCode}_${patId}.md`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } catch (err) {
                    // Fallback to direct client-side blob if API call is unauthorized or fails
                    const content = report.markdown_report || report.text_report || JSON.stringify(report, null, 2);
                    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `Clinical_Report_${diseaseCode}_${patId}.md`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                }
            });
        }
    }

    // --- COUNTERFACTUAL WHAT-IF MODAL CONTROLLER ---
    const modalWhatIf = document.getElementById('modal-what-if');
    const btnCloseWhatIfModal = document.getElementById('btn-close-whatif-modal');
    const btnCloseWhatIfFooter = document.getElementById('btn-close-whatif-footer');
    const btnResetWhatIf = document.getElementById('btn-reset-whatif');
    const btnRunWhatIf = document.getElementById('btn-run-whatif');
    const btnOpenWhatIf = document.getElementById('btn-open-whatif');
    const whatIfModalError = document.getElementById('whatif-modal-error');
    const whatIfLockBanner = document.getElementById('whatif-lock-banner');
    const whatIfLockText = document.getElementById('whatif-lock-text');
    const whatIfActiveContent = document.getElementById('whatif-active-content');
    const whatIfDiseaseBadge = document.getElementById('whatif-disease-badge');
    const whatIfFeaturesGrid = document.getElementById('whatif-features-grid');
    const whatIfDiffContainer = document.getElementById('whatif-diff-container');
    const whatIfDiffTbody = document.getElementById('whatif-diff-tbody');

    const whatIfOrigProbEl = document.getElementById('whatif-orig-prob');
    const whatIfOrigStatusEl = document.getElementById('whatif-orig-status');
    const whatIfOrigLabelEl = document.getElementById('whatif-orig-label');
    const whatIfSimProbEl = document.getElementById('whatif-sim-prob');
    const whatIfSimStatusEl = document.getElementById('whatif-sim-status');
    const whatIfSimLabelEl = document.getElementById('whatif-sim-label');
    const whatIfDeltaBadgeEl = document.getElementById('whatif-delta-badge');
    const whatIfDeltaPointsEl = document.getElementById('whatif-delta-points');
    const whatIfDirectionTextEl = document.getElementById('whatif-direction-text');

    // Request tracking and AbortController to prevent race conditions and stale overwrites
    let activeWhatIfController = null;
    let latestWhatIfRequestId = 0;

    function invalidateWhatIfResults() {
        // Immediately clear and hide Modified Features Breakdown
        if (whatIfDiffTbody) whatIfDiffTbody.innerHTML = '';
        if (whatIfDiffContainer) whatIfDiffContainer.classList.add('hidden');

        // Immediately set simulation card to clear loading state
        if (whatIfSimProbEl) whatIfSimProbEl.textContent = '...';
        if (whatIfSimStatusEl) {
            whatIfSimStatusEl.textContent = 'CALCULATING...';
            whatIfSimStatusEl.className = 'whatif-status-badge status-calculating';
        }
        if (whatIfSimLabelEl) whatIfSimLabelEl.textContent = 'Evaluating changes...';

        // Immediately set delta to clear calculating state
        if (whatIfDeltaPointsEl) whatIfDeltaPointsEl.textContent = '...';
        if (whatIfDeltaBadgeEl) whatIfDeltaBadgeEl.className = 'whatif-delta-pill delta-neutral';
        if (whatIfDirectionTextEl) whatIfDirectionTextEl.textContent = 'Updating...';

        // Clear any previous error
        if (whatIfModalError) {
            whatIfModalError.classList.add('hidden');
            whatIfModalError.textContent = '';
        }

        if (btnRunWhatIf) {
            btnRunWhatIf.disabled = true;
            btnRunWhatIf.innerHTML = '<span>⏳ Simulating...</span>';
        }
    }

    function closeWhatIfModal() {
        if (activeWhatIfController) {
            activeWhatIfController.abort();
            activeWhatIfController = null;
        }
        latestWhatIfRequestId++;
        if (modalWhatIf) modalWhatIf.classList.add('hidden');
    }

    function areWhatIfInputsValid() {
        if (!whatIfFeaturesGrid) return false;
        const inputs = whatIfFeaturesGrid.querySelectorAll('.whatif-input');
        if (inputs.length === 0) return false;
        for (const input of inputs) {
            const val = input.value;
            if (val === undefined || val === null || String(val).trim() === '') {
                return false;
            }
            if (input.type === 'number') {
                const num = Number(val);
                if (isNaN(num) || !isFinite(num) || num < 0) {
                    return false;
                }
            }
        }
        return true;
    }

    function gatherWhatIfModifiedFeatures() {
        if (!whatIfFeaturesGrid) return {};
        const inputs = whatIfFeaturesGrid.querySelectorAll('.whatif-input');
        const modified = { ...(state.whatIfOriginalFeatures || {}) };
        inputs.forEach(input => {
            const name = input.name;
            const val = input.value;
            if (val !== undefined && val !== null && String(val).trim() !== '') {
                if (input.type === 'number') {
                    const num = parseFloat(val);
                    modified[name] = isNaN(num) ? val : num;
                } else if (!isNaN(val) && String(val).trim() !== '') {
                    modified[name] = parseFloat(val);
                } else {
                    modified[name] = val;
                }
            }
        });
        return modified;
    }

    async function openWhatIfModal() {
        if (!modalWhatIf) return;

        // Abort any lingering background simulation
        if (activeWhatIfController) {
            activeWhatIfController.abort();
            activeWhatIfController = null;
        }
        latestWhatIfRequestId++;

        const diseaseId = state.selectedDisease?.id || state.currentReport?.disease || 'diabetes';
        const diseaseObj = state.diseases.find(d => d.id === diseaseId);
        const diseaseTitle = diseaseObj?.title || diseaseId.replace(/_/g, ' ').toUpperCase();

        if (whatIfDiseaseBadge) whatIfDiseaseBadge.textContent = diseaseTitle;
        if (whatIfModalError) {
            whatIfModalError.classList.add('hidden');
            whatIfModalError.textContent = '';
        }

        // Check Chronic Liver governance lock
        if (diseaseId === 'Chronic_liver') {
            if (whatIfLockBanner) whatIfLockBanner.classList.remove('hidden');
            if (whatIfLockText) {
                whatIfLockText.textContent = 'What-If Simulation for Chronic Liver Disease is temporarily locked pending approval of the corrected model.';
            }
            if (whatIfActiveContent) whatIfActiveContent.classList.add('hidden');
            if (btnRunWhatIf) btnRunWhatIf.classList.add('hidden');
            if (btnResetWhatIf) btnResetWhatIf.classList.add('hidden');
            modalWhatIf.classList.remove('hidden');
            return;
        }

        // Active supported disease (e.g. diabetes, heart_disease, Stroke)
        if (whatIfLockBanner) whatIfLockBanner.classList.add('hidden');
        if (whatIfActiveContent) whatIfActiveContent.classList.remove('hidden');
        if (btnRunWhatIf) btnRunWhatIf.classList.remove('hidden');
        if (btnResetWhatIf) btnResetWhatIf.classList.remove('hidden');

        // Retrieve baseline features
        let baseline = state.currentPatientFeatures;
        if (!baseline && state.selectedHistoryItem?.clinical_input_data) {
            baseline = typeof state.selectedHistoryItem.clinical_input_data === 'string'
                ? JSON.parse(state.selectedHistoryItem.clinical_input_data)
                : state.selectedHistoryItem.clinical_input_data;
        }
        if (!baseline && diseaseObj?.demo_patient) {
            baseline = diseaseObj.demo_patient;
        }
        if (!baseline) {
            alert('Baseline patient features could not be loaded for simulation.');
            return;
        }

        state.whatIfOriginalFeatures = JSON.parse(JSON.stringify(baseline));

        // Render features in form grid
        renderWhatIfFeaturesGrid(diseaseId, diseaseObj, state.whatIfOriginalFeatures);

        modalWhatIf.classList.remove('hidden');

        // Run initial simulation with unmodified features to establish baseline parity (Delta: 0.0 pp)
        await executeWhatIfSimulation(diseaseId, state.whatIfOriginalFeatures, state.whatIfOriginalFeatures);
    }

    function renderWhatIfFeaturesGrid(diseaseId, diseaseObj, features) {
        if (!whatIfFeaturesGrid) return;
        const schemaFeatures = diseaseObj?.features || [];
        const featNames = Object.keys(features);

        let gridHtml = '';
        featNames.forEach(featName => {
            const val = features[featName];
            const schemaItem = schemaFeatures.find(f => f.name === featName);
            const label = schemaItem?.label || featName.replace(/_/g, ' ').toUpperCase();
            const type = schemaItem?.type || (typeof val === 'number' ? 'numeric' : 'text');
            const options = schemaItem?.options || [];

            gridHtml += `
                <div class="whatif-field-group" data-feature="${featName}">
                    <label class="whatif-field-label">
                        <span>${escapeHtml(label)}</span>
                        <span class="whatif-field-orig-val">Baseline: ${escapeHtml(String(val))}</span>
                    </label>
            `;

            if (type === 'categorical' && options.length > 0) {
                gridHtml += `<select class="whatif-input" name="${featName}" data-original="${escapeHtml(String(val))}">`;
                options.forEach(opt => {
                    const selected = String(opt.value).toLowerCase() === String(val).toLowerCase() ? 'selected' : '';
                    gridHtml += `<option value="${escapeHtml(String(opt.value))}" ${selected}>${escapeHtml(opt.label)}</option>`;
                });
                gridHtml += `</select>`;
            } else {
                const step = featName === 'ST_depression' ? '0.1' : (Number.isInteger(Number(val)) ? '1' : '0.1');
                gridHtml += `
                    <input type="number" step="${step}" class="whatif-input" name="${featName}" 
                           value="${val}" data-original="${val}" autocomplete="off">
                `;
            }

            gridHtml += `</div>`;
        });

        whatIfFeaturesGrid.innerHTML = gridHtml;

        // Attach change listeners to highlight modified fields and dynamically recalculate simulation
        const inputs = whatIfFeaturesGrid.querySelectorAll('.whatif-input');
        inputs.forEach(input => {
            const handleModification = () => {
                const orig = input.getAttribute('data-original');
                const cur = input.value;
                const grp = input.closest('.whatif-field-group');
                if (grp) {
                    if (String(cur).trim() !== String(orig).trim()) {
                        grp.classList.add('modified');
                    } else {
                        grp.classList.remove('modified');
                    }
                }

                // REQUIREMENT 2 & 3: Immediately invalidate and clear previous results upon input change
                invalidateWhatIfResults();

                // REQUIREMENT 6: Abort any prior in-flight request immediately
                if (activeWhatIfController) {
                    activeWhatIfController.abort();
                    activeWhatIfController = null;
                }

                // If inputs are currently incomplete/invalid, remain in waiting state
                if (!areWhatIfInputsValid()) {
                    if (whatIfSimProbEl) whatIfSimProbEl.textContent = '--%';
                    if (whatIfSimStatusEl) {
                        whatIfSimStatusEl.textContent = 'AWAITING INPUT';
                        whatIfSimStatusEl.className = 'whatif-status-badge status-not-detected';
                    }
                    if (whatIfSimLabelEl) whatIfSimLabelEl.textContent = 'Please enter valid clinical values';
                    if (whatIfDeltaPointsEl) whatIfDeltaPointsEl.textContent = '0.0';
                    if (whatIfDeltaBadgeEl) whatIfDeltaBadgeEl.className = 'whatif-delta-pill delta-neutral';
                    if (whatIfDirectionTextEl) whatIfDirectionTextEl.textContent = 'No Change';
                    if (btnRunWhatIf) {
                        btnRunWhatIf.disabled = true;
                        btnRunWhatIf.innerHTML = '<span>⚡ Re-run Simulation</span>';
                    }
                    return;
                }

                // REQUIREMENT 4 & 8: Recalculate immediately with latest input state (no setTimeout delay)
                const currentDiseaseId = state.selectedDisease?.id || state.currentReport?.disease || 'heart_disease';
                const modFeatures = gatherWhatIfModifiedFeatures();
                executeWhatIfSimulation(currentDiseaseId, state.whatIfOriginalFeatures, modFeatures);
            };

            input.addEventListener('input', handleModification);
            input.addEventListener('change', handleModification);
        });
    }

    async function executeWhatIfSimulation(diseaseId, origFeatures, modFeatures) {
        if (!whatIfOrigProbEl || !whatIfSimProbEl) return;

        // Abort prior in-flight request if still running
        if (activeWhatIfController) {
            activeWhatIfController.abort();
            activeWhatIfController = null;
        }

        // Invalidate results and show clear loading state
        invalidateWhatIfResults();

        const controller = new AbortController();
        activeWhatIfController = controller;
        const currentRequestId = ++latestWhatIfRequestId;
        const snapshotJson = JSON.stringify(modFeatures);

        try {
            const res = await apiFetch('/api/what-if', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    disease: diseaseId,
                    original_features: origFeatures,
                    modified_features: modFeatures
                }),
                signal: controller.signal
            });

            // REQUIREMENT 6: Drop response if a newer request was dispatched or this request was aborted
            if (currentRequestId !== latestWhatIfRequestId || controller.signal.aborted) {
                return;
            }

            const data = await res.json();

            // Check again after json parsing
            if (currentRequestId !== latestWhatIfRequestId || controller.signal.aborted) {
                return;
            }

            // REQUIREMENT 1 & 5: Ensure currently displayed clinical input values match this snapshot
            const currentDomFeatures = gatherWhatIfModifiedFeatures();
            if (JSON.stringify(currentDomFeatures) !== snapshotJson) {
                // DOM has moved on to different values while request was in-flight; drop stale result!
                return;
            }

            if (data.status === 'success') {
                // Update Baseline Card
                whatIfOrigProbEl.textContent = data.original.probability_formatted;
                whatIfOrigStatusEl.textContent = data.original.clinical_status;
                whatIfOrigStatusEl.className = 'whatif-status-badge ' +
                    (data.original.clinical_status === 'DETECTED' ? 'status-detected' : 'status-not-detected');
                whatIfOrigLabelEl.textContent = data.original.predicted_label;

                // Update Counterfactual Card
                whatIfSimProbEl.textContent = data.counterfactual.probability_formatted;
                whatIfSimStatusEl.textContent = data.counterfactual.clinical_status;
                whatIfSimStatusEl.className = 'whatif-status-badge ' +
                    (data.counterfactual.clinical_status === 'DETECTED' ? 'status-detected' : 'status-not-detected');
                whatIfSimLabelEl.textContent = data.counterfactual.predicted_label;

                // Update Delta
                const pts = data.delta.percentage_points_change;
                whatIfDeltaPointsEl.textContent = (pts > 0 ? '+' : '') + pts.toFixed(2);
                if (data.delta.direction === 'decrease' || pts < 0) {
                    whatIfDeltaBadgeEl.className = 'whatif-delta-pill delta-decrease';
                    whatIfDirectionTextEl.textContent = 'DECREASE';
                } else if (data.delta.direction === 'increase' || pts > 0) {
                    whatIfDeltaBadgeEl.className = 'whatif-delta-pill delta-increase';
                    whatIfDirectionTextEl.textContent = 'INCREASE';
                } else {
                    whatIfDeltaBadgeEl.className = 'whatif-delta-pill delta-neutral';
                    whatIfDirectionTextEl.textContent = 'NO CHANGE';
                }

                // Update Modified Features Table
                const diffs = data.modified_features || [];
                if (diffs.length > 0 && whatIfDiffTbody && whatIfDiffContainer) {
                    let diffRows = '';
                    diffs.forEach(d => {
                        const deltaStr = d.delta !== null && d.delta !== undefined
                            ? `<span class="${d.delta > 0 ? 'whatif-delta-positive' : 'whatif-delta-negative'}">${(d.delta > 0 ? '+' : '') + d.delta}</span>`
                            : '<span>Changed</span>';
                        diffRows += `
                            <tr>
                                <td><strong>${escapeHtml(d.label || d.feature)}</strong></td>
                                <td>${escapeHtml(String(d.original_value))}</td>
                                <td>${escapeHtml(String(d.counterfactual_value))}</td>
                                <td>${deltaStr}</td>
                            </tr>
                        `;
                    });
                    whatIfDiffTbody.innerHTML = diffRows;
                    whatIfDiffContainer.classList.remove('hidden');
                } else if (whatIfDiffContainer) {
                    whatIfDiffContainer.classList.add('hidden');
                    if (whatIfDiffTbody) whatIfDiffTbody.innerHTML = '';
                }
            } else {
                if (whatIfModalError) {
                    whatIfModalError.textContent = data.detail || 'Simulation request failed.';
                    whatIfModalError.classList.remove('hidden');
                }
            }
        } catch (err) {
            if (err.name === 'AbortError' || currentRequestId !== latestWhatIfRequestId) {
                // Silently ignore aborted or outdated requests
                return;
            }
            if (whatIfModalError) {
                whatIfModalError.textContent = err.message || 'Simulation error.';
                whatIfModalError.classList.remove('hidden');
            }
        } finally {
            if (currentRequestId === latestWhatIfRequestId) {
                if (btnRunWhatIf) {
                    btnRunWhatIf.disabled = false;
                    btnRunWhatIf.innerHTML = '<span>⚡ Re-run Simulation</span>';
                }
            }
        }
    }

    if (btnRunWhatIf) {
        btnRunWhatIf.addEventListener('click', async () => {
            if (!areWhatIfInputsValid()) return;
            const diseaseId = state.selectedDisease?.id || state.currentReport?.disease || 'heart_disease';
            const modFeatures = gatherWhatIfModifiedFeatures();
            await executeWhatIfSimulation(diseaseId, state.whatIfOriginalFeatures, modFeatures);
        });
    }

    if (btnResetWhatIf) {
        btnResetWhatIf.addEventListener('click', async () => {
            if (!whatIfFeaturesGrid || !state.whatIfOriginalFeatures) return;
            const diseaseId = state.selectedDisease?.id || state.currentReport?.disease || 'heart_disease';
            const inputs = whatIfFeaturesGrid.querySelectorAll('.whatif-input');
            inputs.forEach(input => {
                const orig = input.getAttribute('data-original');
                input.value = orig;
                const grp = input.closest('.whatif-field-group');
                if (grp) grp.classList.remove('modified');
            });
            await executeWhatIfSimulation(diseaseId, state.whatIfOriginalFeatures, state.whatIfOriginalFeatures);
        });
    }

    if (btnCloseWhatIfModal) {
        btnCloseWhatIfModal.addEventListener('click', closeWhatIfModal);
    }

    if (btnCloseWhatIfFooter) {
        btnCloseWhatIfFooter.addEventListener('click', closeWhatIfModal);
    }

    if (modalWhatIf) {
        modalWhatIf.addEventListener('click', (e) => {
            if (e.target === modalWhatIf) {
                closeWhatIfModal();
            }
        });
    }

    // Expose for runtime inspection and testing
    window.renderReportResults = renderReportResults;
    window.navigateTo = navigateTo;
    window.openWhatIfModal = openWhatIfModal;
    window.invalidateWhatIfResults = invalidateWhatIfResults;
    window.gatherWhatIfModifiedFeatures = gatherWhatIfModifiedFeatures;
    window.executeWhatIfSimulation = executeWhatIfSimulation;
});
