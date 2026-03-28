/**
 * Monaco Editor integration for the OPView calculation notebook.
 * Loads Monaco from CDN, replaces the plain textarea with a full code editor.
 * Falls back to the textarea if Monaco fails to load (offline / CDN blocked).
 */
(function () {
  var VERSION = '0.45.0';
  var CDN = 'https://cdn.jsdelivr.net/npm/monaco-editor@' + VERSION + '/min/vs';

  // ── Completion provider ───────────────────────────────────────────────────
  function registerCompletionProvider() {
    var FK = monaco.languages.CompletionItemKind;

    function getUserVarNames() {
      var el = document.getElementById('notebook-vars-for-js');
      if (!el || !el.value) return [];
      try { return JSON.parse(el.value) || []; } catch (e) { return []; }
    }

    monaco.languages.registerCompletionItemProvider('nb', {
      triggerCharacters: [],
      provideCompletionItems: function (model, position) {
        var word  = model.getWordUntilPosition(position);
        var range = {
          startLineNumber: position.lineNumber,
          endLineNumber:   position.lineNumber,
          startColumn:     word.startColumn,
          endColumn:       word.endColumn,
        };
        var suggestions = [];

        // Built-in catalogue from notebook_autocomplete.js
        (window._nbCompletions || []).forEach(function (c) {
          suggestions.push({
            label:      c.match,
            kind:       c.insert.slice(-1) === '(' ? FK.Function : FK.Constant,
            insertText: c.insert,
            detail:     c.sig,
            sortText:   '0' + c.match,
            range:      range,
          });
        });

        // User-defined notebook variables
        getUserVarNames().forEach(function (name) {
          suggestions.push({
            label:      name,
            kind:       FK.Variable,
            insertText: name,
            detail:     'notebook variable',
            sortText:   '1' + name,
            range:      range,
          });
        });

        return { suggestions: suggestions };
      },
    });
  }

  // ── Language definition ───────────────────────────────────────────────────
  function registerLanguage() {
    monaco.languages.register({ id: 'nb' });

    monaco.languages.setMonarchTokensProvider('nb', {
      tokenizer: {
        root: [
          // Comments  (// and #)
          [/\/\/.*$/, 'comment'],
          [/#.*$/,    'comment'],
          // Keywords
          [/\b(for|if|elif|else|in|and|or|not|True|False|None|range|enumerate|zip|len)\b/, 'keyword'],
          // Numbers (int, float, scientific)
          [/\b\d+(\.\d+)?([eE][+-]?\d+)?\b/, 'number'],
          // Function calls — word followed by (
          [/[A-Za-z_]\w*(?=\s*\()/, 'function'],
        ]
      }
    });

    registerCompletionProvider();

    monaco.editor.defineTheme('nb-light', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'comment',  foreground: '94a3b8', fontStyle: 'italic' },
        { token: 'keyword',  foreground: '6d28d9', fontStyle: 'bold'   },
        { token: 'number',   foreground: '0369a1'                       },
        { token: 'function', foreground: '0f766e'                       },
      ],
      colors: {
        'editor.background':                  '#fffdf8',
        'editor.lineHighlightBackground':     '#f0f4f8',
        'editorLineNumber.foreground':        '#b8c5d0',
        'editorLineNumber.activeForeground':  '#475467',
        'editor.selectionBackground':         '#dbeafe',
        'editorBracketMatch.background':      '#fef9c3',
        'editorBracketMatch.border':          '#f59e0b',
        'editorIndentGuide.background':       '#e2e8f0',
      }
    });
  }

  // ── Editor creation ───────────────────────────────────────────────────────
  function createEditor() {
    var container = document.getElementById('notebook-monaco-container');
    var textarea  = document.getElementById('notebook-textarea');
    var hidden    = document.getElementById('notebook-live-text');
    var lineNums  = document.getElementById('notebook-line-numbers');

    if (!container || window._monacoEditor) return;

    registerLanguage();

    // Show Monaco container, hide plain textarea and old line-number column
    container.style.display = 'flex';
    if (textarea)  textarea.style.display  = 'none';
    if (lineNums)  lineNums.style.display   = 'none';

    // Restore from localStorage if textarea is empty (page refresh)
    var initialValue = textarea ? (textarea.value || '') : '';
    if (!initialValue) {
      try {
        var saved = localStorage.getItem('opview_notebook');
        if (saved) initialValue = saved;
      } catch (e) {}
    }

    var editor = monaco.editor.create(container, {
      value:                initialValue,
      language:             'nb',
      theme:                'nb-light',
      fontSize:             14,
      lineHeight:           34,
      fontFamily:           "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
      minimap:              { enabled: true, scale: 1 },
      lineNumbers:          'on',
      automaticLayout:      true,
      scrollBeyondLastLine: false,
      wordWrap:             'off',
      renderLineHighlight:  'line',
      tabSize:              4,
      insertSpaces:         true,
      autoIndent:           'advanced',
      matchBrackets:        'always',
      padding:              { top: 18, bottom: 18 },
      scrollbar:            { verticalScrollbarSize: 8, horizontalScrollbarSize: 8 },
      suggest:              { showWords: false },
      quickSuggestions:     { other: true, comments: false, strings: false },
    });

    window._monacoEditor = editor;

    // Debounced localStorage save
    var _saveTimer = null;
    function schedSave(val) {
      if (_saveTimer) clearTimeout(_saveTimer);
      _saveTimer = setTimeout(function () {
        try { localStorage.setItem('opview_notebook', val); } catch (e) {}
      }, 800);
    }

    // ── Monaco → Dash (via hidden input) ─────────────────────────────────
    // _monacoSyncing prevents re-triggering when WE set the value from Dash
    editor.onDidChangeModelContent(function () {
      if (window._monacoSyncing) return;
      var val = editor.getValue();
      schedSave(val);
      if (hidden) {
        hidden.value = val;
        hidden.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (window._notebookRenderResults) window._notebookRenderResults(val);
    });

    // ── Monaco scroll → results gutter (pixel-locked via translateY) ─────
    editor.onDidScrollChange(function (e) {
      var resultsEl = document.getElementById('notebook-results');
      if (resultsEl) resultsEl.style.transform = 'translateY(-' + e.scrollTop + 'px)';
    });

    // Initial client-side render
    if (window._notebookRenderResults) {
      window._notebookRenderResults(editor.getValue());
    }
  }

  // ── CDN loader ────────────────────────────────────────────────────────────
  function loadMonaco() {
    if (window.monaco)                               { createEditor(); return; }
    if (document.getElementById('_monaco_loader'))   { return; }

    var s   = document.createElement('script');
    s.id    = '_monaco_loader';
    s.src   = CDN + '/loader.js';
    s.async = true;
    s.onload = function () {
      window.require.config({ paths: { vs: CDN } });
      window.require(['vs/editor/editor.main'], createEditor);
    };
    s.onerror = function () {
      console.warn('[OPView] Monaco CDN unavailable — falling back to plain textarea.');
    };
    document.head.appendChild(s);
  }

  // ── Dash → Monaco sync (called from Dash clientside callback) ─────────
  window._syncToMonaco = function (val) {
    if (!window._monacoEditor) return;
    var current = window._monacoEditor.getValue();
    if (current === (val || '')) return;
    window._monacoSyncing = true;
    window._monacoEditor.setValue(val || '');
    window._monacoSyncing = false;
    // Re-render results after external value change
    if (window._notebookRenderResults) {
      window._notebookRenderResults(val || '');
    }
  };

  // ── Boot ─────────────────────────────────────────────────────────────────
  window.addEventListener('load', function () {
    loadMonaco();
    // Re-try when Dash rebuilds the DOM (tab switches, etc.)
    new MutationObserver(function () {
      if (!window._monacoEditor) loadMonaco();
    }).observe(document.body, { childList: true, subtree: true });
  });
})();
