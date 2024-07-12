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


window.onload = function () {
    // Sprawdzenie szerokości ekranu
    if (window.innerWidth <= 768) {
        window.scrollTo(700, 300);
    }
};

// Opcjonalnie dodaj nasłuchiwacza zdarzeń na zmianę rozmiaru okna, aby dostosować przewijanie, gdy zmienia się rozmiar okna
window.onresize = function () {
    if (window.innerWidth <= 768) {
        window.scrollTo(700, 300);
    } else {
        window.scrollTo(0, 0); // Opcjonalnie można dodać powrót do góry strony na większych ekranach
    }
};