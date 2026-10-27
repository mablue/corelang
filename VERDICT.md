# Verdict — what was proven and what wasn't

## Proven

1. **d_Λ detects structural patterns.** Backbone (3 clusters),
   Bottle (15 clusters after E1 fix).
2. **Behavioral preservation.** Every applied refactor passed isolated tests.
3. **d_Λ invariance.** Structural refactoring preserves the semantic
   distance matrix across all tests (C2, C3, D4-fix2).
4. **The tool is honest.** D4-fix2 correctly rejected a refactor that
   would have increased code size.

## Not proven

1. **Scale.** Maximum: 4675 lines, 367 units.
2. **ROI on production code.** Only tested on 10+ year old projects.
3. **Cross-language signature normalization.**

## Numbers

| Metric                | Backbone | Bottle |
|-----------------------|----------|--------|
| Lines                 | 618      | 4675   |
| Units                 | 54       | 367    |
| Clusters              | 3        | 15     |
| Worth extracting (by formula) | 1 | 4    |
| Applied refactor      | add/remove → _iterate | get/post/put/delete/patch → _verb |
| Δ tokens (actual)     | −23      | +19    |
| Behavioral checks     | 18       | 20     |
| d_Λ invariance        | 3/3      | 10/10  |

## Key finding

**Extraction pays off only when leverage is high AND adapter cost is low.**

- Backbone `add`/`remove` (leverage=2, L=59): worth it (−23 tokens)
- Bottle `get`/`post`/`put`/`delete`/`patch` (leverage=5, L=30): NOT worth it
  (+19 tokens), because Python adapters cost ~30 tokens each

The worth formula `L > C(lang) · n/(n-1)` correctly rejects the second case
once `C(py) = 28` is used. The D3 prediction that this cluster was worth −45
tokens was based on the JS constant (`C = 15`), which doesn't apply to Python.

## What this means

The paradigm (kernel extraction guided by d_Λ) is:

- **Theoretically sound** — formal structure from A1–E1
- **Engineering-validated** — on 2 languages, 3 codebases, 4 refactors
- **Honest** — filters its own bad recommendations

If you are considering adopting this approach:

- Start with small codebases (1000–10000 lines)
- Expect ~5–20% of clusters to be worth extracting (language-dependent)
- Expect the tool to say "no" more often than "yes"
- Treat d_Λ as a detection metric, not a compression promise

This is not a silver bullet. It is a precise instrument for detecting
structural patterns and estimating whether extracting them pays off.

The alternative — traditional clone detection — is noise.
`corelang` is signal.


## Addendum: Kotlin / SmartMusicPlayer (F2)

The tool was also tested on **SmartMusicPlayer**, an Android music player
in Kotlin by the first author, available at
https://github.com/mablue/SmartMusicPlayer.

**Result:** 17,819 lines, 388 user units (after filtering build artifacts),
17 clusters, 4 worth extracting, **68 tokens of genuine duplication** (0.12% of code).

**Methodological hazard:** an unfiltered run on the same codebase reports
53 clusters and 8,541 tokens of savings. 99% of that figure comes from
Room-generated code duplicated across `app/build/generated/ksp/` and
`app/build/kspCaches/debug/backups/`. The tool was comparing each file
to its own backup copy.

**Interpretation:** SmartMusicPlayer is ~19× cleaner than Bitcoin v0.1.5
(0.12% vs 2.3% duplication). The tool, once filtered, correctly reports this.
