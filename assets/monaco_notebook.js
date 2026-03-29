/**
 * Monaco Editor integration for the OPView calculation notebook.
 * Loads Monaco from CDN, replaces the plain textarea with a full code editor.
 * Falls back to the textarea if Monaco fails to load (offline / CDN blocked).
 */
(function () {
  var VERSION = '0.45.0';
  var CDN = 'https://cdn.jsdelivr.net/npm/monaco-editor@' + VERSION + '/min/vs';

  function setClientDebug(message) {
    var debugEl = document.getElementById('notebook-client-debug');
    if (!debugEl) return;
    var stamp = new Date().toLocaleTimeString();
    debugEl.textContent = '[Client ' + stamp + '] ' + message;
  }

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
      keywords: ['for', 'if', 'elif', 'else', 'in', 'and', 'or', 'not', 'range', 'enumerate', 'zip', 'len'],
      languageConstants: ['True', 'False', 'None'],
      trigFunctions: ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh'],
      mathFunctions: [
        'exp', 'log', 'log10', 'sqrt', 'abs', 'floor', 'ceil', 'round', 'hypot',
        'min', 'max', 'sign', 'log2', 'degrees', 'radians', 'clamp', 'lerp',
        'factorial', 'gcd', 'lcm', 'erf', 'erfc', 'gamma', 'lgamma', 'beta'
      ],
      engineeringFunctions: [
        'cfl_dt', 'diffusion_dt', 'fourier_number', 'peclet', 'cell_size',
        'domain_points', 'reynolds', 'mach', 'prandtl', 'nusselt_dittus',
        'biot', 'fourier_thermal', 'lewis', 'weber', 'stokes', 'grashof'
      ],
      constitutiveFunctions: [
        'von_mises', 'shear_modulus', 'lame_lambda', 'hooke_1d', 'hooke_3d',
        'plane_strain', 'plane_stress', 'plane_stress_ezz'
      ],
      vectorFunctions: ['dot', 'cross', 'norm', 'normalize', 'length', 'outer', 'norm_p'],
      matrixFunctions: [
        'det', 'inv', 'transpose', 'trace', 'rank', 'eig', 'diag', 'solve',
        'lstsq', 'svd', 'pinv', 'cond', 'matrix_power', 'kron', 'cholesky',
        'qr', 'eig_full'
      ],
      builderFunctions: [
        'eye', 'zeros', 'ones', 'shape', 'linspace', 'arange', 'flatten',
        'vstack', 'hstack', 'meshgrid', 'full', 'reshape', 'concat', 'append',
        'repeat', 'tile', 'roll', 'flip', 'sort', 'argsort', 'unique', 'clip',
        'where'
      ],
      statisticsFunctions: [
        'sum', 'mean', 'std', 'variance', 'median', 'prod', 'cumsum', 'diff',
        'diff2', 'cov', 'histogram', 'mode', 'percentile', 'quantile',
        'corrcoef', 'zscore', 'norm01'
      ],
      signalFunctions: [
        'interp', 'polyfit', 'polyval', 'gradient', 'trapz', 'cumtrapz',
        'fft', 'ifft', 'fftfreq', 'fftshift', 'real', 'imag', 'angle'
      ],
      compositionFunctions: ['wt_to_mol', 'wt_to_mol2', 'mol_to_wt'],
      constants: ['pi', 'e', 'tau', 'deg', 'inf', 'g_n', 'c_0', 'R_gas', 'k_B', 'N_A', 'h_p', 'sigma_SB', 'mu_0', 'eps_0'],
      units: [
        'nm', 'um', 'mm', 'cm', 'm', 'km', 'Pa', 'kPa', 'MPa', 'GPa', 'sec',
        'hour', 'day', 'week', 'month', 'ms', 'us', 'min', 'h', 'kg', 'N',
        'kN', 'MN', 'J', 'kJ', 'MJ', 'W', 'kW', 'MW', 'Hz', 'kHz', 'MHz',
        'bar', 'mbar', 'kWh', 'atm', 'L'
      ],
      tokenizer: {
        root: [
          // Comments  (// and inline #)
          [/\/\/.*$/, 'comment'],
          [/#.*$/,    'comment'],
          // Numbers (int, float, scientific)
          [/\b\d+(\.\d+)?([eE][+-]?\d+)?\b/, 'number'],
          // Strings
          [/"(?:[^"\\]|\\.)*"/, 'string'],
          [/'(?:[^'\\]|\\.)*'/, 'string'],
          // Matrix multiply operator before generic operators
          [/@/, 'operator.matrix'],
          // Operators
          [/[+\-*/%^=<>!~:&|]+/, 'operator'],
          // Brackets / punctuation
          [/\[/, 'delimiter.square'],
          [/\]/, 'delimiter.square'],
          [/\(/, 'delimiter.parenthesis'],
          [/\)/, 'delimiter.parenthesis'],
          [/\{/, 'delimiter.curly'],
          [/\}/, 'delimiter.curly'],
          [/,|;|:/, 'delimiter'],
          // Built-in and user-defined function calls
          [/[A-Za-z_]\w*(?=\s*\()/, {
            cases: {
              '@trigFunctions':         'function.trig',
              '@mathFunctions':         'function.math',
              '@engineeringFunctions':  'function.engineering',
              '@constitutiveFunctions': 'function.constitutive',
              '@vectorFunctions':       'function.vector',
              '@matrixFunctions':       'function.matrix',
              '@builderFunctions':      'function.builder',
              '@statisticsFunctions':   'function.stats',
              '@signalFunctions':       'function.signal',
              '@compositionFunctions':  'function.composition',
              '@keywords':              'keyword',
              '@default':               'function.user'
            }
          }],
          // Bare identifiers / predefined constants / units
          [/[A-Za-z_]\w*/, {
            cases: {
              '@keywords':           'keyword',
              '@languageConstants':  'constant.language',
              '@constants':          'constant.predefined',
              '@units':              'unit.predefined',
              '@default':            'identifier'
            }
          }],
        ]
      }
    });

    registerCompletionProvider();

    // ── Theme definitions ─────────────────────────────────────────────────

    var THEMES = {
      // ── Light (default) ──────────────────────────────────────────────────
      'nb-light': {
        base: 'vs', inherit: true,
        rules: [
          { token: 'comment',               foreground: '94a3b8', fontStyle: 'italic' },
          { token: 'keyword',               foreground: '7c3aed', fontStyle: 'bold' },
          { token: 'number',                foreground: '111827' },
          { token: 'string',                foreground: 'b45309' },
          { token: 'constant.language',     foreground: '7c3aed', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: '7e22ce', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'c2410c', fontStyle: 'bold' },
          { token: 'identifier',            foreground: '111827' },
          { token: 'function.trig',         foreground: '0f766e', fontStyle: 'bold' },
          { token: 'function.math',         foreground: '0d9488' },
          { token: 'function.engineering',  foreground: 'ea580c', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'be185d', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: '15803d', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '0f766e', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: '16a34a', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: '7c2d12' },
          { token: 'function.signal',       foreground: '9333ea' },
          { token: 'function.composition',  foreground: 'b91c1c' },
          { token: 'function.user',         foreground: '2563eb' },
          { token: 'operator',              foreground: '475569' },
          { token: 'operator.matrix',       foreground: '0f766e', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: '64748b' },
          { token: 'delimiter.square',      foreground: '166534', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: '334155' },
          { token: 'delimiter.curly',       foreground: '7c2d12' },
        ],
        colors: {
          'editor.background':                   '#fffdf8',
          'editor.lineHighlightBackground':      '#f0f4f8',
          'editorLineNumber.foreground':         '#b8c5d0',
          'editorLineNumber.activeForeground':   '#475467',
          'editor.selectionBackground':          '#93c5fd99',
          'editor.inactiveSelectionBackground':  '#bfdbfe88',
          'editor.selectionHighlightBackground': '#93c5fd55',
          'editorBracketMatch.background':       '#fef9c3',
          'editorBracketMatch.border':           '#f59e0b',
          'editorIndentGuide.background':        '#e2e8f0',
        }
      },

      // ── Dark (VS Code Dark+) ──────────────────────────────────────────────
      'nb-dark': {
        base: 'vs-dark', inherit: true,
        rules: [
          { token: 'comment',               foreground: '6a9955', fontStyle: 'italic' },
          { token: 'keyword',               foreground: '569cd6', fontStyle: 'bold' },
          { token: 'number',                foreground: 'b5cea8' },
          { token: 'string',                foreground: 'ce9178' },
          { token: 'constant.language',     foreground: '569cd6', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: '9cdcfe', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'f78c6c', fontStyle: 'bold' },
          { token: 'identifier',            foreground: 'd4d4d4' },
          { token: 'function.trig',         foreground: '4ec9b0', fontStyle: 'bold' },
          { token: 'function.math',         foreground: '4ec9b0' },
          { token: 'function.engineering',  foreground: 'f78c6c', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'c586c0', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: '4ec9b0', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '4ec9b0', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: 'dcdcaa', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: 'dcdcaa' },
          { token: 'function.signal',       foreground: 'c586c0' },
          { token: 'function.composition',  foreground: 'f44747' },
          { token: 'function.user',         foreground: '9cdcfe' },
          { token: 'operator',              foreground: 'd4d4d4' },
          { token: 'operator.matrix',       foreground: '4ec9b0', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: '808080' },
          { token: 'delimiter.square',      foreground: 'ffd700', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: 'd4d4d4' },
          { token: 'delimiter.curly',       foreground: 'f44747' },
        ],
        colors: {
          'editor.background':                   '#1e1e1e',
          'editor.foreground':                   '#d4d4d4',
          'editor.lineHighlightBackground':      '#2a2d2e',
          'editorLineNumber.foreground':         '#858585',
          'editorLineNumber.activeForeground':   '#c6c6c6',
          'editor.selectionBackground':          '#264f78',
          'editor.inactiveSelectionBackground':  '#3a3d41',
          'editorBracketMatch.background':       '#0d3a58',
          'editorBracketMatch.border':           '#888888',
        }
      },

      // ── Dracula ───────────────────────────────────────────────────────────
      'nb-dracula': {
        base: 'vs-dark', inherit: true,
        rules: [
          { token: 'comment',               foreground: '6272a4', fontStyle: 'italic' },
          { token: 'keyword',               foreground: 'ff79c6', fontStyle: 'bold' },
          { token: 'number',                foreground: 'bd93f9' },
          { token: 'string',                foreground: 'f1fa8c' },
          { token: 'constant.language',     foreground: 'ff79c6', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: 'bd93f9', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'ffb86c', fontStyle: 'bold' },
          { token: 'identifier',            foreground: 'f8f8f2' },
          { token: 'function.trig',         foreground: '50fa7b', fontStyle: 'bold' },
          { token: 'function.math',         foreground: '50fa7b' },
          { token: 'function.engineering',  foreground: 'ffb86c', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'ff79c6', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: '50fa7b', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '8be9fd', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: '50fa7b', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: 'ffb86c' },
          { token: 'function.signal',       foreground: 'bd93f9' },
          { token: 'function.composition',  foreground: 'ff5555' },
          { token: 'function.user',         foreground: '8be9fd' },
          { token: 'operator',              foreground: 'ff79c6' },
          { token: 'operator.matrix',       foreground: '8be9fd', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: 'f8f8f2' },
          { token: 'delimiter.square',      foreground: '50fa7b', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: 'f8f8f2' },
          { token: 'delimiter.curly',       foreground: 'ff5555' },
        ],
        colors: {
          'editor.background':                   '#282a36',
          'editor.foreground':                   '#f8f8f2',
          'editor.lineHighlightBackground':      '#44475a',
          'editorLineNumber.foreground':         '#6272a4',
          'editorLineNumber.activeForeground':   '#f8f8f2',
          'editor.selectionBackground':          '#44475a',
          'editor.inactiveSelectionBackground':  '#3d4058',
          'editorBracketMatch.background':       '#44475a',
          'editorBracketMatch.border':           '#ff79c6',
        }
      },

      // ── Monokai ───────────────────────────────────────────────────────────
      'nb-monokai': {
        base: 'vs-dark', inherit: true,
        rules: [
          { token: 'comment',               foreground: '75715e', fontStyle: 'italic' },
          { token: 'keyword',               foreground: 'f92672', fontStyle: 'bold' },
          { token: 'number',                foreground: 'ae81ff' },
          { token: 'string',                foreground: 'e6db74' },
          { token: 'constant.language',     foreground: 'f92672', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: 'ae81ff', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'fd971f', fontStyle: 'bold' },
          { token: 'identifier',            foreground: 'f8f8f2' },
          { token: 'function.trig',         foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'function.math',         foreground: 'a6e22e' },
          { token: 'function.engineering',  foreground: 'fd971f', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'f92672', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '66d9e8', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: 'fd971f' },
          { token: 'function.signal',       foreground: 'ae81ff' },
          { token: 'function.composition',  foreground: 'f92672' },
          { token: 'function.user',         foreground: '66d9e8' },
          { token: 'operator',              foreground: 'f92672' },
          { token: 'operator.matrix',       foreground: '66d9e8', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: 'f8f8f2' },
          { token: 'delimiter.square',      foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: 'f8f8f2' },
          { token: 'delimiter.curly',       foreground: 'f92672' },
        ],
        colors: {
          'editor.background':                   '#272822',
          'editor.foreground':                   '#f8f8f2',
          'editor.lineHighlightBackground':      '#3e3d32',
          'editorLineNumber.foreground':         '#75715e',
          'editorLineNumber.activeForeground':   '#f8f8f2',
          'editor.selectionBackground':          '#49483e',
          'editor.inactiveSelectionBackground':  '#3e3d32',
          'editorBracketMatch.background':       '#49483e',
          'editorBracketMatch.border':           '#a6e22e',
        }
      },

      // ── Monokai ───────────────────────────────────────────────────────────
      'nb-monokai': {
        base: 'vs-dark', inherit: true,
        rules: [
          { token: 'comment',               foreground: '75715e', fontStyle: 'italic' },
          { token: 'keyword',               foreground: 'f92672', fontStyle: 'bold' },
          { token: 'number',                foreground: 'ae81ff' },
          { token: 'string',                foreground: 'e6db74' },
          { token: 'constant.language',     foreground: 'f92672', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: 'ae81ff', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'fd971f', fontStyle: 'bold' },
          { token: 'identifier',            foreground: 'f8f8f2' },
          { token: 'function.trig',         foreground: '66d9ef', fontStyle: 'bold' },
          { token: 'function.math',         foreground: '66d9ef' },
          { token: 'function.engineering',  foreground: 'fd971f', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'f92672', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '66d9ef', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: 'e6db74' },
          { token: 'function.signal',       foreground: 'ae81ff' },
          { token: 'function.composition',  foreground: 'f92672' },
          { token: 'function.user',         foreground: '66d9ef' },
          { token: 'operator',              foreground: 'f92672' },
          { token: 'operator.matrix',       foreground: '66d9ef', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: 'f8f8f2' },
          { token: 'delimiter.square',      foreground: 'a6e22e', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: 'f8f8f2' },
          { token: 'delimiter.curly',       foreground: 'f92672' },
        ],
        colors: {
          'editor.background':                   '#272822',
          'editor.foreground':                   '#f8f8f2',
          'editor.lineHighlightBackground':      '#3e3d32',
          'editorLineNumber.foreground':         '#75715e',
          'editorLineNumber.activeForeground':   '#f8f8f2',
          'editor.selectionBackground':          '#49483e',
          'editor.inactiveSelectionBackground':  '#3e3d32',
          'editorBracketMatch.background':       '#49483e',
          'editorBracketMatch.border':           '#a6e22e',
        }
      },

      // ── Solarized Dark ────────────────────────────────────────────────────
      'nb-solarized': {
        base: 'vs-dark', inherit: true,
        rules: [
          { token: 'comment',               foreground: '657b83', fontStyle: 'italic' },
          { token: 'keyword',               foreground: '859900', fontStyle: 'bold' },
          { token: 'number',                foreground: 'd33682' },
          { token: 'string',                foreground: '2aa198' },
          { token: 'constant.language',     foreground: 'cb4b16', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: 'b58900', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'cb4b16', fontStyle: 'bold' },
          { token: 'identifier',            foreground: '839496' },
          { token: 'function.trig',         foreground: '268bd2', fontStyle: 'bold' },
          { token: 'function.math',         foreground: '268bd2' },
          { token: 'function.engineering',  foreground: 'cb4b16', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'd33682', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: '859900', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '2aa198', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: '859900', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: 'b58900' },
          { token: 'function.signal',       foreground: '6c71c4' },
          { token: 'function.composition',  foreground: 'dc322f' },
          { token: 'function.user',         foreground: '93a1a1' },
          { token: 'operator',              foreground: '859900' },
          { token: 'operator.matrix',       foreground: '2aa198', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: '657b83' },
          { token: 'delimiter.square',      foreground: '859900', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: '839496' },
          { token: 'delimiter.curly',       foreground: 'dc322f' },
        ],
        colors: {
          'editor.background':                   '#002b36',
          'editor.foreground':                   '#839496',
          'editor.lineHighlightBackground':      '#073642',
          'editorLineNumber.foreground':         '#586e75',
          'editorLineNumber.activeForeground':   '#93a1a1',
          'editor.selectionBackground':          '#073642',
          'editor.inactiveSelectionBackground':  '#073642aa',
          'editorBracketMatch.background':       '#073642',
          'editorBracketMatch.border':           '#2aa198',
        }
      },

      // ── GitHub Light ──────────────────────────────────────────────────────
      'nb-github': {
        base: 'vs', inherit: true,
        rules: [
          { token: 'comment',               foreground: '6e7781', fontStyle: 'italic' },
          { token: 'keyword',               foreground: 'cf222e', fontStyle: 'bold' },
          { token: 'number',                foreground: '0550ae' },
          { token: 'string',                foreground: '0a3069' },
          { token: 'constant.language',     foreground: 'cf222e', fontStyle: 'bold' },
          { token: 'constant.predefined',   foreground: '8250df', fontStyle: 'bold' },
          { token: 'unit.predefined',       foreground: 'e16d3a', fontStyle: 'bold' },
          { token: 'identifier',            foreground: '24292f' },
          { token: 'function.trig',         foreground: '116329', fontStyle: 'bold' },
          { token: 'function.math',         foreground: '116329' },
          { token: 'function.engineering',  foreground: 'e16d3a', fontStyle: 'bold' },
          { token: 'function.constitutive', foreground: 'a475f9', fontStyle: 'bold' },
          { token: 'function.vector',       foreground: '116329', fontStyle: 'bold' },
          { token: 'function.matrix',       foreground: '0550ae', fontStyle: 'bold' },
          { token: 'function.builder',      foreground: '116329', fontStyle: 'bold' },
          { token: 'function.stats',        foreground: '953800' },
          { token: 'function.signal',       foreground: '8250df' },
          { token: 'function.composition',  foreground: 'cf222e' },
          { token: 'function.user',         foreground: '0550ae' },
          { token: 'operator',              foreground: 'cf222e' },
          { token: 'operator.matrix',       foreground: '0550ae', fontStyle: 'bold' },
          { token: 'delimiter',             foreground: '57606a' },
          { token: 'delimiter.square',      foreground: '116329', fontStyle: 'bold' },
          { token: 'delimiter.parenthesis', foreground: '24292f' },
          { token: 'delimiter.curly',       foreground: 'cf222e' },
        ],
        colors: {
          'editor.background':                   '#ffffff',
          'editor.foreground':                   '#24292f',
          'editor.lineHighlightBackground':      '#f6f8fa',
          'editorLineNumber.foreground':         '#8c959f',
          'editorLineNumber.activeForeground':   '#24292f',
          'editor.selectionBackground':          '#0969da33',
          'editor.inactiveSelectionBackground':  '#0969da1a',
          'editorBracketMatch.background':       '#dafbe1',
          'editorBracketMatch.border':           '#2da44e',
          'editorIndentGuide.background':        '#d8dee4',
        }
      },
    };

    Object.keys(THEMES).forEach(function (name) {
      monaco.editor.defineTheme(name, THEMES[name]);
    });

    registerSignatureHelpProvider();
  }

  // ── Signature help ───────────────────────────────────────────────────────
  function registerSignatureHelpProvider() {
    var SIGS = {
      // Trig
      sin:    { sig: 'sin(x)',           params: ['x — angle in radians'] },
      cos:    { sig: 'cos(x)',           params: ['x — angle in radians'] },
      tan:    { sig: 'tan(x)',           params: ['x — angle in radians'] },
      asin:   { sig: 'asin(x)',          params: ['x — value in [-1, 1]'] },
      acos:   { sig: 'acos(x)',          params: ['x — value in [-1, 1]'] },
      atan:   { sig: 'atan(x)',          params: ['x'] },
      atan2:  { sig: 'atan2(y, x)',      params: ['y', 'x'] },
      sinh:   { sig: 'sinh(x)',          params: ['x'] },
      cosh:   { sig: 'cosh(x)',          params: ['x'] },
      tanh:   { sig: 'tanh(x)',          params: ['x'] },
      // Math
      sqrt:   { sig: 'sqrt(x)',          params: ['x — non-negative number'] },
      exp:    { sig: 'exp(x)',           params: ['x'] },
      log:    { sig: 'log(x)',           params: ['x — natural logarithm'] },
      log10:  { sig: 'log10(x)',         params: ['x'] },
      log2:   { sig: 'log2(x)',          params: ['x'] },
      abs:    { sig: 'abs(x)',           params: ['x'] },
      floor:  { sig: 'floor(x)',         params: ['x'] },
      ceil:   { sig: 'ceil(x)',          params: ['x'] },
      round:  { sig: 'round(x)',         params: ['x'] },
      sign:   { sig: 'sign(x)',          params: ['x — returns -1, 0, or 1'] },
      hypot:  { sig: 'hypot(x, y)',      params: ['x', 'y'] },
      clamp:  { sig: 'clamp(x, lo, hi)', params: ['x', 'lo — lower bound', 'hi — upper bound'] },
      lerp:   { sig: 'lerp(a, b, t)',    params: ['a — start', 'b — end', 't — in [0,1]'] },
      min:    { sig: 'min(a, b)',        params: ['a', 'b'] },
      max:    { sig: 'max(a, b)',        params: ['a', 'b'] },
      // Stats
      sum:      { sig: 'sum(v)',           params: ['v — vector'] },
      mean:     { sig: 'mean(v)',          params: ['v — vector'] },
      std:      { sig: 'std(v)',           params: ['v — vector'] },
      variance: { sig: 'variance(v)',      params: ['v — vector'] },
      median:   { sig: 'median(v)',        params: ['v — vector'] },
      prod:     { sig: 'prod(v)',          params: ['v — vector'] },
      cumsum:   { sig: 'cumsum(v)',        params: ['v — vector'] },
      diff:     { sig: 'diff(v)',          params: ['v — vector'] },
      // Arrays
      linspace: { sig: 'linspace(a, b, n)',    params: ['a — start', 'b — end', 'n — number of points'] },
      arange:   { sig: 'arange(a, b, step)',   params: ['a — start', 'b — stop (exclusive)', 'step'] },
      zeros:    { sig: 'zeros(rows, cols?)',   params: ['rows', 'cols — omit for vector'] },
      ones:     { sig: 'ones(rows, cols?)',    params: ['rows', 'cols — omit for vector'] },
      eye:      { sig: 'eye(n)',              params: ['n — size of identity matrix'] },
      reshape:  { sig: 'reshape(v, rows, cols)', params: ['v — flat array', 'rows', 'cols'] },
      // Vectors
      dot:       { sig: 'dot(a, b)',      params: ['a — vector', 'b — vector'] },
      cross:     { sig: 'cross(a, b)',    params: ['a — 3D vector', 'b — 3D vector'] },
      norm:      { sig: 'norm(v)',        params: ['v — vector or matrix'] },
      normalize: { sig: 'normalize(v)',   params: ['v — vector'] },
      // Matrix
      det:       { sig: 'det(M)',         params: ['M — square matrix'] },
      inv:       { sig: 'inv(M)',         params: ['M — square matrix'] },
      transpose: { sig: 'transpose(M)',   params: ['M — matrix'] },
      solve:     { sig: 'solve(A, b)',    params: ['A — square matrix', 'b — right-hand side vector'] },
      eig:       { sig: 'eig(M)',         params: ['M — square matrix'] },
      // Engineering
      cfl_dt:        { sig: 'cfl_dt(dx, u, cfl=1)',      params: ['dx — grid spacing', 'u — velocity', 'cfl — CFL number (default 1)'] },
      diffusion_dt:  { sig: 'diffusion_dt(dx, D, f=0.5)',params: ['dx — grid spacing', 'D — diffusivity', 'f — safety factor (default 0.5)'] },
      von_mises:     { sig: 'von_mises(s11, s22, s33, s12=0, s23=0, s13=0)', params: ['s11', 's22', 's33', 's12', 's23', 's13'] },
      shear_modulus: { sig: 'shear_modulus(E, nu)',       params: ['E — Young\'s modulus', 'nu — Poisson\'s ratio'] },
      lame_lambda:   { sig: 'lame_lambda(E, nu)',         params: ['E — Young\'s modulus', 'nu — Poisson\'s ratio'] },
      hooke_1d:      { sig: 'hooke_1d(E, eps)',           params: ['E — Young\'s modulus', 'eps — strain'] },
      plane_stress:  { sig: 'plane_stress(E, nu, exx, eyy, exy=0)', params: ['E', 'nu', 'exx', 'eyy', 'exy'] },
      // Signal
      interp:   { sig: 'interp(x, xp, fp)',   params: ['x — query points', 'xp — data x', 'fp — data y'] },
      polyfit:  { sig: 'polyfit(x, y, deg)',   params: ['x — data x', 'y — data y', 'deg — polynomial degree'] },
      gradient: { sig: 'gradient(v)',          params: ['v — vector'] },
      trapz:    { sig: 'trapz(y, x?)',         params: ['y — values', 'x — optional x positions'] },
      fft:      { sig: 'fft(v)',               params: ['v — signal vector'] },
      // Composition
      wt_to_mol:  { sig: 'wt_to_mol(wt, M)',  params: ['wt — weight fractions array', 'M — molar masses array'] },
      mol_to_wt:  { sig: 'mol_to_wt(x, M)',   params: ['x — mole fractions array', 'M — molar masses array'] },
      // Plot
      plot: { sig: 'plot(x, y, type?, title?, xlabel?, ylabel?)',
              params: ['x — x-axis variable', 'y — y-axis variable(s)',
                       'type — "line" | "scatter" | "bar" | "hist" (default "line")',
                       'title — plot title', 'xlabel — x-axis label', 'ylabel — y-axis label'] },
    };

    monaco.languages.registerSignatureHelpProvider('nb', {
      signatureHelpTriggerCharacters: ['(', ','],
      provideSignatureHelp: function (model, position) {
        var textBefore = model.getValueInRange({
          startLineNumber: position.lineNumber, startColumn: 1,
          endLineNumber:   position.lineNumber, endColumn: position.column,
        });
        // Find the innermost open function call
        var depth = 0, commaCount = 0, funcName = '', i = textBefore.length - 1;
        for (; i >= 0; i--) {
          var c = textBefore[i];
          if (c === ')') { depth++; }
          else if (c === '(') {
            if (depth === 0) { break; }
            depth--;
          } else if (c === ',' && depth === 0) { commaCount++; }
        }
        if (i > 0) {
          var before = textBefore.slice(0, i).trimEnd();
          var m = before.match(/([a-zA-Z_]\w*)$/);
          if (m) funcName = m[1];
        }
        var sig = SIGS[funcName];
        if (!sig) return null;
        return {
          value: {
            signatures: [{
              label: sig.sig,
              parameters: sig.params.map(function(p) { return { label: p }; }),
            }],
            activeSignature: 0,
            activeParameter: Math.min(commaCount, sig.params.length - 1),
          },
          dispose: function() {},
        };
      },
    });
  }

  // ── Editor creation ───────────────────────────────────────────────────────
  function createEditor() {
    var container = document.getElementById('notebook-monaco-container');
    var textarea  = document.getElementById('notebook-textarea');
    var lineNums  = document.getElementById('notebook-line-numbers');
    var runButton = document.getElementById('notebook-run-btn');

    if (!container || window._monacoEditor) return;

    registerLanguage();

    // Show Monaco container, hide plain textarea and old line-number column
    container.style.display = 'block';
    if (textarea)  textarea.style.display  = 'none';
    if (lineNums)  lineNums.style.display   = 'none';

    // Restore from sessionStorage if textarea is empty (tab switch / page refresh within same session)
    var initialValue = textarea ? (textarea.value || '') : '';
    if (!initialValue) {
      try {
        var saved = sessionStorage.getItem('opview_notebook');
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
      minimap:              { enabled: false },
      lineNumbers:          'on',
      automaticLayout:      false,
      scrollBeyondLastLine: false,
      wordWrap:             'off',
      renderLineHighlight:  'line',
      tabSize:              4,
      insertSpaces:         true,
      autoIndent:           'advanced',
      matchBrackets:        'always',
      padding:              { top: 18, bottom: 36 },
      scrollbar:            {
        vertical:             'hidden',
        horizontal:           'hidden',
        verticalScrollbarSize: 0,
        horizontalScrollbarSize: 0,
        handleMouseWheel:     false,
      },
      suggest:              { showWords: false },
      quickSuggestions:     { other: true, comments: false, strings: false },
    });

    container.classList.add('theme-nb-light');
    window._monacoEditor = editor;
    initVimToggle(editor);
    var altLineDecorations = [];
    function isAutoUpdateEnabled() {
      // Read checkbox state directly — no cache, no async Dash delay
      var box = document.getElementById('notebook-auto-update');
      if (box) return !!box.querySelector('input[type="checkbox"]:checked');
      return true;
    }

    function getLiveHiddenInput() {
      return document.getElementById('notebook-live-text');
    }

    function getRunHiddenInput() {
      return document.getElementById('notebook-run-text');
    }

    function pushHiddenValue(el, val) {
      if (!el || !document.body.contains(el)) {
        setClientDebug('push skipped: hidden input missing or detached');
        return;
      }
      var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
      if (setter && setter.set) setter.set.call(el, val);
      else el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function runNotebook(force) {
      var val = editor.getValue();
      setClientDebug('runNotebook(force=' + (!!force) + ', auto=' + isAutoUpdateEnabled() + ', len=' + val.length + ')');
      pushHiddenValue(getLiveHiddenInput(), val);
      if (force || isAutoUpdateEnabled()) {
        pushHiddenValue(getRunHiddenInput(), val);
      }
    }

    function updateAlternatingLines() {
      var model = editor.getModel();
      if (!model) return;
      var lineCount = model.getLineCount();
      var decorations = [];
      for (var line = 1; line <= lineCount; line += 1) {
        decorations.push({
          range: new monaco.Range(line, 1, line, 1),
          options: {
            isWholeLine: true,
            className: (line % 2 === 1) ? 'nb-alt-line-a' : 'nb-alt-line-b',
          }
        });
      }
      altLineDecorations = editor.deltaDecorations(altLineDecorations, decorations);
    }
    window._refreshMonacoAltLines = updateAlternatingLines;

    // ── Grow Monaco container with content (no internal scroll) ──────────
    function updateEditorHeight() {
      var contentHeight = Math.max(400, editor.getContentHeight());
      container.style.height = contentHeight + 'px';
      editor.layout({ width: container.offsetWidth, height: contentHeight });
      // Also stretch the results gutter to the same height so they grow together
      var gutter = document.getElementById('notebook-results');
      if (gutter && gutter.parentElement) {
        gutter.parentElement.style.minHeight = contentHeight + 'px';
      }
    }
    editor.onDidContentSizeChange(updateEditorHeight);
    // Set initial height after first render tick
    setTimeout(function () {
      updateEditorHeight();
      updateAlternatingLines();
    }, 0);

    // Re-layout when window resizes (width changes)
    window.addEventListener('resize', function () {
      if (window._monacoEditor) updateEditorHeight();
    });

    // Debounced sessionStorage save (cleared on server restart automatically)
    var _saveTimer = null;
    function schedSave(val) {
      if (_saveTimer) clearTimeout(_saveTimer);
      _saveTimer = setTimeout(function () {
        try { sessionStorage.setItem('opview_notebook', val); } catch (e) {}
      }, 800);
    }

    // ── Monaco → Dash (via hidden input) ─────────────────────────────────
    // _monacoSyncing prevents re-triggering when WE set the value from Dash
    editor.onDidChangeModelContent(function () {
      if (window._monacoSyncing) return;
      updateAlternatingLines();
      var val = editor.getValue();
      setClientDebug('editor change -> len=' + val.length + ', auto=' + isAutoUpdateEnabled());
      schedSave(val);
      pushHiddenValue(getLiveHiddenInput(), val);
      if (isAutoUpdateEnabled()) {
        pushHiddenValue(getRunHiddenInput(), val);
        if (window._notebookRenderResults) window._notebookRenderResults(val);
      }
    });

    // Initial client-side render
    runNotebook(true);

    if (runButton) {
      runButton.addEventListener('click', function () {
        runNotebook(true);
      });
    }
    var autoBox = document.getElementById('notebook-auto-update');
    if (autoBox) {
      autoBox.addEventListener('change', function () {
        setClientDebug('auto update toggled -> ' + isAutoUpdateEnabled());
        if (isAutoUpdateEnabled()) {
          runNotebook(true);
        }
      });
    }
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, function () {
      runNotebook(true);
    });
  }

  // ── Vim mode toggle ──────────────────────────────────────────────────────
  var VIM_CDNS = [
    '/vendor/monaco-vim.umd.js',
    'https://cdn.jsdelivr.net/npm/monaco-vim/dist/monaco-vim.js',
    'https://unpkg.com/monaco-vim/dist/monaco-vim.js'
  ];
  var _vimLoadState = 'idle';
  var _vimWaiters = [];

  function flushVimWaiters(ok) {
    var waiters = _vimWaiters.slice();
    _vimWaiters = [];
    waiters.forEach(function (pair) {
      try {
        if (ok) pair.ok();
        else if (pair.fail) pair.fail();
      } catch (e) {}
    });
  }

  function loadVimPlugin(onReady, onFail) {
    if (window.MonacoVim) {
      _vimLoadState = 'ready';
      if (onReady) onReady();
      return;
    }
    if (_vimLoadState === 'ready') {
      if (onReady) onReady();
      return;
    }
    if (_vimLoadState === 'loading') {
      _vimWaiters.push({ ok: onReady || function(){}, fail: onFail || function(){} });
      return;
    }
    if (_vimLoadState === 'failed') {
      if (onFail) onFail();
      return;
    }

    _vimLoadState = 'loading';
    _vimWaiters.push({ ok: onReady || function(){}, fail: onFail || function(){} });

    function tryIndex(idx) {
      if (idx >= VIM_CDNS.length) {
        _vimLoadState = 'failed';
        console.warn('[OPView] monaco-vim failed to load from all configured CDNs.');
        flushVimWaiters(false);
        return;
      }

      var prior = document.getElementById('_monaco_vim_loader');
      if (prior && prior.parentNode) prior.parentNode.removeChild(prior);

      var s = document.createElement('script');
      s.id = '_monaco_vim_loader';
      s.src = VIM_CDNS[idx];
      s.async = true;
      s.onload = function () {
        if (window.MonacoVim) {
          _vimLoadState = 'ready';
          flushVimWaiters(true);
          return;
        }
        tryIndex(idx + 1);
      };
      s.onerror = function () {
        console.warn('[OPView] monaco-vim failed from ' + VIM_CDNS[idx]);
        tryIndex(idx + 1);
      };
      document.head.appendChild(s);
    }

    tryIndex(0);
  }

  function initVimToggle(editor) {
    var toggleWrap = document.getElementById('notebook-vim-toggle');
    var note = document.getElementById('notebook-vim-note');
    var statusBar = document.getElementById('notebook-vim-statusbar');
    if (!toggleWrap) return;
    var checkbox = toggleWrap.querySelector('input[type="checkbox"]');
    if (!checkbox) return;

    var vimMode = null;
    var vimOn = false;

    function setNote(text, color) {
      if (!note) return;
      note.textContent = text || '';
      note.style.color = color || '#94a3b8';
    }

    function syncCheckbox(checked, disabled) {
      checkbox.checked = !!checked;
      checkbox.disabled = !!disabled;
    }

    function enableVim() {
      setNote('Loading Vim...', '#94a3b8');
      loadVimPlugin(function () {
        if (!window.MonacoVim) {
          syncCheckbox(false, true);
          setNote('Vim unavailable', '#b42318');
          return;
        }
        if (vimOn) return;
        vimMode = window.MonacoVim.initVimMode(editor, statusBar);
        if (statusBar) statusBar.style.display = 'block';
        vimOn = true;
        syncCheckbox(true, false);
        setNote('Ctrl+C / Esc supported', '#94a3b8');
      }, function () {
        syncCheckbox(false, true);
        setNote('Vim unavailable', '#b42318');
      });
    }

    function disableVim() {
      if (vimMode) { vimMode.dispose(); vimMode = null; }
      if (statusBar) statusBar.style.display = 'none';
      vimOn = false;
      syncCheckbox(false, false);
      setNote('', '#94a3b8');
    }

    checkbox.addEventListener('change', function () {
      if (checkbox.checked) enableVim();
      else disableVim();
    });

    disableVim();
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
    setClientDebug('external sync received -> len=' + ((val || '').length));
    window._monacoSyncing = true;
    window._monacoEditor.setValue(val || '');
    window._monacoSyncing = false;
    if (window._refreshMonacoAltLines) window._refreshMonacoAltLines();
    setClientDebug('external sync applied -> len=' + ((val || '').length));
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
