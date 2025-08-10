document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.timeline-item');
  const platformIndex = {};
  const contactCounts = {};

  items.forEach(item => {
    const platform = item.dataset.platform || 'unknown';
    const contact = item.dataset.contact || 'unknown';

    if (!(platform in platformIndex)) {
      platformIndex[platform] = Object.keys(platformIndex).length;
    }

    contactCounts[contact] = (contactCounts[contact] || 0) + 1;
  });

  const sortedContacts = Object.entries(contactCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([contact]) => contact);

  const contactIndex = {};
  sortedContacts.forEach((contact, index) => {
    contactIndex[contact] = index;
  });

  items.forEach(item => {
    const platform = item.dataset.platform || 'unknown';
    const contact = item.dataset.contact || 'unknown';

    const x = platformIndex[platform] * 200;
    const z = contactIndex[contact] * 200;
    item.style.transform = `translate3d(${x}px, 0px, ${z}px)`;
  });
});
