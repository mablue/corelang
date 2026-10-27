"""Multi-layer normalization. Each layer semantically safe."""

def strip_separators(tokens):
    return [t for t in tokens if t[1] not in (';', ':')]

def remove_redundant_parens(tokens):
    result, i, n = [], 0, len(tokens)
    while i < n:
        if (i + 4 < n
            and tokens[i] == ('SYM', '(')
            and tokens[i+1] == ('SYM', '(')
            and tokens[i+3] == ('SYM', ')')
            and tokens[i+4] == ('SYM', ')')):
            result.append(tokens[i+2]); i += 5
        else:
            result.append(tokens[i]); i += 1
    return result

def canonicalize_comparisons(tokens):
    result, i, n = [], 0, len(tokens)
    SIMPLE = ('ID', 'NUM', 'STR')
    NO_CHAIN = ('<', '>', '<=', '>=', '==', '!=')
    while i < n:
        if (i + 2 < n
            and tokens[i+1][1] in ('>', '>=')
            and tokens[i][0] in SIMPLE
            and tokens[i+2][0] in SIMPLE
            and (i == 0 or tokens[i-1][1] not in NO_CHAIN)):
            new_op = '<' if tokens[i+1][1] == '>' else '<='
            result.extend([tokens[i+2], ('SYM', new_op), tokens[i]])
            i += 3
        else:
            result.append(tokens[i]); i += 1
    return result

def push_negations(tokens):
    INV = {'<': '>=', '>': '<=', '<=': '>', '>=': '<', '==': '!=', '!=': '=='}
    result, i, n = [], 0, len(tokens)
    SIMPLE = ('ID', 'NUM', 'STR')
    while i < n:
        if (i + 5 < n
            and tokens[i] == ('SYM', '!')
            and tokens[i+1] == ('SYM', '(')
            and tokens[i+3][1] in INV
            and tokens[i+5] == ('SYM', ')')
            and tokens[i+2][0] in SIMPLE
            and tokens[i+4][0] in SIMPLE):
            result.extend([tokens[i+2], ('SYM', INV[tokens[i+3][1]]), tokens[i+4]])
            i += 6
        else:
            result.append(tokens[i]); i += 1
    return result

def sort_commutative(tokens):
    SAFE = {'*', '&&', '||', '==', '!='}
    SIMPLE = ('ID', 'NUM', 'STR')
    result, i, n = [], 0, len(tokens)
    while i < n:
        if (i + 2 < n
            and tokens[i+1][1] in SAFE
            and tokens[i][0] in SIMPLE
            and tokens[i+2][0] in SIMPLE):
            a, b = tokens[i], tokens[i+2]
            if (a[0], a[1]) > (b[0], b[1]):
                a, b = b, a
            result.extend([a, tokens[i+1], b])
            i += 3
        else:
            result.append(tokens[i]); i += 1
    return result

def normalize(tokens):
    t = strip_separators(tokens)
    t = remove_redundant_parens(t)
    t = canonicalize_comparisons(t)
    t = push_negations(t)
    t = canonicalize_comparisons(t)
    t = sort_commutative(t)
    return t
