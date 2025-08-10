document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.timeline-item');
  const platformIndex = {};
  const contactIndex = {};

  items.forEach(item => {
    const platform = item.dataset.platform || 'unknown';
    const contact = item.dataset.contact || 'unknown';

    if (!(platform in platformIndex)) {
      platformIndex[platform] = Object.keys(platformIndex).length;
    }
    if (!(contact in contactIndex)) {
      contactIndex[contact] = Object.keys(contactIndex).length;
    }

    const x = platformIndex[platform] * 200;
    const z = contactIndex[contact] * 200;
    item.style.transform = `translate3d(${x}px, 0px, ${z}px)`;
  });
});
