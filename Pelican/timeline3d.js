(function() {
    function initTimeline3D() {
        var container = document.querySelector('.timeline-container');
        if (!container) {
            return;
        }

        container.classList.add('timeline-3d-container');

        var items = container.querySelectorAll('.timeline-item');
        var depthStep = 100;
        var z = 0;

        items.forEach(function(item) {
            item.style.transform = 'translateZ(' + z + 'px)';
            z -= depthStep;
        });
    }

    window.initTimeline3D = initTimeline3D;
})();
