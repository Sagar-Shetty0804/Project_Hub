document.addEventListener('DOMContentLoaded', function() 
{
    // Password update functionality
    const updatePasswordBtn = document.querySelector('.update');
    updatePasswordBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (newPassword !== confirmPassword) {
            alert('New passwords do not match!');
        } 
        else {
            // Here you would typically send this data to a server to update the password
            alert('Password updated successfully!');
        }
    });

    // Logout functionality
    const logoutBtn = document.querySelector('.logout');
    logoutBtn.addEventListener('click', function() {
        // Here you would typically clear session data and redirect to login page
        alert('Logging out...');
        // window.location.href = 'login.html';
    });

    // Account deletion
    const deleteAccountBtn = document.querySelector('.deletion');
    deleteAccountBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
            // Here you would typically send a request to the server to delete the account
            alert('Account deleted successfully.');
            // window.location.href = 'homepage.html';
        }
    });

    // Get elements
    const popupBtn = document.getElementById('popupBtn');
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