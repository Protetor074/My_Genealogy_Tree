async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            'username': username,
            'password': password
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
