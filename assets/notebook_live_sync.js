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

  // Wraps any scalar function so it applies element-wise when given array args.
  // Mixed scalar/array: scalar is broadcast to match the array length.
  function elementwise(fn) {
    return function () {
      var args = Array.prototype.slice.call(arguments);
      var firstArr = args.find(Array.isArray);
      if (!firstArr) return fn.apply(null, args);
      return firstArr.map(function (_, i) {
        return fn.apply(null, args.map(function (a) { return Array.isArray(a) ? a[i] : a; }));
      });
    };
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

  function splitTopLevelArgs(argsStr) {
    const result = [];
    let depth = 0;
    let start = 0;
    for (let i = 0; i < argsStr.length; i++) {
      const ch = argsStr[i];
      if (ch === '(' || ch === '[') depth++;
      else if (ch === ')' || ch === ']') depth--;
      else if (ch === ',' && depth === 0) {
        result.push(argsStr.slice(start, i).trim());
        start = i + 1;
      }
    }
    const last = argsStr.slice(start).trim();
    if (last) result.push(last);
    return result;
  }

  function findTopLevelColon(expr) {
    let depthRound = 0;
    let depthSquare = 0;
    for (let i = 0; i < expr.length; i += 1) {
      const ch = expr[i];
      if (ch === "(") depthRound += 1;
      else if (ch === ")") depthRound -= 1;
      else if (ch === "[") depthSquare += 1;
      else if (ch === "]") depthSquare -= 1;
      else if (ch === ":" && depthRound === 0 && depthSquare === 0) {
        return i;
      }
    }
    return -1;
  }

  function parseSliceIndices(expr, variables, length) {
    const parts = [];
    let depthRound = 0;
    let depthSquare = 0;
    let start = 0;
    for (let i = 0; i < expr.length; i += 1) {
      const ch = expr[i];
      if (ch === "(") depthRound += 1;
      else if (ch === ")") depthRound -= 1;
      else if (ch === "[") depthSquare += 1;
      else if (ch === "]") depthSquare -= 1;
      else if (ch === ":" && depthRound === 0 && depthSquare === 0) {
        parts.push(expr.slice(start, i).trim());
        start = i + 1;
      }
    }
    parts.push(expr.slice(start).trim());
    if (parts.length < 2 || parts.length > 3) {
      throw new Error("Invalid slice syntax");
    }

    function evalMaybe(part, fallback) {
      if (!part) return fallback;
      return Number(evaluateExpression(part, variables));
    }

    function normalizeIndex(idx, fallback) {
      if (!Number.isFinite(idx)) return fallback;
      let value = Math.trunc(idx);
      if (value < 0) value += length;
      return value;
    }

    const rawStart = evalMaybe(parts[0], 0);
    const rawEnd = evalMaybe(parts[1], length);
    const rawStep = evalMaybe(parts[2], 1);
    const step = Math.trunc(rawStep);
    if (step === 0) throw new Error("Slice step cannot be zero");

    let sliceStart = normalizeIndex(rawStart, step > 0 ? 0 : length - 1);
    let sliceEnd = normalizeIndex(rawEnd, step > 0 ? length : -1);
    sliceStart = Math.max(-1, Math.min(length, sliceStart));
    sliceEnd = Math.max(-1, Math.min(length, sliceEnd));

    const indices = [];
    if (step > 0) {
      for (let i = sliceStart; i < sliceEnd; i += step) indices.push(i);
    } else {
      for (let i = sliceStart; i > sliceEnd; i += step) indices.push(i);
    }
    return indices.filter(function (i) { return i >= 0 && i < length; });
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
    const power = splitByTopLevelOperator(expr, ["^"]);
    if (power) {
      return `Math.pow(${transformNotebookOperators(power.left)}, ${transformNotebookOperators(power.right)})`;
    }
    // Unary negation: -expr → op_sub(0, expr) so arrays are negated element-wise
    if (expr[0] === '-') {
      const inner = expr.slice(1).trim();
      return `op_sub(0, ${transformNotebookOperators(inner)})`;
    }
    // Function call: recurse into each argument so operators inside are transformed
    const funcMatch = /^([a-zA-Z_]\w*)\((.*)\)$/s.exec(expr);
    if (funcMatch) {
      const funcName = funcMatch[1];
      const args = splitTopLevelArgs(funcMatch[2]);
      return `${funcName}(${args.map(a => transformNotebookOperators(a)).join(', ')})`;
    }
    return expr;
  }

  function normalizeExpression(expression) {
    let normalized = stripInlineComment(expression || "");
    // Do NOT convert ^ to ** here — transformNotebookOperators handles ^ directly
    // so that x**2 splitting does not corrupt the expression.
    normalized = normalized.trim();
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
      // Integer check
      if (Math.abs(value - Math.round(value)) < 1e-9 * Math.max(1, absValue)) {
        return String(Math.round(value));
      }
      // Scientific notation for very large or very small
      if (absValue >= 1e4 || (absValue > 0 && absValue < 1e-3)) {
        return value
          .toExponential(3)
          .replace(/\.?0+e/, "e")
          .replace("e+", "e")
          .replace(/e(-?)0+(\d+)/, "e$1$2");
      }
      // Normal range: 3 decimal places, trim trailing zeros
      return value.toFixed(3).replace(/\.?0+$/, "").replace(/\.$/, "");
    }
    if (Array.isArray(value)) {
      const flat = value.every(function (v) { return !Array.isArray(v); });
      if (flat && value.length > 4) {
        const head = value.slice(0, 3).map(formatScalar).join(", ");
        const tail = formatScalar(value[value.length - 1]);
        return `[${head} ... ${tail}]`;
      }
      const inner = value.map(function (item) { return formatScalar(item); }).join(", ");
      return `[${inner}]`;
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

  function resultLabel(expression) {
    const raw = (expression || "").trim();
    if (!raw) return "";
    const stripped = stripInlineComment(raw).trim();
    if (!stripped) return "";
    if (stripped.includes("=") && !/(==|!=|<=|>=)/.test(stripped)) {
      const lhs = stripped.split("=", 1)[0].trim();
      if (/^[A-Za-z_]\w*$/.test(lhs)) {
        return lhs;
      }
    }
    return stripped;
  }

  function zeros(rows, cols) {
    if (!Number.isInteger(rows) || rows <= 0) {
      throw new Error("zeros requires positive integer dimensions");
    }
    if (cols === undefined) {
      return Array.from({ length: rows }, () => 0);
    }
    if (!Number.isInteger(cols) || cols <= 0) {
      throw new Error("zeros requires positive integer dimensions");
    }
    return Array.from({ length: rows }, () => Array.from({ length: cols }, () => 0));
  }

  function ones(rows, cols) {
    if (!Number.isInteger(rows) || rows <= 0) {
      throw new Error("ones requires positive integer dimensions");
    }
    if (cols === undefined) {
      return Array.from({ length: rows }, () => 1);
    }
    if (!Number.isInteger(cols) || cols <= 0) {
      throw new Error("ones requires positive integer dimensions");
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
    return Math.round(Math.abs(L) / Math.abs(dx)) + 1;
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
    const tr = exx + eyy + ezz;
    // Returns [sxx, syy, szz, sxy, syz, sxz] matching Python
    return [lam*tr + 2*G*exx, lam*tr + 2*G*eyy, lam*tr + 2*G*ezz,
            2*G*exy, 2*G*eyz, 2*G*exz];
  }

  function plane_strain(E, nu, exx, eyy, exy = 0) {
    if (![E, nu, exx, eyy, exy].every(isScalar)) {
      throw new Error("plane_strain expects scalar inputs");
    }
    const G = shear_modulus(E, nu);
    const lam = lame_lambda(E, nu);
    // Returns [sxx, syy, txy] matching Python
    return [(lam + 2*G)*exx + lam*eyy, lam*exx + (lam + 2*G)*eyy, 2*G*exy];
  }

  function plane_stress(E, nu, exx, eyy, exy = 0) {
    if (![E, nu, exx, eyy, exy].every(isScalar)) {
      throw new Error("plane_stress expects scalar inputs");
    }
    const C = E / (1 - nu * nu);
    const G = E / (2 * (1 + nu));
    // Returns [sxx, syy, txy] matching Python
    return [C*(exx + nu*eyy), C*(eyy + nu*exx), 2*G*exy];
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
  min_arr.valueOf = function () { return UNIT_FACTORS.min; };
  min_arr.toString = function () { return String(UNIT_FACTORS.min); };

  // ── Array builders ───────────────────────────────────────────────────────────
  function linspace(start, stop, num) {
    if (num === undefined) num = 50;
    num = Math.max(1, Math.round(num));
    if (num === 1) return [start];
    const step = (stop - start) / (num - 1);
    return Array.from({ length: num }, (_, i) => start + i * step);
  }
  function arange(start, stop, step) {
    // arange(n) → [0, 1, ..., n-1]
    if (stop === undefined) { stop = start; start = 0; }
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
  function stokes(rho, mu, g_acc, d) { return Math.abs(rho) * Math.abs(g_acc) * d ** 2 / (18 * Math.abs(mu) + 1e-300); }

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

  // ── Alloy composition ────────────────────────────────────────────────────────
  function wt_to_mol(wt, M) {
    const w = _toArr(wt), m = _toArr(M);
    if (w.length !== m.length) throw new Error("wt_to_mol: wt and M must have the same length");
    const n = w.map((wi, i) => wi / m[i]);
    const total = n.reduce((s, x) => s + x, 0);
    return n.map(x => x / (total || 1));
  }
  function mol_to_wt(x, M) {
    const xv = _toArr(x), mv = _toArr(M);
    if (xv.length !== mv.length) throw new Error("mol_to_wt: x and M must have the same length");
    const w = xv.map((xi, i) => xi * mv[i]);
    const total = w.reduce((s, v) => s + v, 0);
    return w.map(v => 100 * v / (total || 1));
  }
  function wt_to_mol2(wt_B, M_A, M_B) {
    const arr = Array.isArray(wt_B) ? wt_B : [wt_B];
    const result = arr.map(w => {
      const nB = w / M_B;
      const nA = (100 - w) / M_A;
      return nB / (nA + nB || 1);
    });
    return result.length === 1 ? result[0] : result;
  }

  // ── FFT (magnitude spectrum, matching Python np.abs(np.fft.fft(v))) ─────────
  function fft(v) {
    const a = _toArr(v);
    const n = a.length;
    if (n > 4096) throw new Error("fft: array too large for client-side (use Python side for n > 4096)");
    const re = new Array(n).fill(0);
    const im = new Array(n).fill(0);
    for (let k = 0; k < n; k++) {
      for (let t = 0; t < n; t++) {
        const ang = 2 * Math.PI * k * t / n;
        re[k] += a[t] * Math.cos(ang);
        im[k] -= a[t] * Math.sin(ang);
      }
    }
    return re.map((r, i) => Math.sqrt(r * r + im[i] * im[i]));
  }
  function ifft(v) {
    // Returns real part of inverse DFT
    const a = _toArr(v);
    const n = a.length;
    if (n > 4096) throw new Error("ifft: array too large for client-side");
    const out = new Array(n).fill(0);
    for (let t = 0; t < n; t++) {
      for (let k = 0; k < n; k++) {
        out[t] += a[k] * Math.cos(2 * Math.PI * k * t / n);
      }
      out[t] /= n;
    }
    return out;
  }
  function fftfreq(n, dt) {
    if (dt === undefined) dt = 1.0;
    n = Math.round(n);
    const freqs = new Array(n);
    const half = Math.floor((n - 1) / 2) + 1;
    for (let i = 0; i < half; i++) freqs[i] = i / (n * dt);
    for (let i = half; i < n; i++) freqs[i] = (i - n) / (n * dt);
    return freqs;
  }
  function fftshift(v) {
    const a = _toArr(v);
    const mid = Math.floor(a.length / 2);
    return [...a.slice(mid), ...a.slice(0, mid)];
  }
  function real_fn(v) { return Array.isArray(v) ? _toArr(v) : v; }
  function imag_fn(v) { return Array.isArray(v) ? new Array(_toArr(v).length).fill(0) : 0; }
  function angle_fn(v) { return Array.isArray(v) ? new Array(_toArr(v).length).fill(0) : 0; }

  function evaluateExpression(expression, variables) {
    const expr = normalizeExpression(expression);
    if (!expr) {
      return null;
    }

    const scope = {};
    for (const name of MATH_NAMES) {
      const mathFn = Math[name];
      scope[name] = function () {
        const args = Array.prototype.slice.call(arguments);
        if (args.length === 1) {
          const a = args[0];
          if (isVector(a)) return a.map(function (x) { return mathFn(x); });
          if (isMatrix(a)) return a.map(function (row) { return row.map(function (x) { return mathFn(x); }); });
          return mathFn(a);
        }
        if (args.length === 2) {
          return applyElementwise(args[0], args[1], function (a, b) { return mathFn(a, b); }, name);
        }
        return mathFn.apply(Math, args);
      };
    }
    for (const [unitName, factor] of Object.entries(UNIT_FACTORS)) {
      scope[unitName] = factor;
    }
    scope.len = (v) => Array.isArray(v) ? v.length : (typeof v === 'string' ? v.length : 0);
    scope.range = (a, b, s) => { if (b === undefined) { b = a; a = 0; } if (s === undefined) s = 1; return arange(a, b, s); };
    scope.enumerate = (v) => _toArr(v).map((x, i) => [i, x]);
    scope.zip = (...arrays) => { const n = Math.min(...arrays.map(a => _toArr(a).length)); return Array.from({length: n}, (_, i) => arrays.map(a => _toArr(a)[i])); };
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
    scope.cfl_dt = elementwise(cfl_dt);
    scope.diffusion_dt = elementwise(diffusion_dt);
    scope.fourier_number = elementwise(fourier_number);
    scope.peclet = elementwise(peclet);
    scope.cell_size = elementwise(cell_size);
    scope.domain_points = elementwise(domain_points);
    scope.von_mises = elementwise(von_mises);
    scope.shear_modulus = elementwise(shear_modulus);
    scope.lame_lambda = elementwise(lame_lambda);
    scope.hooke_1d = elementwise(hooke_1d);
    scope.hooke_3d = hooke_3d;
    scope.plane_strain = plane_strain;
    scope.plane_stress = plane_stress;
    scope.plane_stress_ezz = elementwise(plane_stress_ezz);
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
    // Math helpers — all element-wise on arrays
    scope.sign = elementwise(sign);
    scope.log2 = elementwise(log2);
    scope.degrees = elementwise(degrees);
    scope.radians = elementwise(radians);
    scope.clamp = elementwise(clamp);
    scope.lerp = elementwise(lerp);
    scope.factorial = elementwise(factorial);
    scope.gcd = elementwise(gcd);
    scope.lcm = elementwise(lcm);
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
    // Dimensionless numbers — element-wise on arrays
    scope.reynolds = elementwise(reynolds);
    scope.mach = elementwise(mach);
    scope.prandtl = elementwise(prandtl);
    scope.nusselt_dittus = elementwise(nusselt_dittus);
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
    // Special math — element-wise on arrays
    scope.erf   = elementwise(erf);
    scope.erfc  = elementwise(erfc);
    scope.gamma = elementwise(gamma_fn);
    scope.lgamma = elementwise(lgamma_fn);
    scope.beta  = elementwise(beta_fn);
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
    // More dimensionless — element-wise on arrays
    scope.biot           = elementwise(biot);
    scope.fourier_thermal = elementwise(fourier_thermal);
    scope.lewis          = elementwise(lewis);
    scope.weber          = elementwise(weber);
    scope.grashof        = elementwise(grashof);
    scope.stokes         = elementwise(stokes);
    // Extra array / stats
    scope.diff2     = diff2_fn;
    scope.vstack    = vstack_fn;
    scope.hstack    = hstack_fn;
    scope.meshgrid  = meshgrid_fn;
    scope.cov       = cov_fn;
    scope.histogram = histogram_fn;
    scope.mode      = mode_fn;
    scope.eig_full  = eig_full_fn;
    // Alloy
    scope.wt_to_mol  = wt_to_mol;
    scope.mol_to_wt  = mol_to_wt;
    scope.wt_to_mol2 = wt_to_mol2;
    // FFT
    scope.fft      = fft;
    scope.ifft     = ifft;
    scope.fftfreq  = fftfreq;
    scope.fftshift = fftshift;
    scope.real     = real_fn;
    scope.imag     = imag_fn;
    scope.angle    = angle_fn;

    // User-defined variables override built-ins (e.g. user may name a var "angle")
    Object.assign(scope, variables);

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

  // ── Statement execution helpers ─────────────────────────────────────────────

  function findAssignEq(s) {
    for (var _i = 0; _i < s.length; _i++) {
      if (s[_i] === '=') {
        var prev = _i > 0 ? s[_i - 1] : '';
        var next = _i < s.length - 1 ? s[_i + 1] : '';
        if (prev !== '!' && prev !== '<' && prev !== '>' && prev !== '=' && next !== '=') return _i;
      }
    }
    return -1;
  }

  // Execute one statement, mutate variables in place, return the assigned/evaluated value.
  function executeStatement(expression, variables) {
    const assignEq = findAssignEq(expression);
    if (assignEq !== -1) {
      const lhs = expression.slice(0, assignEq).trim();
      const rhs = expression.slice(assignEq + 1).trim();

      if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(lhs)) {
        const value = evaluateExpression(rhs, variables);
        variables[lhs] = value;
        return value;
      }
      // Index assignment: x[i] = val  or  x[i][j] = val
      const m = lhs.match(/^([A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\](?:\[([^\]]+)\])?$/);
      if (!m) throw new Error("Invalid assignment target");
      const arrName = m[1], idx1Expr = m[2], idx2Expr = m[3];
      if (!(arrName in variables)) throw new Error(`${arrName} is not defined`);
      const arr = variables[arrName];
      if (!Array.isArray(arr)) throw new Error(`${arrName} is not an array`);
      const newArr = arr.map(function (row) { return Array.isArray(row) ? row.slice() : row; });
      const value = evaluateExpression(rhs, variables);
      if (idx2Expr !== undefined) {
        const idx1 = Math.round(Number(evaluateExpression(idx1Expr, variables)));
        const idx2 = Math.round(Number(evaluateExpression(idx2Expr, variables)));
        if (!Array.isArray(newArr[idx1])) throw new Error(`${arrName}[${idx1}] is not an array`);
        newArr[idx1][idx2] = value;
      } else if (findTopLevelColon(idx1Expr) !== -1) {
        const indices = parseSliceIndices(idx1Expr, variables, newArr.length);
        if (Array.isArray(value)) {
          if (value.length !== indices.length) {
            throw new Error("Slice assignment length mismatch");
          }
          indices.forEach(function (idx, index) {
            newArr[idx] = value[index];
          });
        } else {
          indices.forEach(function (idx) {
            newArr[idx] = value;
          });
        }
      } else {
        const idx1 = Math.round(Number(evaluateExpression(idx1Expr, variables)));
        newArr[idx1] = value;
      }
      variables[arrName] = newArr;
      return value;
    }
    return evaluateExpression(expression, variables);
  }

  // ── Block executor (handles nested for / if / elif / else) ─────────────────

  function indentOf(raw) {
    var n = 0;
    for (var _c = 0; _c < raw.length; _c++) {
      if (raw[_c] === ' ') n++;
      else if (raw[_c] === '\t') n += 4;
      else break;
    }
    return n;
  }

  // Evaluate a condition expression (may return boolean, number, etc.)
  function evaluateCondition(expr, variables) {
    // Convert Python boolean operators to JS
    var jsExpr = expr
      .replace(/\bnot\s+in\b/g, '__notIn__')
      .replace(/\bin\b/g, 'in')           // JS `in` is object-key check — best-effort
      .replace(/\b__notIn__\b/g, '!in')
      .replace(/\band\b/g, '&&')
      .replace(/\bor\b/g, '||')
      .replace(/\bnot\b/g, '!');
    var scope = {};
    Object.assign(scope, variables);
    MATH_NAMES.forEach(function (n) { if (!(n in scope)) scope[n] = Math[n]; });
    scope.pi = Math.PI; scope.e = Math.E; scope.tau = 2 * Math.PI;
    var names = Object.keys(scope);
    var values = Object.values(scope);
    try {
      var fn = new Function(names, 'return !!(' + jsExpr + ');');
      return fn.apply(null, values);
    } catch (e) { return false; }
  }

  // Execute a flat list of raw lines as a block, handling nested for/if/elif/else.
  // All lines are expected to share the same minimum indentation.
  function executeBlock(lines, variables) {
    var li = 0;
    while (li < lines.length) {
      var raw = lines[li] || '';
      var stmt = stripInlineComment(raw).trim();

      if (!stmt) { li++; continue; }

      var myIndent = indentOf(raw);

      // Collect immediately-following lines that are MORE indented (= sub-body)
      function collectSubBody() {
        var sub = [];
        li++;
        while (li < lines.length) {
          var subRaw = lines[li] || '';
          if (subRaw.trim() === '') { sub.push(subRaw); li++; continue; }
          if (indentOf(subRaw) > myIndent) { sub.push(subRaw); li++; }
          else break;
        }
        return sub;
      }

      if (/^for\s/.test(stmt) && stmt.endsWith(':')) {
        var fmatch = stmt.match(/^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+?)\s*:$/);
        var subBody = collectSubBody();
        if (fmatch) {
          try {
            var iterable = evaluateExpression(fmatch[2], variables);
            if (Array.isArray(iterable)) {
              for (var fi = 0; fi < iterable.length; fi++) {
                variables[fmatch[1]] = iterable[fi];
                executeBlock(subBody, variables);
              }
            }
          } catch (e) { /* skip on error */ }
        }
        continue;
      }

      if (/^if\s/.test(stmt) && stmt.endsWith(':')) {
        var condExpr = stmt.replace(/^if\s+/, '').replace(/\s*:\s*$/, '');
        var ifBody = collectSubBody();
        var executed = false;
        try {
          if (evaluateCondition(condExpr, variables)) {
            executeBlock(ifBody, variables);
            executed = true;
          }
        } catch (e) {}

        // Handle elif / else chain at same indent
        while (li < lines.length) {
          var chainRaw = lines[li] || '';
          var chainStmt = stripInlineComment(chainRaw).trim();
          if (!chainStmt) { li++; continue; }
          if (indentOf(chainRaw) !== myIndent) break;
          if (!/^(elif\s|else\s*:)/.test(chainStmt)) break;

          var chainIndent = indentOf(chainRaw);
          myIndent = chainIndent;   // update for collectSubBody
          var chainBody = collectSubBody();

          if (!executed) {
            if (/^else\s*:/.test(chainStmt)) {
              executeBlock(chainBody, variables);
              executed = true;
            } else {
              var elifExpr = chainStmt.replace(/^elif\s+/, '').replace(/\s*:\s*$/, '');
              try {
                if (evaluateCondition(elifExpr, variables)) {
                  executeBlock(chainBody, variables);
                  executed = true;
                }
              } catch (e) {}
            }
          }
        }
        continue;
      }

      if (/^(elif\s|else\s*:)/.test(stmt)) {
        // Orphaned elif/else — skip with body
        collectSubBody();
        continue;
      }

      // Plain statement
      try { executeStatement(stmt, variables); } catch (e) {}
      li++;
    }
  }

  // ── plot() call parsing ──────────────────────────────────────────────────────

  function splitArgsTopLevel(str) {
    var depth = 0, current = "", args = [];
    for (var i = 0; i < str.length; i++) {
      var c = str[i];
      if ("([{".indexOf(c) >= 0) depth++;
      else if (")]}".indexOf(c) >= 0) depth--;
      if (c === "," && depth === 0) { args.push(current.trim()); current = ""; }
      else current += c;
    }
    if (current.trim()) args.push(current.trim());
    return args;
  }

  function parseYVarNames(arg) {
    arg = arg.trim();
    if (arg.startsWith("[")) {
      var inner = arg.slice(1, arg.lastIndexOf("]"));
      return inner.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
    }
    return arg ? [arg] : [];
  }

  function parsePlotCall(expr) {
    var m = expr.match(/^plot\s*\((.+)\)$/);
    if (!m) return null;
    var args = splitArgsTopLevel(m[1]);
    var x_var = null, y_vars = [], plot_type = "lines", title = null, x_title = null, y_title = null;
    var positional = [];
    for (var i = 0; i < args.length; i++) {
      var kv = args[i].match(/^(\w+)\s*=\s*(.+)$/);
      if (kv) {
        var key = kv[1], val = kv[2].trim().replace(/^["'`]|["'`]$/g, "");
        if (key === "type")                         plot_type = val;
        else if (key === "title")                   title = val;
        else if (key === "xlabel" || key === "x_title") x_title = val;
        else if (key === "ylabel" || key === "y_title") y_title = val;
      } else {
        positional.push(args[i].trim());
      }
    }
    if (positional.length === 1) {
      y_vars = parseYVarNames(positional[0]);
    } else if (positional.length >= 2) {
      x_var = positional[0];
      y_vars = parseYVarNames(positional[1]);
      if (positional[2]) plot_type = positional[2].replace(/^["'`]|["'`]$/g, "").trim();
    }
    if (!y_vars.length) return null;
    return { x_var: x_var, y_vars: y_vars, plot_type: plot_type, title: title, x_title: x_title, y_title: y_title };
  }

  // ─────────────────────────────────────────────────────────────────────────────

  function buildResultRows(lines) {
    const variables = {};
    const results = new Array(lines.length).fill("");

    let li = 0;
    while (li < lines.length) {
      const raw = lines[li] || "";
      const expression = stripInlineComment(raw).trim();

      if (!expression || isIndentedLine(raw)) {
        li++;
        continue;
      }

      // Detect plot() call — show icon in gutter, skip normal evaluation
      const plotSpec = parsePlotCall(expression);
      if (plotSpec) {
        results[li] = { name: "plot", value: "📊 plot", count: "", error: false };
        li++;
        continue;
      }

      if (isBlockHeader(expression)) {
        // Collect this block header + all immediately following indented lines,
        // then hand the whole chunk to executeBlock which handles nested for/if/elif/else.
        const headerIdx = li;
        const blockLines = [raw];   // include the header line itself
        li++;
        while (li < lines.length && isIndentedLine(lines[li] || "")) {
          blockLines.push(lines[li]);
          li++;
        }
        try {
          executeBlock(blockLines, variables);
        } catch (err) {
          results[headerIdx] = { name: resultLabel(expression), value: "Error: " + err.message, count: "", error: true };
        }
        continue;
      }

      try {
        const value = executeStatement(expression, variables);
        const label = resultLabel(expression);
        results[li] = {
          name: label,
          value: formatScalar(value),
          count: Array.isArray(value) ? value.length : "",
          error: false,
        };
      } catch (err) {
        results[li] = { name: resultLabel(expression), value: "Error: " + err.message, count: "", error: true };
      }
      li++;
    }

    return { results, variables };
  }

  // ── Monaco CSS injections ─────────────────────────────────────────────────
  (function injectEditorCSS() {
    if (document.getElementById('_nb_editor_style')) return;
    var s = document.createElement('style');
    s.id = '_nb_editor_style';
    s.textContent = '.nb-array-var   { color: #1d4ed8 !important; font-weight: 700 !important; }'
                  + '.nb-scalar-var  { color: #0f766e !important; font-weight: 700 !important; }'
                  + '.nb-error-line  { background: rgba(239,68,68,0.08) !important; }'
                  + '.nb-error-glyph::before { content: "●"; color: #ef4444; font-size: 10px; margin-left: 4px; }';
    document.head.appendChild(s);
  }());

  function applyErrorDecorations(errorLineIndices) {
    var editors = (window._cellEditors && Object.keys(window._cellEditors).length > 0)
      ? Object.values(window._cellEditors)
      : (window._monacoEditor ? [window._monacoEditor] : []);
    editors.forEach(function(editor) {
      if (!editor || !editor.getModel) return;
      var decorations = errorLineIndices.map(function(lineIdx) {
        return {
          range: new monaco.Range(lineIdx + 1, 1, lineIdx + 1, 1),
          options: {
            isWholeLine: true,
            className: 'nb-error-line',
            glyphMarginClassName: 'nb-error-glyph',
            overviewRuler: { color: '#ef4444', position: monaco.editor.OverviewRulerLane.Left },
          },
        };
      });
      if (!editor._nbErrorDecorations) editor._nbErrorDecorations = [];
      editor._nbErrorDecorations = editor.deltaDecorations(editor._nbErrorDecorations, decorations);
    });
  }

  function _fmtNum(x) {
    if (!isFinite(x)) return String(x);
    var a = Math.abs(x);
    if (a === 0) return '0';
    if (a >= 1e4 || (a > 0 && a < 1e-2)) {
      var s = x.toExponential(2).replace(/\.?0+e/, 'e').replace('e+', 'e').replace(/e(-?)0*(\d+)/, 'e$1$2');
      return s;
    }
    var s3 = parseFloat(x.toPrecision(3));
    return String(s3);
  }

  function renderVarInspector(variables) {
    var panel = document.getElementById('nb-var-inspector-body');
    if (!panel) return;
    var names = Object.keys(variables);
    if (names.length === 0) {
      panel.innerHTML = '<div style="color:#94a3b8;font-size:12px;padding:8px;font-style:italic">No variables defined yet.</div>';
      return;
    }
    var rows = names.map(function(name) {
      var v = variables[name];
      var type, shape, preview;
      if (Array.isArray(v)) {
        if (v.length > 0 && Array.isArray(v[0])) {
          type = 'matrix'; shape = v.length + '×' + v[0].length;
          preview = '[[' + v[0].slice(0,3).map(_fmtNum).join(', ') + (v[0].length>3?', …':'') + '], …]';
        } else {
          type = 'vector'; shape = '[' + v.length + ']';
          preview = '[' + v.slice(0,5).map(_fmtNum).join(', ') + (v.length>5?', …':'') + ']';
        }
      } else if (typeof v === 'number') {
        type = 'scalar'; shape = '—';
        preview = isFinite(v) ? _fmtNum(v) : String(v);
      } else if (typeof v === 'object' && v !== null) {
        type = 'object'; shape = '—';
        preview = JSON.stringify(v).slice(0, 60);
      } else {
        type = typeof v; shape = '—'; preview = String(v);
      }
      return '<tr style="border-bottom:1px solid #f1f5f9">'
        + '<td style="padding:4px 8px;font-weight:600;color:#1e293b;font-family:monospace;font-size:12px">' + name + '</td>'
        + '<td style="padding:4px 8px;color:#001f41;font-size:11px">' + type + '</td>'
        + '<td style="padding:4px 8px;color:#64748b;font-size:11px">' + shape + '</td>'
        + '<td style="padding:4px 8px;color:#334155;font-family:monospace;font-size:11px;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + preview + '</td>'
        + '</tr>';
    }).join('');
    panel.innerHTML = '<table style="width:100%;border-collapse:collapse">'
      + '<thead><tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0">'
      + '<th style="padding:4px 8px;text-align:left;font-size:11px;color:#64748b;font-weight:600">Name</th>'
      + '<th style="padding:4px 8px;text-align:left;font-size:11px;color:#64748b;font-weight:600">Type</th>'
      + '<th style="padding:4px 8px;text-align:left;font-size:11px;color:#64748b;font-weight:600">Shape</th>'
      + '<th style="padding:4px 8px;text-align:left;font-size:11px;color:#64748b;font-weight:600">Value</th>'
      + '</tr></thead><tbody>' + rows + '</tbody></table>';
  }

  function applyVarDecorations(arrayVarNames, scalarVarNames) {
    var editors = (window._cellEditors && Object.keys(window._cellEditors).length > 0)
      ? Object.values(window._cellEditors)
      : (window._monacoEditor ? [window._monacoEditor] : []);
    editors.forEach(function(editor) {
      if (!editor || !editor.getModel) return;
      var model = editor.getModel();
      if (!model) return;
      var decorations = [];
      function addDecorations(names, cls) {
        names.forEach(function (name) {
          var escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          var matches = model.findMatches('\\b' + escaped + '\\b', false, true, true, null, false);
          matches.forEach(function (m) {
            decorations.push({ range: m.range, options: { inlineClassName: cls } });
          });
        });
      }
      addDecorations(arrayVarNames,  'nb-array-var');
      addDecorations(scalarVarNames, 'nb-scalar-var');
      if (!editor._nbVarDecorations) editor._nbVarDecorations = [];
      editor._nbVarDecorations = editor.deltaDecorations(editor._nbVarDecorations, decorations);
    });
  }

  function refreshVarsFromState(state) {
    var safeState = state || {};
    var scalarVars = safeState.variables || {};
    var arrayVars = safeState.array_variables || {};
    var arrayNames = Object.keys(arrayVars);
    var scalarNames = Object.keys(scalarVars);
    applyVarDecorations(arrayNames, scalarNames);

    var merged = {};
    Object.keys(scalarVars).forEach(function (name) { merged[name] = scalarVars[name]; });
    Object.keys(arrayVars).forEach(function (name) { merged[name] = arrayVars[name]; });
    renderVarInspector(merged);
  }
  window._nbRefreshVarsFromState = refreshVarsFromState;

  function renderResults(resultsContainer, debugContainer, text) {
    if (!resultsContainer) {
      return;
    }
    const lines = (text || "").split("\n");
    const evaluation = buildResultRows(lines);
    const rows = Math.max(NOTEBOOK_ROWS, evaluation.results.length);
    const maxLabelLen = evaluation.results.reduce(function(acc, entry) {
      if (!entry || typeof entry !== "object") return acc;
      const len = String(entry.name || "").length;
      return Math.max(acc, len);
    }, 0);
    const nameColWidth = Math.max(72, Math.min(220, maxLabelLen * 9 + 16));
    const colTemplate = nameColWidth + "px minmax(0, 1fr) 56px";

    // Sync header column widths with data rows
    const headerSibling = resultsContainer.previousElementSibling;
    if (headerSibling) headerSibling.style.gridTemplateColumns = colTemplate;

    // Highlight variable names in the editor by type
    const arrayVarNames  = Object.keys(evaluation.variables).filter(function (k) { return Array.isArray(evaluation.variables[k]); });
    const scalarVarNames = Object.keys(evaluation.variables).filter(function (k) { return typeof evaluation.variables[k] === 'number'; });
    applyVarDecorations(arrayVarNames, scalarVarNames);

    // Error line decorations
    const errorLineIndices = evaluation.results.reduce(function(acc, r, i) {
      if (r && r.error) acc.push(i);
      return acc;
    }, []);
    applyErrorDecorations(errorLineIndices);

    // Variable inspector
    renderVarInspector(evaluation.variables);

    resultsContainer.style.position = "";
    resultsContainer.style.height = "";
    resultsContainer.innerHTML = "";
    resultsContainer.style.borderTop = "none";
    resultsContainer.style.borderRight = "1px solid #e2e8f0";
    resultsContainer.style.borderBottom = "1px solid #e2e8f0";
    resultsContainer.style.borderLeft = "1px solid #e2e8f0";
    resultsContainer.style.borderRadius = "0 0 4px 4px";
    resultsContainer.style.overflow = "hidden";

    for (let index = 0; index < rows; index += 1) {
      const entry = evaluation.results[index] || { name: "", value: "", count: "", error: false };
      const row = document.createElement("div");
      row.style.display = "grid";
      row.style.gridTemplateColumns = colTemplate;
      row.style.columnGap = "0";
      row.style.height = "34px";
      row.style.lineHeight = "34px";
      row.style.fontFamily = "monospace";
      row.style.fontSize = "13px";
      row.style.alignItems = "center";
      row.style.borderBottom = "1px solid #e2e8f0";
      const isError = !!entry.error;
      const isPlot  = String(entry.value || "").startsWith("📊");

      const cellBase = "padding:0 8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;height:34px;line-height:34px;";

      const nameCell = document.createElement("div");
      nameCell.textContent = entry.name || "";
      nameCell.title = "Data";
      nameCell.style.cssText = cellBase + "border-right:1px solid #e2e8f0;font-weight:600;color:" + (isError ? "#b42318" : "#475467") + ";";

      const valueCell = document.createElement("div");
      valueCell.textContent = entry.value || "";
      valueCell.title = "Value";
      valueCell.style.cssText = cellBase + "border-right:1px solid #e2e8f0;font-weight:" + (isPlot ? "700" : "600") + ";color:" + (isError ? "#b42318" : isPlot ? "#001f41" : (entry.value ? "#1e3a8a" : "#98a2b3")) + ";";

      const countCell = document.createElement("div");
      countCell.textContent = entry.count === "" ? "" : String(entry.count);
      countCell.title = "Count";
      countCell.style.cssText = cellBase + "text-align:right;color:" + (entry.count === "" ? "#98a2b3" : "#64748b") + ";font-weight:600;";

      row.appendChild(nameCell);
      row.appendChild(valueCell);
      row.appendChild(countCell);
      resultsContainer.appendChild(row);
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
    // Skip legacy runtime when the cell-based notebook is active
    if (document.getElementById("notebook-cells-container")) return;

    const textarea = document.getElementById("notebook-textarea");
    const hiddenInput = document.getElementById("notebook-live-text");
    const runInput = document.getElementById("notebook-run-text");
    const results = document.getElementById("notebook-results");
    const debug = document.getElementById("notebook-debug");
    const lineNumbers = document.getElementById("notebook-line-numbers");
    const clearButton = document.getElementById("notebook-clear-btn");
    const runButton = document.getElementById("notebook-run-btn");
    const autoBox = document.getElementById("notebook-auto-update");
    if (!textarea || !results || textarea.dataset.liveSyncAttached === "true") {
      return;
    }

    // Always expose the render function so Monaco can call it
    exposeRenderGlobal(results, debug);

    const isAutoUpdateEnabled = function () {
      if (!autoBox) return true;
      return !!autoBox.querySelector('input[type="checkbox"]:checked');
    };

    const setDashValue = function (el, value) {
      if (!el) return;
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value");
      if (setter && setter.set) setter.set.call(el, value);
      else el.value = value;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    };

    const runCurrentValue = function () {
      const value = textarea.value || "";
      setDashValue(hiddenInput, value);
      setDashValue(runInput, value);
      textarea.style.height = "auto";
      textarea.style.height = Math.max(400, textarea.scrollHeight) + "px";
    renderResults(results, debug, value);
    if (lineNumbers) updateLineNumbers(lineNumbers, value);
  };

    const pushValue = function () {
      // If Monaco has taken over, skip textarea-based sync
      if (window._monacoEditor) return;
      const value = textarea.value || "";
      setDashValue(hiddenInput, value);
      // Auto-grow textarea to fit content (no internal scroll)
      textarea.style.height = "auto";
      textarea.style.height = Math.max(400, textarea.scrollHeight) + "px";
      if (lineNumbers) updateLineNumbers(lineNumbers, value);
      if (isAutoUpdateEnabled()) {
        setDashValue(runInput, value);
        renderResults(results, debug, value);
      }
    };

    textarea.addEventListener("input", pushValue);
    textarea.addEventListener("keyup", pushValue);
    textarea.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        runCurrentValue();
      }
    });
    if (clearButton && clearButton.dataset.liveSyncAttached !== "true") {
      clearButton.addEventListener("click", function () {
        window.setTimeout(pushValue, 0);
      });
      clearButton.dataset.liveSyncAttached = "true";
    }
    if (runButton && runButton.dataset.liveSyncAttached !== "true") {
      runButton.addEventListener("click", function () {
        runCurrentValue();
      });
      runButton.dataset.liveSyncAttached = "true";
    }
    if (autoBox && autoBox.dataset.liveSyncAttached !== "true") {
      autoBox.addEventListener("change", function () {
        if (isAutoUpdateEnabled()) {
          runCurrentValue();
        }
      });
      autoBox.dataset.liveSyncAttached = "true";
    }
    textarea.dataset.liveSyncAttached = "true";
    runCurrentValue();
  }

  // ── AI insert helper (shared by formula bar and chat) ────────────────────
  function insertCodeIntoMonaco(code, ts, lastTsRef) {
    if (!code || ts === lastTsRef.val) return false;
    lastTsRef.val = ts;
    var editor = window._monacoEditor;
    if (!editor) {
      var ta = document.getElementById('notebook-textarea');
      if (ta) {
        ta.value = (ta.value || '').trimEnd() + '\n' + code + '\n';
        ta.dispatchEvent(new Event('input', { bubbles: true }));
      }
      return true;
    }
    var sel   = editor.getSelection();
    var model = editor.getModel();
    var line  = sel ? sel.endLineNumber : model.getLineCount();
    var lineLen = model.getLineMaxColumn(line);
    editor.executeEdits('ai-insert', [{
      range: new monaco.Range(line, lineLen, line, lineLen),
      text: '\n' + code,
      forceMoveMarkers: true,
    }]);
    var newLine = line + code.split('\n').length;
    editor.setPosition({ lineNumber: newLine, column: model.getLineMaxColumn(newLine) });
    editor.focus();
    return true;
  }

  // ── Chat insert (from Insert button in chat messages) ─────────────────────
  (function watchChatInsert() {
    var lastTs = { val: null };
    function tryInsert() {
      var storeEl = document.getElementById('nb-chat-insert');
      if (!storeEl || !storeEl.value) return;
      var data;
      try { data = JSON.parse(storeEl.value); } catch(e) { return; }
      if (data && data.code) insertCodeIntoMonaco(data.code, data.ts, lastTs);
    }
    setInterval(tryInsert, 400);
  })();

  // ── Shared streaming utilities ────────────────────────────────────────────

  function readStore(id) {
    var el = document.getElementById(id);
    if (!el || !el.value) return null;
    try { return JSON.parse(el.value); } catch(e) { return null; }
  }

  function writeStore(id, data) {
    var el = document.getElementById(id);
    if (!el) return;
    var json = JSON.stringify(data);
    try {
      var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      nativeSetter.call(el, json);
    } catch(e) { el.value = json; }
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function parseMarkdownParts(text) {
    var parts = [];
    var re = /```(?:\w+)?\n?([\s\S]*?)```/g;
    var last = 0, m;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) parts.push({ type: 'text', content: text.slice(last, m.index) });
      parts.push({ type: 'code', content: m[1].trim() });
      last = m.index + m[0].length;
    }
    if (last < text.length) parts.push({ type: 'text', content: text.slice(last) });
    return parts;
  }

  // Build a rendered AI bubble with optional Insert buttons
  // theme: 'notebook' | 'floating'
  function buildAiBubble(text, insertTs, theme) {
    var wrap = document.createElement('div');
    if (theme === 'floating') {
      wrap.className = 'fchat-bubble-ai';
    } else {
      wrap.style.cssText = 'padding:8px 12px;border-radius:10px;font-size:13px;line-height:1.55;max-width:88%;word-break:break-word;background:#f1f5f9;color:#1e293b;align-self:flex-start';
    }
    var parts = parseMarkdownParts(text);
    var codeIdx = 0;
    parts.forEach(function(part) {
      if (part.type === 'text') {
        if (part.content.trim()) {
          var s = document.createElement('span');
          s.style.whiteSpace = 'pre-wrap';
          s.textContent = part.content;
          wrap.appendChild(s);
        }
      } else {
        var code = part.content;
        var btnKey = String((insertTs || 0) * 1000 + codeIdx);
        var pre = document.createElement('pre');
        if (theme === 'floating') {
          pre.className = 'fchat-code-block';
        } else {
          pre.style.cssText = 'background:#1e1e2e;color:#cdd6f4;border-radius:6px;padding:8px 10px;font-size:12px;margin:6px 0;overflow-x:auto;white-space:pre-wrap';
        }
        pre.textContent = code;
        var btn = document.createElement('button');
        btn.textContent = '↑ Insert';
        btn.setAttribute('data-code-key', btnKey);
        btn.setAttribute('data-code-val', code);
        if (theme === 'floating') {
          btn.className = 'fchat-insert-btn';
        } else {
          btn.style.cssText = 'font-size:11px;padding:2px 10px;border-radius:6px;border:1px solid #c4b5fd;background:#faf5ff;color:#7c3aed;cursor:pointer;margin-bottom:4px';
        }
        (function(c) {
          btn.addEventListener('click', function() {
            insertCodeIntoMonaco(c, Date.now(), { val: null });
          });
        })(code);
        var block = document.createElement('div');
        block.appendChild(pre);
        block.appendChild(btn);
        wrap.appendChild(block);
        codeIdx++;
      }
    });
    return wrap;
  }

  // Generic streaming chat instance factory
  function makeChatStreamer(cfg) {
    // cfg: { pendingId, historyId, codeMapId, messagesId,
    //        theme, buildContextMessages }
    var _lastKey = null;
    var _busy = false;

    async function doStream(pending) {
      if (_busy) return;
      _busy = true;
      var userText = pending.text;
      var ts = pending.ts || 0;
      var history = readStore(cfg.historyId) || [];
      var msgEl = document.getElementById(cfg.messagesId);
      if (!msgEl) { _busy = false; return; }

      // Remove thinking indicator
      var thinking = msgEl.querySelector('[data-thinking]');
      if (thinking) msgEl.removeChild(thinking);

      // Streaming bubble placeholder
      var insertTs = ts * 1000 + history.length + 1;
      var aiBubble = document.createElement('div');
      if (cfg.theme === 'floating') {
        aiBubble.className = 'fchat-bubble-ai';
      } else {
        aiBubble.style.cssText = 'padding:8px 12px;border-radius:10px;font-size:13px;line-height:1.55;max-width:88%;word-break:break-word;background:#f1f5f9;color:#1e293b;align-self:flex-start';
      }
      var textSpan = document.createElement('span');
      textSpan.style.whiteSpace = 'pre-wrap';
      aiBubble.appendChild(textSpan);
      msgEl.appendChild(aiBubble);
      msgEl.scrollTop = msgEl.scrollHeight;

      var fullText = '';
      try {
        var resp = await fetch('/api/nb-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: cfg.buildContextMessages(userText, history) })
        });
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        var reader = resp.body.getReader();
        var decoder = new TextDecoder();
        var buf = '';
        outer: while (true) {
          var chunk = await reader.read();
          if (chunk.done) break;
          buf += decoder.decode(chunk.value, { stream: true });
          var lines = buf.split('\n');
          buf = lines.pop();
          for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (!line.startsWith('data:')) continue;
            var payload = line.slice(5).trim();
            if (payload === '[DONE]') break outer;
            try {
              var evt = JSON.parse(payload);
              if (evt.error) {
                textSpan.textContent = 'Error: ' + evt.error;
                if (cfg.theme === 'floating') aiBubble.className = 'fchat-error';
                else aiBubble.style.color = '#ef4444';
                fullText = '';
                break outer;
              }
              if (evt.t) {
                fullText += evt.t;
                textSpan.textContent = fullText;
                msgEl.scrollTop = msgEl.scrollHeight;
              }
            } catch(e) {}
          }
        }
      } catch(e) {
        textSpan.textContent = 'Error: ' + e.message;
        if (cfg.theme === 'floating') aiBubble.className = 'fchat-error';
        else aiBubble.style.color = '#ef4444';
        fullText = '';
      }

      // Replace streaming bubble with final rendered bubble (code blocks + Insert buttons)
      if (fullText) {
        msgEl.removeChild(aiBubble);
        var finalBubble = buildAiBubble(fullText, insertTs, cfg.theme);
        msgEl.appendChild(finalBubble);
        msgEl.scrollTop = msgEl.scrollHeight;

        var newHistory = history.concat([
          { role: 'user', content: userText },
          { role: 'assistant', content: fullText }
        ]);
        writeStore(cfg.historyId, newHistory);

        var codeMap = {};
        finalBubble.querySelectorAll('[data-code-key]').forEach(function(btn) {
          codeMap[btn.getAttribute('data-code-key')] = btn.getAttribute('data-code-val') || '';
        });
        writeStore(cfg.codeMapId, codeMap);
      }

      _busy = false;
    }

    setInterval(function() {
      var pending = readStore(cfg.pendingId);
      if (!pending || !pending.text) return;
      var key = pending.ts + ':' + pending.text;
      if (key === _lastKey) return;
      _lastKey = key;
      doStream(pending);
    }, 200);
  }

  // ── Notebook chat streamer ────────────────────────────────────────────────
  var _NB_SYSTEM = (
    "You are an expert assistant embedded in a physics/materials-science calculation notebook. " +
    "The notebook uses its OWN built-in functions — do NOT use numpy, scipy, or any Python imports. " +
    "Available functions include: linspace, arange, zeros, ones, exp, log, log10, sin, cos, sqrt, abs, " +
    "sum, mean, std, min, max, cumsum, diff, sort, where, clip, interp, gradient, trapz, fft, " +
    "solve, dot, norm, eig, and more. " +
    "One expression or assignment per line. Variables carry forward automatically. " +
    "Use plot(x, y) to plot arrays. Use ^ for power (not **).\n" +
    "When suggesting code to insert, wrap it in a fenced code block (```). " +
    "Be concise. Focus on the user's specific notebook context."
  );

  // ── Floating chat toggle (pure JS, no Dash round-trip) ──────────────────
  (function watchFChatToggle() {
    function attach() {
      var toggleBtn = document.getElementById('fchat-toggle-btn');
      var closeBtn  = document.getElementById('fchat-close-btn');
      var panel     = document.getElementById('fchat-panel');
      if (!toggleBtn || !panel) return false;

      if (!toggleBtn._fchatAttached) {
        toggleBtn._fchatAttached = true;
        toggleBtn.addEventListener('click', function(e) {
          e.stopPropagation();
          var open = panel.classList.contains('open');
          if (open) {
            panel.classList.remove('open');
          } else {
            panel.classList.add('open');
            var inp = document.getElementById('fchat-input');
            if (inp) setTimeout(function() { inp.focus(); }, 60);
          }
        });
      }
      if (closeBtn && !closeBtn._fchatAttached) {
        closeBtn._fchatAttached = true;
        closeBtn.addEventListener('click', function(e) {
          e.stopPropagation();
          panel.classList.remove('open');
        });
      }
      return true;
    }

    var done = false;
    var iv = setInterval(function() {
      if (!done) done = attach();
      else clearInterval(iv);
    }, 300);
  })();

  // ── Floating chat streamer ────────────────────────────────────────────────
  makeChatStreamer({
    pendingId:  'fchat-pending',
    historyId:  'fchat-history',
    codeMapId:  'fchat-code-map',
    messagesId: 'fchat-messages',
    theme: 'floating',
    buildContextMessages: function(userText, history) {
      var sys = "You are a helpful AI assistant for OPView, a materials science simulation visualization tool. " +
                "Help with simulation analysis, materials science concepts, and data interpretation. " +
                "When suggesting code for the OPView notebook, wrap it in a fenced code block (```) " +
                "and use the notebook's built-in functions (linspace, exp, log, plot, etc.) — no numpy/scipy imports.";
      var codeEl = document.getElementById('notebook-live-text');
      var codeCtx = codeEl ? (codeEl.value || '').trim() : '';
      if (!codeCtx && window._monacoEditor) codeCtx = (window._monacoEditor.getValue() || '').trim();
      var varsCtx = '';
      var nbState = readStore('notebook-state');
      if (nbState && nbState.variables) {
        varsCtx = Object.entries(nbState.variables).slice(0, 20)
          .map(function(kv) { return '  ' + kv[0] + ' = ' + kv[1]; }).join('\n');
      }
      if (codeCtx) sys += '\n\nCurrent notebook code:\n```\n' + codeCtx + '\n```';
      if (varsCtx) sys += '\n\nCurrent variable values:\n' + varsCtx;
      var msgs = [{ role: 'system', content: sys }];
      (history || []).forEach(function(m) { msgs.push({ role: m.role, content: m.content }); });
      msgs.push({ role: 'user', content: userText });
      return msgs;
    }
  });

  window.addEventListener("load", function () {
    attachNotebookRuntime();
    const observer = new MutationObserver(attachNotebookRuntime);
    observer.observe(document.body, { childList: true, subtree: true });
    loadMarkdownLibs();
  });

  // ── Markdown + KaTeX rendering ────────────────────────────────────────────

  var _markdownReady = false;

  function loadMarkdownLibs() {
    if (window.marked && window.katex && window.renderMathInElement) {
      _markdownReady = true;
      return;
    }

    // Load KaTeX CSS
    if (!document.getElementById('_katex_css')) {
      var link = document.createElement('link');
      link.id = '_katex_css';
      link.rel = 'stylesheet';
      link.href = '/assets/vendor/katex.min.css';
      document.head.appendChild(link);
    }

    // Load marked.js
    function loadScript(src, id, onload) {
      var existing = document.getElementById(id);
      if (existing) {
        if (existing.dataset.loaded === 'true') {
          if (onload) onload();
        } else if (onload) {
          existing.addEventListener('load', onload, { once: true });
        }
        return;
      }
      var s = document.createElement('script');
      s.id = id; s.src = src; s.async = true;
      s.onload = function () {
        s.dataset.loaded = 'true';
        if (onload) onload();
      };
      document.head.appendChild(s);
    }

    loadScript('/assets/vendor/marked.min.js', '_marked_js', function () {
      loadScript('/assets/vendor/katex.min.js', '_katex_js', function () {
        loadScript('/assets/vendor/katex-auto-render.min.js', '_katex_auto_js', function () {
          _markdownReady = true;
          // Render any pending markdown cells
          document.querySelectorAll('[data-md-pending="true"]').forEach(function(el) {
            var cellId = el.getAttribute('data-md-cell-id');
            var src = el.getAttribute('data-md-src') || '';
            if (cellId) renderMarkdownInto(cellId, src);
          });
        });
      });
    });
  }

  function _sanitizeHtml(html) {
    var tmp = document.createElement('div');
    tmp.innerHTML = html;
    // Remove script and style elements entirely
    tmp.querySelectorAll('script, style').forEach(function(el) { el.remove(); });
    // Strip on* event handlers and javascript: URIs from every element
    tmp.querySelectorAll('*').forEach(function(el) {
      Array.from(el.attributes).forEach(function(attr) {
        if (/^on/i.test(attr.name)) {
          el.removeAttribute(attr.name);
        }
      });
      var href = el.getAttribute('href');
      if (href && /^\s*javascript:/i.test(href)) el.removeAttribute('href');
      var src = el.getAttribute('src');
      if (src && /^\s*javascript:/i.test(src)) el.removeAttribute('src');
    });
    return tmp.innerHTML;
  }

  function _normalizeMarkdownMathHtml(html) {
    if (!html) return html;
    return html
      .replace(/<p>\s*\$\$<br\s*\/?>\s*([\s\S]*?)\s*<br\s*\/?>\s*\$\$\s*<\/p>/gi, function(_, inner) {
        return '<div class="nb-math-block">$$' + inner.replace(/<br\s*\/?>/gi, '\n') + '$$</div>';
      })
      .replace(/<p>\s*\\\[\s*<br\s*\/?>\s*([\s\S]*?)\s*<br\s*\/?>\s*\\\]\s*<\/p>/gi, function(_, inner) {
        return '<div class="nb-math-block">\\[' + inner.replace(/<br\s*\/?>/gi, '\n') + '\\]</div>';
      });
  }

  function _renderDirectKatexBlocks(container) {
    if (!container || !window.katex) return 0;
    var count = 0;
    container.querySelectorAll('.nb-math-block').forEach(function (el) {
      var text = (el.textContent || '').trim();
      var expr = text;
      if (expr.startsWith('$$') && expr.endsWith('$$')) {
        expr = expr.slice(2, -2).trim();
      } else if (expr.startsWith('\\[') && expr.endsWith('\\]')) {
        expr = expr.slice(2, -2).trim();
      }
      if (!expr) return;
      try {
        window.katex.render(expr, el, {
          displayMode: true,
          throwOnError: false
        });
        count += 1;
      } catch (e) {}
    });
    return count;
  }

  function _renderDirectKatexInline(container) {
    if (!container || !window.katex) return 0;
    var count = 0;
    container.querySelectorAll('p, li, td, th, span').forEach(function (el) {
      if (el.closest && el.closest('.katex, .katex-display, .nb-math-block')) return;
      var text = el.textContent || '';
      if (!text || text.indexOf('$') === -1) return;
      var html = el.innerHTML;
      var replaced = false;

      html = html.replace(/\$([^$\n]+)\$/g, function (_, expr) {
        expr = expr.trim();
        if (!expr) return _;
        try {
          replaced = true;
          count += 1;
          return window.katex.renderToString(expr, {
            displayMode: false,
            throwOnError: false
          });
        } catch (e) {
          return _;
        }
      });

      html = html.replace(/\\\(([^()\n]+)\\\)/g, function (_, expr) {
        expr = expr.trim();
        if (!expr) return _;
        try {
          replaced = true;
          count += 1;
          return window.katex.renderToString(expr, {
            displayMode: false,
            throwOnError: false
          });
        } catch (e) {
          return _;
        }
      });

      if (replaced) el.innerHTML = html;
    });
    return count;
  }

  function renderMarkdownInto(cellId, source) {
    var container = document.getElementById('nb-cell-md-preview-' + cellId);
    var editorContainer = document.getElementById('nb-cell-editor-' + cellId);
    if (!container) return;
    if (!_markdownReady || !window.marked) {
      // Store for later rendering
      container.setAttribute('data-md-pending', 'true');
      container.setAttribute('data-md-cell-id', cellId);
      container.setAttribute('data-md-src', source);
      return;
    }

    // Render markdown
    try {
      var rawHtml = window.marked.parse(source || '', { breaks: true, gfm: true });
      var normalizedHtml = _normalizeMarkdownMathHtml(rawHtml);
      container.innerHTML = _sanitizeHtml(normalizedHtml);
    } catch(e) {
      var pre = document.createElement('pre');
      pre.textContent = source || '';
      container.innerHTML = '';
      container.appendChild(pre);
    }

    // Render math with KaTeX
    if (window.renderMathInElement) {
      try {
        window.renderMathInElement(container, {
          delimiters: [
            { left: '$$', right: '$$', display: true  },
            { left: '$',  right: '$',  display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true  },
            { left: '\\begin{equation}', right: '\\end{equation}', display: true },
            { left: '\\begin{align}', right: '\\end{align}', display: true },
            { left: '\\begin{alignat}', right: '\\end{alignat}', display: true },
            { left: '\\begin{gather}', right: '\\end{gather}', display: true },
          ],
          throwOnError: false,
        });
      } catch(e) {}
    } else {
    }

    var directBlocks = _renderDirectKatexBlocks(container);
    var directInline = _renderDirectKatexInline(container);

    container.removeAttribute('data-md-pending');
    container.style.display = 'block';

    // Show preview, hide monaco editor div
    if (editorContainer) editorContainer.style.display = 'none';
  }

  function showMarkdownEditor(cellId) {
    var container = document.getElementById('nb-cell-md-preview-' + cellId);
    var editorContainer = document.getElementById('nb-cell-editor-' + cellId);
    if (container) container.style.display = 'none';
    if (editorContainer) {
      editorContainer.style.display = 'block';
      // Re-layout Monaco
      if (window._cellEditors && window._cellEditors[cellId]) {
        window._cellEditors[cellId].layout();
        window._cellEditors[cellId].focus();
      }
    }
  }

  document.addEventListener('mousedown', function (event) {
    window._markdownJustOpened = window._markdownJustOpened || {};
    var target = event.target && event.target.nodeType === 3
      ? event.target.parentElement
      : event.target;
    var preview = target && target.closest
      ? target.closest('[id^="nb-cell-md-preview-"]')
      : null;
    if (!preview) return;
    var cellId = preview.id.replace('nb-cell-md-preview-', '');
    if (!cellId) return;
    window._markdownJustOpened[cellId] = true;
    window.setTimeout(function () {
      delete window._markdownJustOpened[cellId];
    }, 220);
    showMarkdownEditor(cellId);
  });

  // Expose globally for Monaco and button click handlers
  window._renderMarkdownCell = renderMarkdownInto;
  window._showMarkdownEditor = showMarkdownEditor;
})();
