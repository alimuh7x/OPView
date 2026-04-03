# AGENTS.md

This file gives repo-wide instructions for Codex and other coding agents working in OPView.


## Scope
- These rules apply to the whole project.
- Keep changes focused on the user request. Do not refactor unrelated areas.
- Prefer small, local edits over broad rewrites.

## Project Structure
- Keep UI/layout construction in `ui/`.
- Keep Dash callback wiring and app state handling in `callbacks/`.
- Keep reusable parsing, evaluation, and other pure logic in `utils/`.
- Put new code in the closest existing module instead of creating parallel patterns.

## Coding Rules
- Follow existing OPView patterns before introducing new abstractions.
- Prefer helper functions for non-trivial logic instead of embedding large blocks inside callbacks.
- Keep computation and validation out of UI builders when possible.
- Keep computation and parsing out of callbacks when possible.
- Normalize and validate user input defensively.
- Fail with clear, user-facing error messages instead of silent fallback when correctness matters.
- Use descriptive names and short docstrings for non-obvious helpers.
- Avoid adding dependencies unless they are clearly necessary.

## Dash and UI Rules
- Preserve the current separation between layout code and callback code.
- Match the existing style of Dash components, state dictionaries, and callback helpers.
- Extend existing panel/state structures instead of inventing a second state model.
- Reuse existing styling conventions and constants where possible.
- Do not introduce large visual redesigns unless the task explicitly asks for them.

## Formula and Data Logic
- Keep formula evaluation safe and explicit.
- Prefer pure helper functions for parsing, math, interpolation, and numeric analysis.
- Keep allowed-symbol or allowed-function lists centralized when working on formula features.
- When adding analysis features, make edge-case handling explicit for invalid, empty, non-finite, or shape-mismatched data.

## Editing Rules
- Do not rename, move, or split files unless the task needs it.
- Do not replace working callback flows with a new framework or pattern.
- Keep comments sparse and useful.
- Preserve backward-compatible behavior unless the user asked for a behavior change.

## Verification
- Run the most relevant targeted check available after changes.
- Prefer focused verification for the touched area over unrelated full-project churn.
- If you cannot run verification, say so clearly in the final response.

---

## size
- input with -/+ min width should be 150px. if we change value using +/- : 1 -> 2, 0.1 -> 0.2, 0.01 -> 0.02 and go on.
- dropdown should be flex: "1 1 px"

## Mandatory Debug
- Any new feature added to OPView must include verbose debug output.
- Add debug prints before and after important operations, and inside exception paths.
- No new feature is complete unless its debug flow is visible in the terminal.

## Form Style
- Default OPView form layout must be:
  - title on top
  - input below
- This applies to dropdowns, numeric inputs, steppers, and similar controls.
- Prefer one field per block, not label on the left and value on the right.

## Multi-Field Row Rule
- If one item has multiple related fields, show it as a table-like row.
- Put the item label first, then the related fields as columns with headers above.
- Do not split such related fields into separate stacked blocks unless explicitly requested.
- Example:
    - Component | Type   | Value
    - XX        | Stress | [-] 350e6 [+]
    - YY        | None   | [-] 0 [+]
    - ZZ        | Strain | [-] 0.01 [+]

## Button Colors
- Use deep blue (#001f41) as the default button color and deep red (#95041a) on hover. Keep white text, soft shadows, and rounded corners. Do not introduce new colors for buttons.

## Colors:
- #001f41
- #001f41
 
## Icons
- use x icon and its hover from assets png
- use addition and addition hover from the assets png
- use on and off from assets png
