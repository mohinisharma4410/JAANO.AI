function generateContent() {
    const title = document.getElementById('title').value;
    const article = document.getElementById('article').value;
    const image = document.getElementById('image').files[0];

    const formData = new FormData();
    formData.append('title', title);
    formData.append('article', article);
    if (image) {
        formData.append('image', image);
    }

    // Show loading spinner
    document.getElementById('overlay').style.display = 'flex';

    fetch('/generate_video', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading spinner
        document.getElementById('overlay').style.display = 'none';
        if (data.success) {
            alert('Video generated successfully! Redirecting to the video gallery.');
            redirectToGallery(); // Redirect to gallery page
        } else {
            alert('Failed to generate video.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Hide loading spinner
        document.getElementById('overlay').style.display = 'none';
        alert('An error occurred while generating the video.');
    });
}

function redirectToGallery() {
    window.location.href = '/gallery';
}
function showPopup() {
    const title = document.getElementById('title').value;
    const article = document.getElementById('article').value;
    const image = document.getElementById('image').files[0];
    
    document.getElementById('popup-title').innerText = title;
    document.getElementById('popup-article').innerText = article;

    if (image) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const popupImage = document.getElementById('popup-image');
            popupImage.src = e.target.result;
            popupImage.style.display = 'block';
        };
        reader.readAsDataURL(image);
    } else {
        document.getElementById('popup-image').style.display = 'none';
    }

    document.getElementById('popup').style.display = 'flex';
}

function closePopup() {
    document.getElementById('popup').style.display = 'none';
}

function submitForm() {
    document.getElementById('popup').style.display = 'none';
    document.getElementById('articleForm').submit();
}
