#!/usr/bin/env python3
"""corelang analyzer — language-agnostic structural analysis."""
import sys, json, hashlib, io, tokenize as pytok, ast
from pathlib import Path
from collections import defaultdict

PY_KW = {'False','None','True','and','as','assert','async','await','break',
    'class','continue','def','del','elif','else','except','finally','for',
    'from','global','if','import','in','is','lambda','nonlocal','not','or',
    'pass','raise','return','try','while','with','yield'}
JS_KW = {'if','else','for','while','do','switch','case','default','break',
    'continue','return','throw','try','catch','finally','var','function',
    'new','delete','typeof','instanceof','in','of','this','true','false',
    'null','undefined','void','with'}
JS_SYM = sorted(['>>>=','===','!==','>>>','<<=','>>=','==','!=','<=','>=',
    '&&','||','++','--','+=','-=','*=','/=','%=','&=','|=','^=','<<','>>',
    '{','}','(',')','[',']',';',',','.',':','+','-','*','/','%','=','<','>',
    '&','|','^','~','!','?'], key=len, reverse=True)

# ─── Python tokenizer ────────────────────────────────────
def tokenize_py(text):
    toks = []
    try:
        for t in pytok.generate_tokens(io.StringIO(text).readline):
            if t.type == pytok.NAME:
                toks.append(('KW' if t.string in PY_KW else 'ID', t.string))
            elif t.type == pytok.NUMBER:
                toks.append(('NUM', t.string))
            elif t.type == pytok.STRING:
                toks.append(('STR', t.string))
            elif t.type == pytok.OP:
                toks.append(('SYM', t.string))
    except (pytok.TokenError, IndentationError):
        pass
    return toks

# ─── JS tokenizer (from B2) ──────────────────────────────
def tokenize_js(text):
    i, L, out = 0, len(text), []
    while i < L:
        c = text[i]
        if c.isspace(): i += 1; continue
        if c == '/' and i+1 < L and text[i+1] == '/':
            while i < L and text[i] != '\n': i += 1
            continue
        if c == '/' and i+1 < L and text[i+1] == '*':
            i += 2
            while i+1 < L and not (text[i]=='*' and text[i+1]=='/'): i += 1
            i += 2; continue
        if c in '"\'':
            q = c; i += 1; start = i
            while i < L:
                if text[i] == '\\': i += 2; continue
                if text[i] == q: break
                i += 1
            out.append(('STR', text[start:i])); i += 1; continue
        if c.isdigit() or (c == '.' and i+1 < L and text[i+1].isdigit()):
            j = i
            while j < L and (text[j].isalnum() or text[j] in '._'): j += 1
            out.append(('NUM', text[i:j])); i = j; continue
        if c.isalpha() or c in '_$':
            j = i
            while j < L and (text[j].isalnum() or text[j] in '_$'): j += 1
            w = text[i:j]
            out.append(('KW', w) if w in JS_KW else ('ID', w))
            i = j; continue
        for s in JS_SYM:
            if text.startswith(s, i):
                out.append(('SYM', s)); i += len(s); break
        else:
            out.append(('UNK', c)); i += 1
    return out

