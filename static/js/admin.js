async function generateAccessKey(event) {
    event.preventDefault();
    const level = document.getElementById('level').value;
    const expirationDate = document.getElementById('expiration_date').value;
    fetch('/generate_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({level, expiration_date: expirationDate})
    })
        .then(response => response.json())
        .then(data => {
            alert(`Generated Key: ${data.key}`);
            location.reload();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

async function deleteKey(key) {
    if (confirm(`Czy na pewno chcesz usunąć klucz: ${key}?`)) {
        fetch('/delete_key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'key': key
            })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
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

async function updateUserKey(userId) {
    const newKey = document.getElementById(`new-key-${userId}`).value;
    const response = await fetch('/update_user_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'user_id': userId,
            'new_key': newKey,
        })
    });

    const data = await response.json();
    alert(data.message);
    location.reload();
}

function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        for (let j = 0; j < cells.length; j++) {
            if (cells[j]) {
                if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        rows[i].style.display = found ? '' : 'none';
    }
}

async function deleteLog(logId) {

    fetch('/delete_logs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({log_ids: [logId]})
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Log deleted successfully');
                location.reload();
            } else {
                alert('Failed to delete log');
            }
        });

}

async function deleteSelectedLogs() {
    const checkboxes = document.querySelectorAll('.log-checkbox:checked');
    const logIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    if (logIds.length > 0) {
        fetch('/delete_logs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({log_ids: logIds})
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Selected logs deleted successfully');
                    location.reload();
                } else {
                    alert('Failed to delete selected logs');
                }
            });
    }
}

function toggleAllCheckboxes(source) {
    const checkboxes = document.querySelectorAll('.log-checkbox');
    for (const checkbox of checkboxes) {
        checkbox.checked = source.checked;
    }
}