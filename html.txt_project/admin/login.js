const emailOtpBox = document.getElementById('emailOtpBox');
const emailStatus = document.getElementById('emailStatus');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const confirmPasswordStatus = document.getElementById('confirmPasswordStatus');
const addressPanel = document.getElementById('addressPanel');
const submitButton = document.getElementById('submitButton');
const passwordRequirements = document.getElementById('passwordRequirements');
const phoneInput = document.getElementById('phone');
const editParams = new URLSearchParams(window.location.search);
const editMode = editParams.get('edit') === '1';

const generatedOtps = {
  email: '',
};

const verificationState = {
  email: false,
};

function setStatus(element, message, type) {
  element.textContent = message;
  element.classList.remove('success', 'error');
  if (type) {
    element.classList.add(type);
  }
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePassword(password) {
  return password.length > 8
    && /[A-Z]/.test(password)
    && /[a-z]/.test(password)
    && /[0-9]/.test(password)
    && /[^A-Za-z0-9]/.test(password);
}

function updatePasswordRequirements() {
  const password = passwordInput.value;
  passwordRequirements.open = password.length > 0;
  const rules = {
    length: password.length > 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };

  Object.entries(rules).forEach(([rule, valid]) => {
    document.querySelector(`[data-rule="${rule}"]`).classList.toggle('valid', valid);
  });

  const passwordsMatch = password.length > 0 && password === confirmPasswordInput.value;
  const ready = validatePassword(password) && passwordsMatch;
  addressPanel.inert = !ready;
  submitButton.disabled = !ready;

  if (!confirmPasswordInput.value) {
    setStatus(confirmPasswordStatus, '', '');
  } else if (passwordsMatch) {
    setStatus(confirmPasswordStatus, 'Passwords match.', 'success');
  } else {
    setStatus(confirmPasswordStatus, 'Passwords do not match.', 'error');
  }
}

function readEmailFromUrl() {
  return editParams.get('email') || '';
}

async function initializeEditMode() {
  const email = readEmailFromUrl();
  if (!email) {
    window.location.href = '../profile.html';
    return;
  }

  document.querySelector('.eyebrow').textContent = 'Account settings';
  document.querySelector('h1').textContent = 'Update your details';
  document.getElementById('email').value = email;
  document.getElementById('email').readOnly = true;
  document.getElementById('sendEmailOtp').closest('.otp-group').classList.add('hidden');
  emailOtpBox.classList.add('hidden');
  document.querySelectorAll('.password-field').forEach((field) => field.classList.add('hidden'));
  passwordInput.required = false;
  confirmPasswordInput.required = false;
  addressPanel.open = true;
  addressPanel.inert = false;
  submitButton.disabled = false;
  submitButton.textContent = 'Save and Update';

  try {
    const response = await fetch('http://localhost:8000/api/user-details', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const result = await response.json();
    if (!response.ok || !result.success) throw new Error(result.message || 'Unable to load account details.');
    const user = result.user;
    document.getElementById('name').value = user.name || '';
    document.getElementById('dob').value = user.dob || '';
    document.querySelectorAll('input[name="gender"]').forEach((input) => {
      input.checked = input.value === user.gender;
    });
    phoneInput.value = user.phone || '';
    document.getElementById('building').value = user.building_no || '';
    document.getElementById('locality').value = user.locality || '';
    document.getElementById('city').value = user.city || '';
    document.getElementById('district').value = user.district || '';
    document.getElementById('country').value = user.country || '';
    document.getElementById('pincode').value = user.pincode || '';
    document.getElementById('landmark').value = user.landmark || '';
  } catch (error) {
    setStatus(emailStatus, error.message || 'Unable to load account details.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const initialEmail = readEmailFromUrl();
  if (initialEmail) {
    document.getElementById('email').value = initialEmail;
  }
  if (editMode) initializeEditMode();
});

document.querySelectorAll('.password-toggle').forEach((button) => {
  button.addEventListener('click', () => {
    const input = document.getElementById(button.dataset.target);
    const showing = input.type === 'text';
    input.type = showing ? 'password' : 'text';
    button.innerHTML = showing ? '&#128065;' : '&#128584;';
    button.setAttribute('aria-label', `${showing ? 'Show' : 'Hide'} ${input.id === 'password' ? 'password' : 'confirm password'}`);
  });
});

passwordInput.addEventListener('input', updatePasswordRequirements);
confirmPasswordInput.addEventListener('input', updatePasswordRequirements);

document.getElementById('sendEmailOtp').addEventListener('click', async () => {
  const email = document.getElementById('email').value.trim();

  if (!email || !validateEmail(email)) {
    setStatus(emailStatus, 'Please enter a valid email address first.', 'error');
    return;
  }

  try {
    const response = await fetch('http://localhost:8000/api/send-email-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || 'Unable to send OTP.');
    }

    verificationState.email = false;
    emailOtpBox.classList.remove('hidden');
    const deliveryMessage = result.developmentOtp
      ? `OTP sent successfully. Development OTP: ${result.developmentOtp}`
      : 'OTP sent successfully. Check your inbox.';
    setStatus(emailStatus, deliveryMessage, 'success');
  } catch (error) {
    setStatus(emailStatus, error.message || 'Unable to send OTP.', 'error');
  }
});

document.getElementById('verifyEmailOtp').addEventListener('click', async () => {
  const enteredOtp = document.getElementById('emailOtp').value.trim();
  const email = document.getElementById('email').value.trim();

  if (!email || !validateEmail(email)) {
    setStatus(emailStatus, 'Please enter a valid email address first.', 'error');
    return;
  }

  if (!enteredOtp || enteredOtp.length !== 6) {
    setStatus(emailStatus, 'Please enter the 6-digit OTP sent to your email.', 'error');
    return;
  }

  try {
    const response = await fetch('http://localhost:8000/api/verify-email-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp: enteredOtp }),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || 'OTP verification failed.');
    }

    verificationState.email = true;
    setStatus(emailStatus, 'Email verified successfully.', 'success');
  } catch (error) {
    verificationState.email = false;
    setStatus(emailStatus, error.message || 'Incorrect email OTP. Please try again.', 'error');
  }
});

document.getElementById('signupForm').addEventListener('submit', async (event) => {
  event.preventDefault();

  const formData = {
    name: document.getElementById('name').value.trim(),
    dob: document.getElementById('dob').value,
    gender: document.querySelector('input[name="gender"]:checked')?.value || '',
    email: document.getElementById('email').value.trim(),
    phone: phoneInput.value.trim(),
    building: document.getElementById('building').value.trim(),
    locality: document.getElementById('locality').value.trim(),
    city: document.getElementById('city').value.trim(),
    district: document.getElementById('district').value.trim(),
    country: document.getElementById('country').value.trim(),
    pincode: document.getElementById('pincode').value.trim(),
    landmark: document.getElementById('landmark').value.trim(),
    password: document.getElementById('password').value,
    confirmPassword: document.getElementById('confirmPassword').value,
  };

  const requiredFields = [
    formData.name,
    formData.dob,
    formData.gender,
    formData.email,
    formData.phone,
  ];

  if (requiredFields.some((field) => !field)) {
    alert('Please complete all required fields before submitting.');
    return;
  }

  if (!editMode && !verificationState.email) {
    alert('Please verify your email OTP before submitting.');
    return;
  }

  if (!editMode && !validatePassword(formData.password)) {
    alert('Password must be more than 8 characters and contain an uppercase letter, lowercase letter, number, and special character.');
    return;
  }

  if (!editMode && formData.password !== formData.confirmPassword) {
    alert('Passwords do not match.');
    return;
  }

  try {
    const response = await fetch(`http://localhost:8000/api/${editMode ? 'update-user' : 'register'}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || 'Unable to create account.');
    }

    if (editMode) {
      const session = JSON.parse(localStorage.getItem('whoosh_logged_in_user') || '{}');
      localStorage.setItem('whoosh_logged_in_user', JSON.stringify({ ...session, email: formData.email, name: formData.name }));
      alert('Your details were updated successfully.');
      window.location.href = '../profile.html';
      return;
    }

    alert('Account created successfully and saved to SQLite database!');
    event.target.reset();
    verificationState.email = false;
    generatedOtps.email = '';
    emailOtpBox.classList.add('hidden');
    setStatus(emailStatus, '', '');
    window.location.href = 'whoosh_babyco.html';
  } catch (error) {
    alert(error.message || 'There was an error creating the account.');
  }
});
