"""Application: orchestrate kernel + middleware. No language knowledge."""

from pathlib import Path

from .kernel import js as kernel_js
from .kernel import py as kernel_py
from .kernel import cpp as kernel_cpp
from .middleware.distance import d_lambda, levenshtein, jaccard_bigrams
from .middleware.cluster import DSU, cluster_exact, cluster_fuzzy
from .middleware.worth import worth_extracting

def tokenize_js(source):    return kernel_js.tokenize(source)
def tokenize_py(source):    return kernel_py.tokenize(source)
def scan_js_units(source):  return kernel_js.scan_units(source)
def scan_py_units(source):  return kernel_py.scan_units(source)
def tokenize_cpp(source):   return kernel_cpp.tokenize(source)
def scan_cpp_units(source): return kernel_cpp.scan_units(source)

def analyze(path, lang, threshold=2):
    src = Path(path).read_text(encoding='utf-8', errors='replace')
    if lang == 'py':
        raw = scan_py_units(src)
    elif lang == 'cpp':
        raw = scan_cpp_units(src)
    else:
        raw = scan_js_units(src)
    n_total = len(src)

    units = []
    for u in raw:
        if lang == 'py':
            tk = tokenize_py
        elif lang == 'cpp':
            tk = tokenize_cpp
        else:
            tk = tokenize_js
        toks = tk(u['body'])
        if not toks: continue
        if u['end'] - u['start'] > 0.8 * n_total: continue
        units.append({'name': u['name'], 'tokens': toks, 'length': len(toks)})

    clusters, pc, pm = cluster_exact(units, lang, threshold=threshold)

    cluster_list = []
    for root, members in clusters.items():
        n = len(members)
        avg = sum(units[m]['length'] for m in members) / n
        orig = int(round(avg * n))
        new = int(avg) + 15 * n
        delta = new - orig
        worth = worth_extracting(avg, n, lang)
        cluster_list.append({
            'members': [units[m]['name'] for m in members],
            'size': n,
            'avg_length': round(avg, 1),
            'orig_tokens': orig,
            'projected_new_tokens': new,
            'projected_delta': delta,
            'worth_extracting': worth,
        })
    cluster_list.sort(key=lambda c: (-c['size'], -c['avg_length']))

    return {
        'file': str(path), 'language': lang, 'file_bytes': n_total,
        'units_raw': len(raw), 'units_count': len(units),
        'total_tokens': sum(u['length'] for u in units),
        'pairs_compared': pc, 'pairs_matched': pm,
        'threshold': threshold, 'clusters_found': len(cluster_list),
        'worth_extracting': sum(1 for c in cluster_list if c['worth_extracting']),
        'potential_savings': sum(-c['projected_delta'] for c in cluster_list
                                  if c['worth_extracting'] and c['projected_delta'] < 0),
        'clusters': cluster_list,
    }
