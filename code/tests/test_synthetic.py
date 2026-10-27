"""Synthetic tests from C2, translated to pytest.
Run: pytest ~/corelang/tests/test_synthetic.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / 'corelang' / 'pkg'))

from corelang.analyzer import tokenize_js, d_lambda

CASES = [
    # (name, fn_a, fn_b, expected_d_lambda)
    ('identity',     'function(x){ return x + 1; }',
                     'function(x){ return x + 1; }', 0),
    ('alpha_rename', 'function(x){ return x + 1; }',
                     'function(y){ return y + 1; }', 0),
    ('alpha_in_idx', 'function(x){ return a[x]; }',
                     'function(y){ return a[y]; }', 0),
    ('operator',     'function(x){ return x + 1; }',
                     'function(x){ return x - 1; }', 1),
    ('num_literal',  'function(x){ return x + 1; }',
                     'function(x){ return x + 2; }', 1),
    ('str_literal',  "function(){ return 'a'; }",
                     "function(){ return 'b'; }", 1),
    ('field_access', 'function(x){ return this.a[x]; }',
                     'function(x){ return this.b[x]; }', 1),
    ('field+alpha',  'function(x){ return this.a[x]; }',
                     'function(y){ return this.b[y]; }', 1),
    ('two_fields',   'function(){ return this.a.b; }',
                     'function(){ return this.c.d; }', 2),
    ('method_name',  'function(){ return this._add(); }',
                     'function(){ return this._rm(); }', 1),
]

def test_d_lambda_synthetic():
    failures = []
    for name, a, b, expected in CASES:
        r = d_lambda(tokenize_js(a), tokenize_js(b), 'js')
        actual = r['d_lambda'] if r else None
        if actual != expected:
            failures.append(f'{name}: expected {expected}, got {actual}')
    assert not failures, '\n'.join(failures)

def test_function_name_is_semantic():
    """Regression test for E1 fix: def <name> is semantic, not alpha."""
    from corelang.analyzer import tokenize_py
    a = 'def get(self): return 1'
    b = 'def post(self): return 1'
    r = d_lambda(tokenize_py(a), tokenize_py(b), 'py')
    assert r['d_lambda'] == 1, f'expected 1, got {r["d_lambda"]}'
    assert r['alpha'] == 0, f'expected 0 alpha, got {r["alpha"]}'
