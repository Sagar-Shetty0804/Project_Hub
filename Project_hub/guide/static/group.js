
btn = document.getElementById('submitBtn');
const codeBlock = document.querySelector('pre');
const lines = codeBlock.textContent.split('\n');


btn.addEventListener('click', () => {
    lines.forEach((line, index) => {
        const lineNumber = index + 1;
        const currentUrl = window.location.href;
        const newUrl = `${currentUrl}?line_number=${lineNumber}`;
        window.location.href = newUrl;
        
      });
});

