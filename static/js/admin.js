async function generateUniversalCode() {
    const response = await fetch('/generate_universal_code', { method: 'POST' });
    const data = await response.json();
    document.getElementById('universal-code').innerText = 'Uniwersalny kod: ' + data.code;
}

async function generateTemporaryCode() {
    const response = await fetch('/generate_temporary_code', { method: 'POST' });
    const data = await response.json();
    alert('Wygenerowany kod tymczasowy: ' + data.code);
    location.reload();
}

async function resetPassword(userId) {
    const newPassword = prompt('Podaj nowe hasło dla użytkownika o ID: ' + userId);
    if (newPassword) {
        const response = await fetch('/reset_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'user_id': userId,
                'new_password': newPassword,
            })
        });

        const data = await response.json();
        alert(data.message);
        location.reload();
    }
}

