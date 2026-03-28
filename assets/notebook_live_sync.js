(function () {
  const NOTEBOOK_ROWS = 28;
  const MATH_NAMES = [
    "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "cosh", "exp",
    "floor", "hypot", "log", "log10", "max", "min", "pow", "round",
    "sin", "sinh", "sqrt", "tan", "tanh"
  ];
  const UNIT_FACTORS = {
    nm: 1e-9,
    um: 1e-6,
    us: 1e-6,
    mm: 1e-3,
    cm: 1e-2,
    m: 1,
    km: 1e3,
    ms: 1e-3,
    sec: 1,
    min: 60,
    h: 3600,
    hour: 3600,
    day: 86400,
    week: 604800,
    month: 2592000,
    Pa: 1,
    kPa: 1e3,
    MPa: 1e6,
    GPa: 1e9,
    bar: 1e5,
    mbar: 100.0,
    kWh: 3.6e6,
    kg: 1,
    N: 1,
    kN: 1e3,
    MN: 1e6,
    J: 1,
    kJ: 1e3,
    MJ: 1e6,
    W: 1,
    kW: 1e3,
    MW: 1e6,
    Hz: 1,
    kHz: 1e3,
    MHz: 1e6
  };

  function isNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
  }

  function isVector(value) {
    return Array.isArray(value) && value.every(isNumber);
  }

  function isMatrix(value) {
    return Array.isArray(value) && value.length > 0 && value.every(isVector) &&
      value.every((row) => row.length === value[0].length);
  }

  function isScalar(value) {
    return isNumber(value);
  }

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function sameShape(a, b) {
    if (isVector(a) && isVector(b)) {
      return a.length === b.length;
    }
    if (isMatrix(a) && isMatrix(b)) {
      return a.length === b.length && a[0].length === b[0].length;
    }
    return false;
  }

  function applyElementwise(left, right, fn, name) {
    if (isScalar(left) && isScalar(right)) {
      return fn(left, right);
    }
    if (isVector(left) && isScalar(right)) {
      return left.map((item) => fn(item, right));
    }
    if (isScalar(left) && isVector(right)) {
      return right.map((item) => fn(left, item));
    }
    if (isMatrix(left) && isScalar(right)) {
      return left.map((row) => row.map((item) => fn(item, right)));
    }
    if (isScalar(left) && isMatrix(right)) {
      return right.map((row) => row.map((item) => fn(left, item)));
    }
    if (sameShape(left, right)) {
      if (isVector(left)) {
        return left.map((item, index) => fn(item, right[index]));
      }
      if (isMatrix(left)) {
        return left.map((row, rowIndex) => row.map((item, colIndex) => fn(item, right[rowIndex][colIndex])));
      }
    }
    throw new Error(`${name} operands are incompatible`);
  }

  function ensureVector(value, name) {
    if (!isVector(value)) {
      throw new Error(`${name} requires a vector`);
    }
    return value;
  }

  function ensureMatrix(value, name) {
    if (!isMatrix(value)) {
      throw new Error(`${name} requires a matrix`);
    }
    return value;
  }

  function stripInlineComment(raw) {
    let inSingle = false;
    let inDouble = false;
    for (let i = 0; i < raw.length; i += 1) {
      const char = raw[i];
      const next = raw[i + 1];
      if (char === "'" && !inDouble) {
        inSingle = !inSingle;
        continue;
      }
      if (char === '"' && !inSingle) {
        inDouble = !inDouble;
        continue;
      }
      if (!inSingle && !inDouble) {
        if (char === "#") {
          return raw.slice(0, i);
        }
        if (char === "/" && next === "/") {
          return raw.slice(0, i);
        }
      }
    }
    return raw;
  }

  function transformMatmul(expression) {
    const expr = expression.trim();
    let depthSquare = 0;
    let depthRound = 0;
    for (let i = 0; i < expr.length; i += 1) {
      const ch = expr[i];
      if (ch === "[") depthSquare += 1;
      else if (ch === "]") depthSquare -= 1;
      else if (ch === "(") depthRound += 1;
      else if (ch === ")") depthRound -= 1;
      else if (ch === "@" && depthSquare === 0 && depthRound === 0) {
        const left = expr.slice(0, i).trim();
        const right = expr.slice(i + 1).trim();
        return `matmul(${transformMatmul(left)}, ${transformMatmul(right)})`;
      }
    }
    return expr;
  }

  function trimOuterParens(expression) {
    let expr = expression.trim();
    while (expr.startsWith("(") && expr.endsWith(")")) {
      let depth = 0;
      let wrapsWhole = true;
      for (let i = 0; i < expr.length; i += 1) {
        const ch = expr[i];
        if (ch === "(") depth += 1;
        else if (ch === ")") depth -= 1;
        if (depth === 0 && i < expr.length - 1) {
          wrapsWhole = false;
          break;
        }
      }
      if (!wrapsWhole) {
        break;
      }
      expr = expr.slice(1, -1).trim();
    }
    return expr;
  }

  function isUnaryOperator(expr, index) {
    if (expr[index] !== "+" && expr[index] !== "-") {
      return false;
    }
    let prev = index - 1;
    while (prev >= 0 && /\s/.test(expr[prev])) {
      prev -= 1;
    }
    return prev < 0 || "([,+-*/@".includes(expr[prev]);
  }

  function isExponentSign(expr, index) {
    if (expr[index] !== "+" && expr[index] !== "-") {
      return false;
    }
    const prev = expr[index - 1];
    if (prev !== "e" && prev !== "E") {
      return false;
    }
    const beforePrev = expr[index - 2];
    return !!beforePrev && /[\d.]/.test(beforePrev);
  }

  function splitByTopLevelOperator(expr, operators) {
    let depthRound = 0;
    let depthSquare = 0;
    for (let i = expr.length - 1; i >= 0; i -= 1) {
      const ch = expr[i];
      if (ch === ")") depthRound += 1;
      else if (ch === "(") depthRound -= 1;
      else if (ch === "]") depthSquare += 1;
      else if (ch === "[") depthSquare -= 1;
      else if (depthRound === 0 && depthSquare === 0 && operators.includes(ch)) {
        if (isExponentSign(expr, i)) {
          continue;
        }
        if ((ch === "+" || ch === "-") && isUnaryOperator(expr, i)) {
          continue;
        }
        return {
          operator: ch,
          left: expr.slice(0, i),
          right: expr.slice(i + 1)
        };
      }
    }
    return null;
  }

  function transformNotebookOperators(expression) {
    const expr = trimOuterParens(expression);
    const additive = splitByTopLevelOperator(expr, ["+", "-"]);
    if (additive) {
      const fn = additive.operator === "+" ? "op_add" : "op_sub";
      return `${fn}(${transformNotebookOperators(additive.left)}, ${transformNotebookOperators(additive.right)})`;
    }
    const multiplicative = splitByTopLevelOperator(expr, ["*", "/", "@"]);
    if (multiplicative) {
      const fnMap = { "*": "op_mul", "/": "op_div", "@": "matmul" };
      return `${fnMap[multiplicative.operator]}(${transformNotebookOperators(multiplicative.left)}, ${transformNotebookOperators(multiplicative.right)})`;
    }
    return expr;
  }

  function normalizeExpression(expression) {
    let normalized = stripInlineComment(expression || "");
    normalized = normalized.replace(/\^/g, "**").trim();
    normalized = normalized.replace(
      /(^|[^\w.])(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s+([A-Za-z][A-Za-z0-9]*)\b/g,
      function (_, prefix, number, unit) {
        if (Object.prototype.hasOwnProperty.call(UNIT_FACTORS, unit)) {
          return `${prefix}(${number}*${unit})`;
        }
        return `${prefix}${number} ${unit}`;
      }
    );
    return transformNotebookOperators(normalized);
  }

  function formatScalar(value) {
    if (typeof value === "number" && Number.isFinite(value)) {
      const absValue = Math.abs(value);
      if (absValue >= 1e3 || (absValue > 0 && absValue <= 1e-3)) {
        return value
          .toExponential(6)
          .replace(/\.?0+e/, "e")
          .replace("e+", "e")
          .replace(/e(-?)0+(\d+)/, "e$1$2");
      }
      if (Math.abs(value - Math.round(value)) < 1e-12) {
        return String(Math.round(value));
      }
      return Number(value).toPrecision(12).replace(/\.?0+$/, "");
    }
    if (Array.isArray(value)) {
      return `[${value.map((item) => formatScalar(item)).join(", ")}]`;
    }
    if (value && typeof value === "object" && Array.isArray(value.__tuple__)) {
      return `(${value.__tuple__.map((item) => formatScalar(item)).join(", ")})`;
    }
    if (value && typeof value === "object") {
      const entries = Object.entries(value).map(([key, item]) => `${key}: ${formatScalar(item)}`);
      return `{${entries.join(", ")}}`;
    }
    return String(value);
  }

  function zeros(rows, cols) {
    if (!Number.isInteger(rows) || !Number.isInteger(cols) || rows <= 0 || cols <= 0) {
      throw new Error("zeros(rows, cols) requires positive integer dimensions");
    }
    return Array.from({ length: rows }, () => Array.from({ length: cols }, () => 0));
  }

  function ones(rows, cols) {
    if (!Number.isInteger(rows) || !Number.isInteger(cols) || rows <= 0 || cols <= 0) {
      throw new Error("ones(rows, cols) requires positive integer dimensions");
    }
    return Array.from({ length: rows }, () => Array.from({ length: cols }, () => 1));
  }

  function eye(size) {
    if (!Number.isInteger(size) || size <= 0) {
      throw new Error("eye(n) requires a positive integer");
    }
    return Array.from({ length: size }, (_, i) =>
      Array.from({ length: size }, (_, j) => (i === j ? 1 : 0))
    );
  }

  function transpose(value) {
    const matrix = ensureMatrix(value, "transpose");
    return matrix[0].map((_, col) => matrix.map((row) => row[col]));
  }

  function dot(a, b) {
    const v1 = ensureVector(a, "dot");
    const v2 = ensureVector(b, "dot");
    if (v1.length !== v2.length) {
      throw new Error("dot vectors must have same length");
    }
    return v1.reduce((sum, item, idx) => sum + item * v2[idx], 0);
  }

  function cross(a, b) {
    const v1 = ensureVector(a, "cross");
    const v2 = ensureVector(b, "cross");
    if (v1.length !== 3 || v2.length !== 3) {
      throw new Error("cross requires 3D vectors");
    }
    return [
      v1[1] * v2[2] - v1[2] * v2[1],
      v1[2] * v2[0] - v1[0] * v2[2],
      v1[0] * v2[1] - v1[1] * v2[0]
    ];
  }

  function norm(value) {
    if (isVector(value)) {
      return Math.sqrt(value.reduce((sum, item) => sum + item * item, 0));
    }
    if (isMatrix(value)) {
      return Math.sqrt(value.flat().reduce((sum, item) => sum + item * item, 0));
    }
    throw new Error("norm requires a vector or matrix");
  }

  function normalizeVector(value) {
    const v = ensureVector(value, "normalize");
    const magnitude = norm(v);
    if (Math.abs(magnitude) < 1e-12) {
      throw new Error("cannot normalize zero vector");
    }
    return v.map((item) => item / magnitude);
  }

  function trace(value) {
    const matrix = ensureMatrix(value, "trace");
    if (matrix.length !== matrix[0].length) {
      throw new Error("trace requires a square matrix");
    }
    return matrix.reduce((sum, row, idx) => sum + row[idx], 0);
  }

  function determinant(value) {
    const matrix = ensureMatrix(value, "det");
    if (matrix.length !== matrix[0].length) {
      throw new Error("det requires a square matrix");
    }
    if (matrix.length === 1) {
      return matrix[0][0];
    }
    if (matrix.length === 2) {
      return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
    }
    let detValue = 0;
    for (let col = 0; col < matrix.length; col += 1) {
      const minor = matrix.slice(1).map((row) => row.filter((_, idx) => idx !== col));
      detValue += ((col % 2 === 0 ? 1 : -1) * matrix[0][col] * determinant(minor));
    }
    return detValue;
  }

  function inverse(value) {
    const matrix = ensureMatrix(value, "inv");
    if (matrix.length !== matrix[0].length) {
      throw new Error("inv requires a square matrix");
    }
    const n = matrix.length;
    const augmented = matrix.map((row, i) => [
      ...row.map(Number),
      ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))
    ]);
    for (let col = 0; col < n; col += 1) {
      let pivot = col;
      while (pivot < n && Math.abs(augmented[pivot][col]) < 1e-12) {
        pivot += 1;
      }
      if (pivot === n) {
        throw new Error("matrix is singular");
      }
      if (pivot !== col) {
        const temp = augmented[col];
        augmented[col] = augmented[pivot];
        augmented[pivot] = temp;
      }
      const pivotValue = augmented[col][col];
      for (let j = 0; j < 2 * n; j += 1) {
        augmented[col][j] /= pivotValue;
      }
      for (let row = 0; row < n; row += 1) {
        if (row === col) continue;
        const factor = augmented[row][col];
        for (let j = 0; j < 2 * n; j += 1) {
          augmented[row][j] -= factor * augmented[col][j];
        }
      }
    }
    return augmented.map((row) => row.slice(n));
  }

  function rank(value) {
    const matrix = ensureMatrix(value, "rank").map((row) => row.slice());
    let rankValue = 0;
    let row = 0;
    let col = 0;
    while (row < matrix.length && col < matrix[0].length) {
      let pivot = row;
      while (pivot < matrix.length && Math.abs(matrix[pivot][col]) < 1e-10) {
        pivot += 1;
      }
      if (pivot === matrix.length) {
        col += 1;
        continue;
      }
      if (pivot !== row) {
        const temp = matrix[row];
        matrix[row] = matrix[pivot];
        matrix[pivot] = temp;
      }
      const pivotValue = matrix[row][col];
      for (let j = col; j < matrix[0].length; j += 1) {
        matrix[row][j] /= pivotValue;
      }
      for (let r = 0; r < matrix.length; r += 1) {
        if (r === row) continue;
        const factor = matrix[r][col];
        for (let j = col; j < matrix[0].length; j += 1) {
          matrix[r][j] -= factor * matrix[row][j];
        }
      }
      rankValue += 1;
      row += 1;
      col += 1;
    }
    return rankValue;
  }

  function shape(value) {
    if (isMatrix(value)) {
      return { __tuple__: [value.length, value[0].length] };
    }
    if (isVector(value)) {
      return { __tuple__: [value.length] };
    }
    throw new Error("shape requires a vector or matrix");
  }

  function matmul(leftValue, rightValue) {
    if (isMatrix(leftValue) && isMatrix(rightValue)) {
      const left = ensureMatrix(leftValue, "matmul");
      const right = ensureMatrix(rightValue, "matmul");
      if (left[0].length !== right.length) {
        throw new Error("matrix dimensions do not align for multiplication");
      }
      return left.map((row) =>
        right[0].map((_, col) =>
          row.reduce((sum, item, idx) => sum + item * right[idx][col], 0)
        )
      );
    }
    if (isMatrix(leftValue) && isVector(rightValue)) {
      const left = ensureMatrix(leftValue, "matmul");
      const right = ensureVector(rightValue, "matmul");
      if (left[0].length !== right.length) {
        throw new Error("matrix and vector dimensions do not align");
      }
      return left.map((row) => row.reduce((sum, item, idx) => sum + item * right[idx], 0));
    }
    throw new Error("@ supports matrix*matrix and matrix*vector");
  }

  function op_add(leftValue, rightValue) {
    return applyElementwise(leftValue, rightValue, (a, b) => a + b, "+");
  }

  function op_sub(leftValue, rightValue) {
    return applyElementwise(leftValue, rightValue, (a, b) => a - b, "-");
  }

  function op_mul(leftValue, rightValue) {
    return applyElementwise(leftValue, rightValue, (a, b) => a * b, "*");
  }

  function op_div(leftValue, rightValue) {
    return applyElementwise(leftValue, rightValue, (a, b) => a / b, "/");
  }

  function eig2x2(matrix) {
    const a = matrix[0][0];
    const b = matrix[0][1];
    const c = matrix[1][0];
    const d = matrix[1][1];
    const traceValue = a + d;
    const detValue = a * d - b * c;
    const disc = traceValue * traceValue - 4 * detValue;
    if (disc < 0) {
      throw new Error("eig currently supports real eigenvalues only");
    }
    const root = Math.sqrt(disc);
    const lambda1 = (traceValue + root) / 2;
    const lambda2 = (traceValue - root) / 2;

    function eigenvector(lambda) {
      if (Math.abs(b) > 1e-12) {
        return normalizeVector([b, lambda - a]);
      }
      if (Math.abs(c) > 1e-12) {
        return normalizeVector([lambda - d, c]);
      }
      return normalizeVector([1, 0]);
    }

    return {
      values: [lambda1, lambda2],
      vectors: [eigenvector(lambda1), eigenvector(lambda2)]
    };
  }

  function eig(value) {
    const matrix = ensureMatrix(value, "eig");
    if (matrix.length !== matrix[0].length) {
      throw new Error("eig requires a square matrix");
    }
    if (matrix.length === 1) {
      return { values: [matrix[0][0]], vectors: [[1]] };
    }
    if (matrix.length === 2) {
      return eig2x2(matrix);
    }
    throw new Error("eig currently supports 1x1 and 2x2 matrices");
  }

  function cfl_dt(dx, u, cfl = 1.0) {
    if (!isScalar(dx) || !isScalar(u) || !isScalar(cfl)) {
      throw new Error("cfl_dt expects scalar inputs");
    }
    if (Math.abs(u) < 1e-12) {
      throw new Error("u must be non-zero");
    }
    return cfl * dx / Math.abs(u);
  }

  function diffusion_dt(dx, D, factor = 0.5) {
    if (!isScalar(dx) || !isScalar(D) || !isScalar(factor)) {
      throw new Error("diffusion_dt expects scalar inputs");
    }
    if (Math.abs(D) < 1e-12) {
      throw new Error("D must be non-zero");
    }
    return factor * dx * dx / D;
  }

  function fourier_number(D, dt, dx) {
    if (!isScalar(D) || !isScalar(dt) || !isScalar(dx)) {
      throw new Error("fourier_number expects scalar inputs");
    }
    if (Math.abs(dx) < 1e-12) {
      throw new Error("dx must be non-zero");
    }
    return D * dt / (dx * dx);
  }

  function peclet(u, L, D) {
    if (!isScalar(u) || !isScalar(L) || !isScalar(D)) {
      throw new Error("peclet expects scalar inputs");
    }
    if (Math.abs(D) < 1e-12) {
      throw new Error("D must be non-zero");
    }
    return u * L / D;
  }

  function cell_size(L, N) {
    if (!isScalar(L) || !isScalar(N)) {
      throw new Error("cell_size expects scalar inputs");
    }
    if (Math.abs(N) < 1e-12) {
      throw new Error("N must be non-zero");
    }
    return L / N;
  }

  function domain_points(L, dx) {
    if (!isScalar(L) || !isScalar(dx)) {
      throw new Error("domain_points expects scalar inputs");
    }
    if (Math.abs(dx) < 1e-12) {
      throw new Error("dx must be non-zero");
    }
    return L / dx;
  }

  function von_mises(s11, s22, s33, s12 = 0, s23 = 0, s13 = 0) {
    if (![s11, s22, s33, s12, s23, s13].every(isScalar)) {
      throw new Error("von_mises expects scalar stress components");
    }
    return Math.sqrt(
      0.5 * (
        (s11 - s22) ** 2 +
        (s22 - s33) ** 2 +
        (s33 - s11) ** 2 +
        6 * (s12 ** 2 + s23 ** 2 + s13 ** 2)
      )
    );
  }

  function shear_modulus(E, nu) {
    if (!isScalar(E) || !isScalar(nu)) {
      throw new Error("shear_modulus expects scalar inputs");
    }
    return E / (2 * (1 + nu));
  }

  function lame_lambda(E, nu) {
    if (!isScalar(E) || !isScalar(nu)) {
      throw new Error("lame_lambda expects scalar inputs");
    }
    return (E * nu) / ((1 + nu) * (1 - 2 * nu));
  }

  function hooke_1d(E, eps) {
    if (!isScalar(E) || !isScalar(eps)) {
      throw new Error("hooke_1d expects scalar inputs");
    }
    return E * eps;
  }

  function hooke_3d(E, nu, exx, eyy, ezz, exy = 0, eyz = 0, exz = 0) {
    if (![E, nu, exx, eyy, ezz, exy, eyz, exz].every(isScalar)) {
      throw new Error("hooke_3d expects scalar inputs");
    }
    const G = shear_modulus(E, nu);
    const lam = lame_lambda(E, nu);
    const strainTrace = exx + eyy + ezz;
    return {
      sxx: 2 * G * exx + lam * strainTrace,
      syy: 2 * G * eyy + lam * strainTrace,
      szz: 2 * G * ezz + lam * strainTrace,
      txy: 2 * G * exy,
      tyz: 2 * G * eyz,
      txz: 2 * G * exz,
      G: G,
      lambda: lam
    };
  }

  function plane_strain(E, nu, exx, eyy, exy = 0) {
    if (![E, nu, exx, eyy, exy].every(isScalar)) {
      throw new Error("plane_strain expects scalar inputs");
    }
    const G = shear_modulus(E, nu);
    const lam = lame_lambda(E, nu);
    const trace2d = exx + eyy;
    const sxx = 2 * G * exx + lam * trace2d;
    const syy = 2 * G * eyy + lam * trace2d;
    const szz = lam * trace2d;
    return {
      sxx: sxx,
      syy: syy,
      szz: szz,
      txy: 2 * G * exy,
      ezz: 0
    };
  }

  function plane_stress(E, nu, exx, eyy, exy = 0) {
    if (![E, nu, exx, eyy, exy].every(isScalar)) {
      throw new Error("plane_stress expects scalar inputs");
    }
    const factor = E / (1 - nu * nu);
    const G = shear_modulus(E, nu);
    return {
      sxx: factor * (exx + nu * eyy),
      syy: factor * (eyy + nu * exx),
      szz: 0,
      txy: 2 * G * exy,
      ezz: plane_stress_ezz(nu, exx, eyy)
    };
  }

  function plane_stress_ezz(nu, exx, eyy) {
    if (![nu, exx, eyy].every(isScalar)) {
      throw new Error("plane_stress_ezz expects scalar inputs");
    }
    return -(nu / (1 - nu)) * (exx + eyy);
  }

  // ── Math helpers ────────────────────────────────────────────────────────────
  function sign(x) { return Math.sign(x); }
  function log2(x) { return Math.log2(x); }
  function degrees(x) { return x * (180 / Math.PI); }
  function radians(x) { return x * (Math.PI / 180); }
  function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }
  function lerp(a, b, t) { return a + t * (b - a); }
  function factorial(n) {
    n = Math.round(Math.abs(n));
    if (n > 170) return Infinity;
    let r = 1;
    for (let i = 2; i <= n; i++) r *= i;
    return r;
  }
  function gcd(a, b) {
    a = Math.abs(Math.round(a)); b = Math.abs(Math.round(b));
    while (b) { const t = b; b = a % b; a = t; }
    return a;
  }
  function lcm(a, b) {
    const g = gcd(a, b);
    return g === 0 ? 0 : Math.abs(Math.round(a)) / g * Math.abs(Math.round(b));
  }

  // ── Statistics ───────────────────────────────────────────────────────────────
  function _toArr(v) {
    if (Array.isArray(v)) return v.map(Number);
    if (typeof v === 'number') return [v];
    throw new Error("Expected array or number");
  }
  function sum(v) { return _toArr(v).reduce((a, b) => a + b, 0); }
  function mean(v) { const a = _toArr(v); return sum(a) / a.length; }
  function variance_fn(v) {
    const a = _toArr(v);
    const m = mean(a);
    return a.reduce((acc, x) => acc + (x - m) ** 2, 0) / a.length;
  }
  function std(v) { return Math.sqrt(variance_fn(_toArr(v))); }
  function median(v) {
    const a = _toArr(v).slice().sort((x, y) => x - y);
    const mid = Math.floor(a.length / 2);
    return a.length % 2 !== 0 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
  }
  function prod(v) { return _toArr(v).reduce((a, b) => a * b, 1); }
  function cumsum(v) {
    const a = _toArr(v);
    const out = [];
    let s = 0;
    for (const x of a) { s += x; out.push(s); }
    return out;
  }
  function diff(v) {
    const a = _toArr(v);
    return a.slice(1).map((x, i) => x - a[i]);
  }
  function min_arr(v) { return Math.min(..._toArr(v)); }
  function max_arr(v) { return Math.max(..._toArr(v)); }

  // ── Array builders ───────────────────────────────────────────────────────────
  function linspace(start, stop, num) {
    num = Math.max(2, Math.round(num));
    const step = (stop - start) / (num - 1);
    return Array.from({ length: num }, (_, i) => start + i * step);
  }
  function arange(start, stop, step) {
    if (step === undefined) { step = 1; }
    if (step === 0) throw new Error("arange: step cannot be 0");
    const out = [];
    if (step > 0) { for (let x = start; x < stop - 1e-14 * Math.abs(step); x += step) out.push(x); }
    else           { for (let x = start; x > stop + 1e-14 * Math.abs(step); x += step) out.push(x); }
    return out;
  }
  function diag(v) {
    const a = _toArr(v);
    const n = a.length;
    return Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => i === j ? a[i] : 0));
  }
  function flatten(M) {
    if (!Array.isArray(M)) return [M];
    return M.flat(Infinity).map(Number);
  }
  function outer(a, b) {
    const av = _toArr(a), bv = _toArr(b);
    return av.map(x => bv.map(y => x * y));
  }

  // ── Linear algebra extras ────────────────────────────────────────────────────
  // Gaussian elimination solve (square systems only, no pivoting for simplicity)
  function solve(A, b) {
    const n = A.length;
    // Deep copy
    const M = A.map(r => [...r.map(Number)]);
    const rhs = b.map(Number);
    for (let col = 0; col < n; col++) {
      // Find pivot
      let maxRow = col;
      for (let r = col + 1; r < n; r++) if (Math.abs(M[r][col]) > Math.abs(M[maxRow][col])) maxRow = r;
      [M[col], M[maxRow]] = [M[maxRow], M[col]];
      [rhs[col], rhs[maxRow]] = [rhs[maxRow], rhs[col]];
      for (let r = col + 1; r < n; r++) {
        const f = M[r][col] / M[col][col];
        rhs[r] -= f * rhs[col];
        for (let c = col; c < n; c++) M[r][c] -= f * M[col][c];
      }
    }
    const x = new Array(n).fill(0);
    for (let i = n - 1; i >= 0; i--) {
      x[i] = rhs[i];
      for (let j = i + 1; j < n; j++) x[i] -= M[i][j] * x[j];
      x[i] /= M[i][i];
    }
    return x;
  }
  // Least-squares via normal equations (A^T A x = A^T b)
  function lstsq(A, b) {
    const m = A.length, n = A[0].length;
    const At = transpose(A);
    const AtA = matmul(At, A);
    const Atb = At.map(row => row.reduce((s, v, i) => s + v * b[i], 0));
    return solve(AtA, Atb);
  }
  // p-norm (default Euclidean p=2)
  function norm_p(v, p) {
    if (p === undefined) p = 2;
    if (p === Infinity) return Math.max(..._toArr(v).map(Math.abs));
    return Math.pow(_toArr(v).reduce((s, x) => s + Math.abs(x) ** p, 0), 1 / p);
  }
  // SVD not practical in vanilla JS — return a stub that signals unavailability
  function svd(_M) { throw new Error("svd() requires the Python side (not available client-side)"); }

  // ── Dimensionless numbers ────────────────────────────────────────────────────
  function reynolds(rho, u, L, mu) { return Math.abs(rho * u * L) / (Math.abs(mu) + 1e-300); }
  function mach(u, a) { return Math.abs(u) / (Math.abs(a) + 1e-300); }
  function prandtl(mu, cp, k) { return Math.abs(mu * cp) / (Math.abs(k) + 1e-300); }
  function nusselt_dittus(Re, Pr, heating) {
    const n = (heating === false || heating === 0) ? 0.3 : 0.4;
    return 0.023 * Math.pow(Math.abs(Re), 0.8) * Math.pow(Math.abs(Pr), n);
  }

  // ── Special math ────────────────────────────────────────────────────────────
  // erf approximation (Abramowitz & Stegun 7.1.26)
  function erf(x) {
    const t = 1 / (1 + 0.3275911 * Math.abs(x));
    const p = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
    const r = 1 - p * Math.exp(-x * x);
    return x >= 0 ? r : -r;
  }
  function erfc(x) { return 1 - erf(x); }
  // Lanczos gamma approximation
  function gamma_fn(z) {
    if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gamma_fn(1 - z));
    z -= 1;
    const g = 7;
    const c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
               771.32342877765313, -176.61502916214059, 12.507343278686905,
               -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
    let x = c[0];
    for (let i = 1; i < g + 2; i++) x += c[i] / (z + i);
    const t = z + g + 0.5;
    return Math.sqrt(2 * Math.PI) * Math.pow(t, z + 0.5) * Math.exp(-t) * x;
  }
  function lgamma_fn(x) { return Math.log(Math.abs(gamma_fn(x))); }
  function beta_fn(a, b) { return gamma_fn(a) * gamma_fn(b) / gamma_fn(a + b); }

  // ── Sorting / array ops ──────────────────────────────────────────────────────
  function sort_fn(v, reverse) {
    const a = _toArr(v).slice().sort((x, y) => x - y);
    return reverse ? a.reverse() : a;
  }
  function argsort(v) {
    const a = _toArr(v);
    return a.map((_, i) => i).sort((i, j) => a[i] - a[j]);
  }
  function unique_fn(v) { return [...new Set(_toArr(v).map(x => x))].sort((a, b) => a - b); }
  function flip_fn(v) { return _toArr(v).slice().reverse(); }
  function clip_fn(v, lo, hi) { return _toArr(v).map(x => Math.max(lo, Math.min(hi, x))); }
  function roll_fn(v, shift) {
    const a = _toArr(v);
    const n = a.length;
    const s = ((shift % n) + n) % n;
    return [...a.slice(n - s), ...a.slice(0, n - s)];
  }
  function repeat_fn(v, n) {
    const a = _toArr(v);
    const out = [];
    for (const x of a) for (let i = 0; i < n; i++) out.push(x);
    return out;
  }
  function tile_fn(v, n) {
    const a = _toArr(v);
    const out = [];
    for (let i = 0; i < n; i++) out.push(...a);
    return out;
  }
  function full_fn(n, val) { return Array.from({ length: n }, () => val); }
  function where_fn(condition, x, y) {
    const c = Array.isArray(condition) ? condition : [condition];
    const xArr = Array.isArray(x) ? x : null;
    const yArr = Array.isArray(y) ? y : null;
    return c.map((v, i) => v ? (xArr ? xArr[i] : x) : (yArr ? yArr[i] : y));
  }
  function concat_fn(...arrays) { return [].concat(...arrays.map(a => Array.isArray(a) ? a : [a])); }
  function append_fn(a, b) { return _toArr(a).concat(_toArr(b)); }

  // ── Interpolation ────────────────────────────────────────────────────────────
  function interp_fn(x, xp, fp) {
    const xpA = _toArr(xp), fpA = _toArr(fp);
    const query = Array.isArray(x) ? x : [x];
    const result = query.map(xi => {
      if (xi <= xpA[0]) return fpA[0];
      if (xi >= xpA[xpA.length - 1]) return fpA[fpA.length - 1];
      let lo = 0, hi = xpA.length - 1;
      while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xpA[mid] <= xi) lo = mid; else hi = mid; }
      const t = (xi - xpA[lo]) / (xpA[hi] - xpA[lo]);
      return fpA[lo] + t * (fpA[hi] - fpA[lo]);
    });
    return Array.isArray(x) ? result : result[0];
  }
  function polyval_fn(p, x) {
    const pA = _toArr(p);
    const eval1 = xi => pA.reduce((acc, c) => acc * xi + c, 0);
    return Array.isArray(x) ? _toArr(x).map(eval1) : eval1(x);
  }

  // ── Calculus ─────────────────────────────────────────────────────────────────
  function gradient_fn(f, dx) {
    dx = dx === undefined ? 1 : dx;
    const a = _toArr(f), n = a.length, g = new Array(n);
    g[0] = (a[1] - a[0]) / dx;
    g[n - 1] = (a[n - 1] - a[n - 2]) / dx;
    for (let i = 1; i < n - 1; i++) g[i] = (a[i + 1] - a[i - 1]) / (2 * dx);
    return g;
  }
  function trapz_fn(y, x, dx) {
    const ya = _toArr(y);
    if (x !== undefined) {
      const xa = _toArr(x);
      let s = 0;
      for (let i = 1; i < ya.length; i++) s += 0.5 * (ya[i] + ya[i - 1]) * (xa[i] - xa[i - 1]);
      return s;
    }
    dx = dx === undefined ? 1 : dx;
    let s = 0;
    for (let i = 1; i < ya.length; i++) s += 0.5 * (ya[i] + ya[i - 1]) * dx;
    return s;
  }
  function cumtrapz_fn(y, dx) {
    dx = dx === undefined ? 1 : dx;
    const a = _toArr(y), out = [0];
    for (let i = 1; i < a.length; i++) out.push(out[i - 1] + 0.5 * (a[i] + a[i - 1]) * dx);
    return out;
  }

  // ── More statistics ──────────────────────────────────────────────────────────
  function percentile_fn(v, p) {
    const a = _toArr(v).slice().sort((x, y) => x - y);
    const idx = (p / 100) * (a.length - 1);
    const lo = Math.floor(idx), hi = Math.ceil(idx);
    return a[lo] + (idx - lo) * (a[hi] - a[lo]);
  }
  function quantile_fn(v, q) { return percentile_fn(v, q * 100); }
  function zscore_fn(v) { const a = _toArr(v); const m = mean(a); const s = std(a); return a.map(x => (x - m) / (s || 1)); }
  function norm01_fn(v) { const a = _toArr(v); const lo = min_arr(a), hi = max_arr(a); return hi > lo ? a.map(x => (x - lo) / (hi - lo)) : a.map(x => 0); }
  function corrcoef_fn(x, y) {
    const xa = _toArr(x), ya = _toArr(y);
    const mx = mean(xa), my = mean(ya);
    const num = xa.reduce((s, v, i) => s + (v - mx) * (ya[i] - my), 0);
    const dx = Math.sqrt(xa.reduce((s, v) => s + (v - mx) ** 2, 0));
    const dy = Math.sqrt(ya.reduce((s, v) => s + (v - my) ** 2, 0));
    return num / (dx * dy + 1e-300);
  }

  // ── More dimensionless ───────────────────────────────────────────────────────
  function biot(h, L, k) { return Math.abs(h) * Math.abs(L) / (Math.abs(k) + 1e-300); }
  function fourier_thermal(alpha, t, L) { return Math.abs(alpha) * Math.abs(t) / (L ** 2 + 1e-300); }
  function lewis(D, alpha_th) { return Math.abs(D) / (Math.abs(alpha_th) + 1e-300); }
  function weber(rho, v, L, sigma) { return Math.abs(rho) * v ** 2 * Math.abs(L) / (Math.abs(sigma) + 1e-300); }
  function grashof(g_acc, beta, dT, L, nu) { return Math.abs(g_acc) * Math.abs(beta) * Math.abs(dT) * L ** 3 / (nu ** 2 + 1e-300); }
  function stokes(rho_p, rho_f, d, mu) { return Math.abs(rho_p - rho_f) * 9.80665 * d ** 2 / (18 * Math.abs(mu) + 1e-300); }

  // ── Extra array / stats functions ────────────────────────────────────────────
  function diff2_fn(v, n) {
    let a = _toArr(v);
    const times = (n === undefined || n === null) ? 1 : Math.round(n);
    for (let i = 0; i < times; i++) {
      const b = [];
      for (let j = 1; j < a.length; j++) b.push(a[j] - a[j - 1]);
      a = b;
    }
    return a;
  }
  function vstack_fn(...arrays) {
    // Returns a 2-D array (array of rows)
    return arrays.map(a => _toArr(a));
  }
  function hstack_fn(...arrays) {
    // Concatenates 1-D arrays horizontally
    return [].concat(...arrays.map(a => _toArr(a)));
  }
  function meshgrid_fn(x, y) {
    const xa = _toArr(x), ya = _toArr(y);
    const X = ya.map(() => xa.slice());
    const Y = ya.map(yi => xa.map(() => yi));
    return [X, Y];
  }
  function cov_fn(x, y) {
    const xa = _toArr(x), ya = _toArr(y);
    const mx = mean(xa), my = mean(ya);
    return xa.reduce((s, v, i) => s + (v - mx) * (ya[i] - my), 0) / (xa.length - 1 || 1);
  }
  function histogram_fn(v, bins) {
    const a = _toArr(v).slice().sort((p, q) => p - q);
    const nbins = (bins === undefined || bins === null) ? 10 : Math.round(bins);
    const lo = a[0], hi = a[a.length - 1], width = (hi - lo) / nbins || 1;
    const counts = new Array(nbins).fill(0);
    for (const x of a) {
      let idx = Math.floor((x - lo) / width);
      if (idx >= nbins) idx = nbins - 1;
      counts[idx]++;
    }
    return counts;
  }
  function mode_fn(v) {
    const a = _toArr(v);
    const freq = new Map();
    for (const x of a) freq.set(x, (freq.get(x) || 0) + 1);
    let best = a[0], bestCount = 0;
    for (const [val, count] of freq) { if (count > bestCount) { bestCount = count; best = val; } }
    return best;
  }
  function eig_full_fn(M) {
    // Delegates to existing eig (returns eigenvalues array)
    return eig(M);
  }

  // ── Reshape / Polyfit ────────────────────────────────────────────────────────
  function reshape_fn(v, rows, cols) {
    const a = _toArr(v);
    if (rows * cols !== a.length) throw new Error('reshape: size mismatch');
    const out = [];
    for (let r = 0; r < rows; r++) { out.push(a.slice(r * cols, (r + 1) * cols)); }
    return out;
  }
  function polyfit_fn(x, y, deg) {
    // Least-squares polynomial fit using normal equations (deg ≤ 8 is fine)
    const xa = _toArr(x), ya = _toArr(y), n = xa.length, d = deg + 1;
    // Build Vandermonde matrix V and solve V^T V c = V^T y via Gauss elimination
    const V = xa.map(xi => Array.from({ length: d }, (_, k) => Math.pow(xi, deg - k)));
    // V^T V
    const VtV = Array.from({ length: d }, (_, i) => Array.from({ length: d }, (_, j) =>
      V.reduce((s, row) => s + row[i] * row[j], 0)));
    // V^T y
    const Vty = Array.from({ length: d }, (_, i) => V.reduce((s, row, r) => s + row[i] * ya[r], 0));
    // Gauss elimination with partial pivoting
    const A = VtV.map((row, i) => [...row, Vty[i]]);
    for (let col = 0; col < d; col++) {
      let maxRow = col;
      for (let r = col + 1; r < d; r++) if (Math.abs(A[r][col]) > Math.abs(A[maxRow][col])) maxRow = r;
      [A[col], A[maxRow]] = [A[maxRow], A[col]];
      for (let r = col + 1; r < d; r++) {
        const f = A[r][col] / (A[col][col] || 1e-300);
        for (let c2 = col; c2 <= d; c2++) A[r][c2] -= f * A[col][c2];
      }
    }
    const coeffs = new Array(d).fill(0);
    for (let i = d - 1; i >= 0; i--) {
      coeffs[i] = A[i][d] / (A[i][i] || 1e-300);
      for (let r = 0; r < i; r++) A[r][d] -= A[r][i] * coeffs[i];
    }
    return coeffs;
  }

  function evaluateExpression(expression, variables) {
    const expr = normalizeExpression(expression);
    if (!expr) {
      return null;
    }

    const scope = Object.assign({}, variables);
    for (const name of MATH_NAMES) {
      scope[name] = Math[name];
    }
    for (const [unitName, factor] of Object.entries(UNIT_FACTORS)) {
      scope[unitName] = factor;
    }
    scope.dot = dot;
    scope.cross = cross;
    scope.norm = norm;
    scope.normalize = normalizeVector;
    scope.length = norm;
    scope.det = determinant;
    scope.inv = inverse;
    scope.transpose = transpose;
    scope.trace = trace;
    scope.eye = eye;
    scope.zeros = zeros;
    scope.ones = ones;
    scope.shape = shape;
    scope.rank = rank;
    scope.eig = eig;
    scope.cfl_dt = cfl_dt;
    scope.diffusion_dt = diffusion_dt;
    scope.fourier_number = fourier_number;
    scope.peclet = peclet;
    scope.cell_size = cell_size;
    scope.domain_points = domain_points;
    scope.von_mises = von_mises;
    scope.shear_modulus = shear_modulus;
    scope.lame_lambda = lame_lambda;
    scope.hooke_1d = hooke_1d;
    scope.hooke_3d = hooke_3d;
    scope.plane_strain = plane_strain;
    scope.plane_stress = plane_stress;
    scope.plane_stress_ezz = plane_stress_ezz;
    scope.matmul = matmul;
    scope.op_add = op_add;
    scope.op_sub = op_sub;
    scope.op_mul = op_mul;
    scope.op_div = op_div;
    scope.pi = Math.PI;
    scope.e = Math.E;
    scope.tau = 2 * Math.PI;
    scope.deg = Math.PI / 180;
    scope.inf = Infinity;
    // Math helpers
    scope.sign = sign;
    scope.log2 = log2;
    scope.degrees = degrees;
    scope.radians = radians;
    scope.clamp = clamp;
    scope.lerp = lerp;
    scope.factorial = factorial;
    scope.gcd = gcd;
    scope.lcm = lcm;
    // Statistics
    scope.sum = sum;
    scope.mean = mean;
    scope.std = std;
    scope.variance = variance_fn;
    scope.median = median;
    scope.prod = prod;
    scope.cumsum = cumsum;
    scope.diff = diff;
    scope.min = min_arr;
    scope.max = max_arr;
    // Array builders
    scope.linspace = linspace;
    scope.arange = arange;
    scope.diag = diag;
    scope.flatten = flatten;
    scope.outer = outer;
    // Linear algebra extras
    scope.solve = solve;
    scope.lstsq = lstsq;
    scope.norm_p = norm_p;
    scope.svd = svd;
    // Dimensionless numbers
    scope.reynolds = reynolds;
    scope.mach = mach;
    scope.prandtl = prandtl;
    scope.nusselt_dittus = nusselt_dittus;
    // Physical constants
    scope.g_n      = 9.80665;
    scope.c_0      = 299792458.0;
    scope.R_gas    = 8.314462618;
    scope.k_B      = 1.380649e-23;
    scope.N_A      = 6.02214076e23;
    scope.h_p      = 6.62607015e-34;
    scope.sigma_SB = 5.670374419e-8;
    scope.mu_0     = 1.25663706212e-6;
    scope.eps_0    = 8.8541878128e-12;
    scope.atm      = 101325.0;
    // New unit constants
    scope.bar  = 1e5;
    scope.mbar = 100.0;
    scope.kWh  = 3.6e6;
    scope.L    = 1e-3;   // litre
    // Special math
    scope.erf   = erf;
    scope.erfc  = erfc;
    scope.gamma = gamma_fn;
    scope.lgamma = lgamma_fn;
    scope.beta  = beta_fn;
    // Sorting / array ops
    scope.sort     = sort_fn;
    scope.argsort  = argsort;
    scope.unique   = unique_fn;
    scope.flip     = flip_fn;
    scope.clip     = clip_fn;
    scope.roll     = roll_fn;
    scope.repeat   = repeat_fn;
    scope.tile     = tile_fn;
    scope.full     = full_fn;
    scope.where    = where_fn;
    scope.concat   = concat_fn;
    scope.append   = append_fn;
    // Interpolation
    scope.interp   = interp_fn;
    scope.polyfit  = polyfit_fn;
    scope.polyval  = polyval_fn;
    scope.reshape  = reshape_fn;
    // Calculus
    scope.gradient  = gradient_fn;
    scope.trapz     = trapz_fn;
    scope.cumtrapz  = cumtrapz_fn;
    // More statistics
    scope.percentile = percentile_fn;
    scope.quantile   = quantile_fn;
    scope.zscore     = zscore_fn;
    scope.norm01     = norm01_fn;
    scope.corrcoef   = corrcoef_fn;
    // More dimensionless
    scope.biot           = biot;
    scope.fourier_thermal = fourier_thermal;
    scope.lewis          = lewis;
    scope.weber          = weber;
    scope.grashof        = grashof;
    scope.stokes         = stokes;
    // Extra array / stats
    scope.diff2     = diff2_fn;
    scope.vstack    = vstack_fn;
    scope.hstack    = hstack_fn;
    scope.meshgrid  = meshgrid_fn;
    scope.cov       = cov_fn;
    scope.histogram = histogram_fn;
    scope.mode      = mode_fn;
    scope.eig_full  = eig_full_fn;

    const names = Object.keys(scope);
    const values = Object.values(scope);
    const fn = new Function(...names, `return (${expr});`);
    const result = fn(...values);

    if (typeof result === "number") {
      if (!Number.isFinite(result)) {
        throw new Error("Result is not a finite number");
      }
      return result;
    }
    if (isVector(result) || isMatrix(result) || (result && typeof result === "object")) {
      return cloneValue(result);
    }
    throw new Error("Unsupported result type");
  }

  function isBlockHeader(expr) {
    return /^(for\b.*:|if\b.*:|elif\b.*:|else\s*:)/.test(expr);
  }

  function isIndentedLine(raw) {
    return raw.length > 0 && (raw[0] === " " || raw[0] === "\t");
  }

  function buildResultRows(lines) {
    const variables = {};
    const results = [];

    lines.forEach((line) => {
      const raw = line || "";
      const expression = stripInlineComment(raw).trim();

      // Block headers (for/if) and indented body lines are handled server-side
      if (isBlockHeader(expression) || isIndentedLine(raw)) {
        results.push("");
        return;
      }

      if (!expression) {
        results.push("");
        return;
      }
      try {
        if (expression.includes("=")) {
          const parts = expression.split("=");
          const variableName = (parts.shift() || "").trim();
          const rhs = parts.join("=").trim();
          if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(variableName)) {
            throw new Error("Variable name is invalid");
          }
          const value = evaluateExpression(rhs, variables);
          variables[variableName] = value;
          results.push(`-> ${formatScalar(value)}`);
        } else {
          const value = evaluateExpression(expression, variables);
          results.push(`-> ${formatScalar(value)}`);
        }
      } catch (error) {
        results.push(`Error: ${error.message}`);
      }
    });

    return { results, variables };
  }

  function renderResults(resultsContainer, debugContainer, text) {
    if (!resultsContainer) {
      return;
    }
    const lines = (text || "").split("\n");
    const evaluation = buildResultRows(lines);
    const rows = Math.max(NOTEBOOK_ROWS, evaluation.results.length);

    // Use absolute positioning so Monaco's translateY scroll keeps results
    // pixel-locked to editor lines (lineHeight=34, top padding=18 on Monaco).
    resultsContainer.style.position = "relative";
    resultsContainer.style.height = (rows * 34) + "px";
    resultsContainer.innerHTML = "";

    for (let index = 0; index < rows; index += 1) {
      const textLine = evaluation.results[index] || "";
      const row = document.createElement("div");
      row.textContent = textLine;
      row.style.position = "absolute";
      row.style.top = (index * 34) + "px";
      row.style.left = "0";
      row.style.right = "0";
      row.style.height = "34px";
      row.style.lineHeight = "34px";
      row.style.fontFamily = "monospace";
      row.style.fontSize = "18px";
      row.style.whiteSpace = "nowrap";
      row.style.overflow = "hidden";
      row.style.textOverflow = "ellipsis";
      row.style.color = textLine.startsWith("Error:") ? "#b42318" : (textLine ? "#0f5132" : "#98a2b3");
      resultsContainer.appendChild(row);
    }
    if (debugContainer) {
      debugContainer.textContent = [
        `[NotebookDebug] lines=${lines.length}`,
        `[NotebookDebug] results=${evaluation.results.length}`,
        `[NotebookDebug] variables=${Object.keys(evaluation.variables).join(", ") || "(none)"}`,
        `[NotebookDebug] preview=${JSON.stringify((text || "").slice(0, 120))}`
      ].join("\n");
    }
  }

  function updateLineNumbers(el, text) {
    if (!el) return;
    const lines = (text || "").split("\n");
    const count = Math.max(NOTEBOOK_ROWS, lines.length);
    const parts = [];
    for (let i = 1; i <= count; i++) {
      parts.push('<div style="height:34px;line-height:34px">' + i + "</div>");
    }
    el.innerHTML = parts.join("");
  }

  // ── Expose render function for Monaco integration ───────────────────────
  // monaco_notebook.js calls this directly after each content change.
  function exposeRenderGlobal(results, debug) {
    window._notebookRenderResults = function (text) {
      renderResults(results, debug, text);
    };
  }

  function attachNotebookRuntime() {
    const textarea = document.getElementById("notebook-textarea");
    const hiddenInput = document.getElementById("notebook-live-text");
    const results = document.getElementById("notebook-results");
    const debug = document.getElementById("notebook-debug");
    const lineNumbers = document.getElementById("notebook-line-numbers");
    const clearButton = document.getElementById("notebook-clear-btn");
    if (!textarea || !results || textarea.dataset.liveSyncAttached === "true") {
      return;
    }

    // Always expose the render function so Monaco can call it
    exposeRenderGlobal(results, debug);

    const pushValue = function () {
      // If Monaco has taken over, skip textarea-based sync
      if (window._monacoEditor) return;
      const value = textarea.value || "";
      if (hiddenInput) {
        hiddenInput.value = value;
      }
      renderResults(results, debug, value);
      if (lineNumbers) updateLineNumbers(lineNumbers, value);
    };

    // Scroll sync (textarea path — Monaco uses onDidScrollChange instead)
    textarea.addEventListener("scroll", function () {
      if (window._monacoEditor) return;
      if (results) results.style.transform = "translateY(-" + textarea.scrollTop + "px)";
      if (lineNumbers) lineNumbers.scrollTop = textarea.scrollTop;
    });

    textarea.addEventListener("input", pushValue);
    textarea.addEventListener("keyup", pushValue);
    if (clearButton && clearButton.dataset.liveSyncAttached !== "true") {
      clearButton.addEventListener("click", function () {
        window.setTimeout(pushValue, 0);
      });
      clearButton.dataset.liveSyncAttached = "true";
    }
    textarea.dataset.liveSyncAttached = "true";
    pushValue();
  }

  window.addEventListener("load", function () {
    attachNotebookRuntime();
    const observer = new MutationObserver(attachNotebookRuntime);
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
