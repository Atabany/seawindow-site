// SeaWindow tide height calculator. Runs locally; nothing is sent anywhere.
(function () {
  'use strict';
  var f = document.getElementById('calc');
  if (!f) return;
  var $ = function (id) { return document.getElementById(id); };
  var mode = 'height';
  var CUM = [0, 1, 3, 6, 9, 11, 12];
  var DEFAULTS = { t1: '01:47', h1: '0.86', t2: '08:35', h2: '5.91', tq: '05:00', hq: '3', unit: 'ft', mode: 'height' };

  function mins(v) { var p = (v || '').split(':'); return p.length < 2 ? NaN : (+p[0]) * 60 + (+p[1]); }
  function clock(m) {
    m = ((Math.round(m) % 1440) + 1440) % 1440;
    var h = Math.floor(m / 60), mm = m % 60, ap = h < 12 ? 'AM' : 'PM', h12 = h % 12 || 12;
    return h12 + ':' + (mm < 10 ? '0' : '') + mm + ' ' + ap;
  }
  function dur(m) { var h = Math.floor(m / 60), mm = Math.round(m % 60); return h + ' h ' + mm + ' min'; }
  function cosF(x) { return (1 - Math.cos(Math.PI * x)) / 2; }
  function twF(x) { var h = Math.min(Math.max(x, 0), 1) * 6, i = Math.min(Math.floor(h), 5); return (CUM[i] + (CUM[i + 1] - CUM[i]) * (h - i)) / 12; }
  function cosInv(fr) { return Math.acos(1 - 2 * fr) / Math.PI; }
  function twInv(fr) {
    var tw = fr * 12;
    for (var i = 0; i < 6; i++) if (tw <= CUM[i + 1]) return (i + (tw - CUM[i]) / (CUM[i + 1] - CUM[i])) / 6;
    return 1;
  }
  function fmt(v, u) { return (Math.round(v * 100) / 100).toFixed(2) + ' ' + u; }

  function read() {
    var t1 = mins($('t1').value), t2 = mins($('t2').value);
    if (t2 <= t1) t2 += 1440;
    return { t1: t1, t2: t2, h1: parseFloat($('h1').value), h2: parseFloat($('h2').value), u: $('unit').value };
  }

  function chart(d, mark) {
    var W = 680, H = 300, L = 54, R = 18, T = 22, B = 40;
    var lo = Math.min(d.h1, d.h2), hi = Math.max(d.h1, d.h2), pad = (hi - lo) * 0.12 || 0.5;
    var y0 = lo - pad, y1 = hi + pad;
    var X = function (x) { return L + x * (W - L - R); };
    var Y = function (h) { return T + (1 - (h - y0) / (y1 - y0)) * (H - T - B); };
    var s = '';
    for (var k = 0; k <= 4; k++) {
      var hv = y0 + (y1 - y0) * k / 4;
      s += '<line class="grid" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(hv).toFixed(1) + '" y2="' + Y(hv).toFixed(1) + '"/>';
      s += '<text x="' + (L - 8) + '" y="' + (Y(hv) + 4).toFixed(1) + '" text-anchor="end">' + hv.toFixed(1) + '</text>';
    }
    for (var j = 0; j <= 6; j++) {
      var tx = X(j / 6);
      s += '<text x="' + tx.toFixed(1) + '" y="' + (H - 14) + '" text-anchor="' + (j === 0 ? 'start' : j === 6 ? 'end' : 'middle') + '">' + clock(d.t1 + (d.t2 - d.t1) * j / 6) + '</text>';
    }
    var pc = '', pt = '';
    for (var i = 0; i <= 120; i++) {
      var x = i / 120;
      pc += (i ? 'L' : 'M') + X(x).toFixed(1) + ' ' + Y(d.h1 + (d.h2 - d.h1) * cosF(x)).toFixed(1);
    }
    for (var m = 0; m <= 6; m++) pt += (m ? 'L' : 'M') + X(m / 6).toFixed(1) + ' ' + Y(d.h1 + (d.h2 - d.h1) * CUM[m] / 12).toFixed(1);
    s += '<path d="' + pt + '" fill="none" stroke="#ffa157" stroke-width="2" stroke-dasharray="6 5"/>';
    s += '<path class="curve" d="' + pc + '"/>';
    if (mark) {
      s += '<line x1="' + X(mark.x).toFixed(1) + '" x2="' + X(mark.x).toFixed(1) + '" y1="' + T + '" y2="' + (H - B) + '" stroke="currentColor" stroke-opacity=".35"/>';
      s += '<circle cx="' + X(mark.x).toFixed(1) + '" cy="' + Y(mark.h).toFixed(1) + '" r="6" fill="#59e0f0" stroke="#07101f" stroke-width="2"/>';
    }
    s += '<text x="' + (W - R) + '" y="14" text-anchor="end"><tspan class="lo">━ cosine</tspan>   <tspan class="hi">┅ twelfths</tspan></text>';
    $('chart').innerHTML = s;
  }

  function hourly(d) {
    var D = d.t2 - d.t1, rows = '';
    for (var j = 0; j <= 6; j++) {
      var x = j / 6;
      rows += '<tr><td>' + clock(d.t1 + D * x) + '</td><td>' + (j === 0 ? 'start' : j + '/6') + '</td><td>' +
        fmt(d.h1 + (d.h2 - d.h1) * CUM[j] / 12, d.u) + '</td><td>' + fmt(d.h1 + (d.h2 - d.h1) * cosF(x), d.u) + '</td></tr>';
    }
    $('hourly-wrap').innerHTML = '<table><thead><tr><th>Time</th><th>Part</th><th>Rule of twelfths</th><th>Cosine</th></tr></thead><tbody>' + rows + '</tbody></table>';
  }

  function update() {
    var d = read();
    if ([d.t1, d.t2, d.h1, d.h2].some(isNaN) || d.h1 === d.h2) {
      $('big').innerHTML = '—';
      $('detail').textContent = 'Enter two different tide heights and both times.';
      return;
    }
    var D = d.t2 - d.t1, rising = d.h2 > d.h1, range = Math.abs(d.h2 - d.h1);
    var info = 'Range ' + fmt(range, d.u) + ' over ' + dur(D) + ', ' + (rising ? 'rising' : 'falling') + '.';
    if (D > 9 * 60 || D < 3 * 60) info += ' That is an unusual gap between two tides; check you entered consecutive tides.';
    if (mode === 'height') {
      var q = mins($('tq').value);
      if (isNaN(q)) return;
      if (q < d.t1) q += 1440;
      var x = (q - d.t1) / D;
      if (x < 0 || x > 1) {
        $('big').innerHTML = '—';
        $('detail').textContent = 'Pick a time between ' + clock(d.t1) + ' and ' + clock(d.t2) + '. ' + info;
        chart(d, null); hourly(d); return;
      }
      var hc = d.h1 + (d.h2 - d.h1) * cosF(x), ht = d.h1 + (d.h2 - d.h1) * twF(x);
      $('big').innerHTML = (Math.round(hc * 100) / 100).toFixed(2) + ' <small>' + d.u + '</small>';
      $('detail').textContent = 'Cosine curve at ' + clock(q) + '. Rule of twelfths: ' + fmt(ht, d.u) + '. ' + info;
      chart(d, { x: x, h: hc });
    } else {
      var h = parseFloat($('hq').value);
      var fr = (h - d.h1) / (d.h2 - d.h1);
      if (isNaN(h) || fr < 0 || fr > 1) {
        $('big').innerHTML = '—';
        $('detail').textContent = 'Pick a height between ' + fmt(Math.min(d.h1, d.h2), d.u) + ' and ' + fmt(Math.max(d.h1, d.h2), d.u) + '. ' + info;
        chart(d, null); hourly(d); return;
      }
      var xc = cosInv(fr), xt = twInv(fr);
      $('big').innerHTML = clock(d.t1 + D * xc);
      $('detail').textContent = 'The water ' + (rising ? 'rises to ' : 'falls to ') + fmt(h, d.u) + ' at about ' + clock(d.t1 + D * xc) +
        ' by the cosine curve, ' + clock(d.t1 + D * xt) + ' by the rule of twelfths. ' + info;
      chart(d, { x: xc, h: h });
    }
    hourly(d);
  }

  function setMode(m) {
    mode = m;
    f.querySelectorAll('[data-mode]').forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.mode === m)); });
    f.querySelectorAll('[data-for]').forEach(function (el) { el.hidden = el.dataset.for !== m; });
    update();
  }

  function load(params) {
    ['t1', 'h1', 't2', 'h2', 'tq', 'hq', 'unit'].forEach(function (k) { if (params[k] != null && params[k] !== '') $(k).value = params[k]; });
    setMode(params.mode === 'time' ? 'time' : 'height');
  }

  f.addEventListener('input', update);
  f.addEventListener('submit', function (e) { e.preventDefault(); });
  f.querySelectorAll('[data-mode]').forEach(function (b) { b.addEventListener('click', function () { setMode(b.dataset.mode); }); });
  $('reset').addEventListener('click', function () { load(DEFAULTS); history.replaceState(null, '', location.pathname); });
  $('share').addEventListener('click', function () {
    var q = new URLSearchParams();
    ['t1', 'h1', 't2', 'h2', 'tq', 'hq', 'unit'].forEach(function (k) { q.set(k, $(k).value); });
    q.set('mode', mode);
    var link = location.origin + location.pathname + '?' + q.toString();
    history.replaceState(null, '', '?' + q.toString());
    var btn = this;
    var done = function () { btn.textContent = 'Link copied'; setTimeout(function () { btn.textContent = 'Copy link to this result'; }, 2000); };
    if (navigator.clipboard) navigator.clipboard.writeText(link).then(done, done); else done();
  });

  var p = {};
  new URLSearchParams(location.search).forEach(function (v, k) { p[k] = v; });
  load(Object.keys(p).length ? p : DEFAULTS);
})();
