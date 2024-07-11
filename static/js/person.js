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
