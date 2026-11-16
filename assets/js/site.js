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

  // 4. Revolving photo carousel, pushed by two stickmen
  document.querySelectorAll('[data-carousel]').forEach(function (c) {
    var stage = c.querySelector('.carousel-stage');
    var ring = c.querySelector('.carousel-ring');
    var slides = ring.querySelectorAll('.slide');
    var n = slides.length; if (!n) return;
    var step = 360 / n, idx = 0, angle = 0, pushTimer, autoTimer, hovering = false, visible = true;

    function layout() {
      var w = slides[0].offsetWidth || 200;
      var r = Math.round((w / 2) / Math.tan(Math.PI / Math.max(n, 3))) + 28;
      c.style.setProperty('--r', r + 'px');
    }
    function apply() {
      ring.style.transform = 'translateZ(calc(var(--r) * -1)) rotateY(' + angle + 'deg)';
      var front = ((Math.round(-angle / step) % n) + n) % n;
      slides.forEach(function (s, i) { s.classList.toggle('is-front', i === front); });
    }
    function push(dir, ms) {
      c.classList.remove('pushing-next', 'pushing-prev');
      c.classList.add(dir > 0 ? 'pushing-next' : 'pushing-prev');
      clearTimeout(pushTimer);
      pushTimer = setTimeout(function () { c.classList.remove('pushing-next', 'pushing-prev'); }, ms || 1200);
    }
    function go(dir) { idx += dir; angle = -idx * step; push(dir); apply(); }

    c.querySelectorAll('.carousel-btn').forEach(function (b) {
      b.addEventListener('click', function () { go(+b.dataset.dir); restartAuto(); });
    });

    // drag to spin
    var dragging = false, startX = 0, startAngle = 0, moved = 0;
    stage.addEventListener('pointerdown', function (e) {
      dragging = true; moved = 0; startX = e.clientX; startAngle = angle;
      ring.style.transition = 'none'; stage.classList.add('dragging');
      stage.setPointerCapture && stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var dx = e.clientX - startX; moved = Math.max(moved, Math.abs(dx));
      angle = startAngle + dx * 0.35;
      if (Math.abs(dx) > 4) push(dx < 0 ? 1 : -1, 400);
      apply();
    });
    function endDrag(e) {
      if (!dragging) return;
      dragging = false; ring.style.transition = ''; stage.classList.remove('dragging');
      if (moved < 5 && e && e.target) {
        var s = e.target.closest && e.target.closest('.slide');
        if (s) {
          var k = +s.dataset.index, cur = ((Math.round(-angle / step) % n) + n) % n;
          var d = ((k - cur) % n + n) % n; if (d > n / 2) d -= n;
          if (d) { idx = Math.round(-angle / step) + d; angle = -idx * step; push(d > 0 ? 1 : -1); apply(); restartAuto(); return; }
        }
      }
      idx = Math.round(-angle / step); angle = -idx * step; apply(); restartAuto();
    }
    stage.addEventListener('pointerup', endDrag);
    stage.addEventListener('pointercancel', endDrag);

    // gentle auto-spin (pauses on hover and when off-screen)
    c.addEventListener('mouseenter', function () { hovering = true; });
    c.addEventListener('mouseleave', function () { hovering = false; });
    function restartAuto() {
      clearInterval(autoTimer);
      autoTimer = setInterval(function () { if (!hovering && visible && !dragging) go(1); }, 4200);
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; }).observe(c);
    }
    window.addEventListener('resize', layout);
    layout(); apply(); restartAuto();
  });
})();