# ─── Python unit extraction via ast ──────────────────────
def scan_py_units(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines = src.splitlines()
    units = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                start = node.lineno - 1
                end = node.end_lineno
                body = '\n'.join(lines[start:end])
                units.append({'name': node.name, 'body': body,
                              'start': start, 'end': end})
            except Exception:
                pass
    return units

# ─── JS unit extraction ──────────────────────────────────
def _skip_string(s, i):
    q = s[i]; i += 1
    while i < len(s):
        if s[i] == '\\': i += 2; continue
        if s[i] == q: return i + 1
        i += 1
    return i
def _skip_line(s, i):
    while i < len(s) and s[i] != '\n': i += 1
    return i
def _skip_block(s, i):
    i += 2
    while i + 1 < len(s) and not (s[i]=='*' and s[i+1]=='/'): i += 1
    return i + 2
def _match_paren(s, i):
    d = 0
    while i < len(s):
        c = s[i]
        if c in '"\'':
            i = _skip_string(s, i); continue
        if c == '/' and i+1 < len(s):
            if s[i+1] == '/': i = _skip_line(s, i); continue
            if s[i+1] == '*': i = _skip_block(s, i); continue
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return i + 1
        i += 1
    return i
def _match_brace(s, i):
    d = 0
    while i < len(s):
        c = s[i]
        if c in '"\'':
            i = _skip_string(s, i); continue
        if c == '/' and i+1 < len(s):
            if s[i+1] == '/': i = _skip_line(s, i); continue
            if s[i+1] == '*': i = _skip_block(s, i); continue
        if c == '{': d += 1
        elif c == '}':
            d -= 1
            if d == 0: return i + 1
        i += 1
    return i
def scan_js_units(src):
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in '"\'':
            i = _skip_string(src, i); continue
        if c == '/' and i+1 < n:
            if src[i+1] == '/': i = _skip_line(src, i); continue
            if src[i+1] == '*': i = _skip_block(src, i); continue
        if src.startswith('function', i):
            prev_ok = i == 0 or not (src[i-1].isalnum() or src[i-1] in '_$')
            next_ok = i+8 >= n or not (src[i+8].isalnum() or src[i+8] in '_$')
            if prev_ok and next_ok:
                j = i + 8
                while j < n and src[j].isspace(): j += 1
                if j < n and (src[j].isalnum() or src[j] in '_$'):
                    while j < n and (src[j].isalnum() or src[j] in '_$'): j += 1
                    while j < n and src[j].isspace(): j += 1
                if j < n and src[j] == '(':
                    j = _match_paren(src, j)
                    while j < n and src[j].isspace(): j += 1
                    if j < n and src[j] == '{':
                        end = _match_brace(src, j)
                        out.append({'name': f'fn@{i}', 'body': src[i:end],
                                    'start': i, 'end': end})
                i += 8; continue
        i += 1
    return out

# ─── context + d_Λ ───────────────────────────────────────
def infer_context(toks, pos, lang):
    prev = toks[pos-1][1] if pos > 0 else None
    nxt  = toks[pos+1][1] if pos+1 < len(toks) else None
    prev2 = toks[pos-2][1] if pos > 1 else None
    prev3 = toks[pos-3][1] if pos > 2 else None
    if prev == '.': return 'field_access'
    if lang == 'js' and prev == 'function': return 'function_name'
    if lang == 'py' and prev == 'def': return 'function_name'
    # Parameter detection (must precede call_argument). Restored in E1-fix3.
    if prev == '(' and prev2 in ('function', 'def'): return 'parameter_name'
    if prev == '(' and prev3 in ('function', 'def'): return 'parameter_name'
    if prev == ',':
        depth = 0
        for j in range(pos - 1, -1, -1):
            s = toks[j][1]
            if s == ')': depth += 1
            elif s == '(':
                if depth == 0:
                    if j > 0 and toks[j-1][1] in ('function', 'def'):
                        return 'parameter_name'
                    if j > 1 and toks[j-2][1] in ('function', 'def'):
                        return 'parameter_name'
                    return 'call_argument'
                depth -= 1
        return 'unknown'
    if prev == '(' and nxt in (')', ','): return 'call_argument'
    if prev == '[' and nxt == ']': return 'index_key'
    return 'unknown'
def d_lambda(a, b, lang):
    if len(a) != len(b): return None
    id_groups = {}; other = 0
    for i in range(len(a)):
        ta, va = a[i]; tb, vb = b[i]
        if ta != tb: return None
        if va == vb: continue
        if ta == 'ID': id_groups.setdefault((va, vb), []).append(i)
        else: other += 1
    alpha = 0; sem = 0
    for (va, vb), poss in id_groups.items():
        ctxs = {infer_context(a, p, lang) for p in poss}
        if ctxs & {'field_access', 'function_name'}: sem += 1
        elif 'parameter_name' in ctxs: alpha += 1
        else: sem += 1
    sem += other
    return {'d_lambda': sem, 'alpha': alpha}

# ─── clustering ──────────────────────────────────────────
class DSU:
    def __init__(self, n): self.p = list(range(n)); self.r = [0]*n
    def find(self, x):
        while self.p[x] != x: self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        if self.r[ra] < self.r[rb]: ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]: self.r[ra] += 1

# ─── main analysis ───────────────────────────────────────
def analyze(path, lang, threshold=2):
    src = Path(path).read_text(encoding='utf-8', errors='replace')
    raw = scan_py_units(src) if lang == 'py' else scan_js_units(src)
    n_total = len(src)

    units = []
    for u in raw:
        body = u['body']
        toks = tokenize_py(body) if lang == 'py' else tokenize_js(body)
        if not toks: continue
        # skip wrapper: >80% of file
        if u['end'] - u['start'] > 0.8 * n_total: continue
        units.append({
            'name': u['name'],
            'body_sha': hashlib.sha256(body.encode()).hexdigest(),
            'tokens': toks,
            'length': len(toks),
        })

    # bucket by length
    by_len = defaultdict(list)
    for i, u in enumerate(units):
        by_len[u['length']].append(i)

    # pairwise d_Λ
    dsu = DSU(len(units))
    pairs_compared = 0
    pairs_matched = 0
    for L, idxs in by_len.items():
        if len(idxs) < 2: continue
        for i in range(len(idxs)):
            for j in range(i+1, len(idxs)):
                pairs_compared += 1
                a, b = idxs[i], idxs[j]
                r = d_lambda(units[a]['tokens'], units[b]['tokens'], lang)
                if r is None: continue
                if r['d_lambda'] <= threshold:
                    pairs_matched += 1
                    dsu.union(a, b)

    # clusters
    cmap = defaultdict(list)
    for i in range(len(units)):
        cmap[dsu.find(i)].append(i)

    clusters = []
    for root, members in cmap.items():
        if len(members) < 2: continue
        n = len(members)
        L = sum(units[m]['length'] for m in members) / n
        orig = int(round(L * n))
        new = int(L) + 15 * n
        delta = new - orig
        worth = L > 15 * n / (n - 1) if n > 1 else False
        clusters.append({
            'members': [units[m]['name'] for m in members],
            'size': n,
            'avg_length': round(L, 1),
            'orig_tokens': orig,
            'projected_new_tokens': new,
            'projected_delta': delta,
            'worth_extracting': worth,
        })
    clusters.sort(key=lambda c: (-c['size'], -c['avg_length']))

    return {
        'file': str(path),
        'language': lang,
        'file_bytes': n_total,
        'units_raw': len(raw),
        'units_count': len(units),
        'total_tokens': sum(u['length'] for u in units),
        'pairs_compared': pairs_compared,
        'pairs_matched': pairs_matched,
        'threshold': threshold,
        'clusters_found': len(clusters),
        'worth_extracting': sum(1 for c in clusters if c['worth_extracting']),
        'potential_savings': sum(-c['projected_delta'] for c in clusters
                                 if c['worth_extracting'] and c['projected_delta'] < 0),
        'clusters': clusters,
    }

if __name__ == '__main__':
    path = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else 'py'
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    result = analyze(path, lang, threshold)
    print(json.dumps(result, indent=2))
