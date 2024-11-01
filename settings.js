// settings.js

document.addEventListener('DOMContentLoaded', function() {
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

    // Save recovery options
    const saveRecoveryBtn = document.querySelector('.save');
    saveRecoveryBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const phoneNumber = document.getElementById('phone number').value;

        // Here you would typically send this data to a server to save
        alert('Recovery options saved successfully!');
    });
    
    // Toggle dark mode
    const darkModeToggle = document.querySelector('.toggle-dark-button');
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
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

    // Save social accounts
    const saveSocialBtn = document.querySelector('#social .save');
    saveSocialBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const linkedInProfile = document.getElementById('link').value;
        const githubProfile = document.getElementById('link').value;

        // Here you would typically send this data to a server to save
        alert('Social accounts saved successfully!');
    });

    // Function to handle checkbox changes
    function handleCheckboxChange(section) {
        const checkboxes = section.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    checkboxes.forEach(cb => {
                        if (cb !== this) cb.checked = false;
                    });
                }
            });
        });
    }

    // Apply checkbox handling to notifications and accessibility sections
    handleCheckboxChange(document.getElementById('notifications'));
    handleCheckboxChange(document.getElementById('accesibility'));
});

// Get elements
const popupBtn = document.getElementById('popupBtn');
const popup = document.getElementById('myPopup');

// Open popup
popupBtn.addEventListener('click', function(e) {
    e.preventDefault();
    popup.style.display = 'block';
});

// Close popup
function closePopup() {
    popup.style.display = 'none';
}

// Close popup when clicking outside
window.addEventListener('click', function(e) {
    if (e.target == popup) {
        closePopup();
    }
});

const overlay = document.getElementById('overlay');

popupBtn.addEventListener('click', function(e) {
    e.preventDefault();
    popup.style.display = 'block';
    overlay.style.display = 'block';
});

function closePopup() {
    popup.style.display = 'none';
    overlay.style.display = 'none';
}