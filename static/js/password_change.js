document.addEventListener('DOMContentLoaded', function() {
    const changePasswordBtn = document.getElementById('change-password-btn');
    const passwordFields = document.getElementById('password-fields');
    const messageContainer = document.getElementById('message-container');

    changePasswordBtn.addEventListener('click', function() {
        // Sprawdź, czy formularz jest aktualnie widoczny
        const isFormVisible = passwordFields.style.display === 'block';

        // Jeśli formularz jest widoczny, ukryj go, w przeciwnym razie pokaż
        passwordFields.style.display = isFormVisible ? 'none' : 'block';
        changePasswordBtn.textContent = isFormVisible ? 'Zmień hasło' : 'Anuluj zmianę'; // Zmiana tekstu na przycisku

        // Wyczyść komunikaty przy każdym kliknięciu zmiany hasła
        messageContainer.innerHTML = '';
    });

    const changePasswordForm = document.getElementById('change-password-form');
    changePasswordForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const currentPassword = document.getElementById('current_password').value;
        const newPassword = document.getElementById('new_password').value;

        try {
            const response = await fetch('/change_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'current_password': currentPassword,
                    'new_password': newPassword
                })
            });

            const data = await response.json();

            if (data.success) {
                messageContainer.innerHTML = `<div class="message success">${data.message}</div>`;
                passwordFields.style.display = 'none'; // Ukryj formularz po udanej zmianie hasła
                changePasswordBtn.textContent = 'Zmień hasło'; // Przywróć tekst na przycisku
            } else {
                messageContainer.innerHTML = `<div class="message danger">${data.message}</div>`;
            }
        } catch (error) {
            console.error('Error:', error);
            messageContainer.innerHTML = `<div class="message danger">An error occurred. Please try again later.</div>`;
        }
    });
});
