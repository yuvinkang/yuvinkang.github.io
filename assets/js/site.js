// Scroll effects: fade sections in, highlight the current side tab, fill the progress line.
(function () {
  var reveals = document.querySelectorAll('.reveal');
  var tabs = document.querySelectorAll('.tab[data-target]');
  var sections = document.querySelectorAll('.section[id]');
  var progress = document.querySelector('.sidenav');
  var hero = document.querySelector('.hero-inner');

  // 1. Fade each section in as it enters the screen
  if ('IntersectionObserver' in window) {
    var revealObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); revealObs.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { revealObs.observe(el); });

    // 2. Highlight the tab for the section in the middle of the screen
    if (sections.length) {
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          tabs.forEach(function (t) { t.classList.toggle('active', t.dataset.target === e.target.id); });
        });
      }, { rootMargin: '-45% 0px -50% 0px' });
      sections.forEach(function (s) { spy.observe(s); });
    }
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // 2b. Only animate stick-figure scenes while they're on screen
  var scenes = document.querySelectorAll('.scene');
  if ('IntersectionObserver' in window) {
    var sceneObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { e.target.classList.toggle('in-view', e.isIntersecting); });
    }, { rootMargin: '80px 0px' });
    scenes.forEach(function (s) { sceneObs.observe(s); });
  } else {
    scenes.forEach(function (s) { s.classList.add('in-view'); });
  }

  // 3. Progress line + gentle hero fade as you scroll away
  function onScroll() {
    var y = window.scrollY, max = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.setProperty('--progress', max > 0 ? Math.min(y / max, 1) : 0);
    if (hero) {
      var f = Math.min(y / (window.innerHeight * 0.7), 1);
      hero.style.opacity = 1 - f;
      hero.style.transform = 'translateY(' + (f * -30) + 'px)';
    }
    if (sections.length && y < window.innerHeight * 0.4) tabs.forEach(function (t) { t.classList.remove('active'); });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
