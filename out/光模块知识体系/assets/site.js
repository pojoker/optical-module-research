(() => {
  const toggle = document.getElementById('toggleQuestions');
  if (toggle) {
    let open = false;
    toggle.addEventListener('click', () => {
      open = !open;
      document.querySelectorAll('.q.more').forEach((el) => {
        el.style.display = open ? 'block' : 'none';
      });
      toggle.textContent = open ? '收起扩展问题' : '展开更多问题';
    });
  }

  const deepTabs = [...document.querySelectorAll('.deep-tab')];
  deepTabs.forEach((tab) => tab.addEventListener('click', () => {
    deepTabs.forEach((item) => item.setAttribute('aria-selected', 'false'));
    document.querySelectorAll('.deep-panel').forEach((panel) => panel.classList.remove('active'));
    tab.setAttribute('aria-selected', 'true');
    document.getElementById(`deep-panel-${tab.dataset.deepTab}`)?.classList.add('active');
  }));

  const companySearch = document.getElementById('companySearch');
  if (companySearch) {
    const rows = [...document.querySelectorAll('#companyTable tbody tr')];
    const count = document.getElementById('companyCount');
    companySearch.addEventListener('input', () => {
      const query = companySearch.value.trim().toLowerCase();
      let shown = 0;
      rows.forEach((row) => {
        const hit = !query || row.textContent.toLowerCase().includes(query);
        row.classList.toggle('hidden', !hit);
        if (hit) shown += 1;
      });
      if (count) count.textContent = `${shown} 条`;
    });
  }

  const companyMarkers = [...document.querySelectorAll('.company-marker')];
  companyMarkers.forEach((marker) => marker.addEventListener('click', (event) => {
    event.stopPropagation();
    const next = !marker.classList.contains('is-open');
    companyMarkers.forEach((item) => item.classList.remove('is-open'));
    marker.classList.toggle('is-open', next);
  }));
  document.addEventListener('click', () => companyMarkers.forEach((marker) => marker.classList.remove('is-open')));

  const localLinks = [...document.querySelectorAll('.local-nav a')];
  const localSections = localLinks.map((link) => document.querySelector(link.getAttribute('href'))).filter(Boolean);
  if ('IntersectionObserver' in window && localSections.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          localLinks.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`));
        }
      });
    }, { rootMargin: '-18% 0px -72% 0px' });
    localSections.forEach((section) => observer.observe(section));
  }
})();
