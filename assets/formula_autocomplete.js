/**
 * Autocomplete for OPView formula expression inputs.
 * Attaches to all dcc.Input elements whose Dash ID type is "formula-row-expression".
 * Suggests math functions + notebook variables read from #notebook-vars-for-js.
 */
(function () {
  'use strict';

  // ── Static completions (math functions & constants) ─────────────────────────
  const STATIC = [
    { match: 'sin',      insert: 'sin(',      sig: 'sin(x)' },
    { match: 'cos',      insert: 'cos(',      sig: 'cos(x)' },
    { match: 'tan',      insert: 'tan(',      sig: 'tan(x)' },
    { match: 'asin',     insert: 'asin(',     sig: 'asin(x)' },
    { match: 'acos',     insert: 'acos(',     sig: 'acos(x)' },
    { match: 'atan',     insert: 'atan(',     sig: 'atan(x)' },
    { match: 'atan2',    insert: 'atan2(',    sig: 'atan2(y, x)' },
    { match: 'sinh',     insert: 'sinh(',     sig: 'sinh(x)' },
    { match: 'cosh',     insert: 'cosh(',     sig: 'cosh(x)' },
    { match: 'tanh',     insert: 'tanh(',     sig: 'tanh(x)' },
    { match: 'exp',      insert: 'exp(',      sig: 'exp(x)' },
    { match: 'log',      insert: 'log(',      sig: 'log(x)  — natural log' },
    { match: 'log10',    insert: 'log10(',    sig: 'log10(x)' },
    { match: 'log2',     insert: 'log2(',     sig: 'log2(x)' },
    { match: 'sqrt',     insert: 'sqrt(',     sig: 'sqrt(x)' },
    { match: 'abs',      insert: 'abs(',      sig: 'abs(x)' },
    { match: 'floor',    insert: 'floor(',    sig: 'floor(x)' },
    { match: 'ceil',     insert: 'ceil(',     sig: 'ceil(x)' },
    { match: 'round',    insert: 'round(',    sig: 'round(x)' },
    { match: 'hypot',    insert: 'hypot(',    sig: 'hypot(x, y)' },
    { match: 'sign',     insert: 'sign(',     sig: 'sign(x)' },
    { match: 'degrees',  insert: 'degrees(',  sig: 'degrees(x)  — rad→deg' },
    { match: 'radians',  insert: 'radians(',  sig: 'radians(x)  — deg→rad' },
    { match: 'clamp',    insert: 'clamp(',    sig: 'clamp(x, lo, hi)' },
    { match: 'lerp',     insert: 'lerp(',     sig: 'lerp(a, b, t)' },
    { match: 'min',      insert: 'min(',      sig: 'min(a, b)' },
    { match: 'max',      insert: 'max(',      sig: 'max(a, b)' },
    { match: 'pi',       insert: 'pi',        sig: 'pi  ≈ 3.14159' },
    { match: 'e',        insert: 'e',         sig: 'e   ≈ 2.71828' },
    { match: 'tau',      insert: 'tau',       sig: 'tau = 2*pi' },
    { match: 'deg',      insert: 'deg',       sig: 'deg = pi/180' },
    { match: 'inf',      insert: 'inf',       sig: 'inf = Infinity' },
  ];

  const STATIC_WORDS = new Set(STATIC.map(c => c.match));

  // ── Read notebook variables from the hidden input ────────────────────────────
  function notebookVarCompletions() {
    const el = document.getElementById('notebook-vars-for-js');
    if (!el || !el.value) return [];
    let names;
    try { names = JSON.parse(el.value); } catch { return []; }
    return (names || [])
      .filter(n => !STATIC_WORDS.has(n))
      .map(n => ({ match: n, insert: n, sig: n + '  (notebook)' }));
  }

  // ── Popup DOM ────────────────────────────────────────────────────────────────
  let popup  = null;
  let active = -1;
  let matches = [];
  let currentInput = null;

  function ensurePopup() {
    if (popup) return popup;
    popup = Object.assign(document.createElement('div'), { id: 'fml-ac-popup' });
    Object.assign(popup.style, {
      position: 'fixed', zIndex: '99999',
      background: '#fff', border: '1px solid #94a3b8',
      borderRadius: '10px', boxShadow: '0 10px 32px rgba(15,23,42,.18)',
      maxHeight: '220px', overflowY: 'auto',
      minWidth: '260px', maxWidth: '480px',
      fontFamily: '"JetBrains Mono","Fira Code",Consolas,monospace',
      fontSize: '13px', display: 'none', padding: '4px 0',
    });
    document.body.appendChild(popup);
    return popup;
  }

  function hide() {
    if (popup) popup.style.display = 'none';
    matches = []; active = -1;
  }

  // ── Word before cursor ────────────────────────────────────────────────────────
  function wordBefore(input) {
    const before = input.value.slice(0, input.selectionStart);
    const m = before.match(/([a-zA-Z_][a-zA-Z0-9_]*)$/);
    return m ? m[1] : '';
  }

  // ── Position dropdown below caret ────────────────────────────────────────────
  function dropdownPos(input) {
    const rect = input.getBoundingClientRect();
    return { x: rect.left, y: rect.bottom + 2 };
  }

  // ── Escape HTML ───────────────────────────────────────────────────────────────
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ── Render ────────────────────────────────────────────────────────────────────
  function render(word) {
    const p = ensurePopup();
    p.innerHTML = '';
    const hi = word.length;
    matches.forEach((m, i) => {
      const el = document.createElement('div');
      Object.assign(el.style, { padding: '6px 14px', cursor: 'pointer', whiteSpace: 'nowrap' });
      el.innerHTML =
        '<span style="color:#2563eb;font-weight:700">' + esc(m.sig.slice(0, hi)) + '</span>' +
        '<span style="color:#334155">'                 + esc(m.sig.slice(hi))    + '</span>';
      el.addEventListener('mouseover', () => setActive(i));
      el.addEventListener('mousedown', e => { e.preventDefault(); apply(matches[i]); });
      p.appendChild(el);
    });
    setActive(0);
  }

  function setActive(i) {
    if (!popup) return;
    popup.querySelectorAll('div').forEach((el, idx) => {
      el.style.background = idx === i ? '#eff6ff' : '';
    });
    active = i;
    const items = popup.querySelectorAll('div');
    if (items[i]) items[i].scrollIntoView({ block: 'nearest' });
  }

  // ── Apply completion ──────────────────────────────────────────────────────────
  function apply(m) {
    if (!currentInput) return;
    const pos    = currentInput.selectionStart;
    const val    = currentInput.value;
    const before = val.slice(0, pos);
    const wMatch = before.match(/([a-zA-Z_][a-zA-Z0-9_]*)$/);
    if (!wMatch) return;
    const wordStart = pos - wMatch[1].length;
    const newVal    = val.slice(0, wordStart) + m.insert + val.slice(pos);
    const newPos    = wordStart + m.insert.length;
    // Use React-compatible native setter
    const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    nativeSetter.call(currentInput, newVal);
    currentInput.setSelectionRange(newPos, newPos);
    currentInput.dispatchEvent(new Event('input', { bubbles: true }));
    hide();
    currentInput.focus();
  }

  // ── Suggest ──────────────────────────────────────────────────────────────────
  function suggest(input) {
    const word = wordBefore(input);
    if (word.length < 1) { hide(); return; }
    const lower = word.toLowerCase();
    const all   = [...STATIC, ...notebookVarCompletions()];
    matches = all.filter(c => c.match.toLowerCase().startsWith(lower) && c.match !== word);
    if (!matches.length) { hide(); return; }
    render(word);
    const p = ensurePopup();
    const { x, y } = dropdownPos(input);
    p.style.left = x + 'px';
    p.style.top  = y + 'px';
    p.style.display = 'block';
    requestAnimationFrame(() => {
      const r = p.getBoundingClientRect();
      if (r.right  > window.innerWidth  - 8) p.style.left = Math.max(4, window.innerWidth  - r.width  - 8) + 'px';
      if (r.bottom > window.innerHeight - 8) p.style.top  = (y - r.height - input.getBoundingClientRect().height - 4) + 'px';
    });
  }

  // ── Event handlers ────────────────────────────────────────────────────────────
  function onInput() { currentInput = this; suggest(this); }

  function onKeydown(e) {
    if (!popup || popup.style.display === 'none' || !matches.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((active + 1) % matches.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((active - 1 + matches.length) % matches.length); }
    else if (e.key === 'Tab') { e.preventDefault(); if (active >= 0) apply(matches[active]); }
    else if (e.key === 'Enter') {
      if (active > 0 || (active === 0 && matches.length === 1)) { e.preventDefault(); apply(matches[active]); }
    }
    else if (e.key === 'Escape') { e.preventDefault(); hide(); }
  }

  function onBlur() { setTimeout(hide, 160); }

  // ── Attach ────────────────────────────────────────────────────────────────────
  function isFormulaInput(el) {
    if (el.tagName !== 'INPUT') return false;
    // Dash renders pattern-matching IDs as JSON in the id attribute
    try {
      const parsed = JSON.parse(el.id || '');
      return parsed && parsed.type === 'formula-row-expression';
    } catch { return false; }
  }

  function attachTo(el) {
    if (el._fmlAcAttached) return;
    el._fmlAcAttached = true;
    el.addEventListener('input',   onInput);
    el.addEventListener('keydown', onKeydown);
    el.addEventListener('blur',    onBlur);
  }

  function scanAndAttach() {
    document.querySelectorAll('input[type="text"], input:not([type])').forEach(el => {
      if (isFormulaInput(el)) attachTo(el);
    });
  }

  // Initial scan + watch for Dash re-renders
  scanAndAttach();
  const obs = new MutationObserver(scanAndAttach);
  obs.observe(document.body, { childList: true, subtree: true });
})();
