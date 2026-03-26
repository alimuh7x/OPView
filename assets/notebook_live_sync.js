(function () {
  const NOTEBOOK_ROWS = 28;
  const MATH_NAMES = [
    "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "exp", "floor",
    "log", "max", "min", "pow", "round", "sin", "sqrt", "tan"
  ];
  const UNIT_FACTORS = {
    nm: 1e-9,
    um: 1e-6,
    mm: 1e-3,
    cm: 1e-2,
    m: 1,
    km: 1e3,
    ms: 1e-3,
    s: 1,
    min: 60,
    h: 3600,
    Pa: 1,
    kPa: 1e3,
    MPa: 1e6,
    GPa: 1e9
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

  function buildResultRows(lines) {
    const variables = {};
    const results = [];

    lines.forEach((line) => {
      const expression = stripInlineComment(line || "").trim();
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
    resultsContainer.innerHTML = "";
    for (let index = 0; index < rows; index += 1) {
      const textLine = evaluation.results[index] || "";
      const row = document.createElement("div");
      row.textContent = textLine;
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

  function attachNotebookRuntime() {
    const textarea = document.getElementById("notebook-textarea");
    const hiddenInput = document.getElementById("notebook-live-text");
    const results = document.getElementById("notebook-results");
    const debug = document.getElementById("notebook-debug");
    const clearButton = document.getElementById("notebook-clear-btn");
    if (!textarea || !results || textarea.dataset.liveSyncAttached === "true") {
      return;
    }

    const pushValue = function () {
      const value = textarea.value || "";
      if (hiddenInput) {
        hiddenInput.value = value;
      }
      renderResults(results, debug, value);
      console.log("[NotebookDebug] bridge push", {
        textareaLength: value.length,
        preview: value.slice(0, 120)
      });
    };

    textarea.addEventListener("input", pushValue);
    textarea.addEventListener("keyup", pushValue);
    if (clearButton && clearButton.dataset.liveSyncAttached !== "true") {
      clearButton.addEventListener("click", function () {
        window.setTimeout(pushValue, 0);
      });
      clearButton.dataset.liveSyncAttached = "true";
    }
    textarea.dataset.liveSyncAttached = "true";
    console.log("[NotebookDebug] bridge attached");
    pushValue();
  }

  window.addEventListener("load", function () {
    attachNotebookRuntime();
    const observer = new MutationObserver(attachNotebookRuntime);
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
