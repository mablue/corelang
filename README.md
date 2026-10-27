# corelang

**Structural code analysis via semantic distance d_Lambda.**

Three-layer architecture (kernel, middleware, application), validated on
JavaScript, Python, C, and C++ across Backbone.js 0.1.0, Bottle.py 0.13,
and Bitcoin v0.1.5.

## Paper

- paper/corelang.pdf -- the full academic paper (18+ pages)
- paper/main.typ -- Typst source
- paper/references.bib -- 29 references

## Quick start

    pip install -e .
    corelang path/to/file.js
    corelang path/to/file.py

## Results

| Codebase       | Lang | LoC    | Units | Clusters | Worth |
|----------------|------|--------|-------|----------|-------|
| Backbone 0.1.0 | JS   | 618    | 53    | 3        | 1     |
| Bottle 0.13    | PY   | 4,675  | 367   | 15       | 4     |
| Bitcoin 0.1.5  | C++  | 19,901 | 1,002 | 75       | 23    |

The worth criterion correctly rejects 117 empty MFC stubs and the 5 Bottle
HTTP verbs (Python's adapter cost makes extraction uneconomical).

## License

MIT.
