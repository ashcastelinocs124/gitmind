# Learnings

### 2026-03-17 -- setuptools build-backend path
- **What:** The build-backend `setuptools.backends._legacy:_Backend` does not exist and causes `pip install -e` to fail with `BackendUnavailable: Cannot import 'setuptools.backends._legacy'`.
- **Why it matters:** This is a common mistake in pyproject.toml scaffolding. The correct value is `setuptools.build_meta`.
- **Fix/Pattern:** Always use `build-backend = "setuptools.build_meta"` in `[build-system]`.

### 2026-03-17 -- Scorer breadth threshold tuning
- **What:** The code impact scorer's file breadth threshold of `avg_files >= 5` for the top tier was too strict. A contributor touching 4-5 files per commit on average is already high-breadth. Lowered to `avg_files >= 4`.
- **Why it matters:** The original threshold caused a test with avg 4.5 files/commit and a merged PR to score 59 instead of 60+. Boundary conditions in scoring heuristics need careful calibration against representative test cases.
- **Fix/Pattern:** When writing scoring heuristics, trace through the math with the exact test data before finalizing thresholds.
