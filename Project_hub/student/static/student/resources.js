document.addEventListener('DOMContentLoaded', function() 
{
      

    

    // Get elements
    const popupBtn = document.getElementById('addLink');
    const popup = document.getElementById('myPopup');
    const overlay = document.getElementById('overlay');

    // Open popup
    popupBtn.addEventListener('click', function(e) {
        e.preventDefault();
        popup.style.display = 'block';
        overlay.style.display = 'block';
    });

    // Close popup function (moved outside to be accessible globally)
    window.closePopup = function() {
        popup.style.display = 'none';
        overlay.style.display = 'none';
    };

    // Close popup when clicking outside
    window.addEventListener('click', function(e) {
        if (e.target == overlay) {
            closePopup();
        }
    });

    // Add event listener for a close button if you have one
    const closeBtn = document.querySelector('.close-btn'); // Assuming you have a close button with this class
    if (closeBtn) {
        closeBtn.addEventListener('click', closePopup);
    }
});