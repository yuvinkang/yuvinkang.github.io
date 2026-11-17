// Site behaviour: scroll fades, active tab, progress line + climber, Ferris wheel, project-page widgets.
(function () {
  var reveals = document.querySelectorAll('.reveal');
  var tabs = document.querySelectorAll('.tab[data-target]');
  var sections = document.querySelectorAll('.section[id]');
  var nav = document.querySelector('.sidenav');
  var hero = document.querySelector('.hero-inner');
  var IO = 'IntersectionObserver' in window;

  // 1. Fade each section in as it enters the screen
  if (IO) {
    var revealObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-visible'); revealObs.unobserve(e.target); }
      });
    }, { threshold: 0.08 });
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
  if (IO) {
    var sceneObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { e.target.classList.toggle('in-view', e.isIntersecting); });
    }, { rootMargin: '80px 0px' });
    scenes.forEach(function (s) { sceneObs.observe(s); });
  } else {
    scenes.forEach(function (s) { s.classList.add('in-view'); });
  }

  // 2c. The closing film quote replays: its lines fade in and float up when it
  //     comes into view, and fade back out when it leaves, either direction.
  var film = document.querySelector('.bio-film');
  if (film) {
    if (IO) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { e.target.classList.toggle('in-view', e.isIntersecting); });
      }, { threshold: 0.4 }).observe(film);
    } else {
      film.classList.add('in-view');
    }
  }

  // 3. Progress line, climbing stickman, gentle hero fade
  var climbTimer;
  function onScroll() {
    var y = window.scrollY, max = document.documentElement.scrollHeight - window.innerHeight;
    var p = max > 0 ? Math.min(y / max, 1) : 0;
    if (nav) {
      nav.style.setProperty('--progress', p);
      nav.classList.add('is-climbing');
      clearTimeout(climbTimer);
      climbTimer = setTimeout(function () { nav.classList.remove('is-climbing'); }, 220);
    }
    if (hero) {
      var f = Math.min(y / (window.innerHeight * 0.8), 1);
      hero.style.opacity = 1 - f * 0.9;
      hero.style.transform = 'translateY(' + (f * -24) + 'px)';
    }
    if (sections.length && y < window.innerHeight * 0.4) tabs.forEach(function (t) { t.classList.remove('active'); });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // 4. Ferris wheel — photos ride in cabins; stickmen speak on hover
  document.querySelectorAll('[data-wheel]').forEach(function (w) {
    var rotor = w.querySelector('.rotor');
    var gondolas = Array.prototype.slice.call(w.querySelectorAll('.gondola'));
    var n = gondolas.length; if (!n || !rotor) return;
    var CX = 250, CY = 232, R = 158, VW = 500, VH = 540;
    var theta = -90, omega = 0, AUTO = 9, relax = 2.4;
    var active = null, dragging = false, moved = 0, visible = true, last = 0;
    var sway = gondolas.map(function () { return { s: 0, v: 0, lastW: 0 }; });

    function setActive(g) {
      if (active === g) return;
      if (active) active.classList.remove('is-active');
      active = g;
      if (g) g.classList.add('is-active');
      w.classList.toggle('is-paused', !!g);
    }

    function frame(t) {
      if (!visible) { last = 0; requestAnimationFrame(frame); return; }
      var dt = last ? Math.min(0.05, (t - last) / 1000) : 0.016; last = t;
      if (!dragging) {
        var target = active ? 0 : AUTO;
        // ease toward the target speed, then let leftover momentum bleed off
        omega += (target - omega) * (1 - Math.exp(-relax * dt));
        if (Math.abs(omega) > Math.abs(target) + 1) omega *= Math.exp(-0.9 * dt);
        theta += omega * dt;
      }
      rotor.setAttribute('transform', 'rotate(' + theta.toFixed(2) + ' ' + CX + ' ' + CY + ')');
      for (var i = 0; i < n; i++) {
        var a = (theta + i * 360 / n) * Math.PI / 180;
        var x = CX + R * Math.cos(a), y = CY + R * Math.sin(a);
        var g = gondolas[i];
        g.style.left = (x / VW * 100) + '%';
        g.style.top = (y / VH * 100) + '%';
        // cabins swing like pendulums when the wheel speeds up or slows down
        // pendulum: driven by the cabin's tangential acceleration, lightly damped
        var st = sway[i];
        var goal = Math.max(-26, Math.min(26, -omega * 0.52 - (omega - st.lastW) / Math.max(dt, .001) * 0.012));
        st.lastW = omega;
        var k = 34, c = 2 * Math.sqrt(k) * 0.26;          // near-critical damping
        st.v += ((goal - st.s) * k - st.v * c) * dt;
        st.s += st.v * dt;
        g.style.setProperty('--sway', st.s.toFixed(2) + 'deg');
        g.style.setProperty('--lean', (st.s * -0.45).toFixed(2) + 'deg');
        g.style.zIndex = active === g ? 30 : Math.round(10 + y / 30);
      }
      w.classList.toggle('is-fast', Math.abs(omega) > AUTO * 1.8);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    if (IO) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; }).observe(w);

    gondolas.forEach(function (g) {
      g.addEventListener('pointerenter', function (e) { if (e.pointerType === 'mouse' && !dragging) setActive(g); });
      g.addEventListener('pointerleave', function (e) { if (e.pointerType === 'mouse' && active === g) setActive(null); });
      g.addEventListener('focus', function () { setActive(g); });
      g.addEventListener('blur', function () { if (active === g) setActive(null); });
      g.addEventListener('click', function () {
        if (moved > 6) return;
        if (active !== g) { setActive(g); return; }   // first tap on touch screens shows the blurb
        openLightbox(g);
      });
    });

    // drag anywhere on the wheel to spin it (with inertia)
    var lastAng = 0, lastTime = 0;
    function pointerAngle(e) {
      var r = w.getBoundingClientRect();
      var hx = r.left + r.width * CX / VW, hy = r.top + r.height * CY / VH;
      return Math.atan2(e.clientY - hy, e.clientX - hx) * 180 / Math.PI;
    }
    w.addEventListener('pointerdown', function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      dragging = true; moved = 0; lastAng = pointerAngle(e); lastTime = performance.now();
      w.classList.add('dragging');
    });
    window.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var ang = pointerAngle(e), d = ang - lastAng;
      if (d > 180) d -= 360; if (d < -180) d += 360;
      var now = performance.now(), dt = Math.max(0.008, (now - lastTime) / 1000);
      theta += d; moved += Math.abs(d) * 3;
      omega = omega * 0.6 + (d / dt) * 0.4;
      lastAng = ang; lastTime = now;
      if (moved > 6) setActive(null);
    });
    window.addEventListener('pointerup', function () {
      if (!dragging) return;
      dragging = false; w.classList.remove('dragging');
      omega = Math.max(-240, Math.min(240, omega));
      setTimeout(function () { moved = 0; }, 0);
    });
    document.addEventListener('pointerdown', function (e) { if (active && !w.contains(e.target)) setActive(null); });
  });

  // 4b. Poke a stick figure and it reacts
  document.querySelectorAll('.scene').forEach(function (sc) {
    sc.addEventListener('click', function () {
      if (sc.classList.contains('is-poked')) return;
      sc.classList.add('is-poked');
      setTimeout(function () { sc.classList.remove('is-poked'); }, 1400);
    });
  });

  // 5. Lightbox for wheel photos
  var box = document.querySelector('.lightbox');
  function openLightbox(g) {
    if (!box || !box.showModal) return;
    box.querySelector('img').src = g.dataset.src;
    box.querySelector('img').alt = g.dataset.caption || '';
    box.querySelector('.lightbox-cap strong').textContent = g.dataset.caption || '';
    box.querySelector('.lightbox-cap span').textContent = g.dataset.blurb || '';
    box.showModal();
  }
  if (box) {
    box.querySelector('.lightbox-close').addEventListener('click', function () { box.close(); });
    box.addEventListener('click', function (e) { if (e.target === box) box.close(); });
  }

  // 6. Project-page widgets (used by the Prari page; harmless elsewhere)
  // 6a. count-up numbers
  var counters = document.querySelectorAll('[data-count]');
  if (IO && counters.length) {
    var cObs = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target, end = parseFloat(el.dataset.count), dec = (el.dataset.count.split('.')[1] || '').length;
        var pre = el.dataset.pre || '', suf = el.dataset.suf || '', t0 = performance.now();
        (function tick(t) {
          var k = Math.min(1, (t - t0) / 1200), v = end * (1 - Math.pow(1 - k, 3));
          el.textContent = pre + v.toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec }) + suf;
          if (k < 1) requestAnimationFrame(tick);
        })(t0);
        cObs.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (c) { cObs.observe(c); });
  }

  // 6b. tab / toggle groups: [data-toggle-group] buttons with data-show="key" toggle [data-panel="key"]
  document.querySelectorAll('[data-toggle-group]').forEach(function (grp) {
    var scope = grp.closest('[data-toggle-scope]') || document;
    var btns = grp.querySelectorAll('[data-show]');
    function show(key) {
      btns.forEach(function (b) { var on = b.dataset.show === key; b.classList.toggle('on', on); b.setAttribute('aria-pressed', on); });
      scope.querySelectorAll('[data-panel]').forEach(function (p) { p.classList.toggle('on', p.dataset.panel === key); });
      scope.setAttribute('data-state', key);
    }
    btns.forEach(function (b) {
      b.addEventListener('click', function () { show(b.dataset.show); });
      if (grp.hasAttribute('data-hover')) b.addEventListener('mouseenter', function () { show(b.dataset.show); });
    });
    if (btns[0]) show(btns[0].dataset.show);
  });

  // 6c. drag / slider to "turn" a stack of render angles
  document.querySelectorAll('[data-turntable]').forEach(function (tt) {
    var imgs = tt.querySelectorAll('img'), range = tt.parentNode.querySelector('input[type=range]'), idx = 0, startX = null;
    function set(i) {
      idx = (i + imgs.length) % imgs.length;
      imgs.forEach(function (im, k) { im.classList.toggle('on', k === idx); });
      if (range) range.value = idx;
    }
    tt.addEventListener('pointerdown', function (e) { startX = e.clientX; tt.setPointerCapture && tt.setPointerCapture(e.pointerId); });
    tt.addEventListener('pointermove', function (e) {
      if (startX === null) return;
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 60) { set(idx + (dx < 0 ? 1 : -1)); startX = e.clientX; }
    });
    tt.addEventListener('pointerup', function () { startX = null; });
    if (range) range.addEventListener('input', function () { set(+range.value); });
    set(0);
  });


  // 7. Ambient background field — drifting objects with inertia that scatter from the cursor
  (function ambient() {
    var host = document.querySelector('[data-ambient] .ambient-field');
    if (!host) return;
    // [symbol, px size, mass, colour class]
    var KINDS = [
      ['note', 30, .9, 'c-music'], ['beam', 36, .9, 'c-music'],
      ['ball', 34, 1.15, 'c-ball'], ['ball', 26, 1.15, 'c-ball'],
      ['plantcell', 42, 1.0, 'c-plant'], ['cell', 40, 1.0, 'c-cell'], ['dna', 32, .85, 'c-cell'],
      ['screwdriver', 30, .8, 'c-tool'], ['wrench', 34, .95, 'c-tool'], ['caliper', 34, .9, 'c-tool'],
      ['gear', 32, 1.0, 'c-tool'],
      ['flask', 30, .85, 'c-lab'], ['pipette', 26, .7, 'c-lab'],
      ['sigma', 30, .8, 'c-math'], ['integral', 32, .75, 'c-math'], ['pi', 28, .7, 'c-math'],
      ['delta', 32, .8, 'c-math'], ['pval', 40, .8, 'c-math'], ['sd', 28, .7, 'c-math'],
      ['euler', 46, .85, 'c-math'], ['mu', 26, .7, 'c-math']
    ];
    var count = innerWidth < 760 ? 12 : (innerWidth < 1200 ? 17 : 23);
    var items = [], W = innerWidth, H = innerHeight;
    var mouse = { x: -9999, y: -9999, active: false };

    for (var i = 0; i < count; i++) {
      var k = KINDS[i % KINDS.length];
      var el = document.createElement('span');
      el.className = 'am ' + k[3];
      el.innerHTML = '<svg viewBox="0 0 40 34" width="' + k[1] + '" height="' + (k[1] * .85) + '"><use href="#am-' + k[0] + '"/></svg>';
      host.appendChild(el);
      var ang = Math.random() * Math.PI * 2, sp = 9 + Math.random() * 11;
      items.push({
        el: el, r: k[1] * .5, m: k[2],
        x: Math.random() * W, y: Math.random() * H,
        vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp,
        a: Math.random() * 360, va: (Math.random() - .5) * 9,
        // each one wanders on its own slow heading
        wa: Math.random() * Math.PI * 2, ws: 0.18 + Math.random() * 0.3
      });
    }

    addEventListener('resize', function () { W = innerWidth; H = innerHeight; });
    addEventListener('pointermove', function (e) { mouse.x = e.clientX; mouse.y = e.clientY; mouse.active = true; }, { passive: true });
    addEventListener('pointerleave', function () { mouse.active = false; mouse.x = mouse.y = -9999; });

    var last = 0, running = true, layer = document.querySelector('[data-ambient]'), fade = 1;
    document.addEventListener('visibilitychange', function () { running = !document.hidden; last = 0; });
    // only on the landing page: fade out over the first screen, then stop
    function updateFade() {
      var hero = document.querySelector('.hero');
      var span = hero ? hero.offsetHeight * 0.7 : innerHeight * 0.7;
      var f = 1 - Math.min(1, Math.max(0, scrollY / span));
      if (Math.abs(f - fade) > 0.01) { fade = f; layer.style.setProperty('--amb-fade', f.toFixed(2)); }
    }
    addEventListener('scroll', updateFade, { passive: true });
    updateFade();

    function step(t) {
      requestAnimationFrame(step);
      if (!running || fade <= 0.02) { last = 0; return; }   // stopped once it has faded out
      var dt = last ? Math.min(0.05, (t - last) / 1000) : 0.016; last = t;
      var R = 170, R2 = R * R;
      for (var i = 0; i < items.length; i++) {
        var p = items[i];
        if (mouse.active) {
          var dx = p.x - mouse.x, dy = p.y - mouse.y, d2 = dx * dx + dy * dy;
          if (d2 < R2 && d2 > 1) {
            var d = Math.sqrt(d2), f = 1 - d / R;
            var push = f * f * 3400 / p.m;
            p.vx += (dx / d) * push * dt;
            p.vy += (dy / d) * push * dt;
            p.va += (dx / d) * f * 90 * dt;
          }
        }
        // slow wandering heading keeps everything drifting instead of settling
        p.wa += (Math.random() - .5) * 1.2 * dt + p.ws * dt;
        p.vx += Math.cos(p.wa) * 13 * dt;
        p.vy += Math.sin(p.wa) * 13 * dt;
        // light drag only — enough to damp a cursor hit, not enough to stop the drift
        var drag = Math.exp(-0.22 * dt);
        p.vx *= drag; p.vy *= drag; p.va *= Math.exp(-0.35 * dt);
        var sp = Math.hypot(p.vx, p.vy);
        if (sp > 190) { p.vx *= 190 / sp; p.vy *= 190 / sp; }
        else if (sp < 5) { var s2 = 5 / (sp || 1); p.vx *= s2; p.vy *= s2; }   // never fully stall
        p.x += p.vx * dt; p.y += p.vy * dt; p.a += p.va * dt;
        if (p.x < p.r) { p.x = p.r; p.vx = Math.abs(p.vx) * .8; p.va += 10; }
        else if (p.x > W - p.r) { p.x = W - p.r; p.vx = -Math.abs(p.vx) * .8; p.va -= 10; }
        if (p.y < p.r) { p.y = p.r; p.vy = Math.abs(p.vy) * .8; }
        else if (p.y > H - p.r) { p.y = H - p.r; p.vy = -Math.abs(p.vy) * .8; }
        p.el.style.transform = 'translate3d(' + (p.x - p.r) + 'px,' + (p.y - p.r * .85) + 'px,0) rotate(' + p.a + 'deg)';
      }
    }
    requestAnimationFrame(step);
  })();
})();
