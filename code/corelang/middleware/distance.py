"""Distance metrics: Levenshtein, d_Λ, Jaccard."""

from .context import infer_context

def levenshtein(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(cur[-1] + 1, prev[j] + 1,
                           prev[j-1] + (0 if x == y else 1)))
        prev = cur
    return prev[-1]

def d_lambda(tokens_a, tokens_b, lang):
    if len(tokens_a) != len(tokens_b):
        return None
    id_groups, other = {}, 0
    for i in range(len(tokens_a)):
        ta, va = tokens_a[i]
        tb, vb = tokens_b[i]
        if ta != tb:
            return None
        if va == vb:
            continue
        if ta == 'ID':
            id_groups.setdefault((va, vb), []).append(i)
        else:
            other += 1
    alpha, sem = 0, 0
    for (va, vb), poss in id_groups.items():
        ctxs = {infer_context(tokens_a, p, lang) for p in poss}
        if ctxs & {'field_access', 'function_name'}:
            sem += 1
        elif ctxs & {'parameter_name', 'alpha_local'}:
            alpha += 1
        else:
            sem += 1
    sem += other
    return {'d_lambda': sem, 'alpha': alpha}

def jaccard_bigrams(a, b):
    if not a or not b:
        return 0.0
    sa = set(zip(a[:-1], a[1:]))
    sb = set(zip(b[:-1], b[1:]))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)
