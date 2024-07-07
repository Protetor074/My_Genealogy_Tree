async function handleRegistration(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const accessKey = document.getElementById('access_key').value;

    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            'username': username,
            'password': password,
            'access_key': accessKey
        })
    });

    const data = await response.json();

    const messageContainer = document.getElementById('message-container');
    messageContainer.innerHTML = '';

    if (data.success) {
        window.location.href = data.redirect;
    } else {
        const message = document.createElement('div');
        message.className = 'message danger';
        message.textContent = data.message;
        messageContainer.appendChild(message);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    registerForm.addEventListener('submit', handleRegistration);
});
