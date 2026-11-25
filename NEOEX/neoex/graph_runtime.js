/* NEOEX canvas graph engine. No chart library dependency required. */
(function () {
  'use strict';

  const SHELL = '.neoex-canvas-shell[data-neoex-graph]';
  const formatter = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3, useGrouping: false });
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const finite = Number.isFinite;
  const fmt = (v) => finite(v) ? formatter.format(Number(v.toFixed(3))) : 'não definido';

  function decodePayload(value) {
    const bytes = Uint8Array.from(atob(value), ch => ch.charCodeAt(0));
    return JSON.parse(new TextDecoder('utf-8').decode(bytes));
  }

  function initialize(shell) {
    if (!shell || !shell.isConnected) return;
    const configText = shell.dataset.config || '';
    const current = shell.__neoexCanvasInstance;
    // A Gradio HTML output can update the data attribute without replacing
    // the outer node. Rebuild whenever the expression payload has changed.
    if (current && current.configText === configText) return;
    if (current) {
      try { current.destroy(); } catch (_) {}
      shell.__neoexCanvasInstance = null;
    }
    delete shell.dataset.ready;
    const canvas = shell.querySelector('canvas[data-role="graph-canvas"]');
    if (!canvas) return;
    // Remove stale fixed pixel sizes left by older runtimes; CSS must control layout.
    canvas.style.removeProperty('width');
    canvas.style.removeProperty('height');
    shell.dataset.ready = '1';
    const listenerController = new AbortController();
    const listen = (target, type, handler, options = {}) => {
      if (!target) return;
      target.addEventListener(type, handler, { ...options, signal: listenerController.signal });
    };

    let cfg;
    try {
      cfg = decodePayload(configText);
    } catch (error) {
      shell.dataset.ready = '0';
      const status = shell.querySelector('[data-role="graph-status"]');
      if (status) status.textContent = 'Não foi possível ler a configuração matemática do gráfico.';
      console.error('NEOEX graph config:', error);
      return;
    }

    let fn;
    try {
      // function_js is generated exclusively from the validated SymPy tree;
      // raw user input is never interpolated into executable JavaScript.
      fn = new Function('x', '"use strict"; try { return (' + cfg.function_js + '); } catch (_) { return NaN; }');
    } catch (error) {
      shell.dataset.ready = '0';
      const status = shell.querySelector('[data-role="graph-status"]');
      if (status) status.textContent = 'A expressão foi reconhecida, mas não pôde ser compilada para o avaliador gráfico.';
      console.error('NEOEX graph compiler:', error);
      return;
    }

    const compareFns = [];
    try {
      (cfg.compare || []).forEach(item => {
        const compareFn = new Function('x', '"use strict"; try { return (' + item.function_js + '); } catch (_) { return NaN; }');
        compareFns.push({
          label: item.label || 'comparação',
          expression: item.expression || '',
          fn: compareFn,
          samples: []
        });
      });
    } catch (error) {
      console.warn('NEOEX comparison function skipped:', error);
    }

    const ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
    if (!ctx) {
      shell.dataset.ready = '0';
      const status = shell.querySelector('[data-role="graph-status"]');
      if (status) status.textContent = 'Este navegador não disponibilizou o Canvas 2D.';
      return;
    }

    const $ = role => shell.querySelector('[data-role="' + role + '"]');
    const status = $('graph-status');
    const pointSlider = $('point-slider');
    const pointInput = $('current-x');
    const lineSlider = $('line-slider');
    const lineInput = $('line-y');
    const rootsToggle = $('roots-toggle');
    const lineToggle = $('line-toggle');
    const rootsOutput = $('roots-output');
    const intersectionsOutput = $('intersections-output');
    const readoutX = $('readout-x');
    const readoutY = $('readout-y');
    const readoutDomain = $('readout-domain');
    const viewXMinInput = $('axis-xmin');
    const viewXMaxInput = $('axis-xmax');
    const viewYMinInput = $('axis-ymin');
    const viewYMaxInput = $('axis-ymax');
    const gridToggle = $('grid-toggle');

    const state = {
      pointMin: cfg.x_min,
      pointMax: cfg.x_max,
      pointX: clamp(cfg.x_point, cfg.x_min, cfg.x_max),
      lineY: Number.isFinite(Number(cfg.line_y)) ? Number(cfg.line_y) : 0,
      showRoots: true,
      showLine: true,
      showGrid: true,
      viewXMin: cfg.x_min,
      viewXMax: cfg.x_max,
      viewYMin: null,
      viewYMax: null,
      manualY: false,
      samples: [],
      resamplePending: false,
      critical: Array.isArray(cfg.critical_points) ? cfg.critical_points : [],
      roots: Array.isArray(cfg.roots) ? cfg.roots : [],
      excluded: Array.isArray(cfg.excluded_points) ? cfg.excluded_points : [],
      plot: null,
      dpr: 1,
      dragging: null,
      pointer: null,
      drawFrame: 0,
      destroyed: false,
      yAuto: true,
      resizeObserver: null,
      intersectionObserver: null,
      waitingForLayout: true,
      lastCssWidth: 0,
      lastCssHeight: 0,
      lastIntersections: [],
      intersectionAll: false,
      intersectionKey: '',
      visibleRoots: Array.isArray(cfg.roots) ? cfg.roots : [],
      rootsKey: '',
      samplesVersion: 0,
      lastPointY: null
    };

    const evalAt = (x) => {
      try {
        const y = Number(fn(Number(x)));
        if (!finite(y) || Math.abs(y) > 1e12) return null;
        for (const hole of state.excluded) if (Math.abs(x - hole) < 1e-9 * Math.max(1, Math.abs(hole))) return null;
        return y;
      } catch (_) { return null; }
    };

    const niceStep = (span, target = 8) => {
      const raw = Math.abs(span) / Math.max(1, target);
      if (!finite(raw) || raw <= 0) return 1;
      const power = Math.pow(10, Math.floor(Math.log10(raw)));
      const normalized = raw / power;
      const factor = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
      return factor * power;
    };

    function sampleCurve() {
      const width = Math.max(320, canvas.clientWidth || 800);
      const count = clamp(Math.round(width * 1.2), 420, 1100);
      const xs = new Array(count + 1);
      const ys = new Array(count + 1);
      const span = state.viewXMax - state.viewXMin;
      for (let i = 0; i <= count; i++) {
        const x = state.viewXMin + span * i / count;
        xs[i] = x;
        ys[i] = evalAt(x);
      }
      // Include exact roots, critical points and holes so tangencies and
      // removable discontinuities are represented even between samples.
      const special = [];
      state.roots.forEach(x => { if (x >= state.viewXMin && x <= state.viewXMax) special.push(x); });
      state.critical.forEach(x => { if (x >= state.viewXMin && x <= state.viewXMax) special.push(x); });
      state.excluded.forEach(x => { if (x >= state.viewXMin && x <= state.viewXMax) special.push(x); });
      special.sort((a, b) => a - b);
      // Merge two sorted arrays instead of repeatedly calling findIndex/splice.
      // This keeps redraw cost close to O(samples + special points).
      const merged = [];
      let baseIndex = 0, specialIndex = 0;
      while (baseIndex < xs.length || specialIndex < special.length) {
        if (baseIndex >= xs.length) { merged.push(special[specialIndex++]); continue; }
        if (specialIndex >= special.length) { merged.push(xs[baseIndex++]); continue; }
        const baseX = xs[baseIndex], specialX = special[specialIndex];
        if (Math.abs(baseX - specialX) <= 1e-12 * Math.max(1, Math.abs(baseX), Math.abs(specialX))) {
          merged.push(baseX); baseIndex++; specialIndex++;
        } else if (baseX < specialX) merged.push(xs[baseIndex++]);
        else merged.push(special[specialIndex++]);
      }
      state.samples = merged.map(x => ({ x, y: evalAt(x) }));
      state.samplesVersion += 1;
      state.intersectionKey = '';
      compareFns.forEach(item => {
        item.samples = state.samples.map(point => {
          try {
            const value = Number(item.fn(point.x));
            return finite(value) && Math.abs(value) < 1e12 ? value : null;
          } catch (_) { return null; }
        });
      });
      updateAutoY();
    }

    function updateAutoY() {
      if (state.manualY) return;
      const values = state.samples.map(p => p.y).filter(v => v !== null && finite(v) && Math.abs(v) < 1e7).sort((a, b) => a - b);
      if (!values.length) {
        state.viewYMin = -5;
        state.viewYMax = 5;
        return;
      }
      const lo = values[Math.floor((values.length - 1) * 0.025)];
      const hi = values[Math.ceil((values.length - 1) * 0.975)];
      let ymin = Math.min(lo, hi, 0);
      let ymax = Math.max(lo, hi, 0);
      const py = evalAt(state.pointX);
      if (py !== null) { ymin = Math.min(ymin, py); ymax = Math.max(ymax, py); }
      if (state.showLine && Math.abs(state.lineY) < 1e7) { ymin = Math.min(ymin, state.lineY); ymax = Math.max(ymax, state.lineY); }
      if (Math.abs(ymax - ymin) < 1e-9) { ymin -= 1; ymax += 1; }
      const pad = (ymax - ymin) * 0.09;
      state.viewYMin = ymin - pad;
      state.viewYMax = ymax + pad;
    }

    function plotRect() {
      const w = canvas.clientWidth || 800;
      const h = canvas.clientHeight || 460;
      return { left: 58, top: 20, right: w - 20, bottom: h - 42, width: w - 78, height: h - 62, w, h };
    }
    const xToPx = (x, r) => r.left + (x - state.viewXMin) / (state.viewXMax - state.viewXMin) * r.width;
    const yToPx = (y, r) => r.bottom - (y - state.viewYMin) / (state.viewYMax - state.viewYMin) * r.height;
    const pxToX = (px, r) => state.viewXMin + (px - r.left) / r.width * (state.viewXMax - state.viewXMin);
    const pxToY = (py, r) => state.viewYMin + (r.bottom - py) / r.height * (state.viewYMax - state.viewYMin);

    function computeIntersections(level) {
      const found = [];
      const add = x => {
        if (!finite(x) || x < state.viewXMin - 1e-8 || x > state.viewXMax + 1e-8) return;
        if (state.excluded.some(h => Math.abs(h - x) < 1e-7 * Math.max(1, Math.abs(x)))) return;
        if (!found.some(v => Math.abs(v - x) < 1e-5 * Math.max(1, Math.abs(x)))) found.push(x);
      };
      if (Math.abs(level) < 1e-12) {
        state.roots.forEach(add);
      }
      const samples = state.samples;
      for (let i = 0; i < samples.length - 1; i++) {
        const a = samples[i], b = samples[i + 1];
        if (a.y === null || b.y === null) continue;
        const da = a.y - level, db = b.y - level;
        if (Math.abs(da) < 1e-9 * Math.max(1, Math.abs(level))) add(a.x);
        if (da * db < 0) {
          let lo = a.x, hi = b.x, flo = da;
          for (let n = 0; n < 38; n++) {
            const mid = (lo + hi) / 2;
            const ym = evalAt(mid);
            if (ym === null) break;
            const fm = ym - level;
            if (Math.abs(fm) < 1e-11 || Math.abs(hi - lo) < 1e-9) { lo = hi = mid; break; }
            if (flo * fm <= 0) hi = mid;
            else { lo = mid; flo = fm; }
          }
          add((lo + hi) / 2);
        }
      }
      // A horizontal line tangent to the curve does not change sign. Check
      // symbolic critical points to retain these double/tangent intersections.
      for (const x of state.critical) {
        if (x < state.viewXMin || x > state.viewXMax) continue;
        const y = evalAt(x);
        if (y !== null && Math.abs(y - level) <= 1e-7 * Math.max(1, Math.abs(y), Math.abs(level))) add(x);
      }
      found.sort((a, b) => a - b);
      return found;
    }

    function getVisibleRoots() {
      const insideInitial = state.viewXMin >= cfg.x_min - 1e-9 && state.viewXMax <= cfg.x_max + 1e-9;
      if (insideInitial) {
        return state.roots.filter(r => r >= state.viewXMin && r <= state.viewXMax);
      }
      const key = String(state.samplesVersion);
      if (state.rootsKey === key) return state.visibleRoots;
      const merged = [];
      const addRoot = x => {
        if (!finite(x) || x < state.viewXMin || x > state.viewXMax) return;
        if (!merged.some(v => Math.abs(v - x) < 1e-4 * Math.max(1, Math.abs(x)))) merged.push(x);
      };
      state.roots.forEach(addRoot);
      computeIntersections(0).forEach(addRoot);
      merged.sort((a, b) => a - b);
      state.visibleRoots = merged;
      state.rootsKey = key;
      return merged;
    }

    function drawText(text, x, y, color = '#b9cce8', align = 'center', font = '11px Inter,Arial') {
      ctx.fillStyle = color;
      ctx.font = font;
      ctx.textAlign = align;
      ctx.textBaseline = 'middle';
      ctx.fillText(text, x, y);
    }

    function draw() {
      if (state.destroyed) return;
      const rect = canvas.getBoundingClientRect();
      // Gradio tabs can be display:none while another tab is active. In that
      // state the canvas reports 0x0; never force a fallback pixel width into
      // its inline style, otherwise it remains permanently narrow after the
      // tab becomes visible again.
      const w = Math.floor(rect.width);
      const h = Math.floor(rect.height);
      if (!finite(w) || !finite(h) || w < 180 || h < 180) {
        state.waitingForLayout = true;
        return;
      }
      state.waitingForLayout = false;
      state.lastCssWidth = w;
      state.lastCssHeight = h;
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const bitmapWidth = Math.max(1, Math.floor(w * dpr));
      const bitmapHeight = Math.max(1, Math.floor(h * dpr));
      if (canvas.width !== bitmapWidth || canvas.height !== bitmapHeight) {
        canvas.width = bitmapWidth;
        canvas.height = bitmapHeight;
        // CSS owns the layout size (width:100%; height:100%). Only the
        // backing bitmap is resized here. Setting style.width/height to a
        // measured pixel value breaks responsive layouts and hidden tabs.
      }
      state.dpr = dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#050d20';
      ctx.fillRect(0, 0, w, h);
      const r = plotRect();
      const xStep = niceStep(state.viewXMax - state.viewXMin, 9);
      const yStep = niceStep(state.viewYMax - state.viewYMin, 7);
      if (lineSlider) {
        const span = state.viewYMax - state.viewYMin;
        lineSlider.min = String(state.viewYMin);
        lineSlider.max = String(state.viewYMax);
        lineSlider.step = String(Math.max(span / 1000, 0.0001));
      }

      // Grid and labels.
      if (state.showGrid) {
        ctx.strokeStyle = 'rgba(88,135,190,.19)';
        ctx.lineWidth = 1;
        for (let x = Math.ceil(state.viewXMin / xStep) * xStep; x <= state.viewXMax + xStep * .01; x += xStep) {
          const px = xToPx(x, r);
          ctx.beginPath(); ctx.moveTo(px, r.top); ctx.lineTo(px, r.bottom); ctx.stroke();
          drawText(fmt(x), px, r.bottom + 17, '#aac0df');
        }
        for (let y = Math.ceil(state.viewYMin / yStep) * yStep; y <= state.viewYMax + yStep * .01; y += yStep) {
          const py = yToPx(y, r);
          ctx.beginPath(); ctx.moveTo(r.left, py); ctx.lineTo(r.right, py); ctx.stroke();
          drawText(fmt(y), r.left - 9, py, '#aac0df', 'right');
        }
      }
      // Cartesian axes.
      ctx.strokeStyle = '#8799b6'; ctx.lineWidth = 1.25;
      if (state.viewYMin <= 0 && state.viewYMax >= 0) {
        const py = yToPx(0, r); ctx.beginPath(); ctx.moveTo(r.left, py); ctx.lineTo(r.right, py); ctx.stroke();
      }
      if (state.viewXMin <= 0 && state.viewXMax >= 0) {
        const px = xToPx(0, r); ctx.beginPath(); ctx.moveTo(px, r.top); ctx.lineTo(px, r.bottom); ctx.stroke();
      }
      drawText('x', r.right, r.bottom + 34, '#d5e5fa', 'right', '600 12px Inter,Arial');
      drawText('y', r.left - 34, r.top + 2, '#d5e5fa', 'center', '600 12px Inter,Arial');

      // Function curve; invalid real-domain samples split the path.
      ctx.save();
      ctx.beginPath();
      ctx.strokeStyle = '#32d6ff'; ctx.lineWidth = 2.7; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.shadowColor = 'rgba(50,214,255,.42)'; ctx.shadowBlur = 8;
      let active = false, previousY = null;
      const ySpan = state.viewYMax - state.viewYMin;
      for (const sample of state.samples) {
        const y = sample.y;
        if (y === null || y < state.viewYMin - ySpan * 2 || y > state.viewYMax + ySpan * 2 || (previousY !== null && Math.abs(y - previousY) > ySpan * 2.5)) {
          active = false; previousY = y; continue;
        }
        const px = xToPx(sample.x, r), py = yToPx(y, r);
        if (!active) { ctx.moveTo(px, py); active = true; }
        else ctx.lineTo(px, py);
        previousY = y;
      }
      ctx.stroke(); ctx.restore();

      // Optional comparison curves are lightweight Canvas paths as well.
      const compareColors = ['#ff6fbd', '#ffc66d', '#a78bfa', '#8ee5c0'];
      compareFns.forEach((item, curveIndex) => {
        ctx.save(); ctx.beginPath();
        ctx.strokeStyle = compareColors[curveIndex % compareColors.length];
        ctx.lineWidth = 1.9; ctx.setLineDash([7, 5]);
        let compareActive = false, previous = null;
        item.samples.forEach((value, index) => {
          const x = state.samples[index] && state.samples[index].x;
          if (value === null || value < state.viewYMin - ySpan * 2 || value > state.viewYMax + ySpan * 2 || (previous !== null && Math.abs(value - previous) > ySpan * 2.5)) {
            compareActive = false; previous = value; return;
          }
          const px = xToPx(x, r), py = yToPx(value, r);
          if (!compareActive) { ctx.moveTo(px, py); compareActive = true; }
          else ctx.lineTo(px, py);
          previous = value;
        });
        ctx.stroke(); ctx.restore();
      });

      // Roots on the x-axis.
      const visibleRoots = getVisibleRoots();
      if (state.showRoots) {
        visibleRoots.forEach((root, i) => {
          const px = xToPx(root, r);
          const py = yToPx(0, r);
          ctx.beginPath(); ctx.fillStyle = '#ffcf72'; ctx.strokeStyle = '#fff2c9'; ctx.lineWidth = 1.5;
          ctx.arc(px, py, 5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
          drawText('x' + (i + 1), px, py - 16, '#ffda8c', 'center', '700 11px JetBrains Mono,monospace');
        });
      }

      // Movable horizontal line and its intersections.
      if (state.showLine && state.lineY >= state.viewYMin && state.lineY <= state.viewYMax) {
        const linePx = yToPx(state.lineY, r);
        ctx.save(); ctx.strokeStyle = '#b58cff'; ctx.lineWidth = 1.7; ctx.setLineDash([8, 5]);
        ctx.beginPath(); ctx.moveTo(r.left, linePx); ctx.lineTo(r.right, linePx); ctx.stroke(); ctx.restore();
        const intersectionKey = state.samplesVersion + ':' + state.lineY.toPrecision(12);
        if (state.intersectionKey !== intersectionKey) {
          if (cfg.constant_function && finite(Number(cfg.constant_value))) {
            state.intersectionAll = Math.abs(state.lineY - Number(cfg.constant_value)) <= 1e-8 * Math.max(1, Math.abs(state.lineY));
            state.lastIntersections = [];
          } else {
            state.intersectionAll = false;
            state.lastIntersections = computeIntersections(state.lineY);
          }
          state.intersectionKey = intersectionKey;
        }
        const intersections = state.lastIntersections;
        intersections.forEach((x, i) => {
          const y = evalAt(x);
          if (y === null) return;
          const px = xToPx(x, r), py = yToPx(y, r);
          ctx.beginPath(); ctx.fillStyle = '#b58cff'; ctx.strokeStyle = '#f4eaff'; ctx.lineWidth = 1.5;
          ctx.arc(px, py, 5.5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
          drawText(String.fromCharCode(65 + (i % 26)), px + 9, py - 13, '#dfc8ff', 'left', '700 11px JetBrains Mono,monospace');
        });
      }

      // Selected movable point and dotted projections to both axes.
      const pointY = evalAt(state.pointX);
      state.lastPointY = pointY;
      if (pointY !== null && state.pointX >= state.viewXMin && state.pointX <= state.viewXMax && pointY >= state.viewYMin && pointY <= state.viewYMax) {
        const px = xToPx(state.pointX, r), py = yToPx(pointY, r);
        ctx.save(); ctx.strokeStyle = 'rgba(103,247,154,.95)'; ctx.lineWidth = 1.6; ctx.setLineDash([3, 4]);
        if (state.viewYMin <= 0 && state.viewYMax >= 0) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px, yToPx(0, r)); ctx.stroke(); }
        if (state.viewXMin <= 0 && state.viewXMax >= 0) { ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(xToPx(0, r), py); ctx.stroke(); }
        ctx.restore();
        ctx.save(); ctx.shadowColor = '#67f79a'; ctx.shadowBlur = 17;
        ctx.beginPath(); ctx.fillStyle = '#67f79a'; ctx.strokeStyle = '#effff5'; ctx.lineWidth = 2;
        ctx.arc(px, py, 7, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); ctx.restore();
      }

      // Minimal legend (including comparison curves).
      let legendX = r.left + 8;
      const drawLegendItem = (text, color, font = '11px Inter,Arial') => {
        if (legendX >= r.right - 24) return;
        ctx.font = font;
        const textWidth = ctx.measureText(text).width;
        if (legendX + textWidth > r.right - 8) return;
        drawText(text, legendX, 10, color, 'left', font);
        legendX += textWidth + 14;
      };
      drawLegendItem('g(x)', '#32d6ff', '700 11px JetBrains Mono,monospace');
      if (state.showRoots) drawLegendItem('raízes', '#ffcf72');
      if (state.showLine) drawLegendItem('y = ' + fmt(state.lineY), '#cbb0ff');
      compareFns.forEach((item, curveIndex) => {
        const color = compareColors[curveIndex % compareColors.length];
        const rawExpr = item.expression ? `${item.label} = ${item.expression}` : item.label;
        const shortText = rawExpr.length > 22 ? rawExpr.slice(0, 21) + '…' : rawExpr;
        drawLegendItem(shortText, color, '600 11px JetBrains Mono,monospace');
      });
      updateOutputs();
    }

    function appendSubstitutedExpression(target, value) {
      // Build the point-substitution readout with real <sup> nodes rather than
      // encoding decimal exponents as Unicode modifier characters. This keeps
      // 4^(4,429) readable and correctly raised in every browser font.
      let source = String(cfg.expression_plain || cfg.expression || 'g(x)');
      const xValue = '(' + fmt(value) + ')';
      source = source.replace(/(?<![A-Za-z])x(?![A-Za-z])/g, xValue);

      const fragment = document.createDocumentFragment();
      let buffer = '';
      const flush = () => {
        if (!buffer) return;
        fragment.appendChild(document.createTextNode(buffer));
        buffer = '';
      };
      let index = 0;
      const findBalancedParen = (start) => {
        let depth = 0;
        for (let end = start; end < source.length; end++) {
          if (source[end] === '(') depth++;
          else if (source[end] === ')') {
            depth--;
            if (depth === 0) return end;
          }
        }
        return -1;
      };
      while (index < source.length) {
        const ch = source[index];
        if (ch === '^') {
          let exponent = null;
          let nextIndex = index + 1;
          if (source[nextIndex] === '(') {
            const end = findBalancedParen(nextIndex);
            if (end !== -1) {
              exponent = '(' + source.slice(nextIndex + 1, end) + ')';
              nextIndex = end + 1;
            }
          } else if ((source[nextIndex] === '-' || source[nextIndex] === '+') && source[nextIndex + 1] === '(') {
            const end = findBalancedParen(nextIndex + 1);
            if (end !== -1) {
              exponent = source[nextIndex] + '(' + source.slice(nextIndex + 2, end) + ')';
              nextIndex = end + 1;
            }
          } else {
            const match = source.slice(nextIndex).match(/^[+-]?(?:\d+(?:[.,]\d+)?|[A-Za-z]+)/);
            if (match) {
              exponent = match[0];
              nextIndex += match[0].length;
            }
          }
          if (exponent !== null) {
            flush();
            const sup = document.createElement('sup');
            sup.textContent = exponent;
            fragment.appendChild(sup);
            index = nextIndex;
            continue;
          }
        }
        if (ch === '*') {
          flush();
          if (source[index + 1] === '*') {
            fragment.appendChild(document.createTextNode('^'));
            index += 2;
          } else {
            fragment.appendChild(document.createTextNode(' · '));
            index += 1;
          }
          continue;
        }
        buffer += ch;
        index += 1;
      }
      flush();
      target.appendChild(fragment);
    }

    function updateOutputs() {
      const y = state.lastPointY;
      if (readoutX) readoutX.textContent = 'x = ' + fmt(state.pointX);
      if (readoutY) {
        if (y === null) readoutY.textContent = 'g(x) não definida neste ponto';
        else {
          const rounded = Number(y.toFixed(3));
          const approximate = Math.abs(y - rounded) > 1e-10 * Math.max(1, Math.abs(y));
          readoutY.replaceChildren();
          readoutY.appendChild(document.createTextNode('g(' + fmt(state.pointX) + ') = '));
          appendSubstitutedExpression(readoutY, state.pointX);
          readoutY.appendChild(document.createTextNode(' ⇒ ' + (approximate ? '≈ ' : '') + fmt(y)));
        }
      }
      if (readoutDomain) readoutDomain.textContent = cfg.domain_plain || '';
      if (pointSlider) pointSlider.value = String(state.pointX);
      if (pointInput && document.activeElement !== pointInput) pointInput.value = fmt(state.pointX);
      if (rootsOutput) {
        const visibleRoots = getVisibleRoots();
        if (!state.showRoots) rootsOutput.textContent = 'Raízes ocultadas.';
        else if (cfg.roots_all) rootsOutput.textContent = 'g(x)=0 em todo o domínio definido no intervalo (respeitando eventuais lacunas).';
        else if (!visibleRoots.length) rootsOutput.textContent = 'Nenhuma raiz real foi encontrada no intervalo atual.';
        else rootsOutput.textContent = 'Raízes: ' + visibleRoots.map((x, i) => 'x' + (i + 1) + ' = (' + fmt(x) + ', 0)').join('   ·   ');
      }
      if (intersectionsOutput) {
        if (!state.showLine) intersectionsOutput.textContent = 'Reta horizontal oculta.';
        else if (state.intersectionAll) intersectionsOutput.textContent = 'A reta coincide com a função: há infinitos pontos de interseção no intervalo.';
        else if (!state.lastIntersections.length) intersectionsOutput.textContent = 'Nenhuma interseção encontrada para y = ' + fmt(state.lineY) + ' neste intervalo.';
        else intersectionsOutput.textContent = 'Interseções: ' + state.lastIntersections.map((x, i) => String.fromCharCode(65 + (i % 26)) + ' = (' + fmt(x) + ', ' + fmt(state.lineY) + ')').join('   ·   ');
      }
    }

    function queueDraw(resample = false) {
      if (resample) state.resamplePending = true;
      if (state.drawFrame || state.destroyed) return;
      state.drawFrame = requestAnimationFrame(() => {
        state.drawFrame = 0;
        if (state.resamplePending) {
          state.resamplePending = false;
          sampleCurve();
        }
        draw();
      });
    }

    function updatePoint(value) {
      if (!finite(value)) return;
      state.pointX = clamp(value, state.pointMin, state.pointMax);
      const y = evalAt(state.pointX);
      if (y !== null && !state.manualY) {
        if (y < state.viewYMin || y > state.viewYMax) {
          state.viewYMin = Math.min(state.viewYMin, y - Math.abs(y) * .08 - .1);
          state.viewYMax = Math.max(state.viewYMax, y + Math.abs(y) * .08 + .1);
        }
      }
      if (status) status.textContent = y === null ? 'Este x está fora do domínio real da função.' : 'Ponto atualizado sobre a curva.';
      queueDraw(false);
    }

    function updateLine(value) {
      if (!finite(value)) return;
      state.lineY = value;
      state.intersectionKey = '';
      if (lineInput && document.activeElement !== lineInput) lineInput.value = fmt(value);
      if (lineSlider) lineSlider.value = String(value);
      queueDraw(false);
    }

    function setView(xmin, xmax, ymin, ymax, manualY) {
      if (!(finite(xmin) && finite(xmax) && xmax > xmin)) return false;
      state.viewXMin = xmin; state.viewXMax = xmax;
      if (manualY && finite(ymin) && finite(ymax) && ymax > ymin) {
        state.viewYMin = ymin; state.viewYMax = ymax; state.manualY = true;
      } else {
        state.manualY = false;
        state.viewYMin = null; state.viewYMax = null;
      }
      queueDraw(true);
      return true;
    }

    function resizeCanvas() {
      if (!canvas.isConnected || state.destroyed) return;
      const rect = canvas.getBoundingClientRect();
      // A hidden Gradio tab has no measurable layout. Leave the canvas alone
      // until ResizeObserver/IntersectionObserver reports the visible size.
      if (!finite(rect.width) || !finite(rect.height) || rect.width < 180 || rect.height < 180) return;
      const width = Math.round(rect.width);
      const height = Math.round(rect.height);
      const changed = width !== state.lastCssWidth || height !== state.lastCssHeight;
      if (changed || state.waitingForLayout) queueDraw(true);
      else queueDraw(false);
    }

    // Controls.
    if (pointSlider) listen(pointSlider, 'input', () => updatePoint(Number(pointSlider.value)));
    if (pointInput) {
      const commitX = () => {
        const raw = String(pointInput.value).trim();
        if (!raw) { pointInput.value = fmt(state.pointX); return; }
        const parsed = Number(raw.replace(',', '.'));
        if (finite(parsed)) updatePoint(parsed);
        else pointInput.value = fmt(state.pointX);
      };
      listen(pointInput, 'keydown', event => { if (event.key === 'Enter') { event.preventDefault(); commitX(); pointInput.blur(); } });
      listen(pointInput, 'blur', commitX);
    }
    if (lineInput) {
      listen(lineInput, 'keydown', event => { if (event.key === 'Enter') { event.preventDefault(); const n = Number(lineInput.value.replace(',', '.')); if (finite(n)) updateLine(n); lineInput.blur(); } });
      listen(lineInput, 'blur', () => { const raw = lineInput.value.trim(); const n = Number(raw.replace(',', '.')); if (raw && finite(n)) updateLine(n); else lineInput.value = fmt(state.lineY); });
    }
    if (lineSlider) listen(lineSlider, 'input', () => updateLine(Number(lineSlider.value)));
    if (rootsToggle) listen(rootsToggle, 'change', () => { state.showRoots = rootsToggle.checked; queueDraw(false); });
    if (lineToggle) listen(lineToggle, 'change', () => { state.showLine = lineToggle.checked; queueDraw(false); });
    if (gridToggle) listen(gridToggle, 'change', () => { state.showGrid = gridToggle.checked; queueDraw(false); });

    const applyPointRange = $('apply-point-range');
    if (applyPointRange) listen(applyPointRange, 'click', () => {
      const min = Number($('point-min').value), max = Number($('point-max').value);
      if (!finite(min) || !finite(max) || min >= max || max - min > 1e6) { if (status) status.textContent = 'Defina um intervalo válido para x.'; return; }
      state.pointMin = min; state.pointMax = max;
      if (pointSlider) { pointSlider.min = String(min); pointSlider.max = String(max); }
      if (viewXMinInput) viewXMinInput.value = String(min);
      if (viewXMaxInput) viewXMaxInput.value = String(max);
      if (viewYMinInput) viewYMinInput.value = '';
      if (viewYMaxInput) viewYMaxInput.value = '';
      setView(min, max, null, null, false);
      updatePoint(state.pointX);
      if (status) status.textContent = 'Intervalo do ponto atualizado.';
    });

    const applyAxes = $('apply-axes');
    if (applyAxes) listen(applyAxes, 'click', () => {
      const xmin = Number(viewXMinInput.value), xmax = Number(viewXMaxInput.value);
      const ymin = viewYMinInput.value.trim() === '' ? null : Number(viewYMinInput.value);
      const ymax = viewYMaxInput.value.trim() === '' ? null : Number(viewYMaxInput.value);
      if (!finite(xmin) || !finite(xmax) || xmin >= xmax) { if (status) status.textContent = 'Os limites de x são inválidos.'; return; }
      if ((ymin !== null || ymax !== null) && (!finite(ymin) || !finite(ymax) || ymin >= ymax)) { if (status) status.textContent = 'Preencha os dois limites de y ou deixe ambos em automático.'; return; }
      setView(xmin, xmax, ymin, ymax, ymin !== null && ymax !== null);
      if (status) status.textContent = 'Enquadramento dos eixos atualizado.';
    });

    // Pointer interactions: point marker, horizontal line, then pan.
    function pointerPosition(event) {
      const box = canvas.getBoundingClientRect();
      return { x: event.clientX - box.left, y: event.clientY - box.top };
    }
    function pointerDown(event) {
      const p = pointerPosition(event), r = plotRect();
      if (p.x < r.left || p.x > r.right || p.y < r.top || p.y > r.bottom) return;
      const pointY = evalAt(state.pointX);
      if (pointY !== null && state.pointX >= state.viewXMin && state.pointX <= state.viewXMax) {
        const dx = p.x - xToPx(state.pointX, r), dy = p.y - yToPx(pointY, r);
        if (dx * dx + dy * dy <= 22 * 22) state.dragging = 'point';
      }
      if (!state.dragging && state.showLine) {
        const linePy = yToPx(state.lineY, r);
        if (Math.abs(p.y - linePy) <= 9) state.dragging = 'line';
      }
      if (!state.dragging) state.dragging = 'pan';
      state.pointer = { ...p, xMin: state.viewXMin, xMax: state.viewXMax, yMin: state.viewYMin, yMax: state.viewYMax };
      canvas.classList.toggle('is-dragging', state.dragging !== 'point');
      canvas.style.cursor = state.dragging === 'point' ? 'grabbing' : state.dragging === 'line' ? 'ns-resize' : 'grabbing';
      try { canvas.setPointerCapture(event.pointerId); } catch (_) {}
      event.preventDefault();
    }
    function pointerMove(event) {
      if (!state.dragging || !state.pointer) return;
      const p = pointerPosition(event), r = plotRect();
      if (state.dragging === 'point') {
        updatePoint(pxToX(clamp(p.x, r.left, r.right), r));
      } else if (state.dragging === 'line') {
        updateLine(pxToY(clamp(p.y, r.top, r.bottom), r));
      } else if (state.dragging === 'pan') {
        const dx = p.x - state.pointer.x, dy = p.y - state.pointer.y;
        const xSpan = state.pointer.xMax - state.pointer.xMin;
        const ySpan = state.pointer.yMax - state.pointer.yMin;
        const nextMin = state.pointer.xMin - dx / r.width * xSpan;
        const nextMax = state.pointer.xMax - dx / r.width * xSpan;
        const nextYMin = state.pointer.yMin + dy / r.height * ySpan;
        const nextYMax = state.pointer.yMax + dy / r.height * ySpan;
        state.viewXMin = nextMin; state.viewXMax = nextMax;
        if (!state.manualY) { state.viewYMin = nextYMin; state.viewYMax = nextYMax; state.manualY = true; }
        else { state.viewYMin = nextYMin; state.viewYMax = nextYMax; }
        queueDraw(true);
      }
    }
    function pointerUp(event) {
      if (!state.dragging) return;
      state.dragging = null; state.pointer = null;
      canvas.classList.remove('is-dragging'); canvas.style.cursor = 'crosshair';
      try { if (event && event.pointerId !== undefined) canvas.releasePointerCapture(event.pointerId); } catch (_) {}
      if (viewXMinInput) viewXMinInput.value = fmt(state.viewXMin).replace(',', '.');
      if (viewXMaxInput) viewXMaxInput.value = fmt(state.viewXMax).replace(',', '.');
      queueDraw(false);
    }
    function wheel(event) {
      const p = pointerPosition(event), r = plotRect();
      if (p.x < r.left || p.x > r.right || p.y < r.top || p.y > r.bottom) return;
      event.preventDefault();
      const factor = Math.exp(clamp(event.deltaY, -500, 500) * 0.0012);
      const anchorX = pxToX(p.x, r), anchorY = pxToY(p.y, r);
      state.viewXMin = anchorX + (state.viewXMin - anchorX) * factor;
      state.viewXMax = anchorX + (state.viewXMax - anchorX) * factor;
      state.viewYMin = anchorY + (state.viewYMin - anchorY) * factor;
      state.viewYMax = anchorY + (state.viewYMax - anchorY) * factor;
      state.manualY = true;
      queueDraw(true);
    }
    listen(canvas, 'pointerdown', pointerDown);
    listen(canvas, 'pointermove', pointerMove);
    listen(canvas, 'pointerup', pointerUp);
    listen(canvas, 'pointercancel', pointerUp);
    listen(canvas, 'wheel', wheel, { passive: false });
    function syncResetView() {
      state.viewXMin = state.pointMin; state.viewXMax = state.pointMax;
      state.manualY = false; queueDraw(true);
      if (viewXMinInput) viewXMinInput.value = String(state.viewXMin);
      if (viewXMaxInput) viewXMaxInput.value = String(state.viewXMax);
      if (viewYMinInput) viewYMinInput.value = '';
      if (viewYMaxInput) viewYMaxInput.value = '';
    }
    listen(canvas, 'dblclick', syncResetView);
    const resetView = $('reset-view');
    if (resetView) listen(resetView, 'click', syncResetView);
    const exportPng = $('export-png');
    if (exportPng) listen(exportPng, 'click', () => {
      try {
        const dataUrl = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = 'neoex-grafico.png';
        document.body.appendChild(link);
        link.click();
        link.remove();
        if (status) status.textContent = 'Imagem PNG exportada.';
      } catch (error) {
        console.warn('NEOEX export PNG:', error);
        if (status) status.textContent = 'Não foi possível exportar a imagem PNG.';
      }
    });
    listen(canvas, 'keydown', event => {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
      event.preventDefault();
      updatePoint(state.pointX + (event.key === 'ArrowRight' ? 1 : -1) * (state.pointMax - state.pointMin) / (event.shiftKey ? 100 : 500));
    });

    const resizeObserver = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(resizeCanvas) : null;
    const canvasWrap = canvas.parentElement || canvas;
    if (resizeObserver) {
      resizeObserver.observe(canvasWrap);
      resizeObserver.observe(shell);
    }
    state.resizeObserver = resizeObserver;
    // IntersectionObserver handles tab switches where the surrounding Gradio
    // layout changes visibility without a conventional window resize.
    const intersectionObserver = typeof IntersectionObserver !== 'undefined'
      ? new IntersectionObserver(entries => {
          if (entries.some(entry => entry.isIntersecting)) resizeCanvas();
        }, { threshold: 0.01 })
      : null;
    if (intersectionObserver) intersectionObserver.observe(canvasWrap);
    state.intersectionObserver = intersectionObserver;
    listen(window, 'resize', resizeCanvas, { passive: true });
    listen(document, 'visibilitychange', () => {
      if (!document.hidden) requestAnimationFrame(resizeCanvas);
    });
    // Gradio tabs are buttons; a short deferred measurement after tab clicks
    // is a lightweight fallback for browsers with delayed layout updates.
    listen(document, 'click', event => {
      const tab = event.target && event.target.closest && event.target.closest('[role="tab"]');
      if (tab) requestAnimationFrame(() => requestAnimationFrame(resizeCanvas));
    }, true);

    // Configure ranges and initial controls.
    if (pointSlider) { pointSlider.min = String(state.pointMin); pointSlider.max = String(state.pointMax); pointSlider.value = String(state.pointX); }
    if (lineSlider) { lineSlider.min = String(state.viewYMin); lineSlider.max = String(state.viewYMax); lineSlider.step = String(Math.max((state.viewYMax-state.viewYMin)/1000,0.0001)); lineSlider.value = String(state.lineY); }
    if (lineInput) lineInput.value = fmt(state.lineY);
    if (rootsToggle) rootsToggle.checked = true;
    if (lineToggle) lineToggle.checked = true;
    if (gridToggle) gridToggle.checked = true;
    if (viewXMinInput) viewXMinInput.value = String(state.viewXMin);
    if (viewXMaxInput) viewXMaxInput.value = String(state.viewXMax);
    sampleCurve();
    updatePoint(state.pointX);
    queueDraw(false);

    shell.__neoexCanvasInstance = {
      configText,
      destroy() {
        state.destroyed = true;
        listenerController.abort();
        if (state.drawFrame) cancelAnimationFrame(state.drawFrame);
        if (state.resizeObserver) state.resizeObserver.disconnect();
        if (state.intersectionObserver) state.intersectionObserver.disconnect();
      }
    };
  }

  function shellsWithin(node) {
    if (!node || node.nodeType !== 1) return [];
    const result = [];
    if (node.matches && node.matches(SHELL)) result.push(node);
    if (node.querySelectorAll) result.push(...node.querySelectorAll(SHELL));
    return result;
  }

  function destroyShell(shell) {
    if (!shell) return;
    if (shell.__neoexCanvasInstance) {
      try { shell.__neoexCanvasInstance.destroy(); } catch (_) {}
      shell.__neoexCanvasInstance = null;
    }
    delete shell.dataset.ready;
  }

  function destroyWithin(node) {
    shellsWithin(node).forEach(destroyShell);
  }

  function startGlobalGraphObserver() {
    if (window.__NEOEX_GRAPH_OBSERVER__ || !document.body) return;

    // One small document-level observer is more reliable than observers tied
    // to Gradio's internal .prose wrapper, which can be replaced on every output.
    // It only reacts to added/removed graph shells and data-config changes.
    shellsWithin(document.body).forEach(initialize);
    const observer = new MutationObserver(records => {
      for (const record of records) {
        if (record.type === 'attributes') {
          const target = record.target;
          if (target && target.matches && target.matches(SHELL)) initialize(target);
          continue;
        }
        if (record.type !== 'childList') continue;
        record.removedNodes.forEach(destroyWithin);
        record.addedNodes.forEach(node => {
          if (node.nodeType !== 1) return;
          // MathJax and UI updates outside the graph are ignored quickly.
          if ((node.matches && node.matches(SHELL)) || (node.querySelector && node.querySelector(SHELL))) {
            shellsWithin(node).forEach(initialize);
          }
        });
      }
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['data-config']
    });
    window.__NEOEX_GRAPH_OBSERVER__ = observer;
  }

  window.NEOEX_attachGraphHost = function (host) {
    if (!host) return;
    startGlobalGraphObserver();
    shellsWithin(host).forEach(initialize);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startGlobalGraphObserver, { once: true });
  } else {
    startGlobalGraphObserver();
  }

  window.NEOEX_initGraphShell = initialize;
  window.dispatchEvent(new Event('neoex-runtime-ready'));
})();
