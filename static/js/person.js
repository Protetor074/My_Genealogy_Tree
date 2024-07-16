var personId = document.querySelector('.modify-button').getAttribute('data-person-id');
var owner = document.querySelector('.modify-button').getAttribute('data-owner');
var userId = document.querySelector('.modify-button').getAttribute('user-id');

var buttons = document.querySelectorAll('.add-photo-button, .modify-button, .remove-person-button, .file-label');
var buttons2 = document.querySelectorAll(' .remove-person-button');

if (owner !== personId && owner !== "1" && userId !== "1") {
    buttons.forEach(function (button) {
        button.disabled = true;
        button.style.backgroundColor = 'grey';
        button.style.cursor = 'not-allowed';
    });
}

if (owner !== personId && userId !== "1") {
    buttons2.forEach(function (button) {
        button.disabled = true;
        button.style.backgroundColor = 'grey';
        button.style.cursor = 'not-allowed';
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

document.addEventListener('DOMContentLoaded', () => {
    const infoBoxes = document.querySelectorAll('.info-box');

    infoBoxes.forEach(box => {
        const dateDisplay = box.querySelector('.date-display');
        const year = dateDisplay.textContent;
        const fullDate = dateDisplay.getAttribute('data-full-date');
        let showingFullDate = false;

        box.addEventListener('click', () => {
            if (showingFullDate) {
                dateDisplay.textContent = year;
            } else {
                dateDisplay.textContent = fullDate;
            }
            showingFullDate = !showingFullDate;
        });
    });
});