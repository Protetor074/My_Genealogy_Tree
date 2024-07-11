var personId = document.querySelector('.modify-button').getAttribute('data-person-id');
var owner = document.querySelector('.modify-button').getAttribute('data-owner');

var buttons = document.querySelectorAll('.add-photo-button, .modify-button, .remove-photo-button');

if (owner !== personId) {
    buttons.forEach(function (button) {
        //button.disabled = true;
        //button.style.backgroundColor = 'grey';
        //button.style.cursor = 'not-allowed';
    });
}


document.addEventListener('DOMContentLoaded', function () {

    document.getElementById('remove_person_form').addEventListener('submit', function (event) {
        event.preventDefault(); // Zapobiegaj domyślnemu wysyłaniu formularza

        // Zapytaj użytkownika o hasło
        var password = prompt("Proszę wprowadzić swoje hasło, aby potwierdzić usunięcie:");

        if (password === null) {
            // Jeśli użytkownik anulował prompt, przerwij
            return;
        }

        var xhr = new XMLHttpRequest();
        xhr.open('POST', this.action, true);
        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        xhr.onload = function () {
            var response = JSON.parse(xhr.responseText);
            if (xhr.status === 200) {
                alert(response.message); // Komunikat
                window.location.href = '/user_page';
            } else {
                alert(response.error); // Komunikat o błędzie
            }
        };

        var params = 'password=' + encodeURIComponent(password);
        xhr.send(params);
    });

});
