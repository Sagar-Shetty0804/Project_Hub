var delBtns = document.querySelector('.deleteSelectedButton');
var checkBoxes = document.querySelectorAll('.groupCheckbox');

var toggle = false; // This will act as a toggle switch

function editGroup() {
    console.log('clicked');
    toggle = !toggle; // Flip the toggle

    // Toggle display for delete buttons
    delBtns.style.display = toggle ? 'block' : 'none';

    // Toggle display for checkboxes
    checkBoxes.forEach(function(checkbox) {
        checkbox.style.display = toggle ? 'block' : 'none';
    });
}
