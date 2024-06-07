// custom.js
document.querySelectorAll('.recording').forEach(item => {
    item.addEventListener('click', event => {
        const audioSrc = event.target.dataset.audio;
        const transcriptSrc = event.target.dataset.transcript;
        // Load and play audio
        // Load and display transcript
    });
});
 
