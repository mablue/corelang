"""Pure Kotlin tokenizer and unit scanner. No semantics."""

KW = {
    'as', 'break', 'class', 'continue', 'do', 'else', 'false', 'for',
    'fun', 'if', 'in', 'interface', 'is', 'null', 'object', 'package',
    'return', 'super', 'this', 'throw', 'true', 'try', 'typealias',
    'typeof', 'val', 'var', 'when', 'while',
    'by', 'catch', 'constructor', 'delegate', 'dynamic', 'field', 'file',
    'finally', 'get', 'import', 'init', 'param', 'property', 'receiver',
    'set', 'setparam', 'where',
    'actual', 'abstract', 'annotation', 'companion', 'const', 'crossinline',
    'data', 'enum', 'expect', 'external', 'final', 'infix', 'inline',
    'inner', 'internal', 'lateinit', 'noinline', 'open', 'operator', 'out',
    'override', 'private', 'protected', 'public', 'reified', 'sealed',
    'suspend', 'tailrec', 'vararg',
}

SYM = sorted([
    '!==', '===', '..<', '?:', '?.', '->', '::', '!!', '..',
    '<=', '>=', '==', '!=', '&&', '||', '++', '--',
    '+=', '-=', '*=', '/=', '%=',
    '{', '}', '(', ')', '[', ']', ';', ',', '.', ':',
    '+', '-', '*', '/', '%', '=', '<', '>', '&', '|', '^', '~', '!', '?', '@',
], key=len, reverse=True)


def _skip_line(s, i):
    while i < len(s) and s[i] != '\n': i += 1
    return i


def _skip_block(s, i):
    i += 2
    while i + 1 < len(s) and not (s[i] == '*' and s[i+1] == '/'): i += 1
    return i + 2


def _skip_string(s, i):
    q = s[i]; i += 1
    while i < len(s):
        if s[i] == '\\': i += 2; continue
        if s[i] == q: return i + 1
        i += 1
    return i


def _skip_triple(s, i):
    i += 3
    while i + 2 < len(s):
        if s[i] == '"' and s[i+1] == '"' and s[i+2] == '"': return i + 3
        i += 1
    return len(s)


def _match_paren(s, i):
    d = 0
    while i < len(s):
        c = s[i]
        if s[i:i+3] == '"""':
            i = _skip_triple(s, i); continue
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
        if s[i:i+3] == '"""':
            i = _skip_triple(s, i); continue
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


def tokenize(source):
    i, L, out = 0, len(source), []
    while i < L:
        c = source[i]
        if c.isspace(): i += 1; continue
        if c == '/' and i+1 < L and source[i+1] == '/':
            while i < L and source[i] != '\n': i += 1
            continue
        if c == '/' and i+1 < L and source[i+1] == '*':
            i += 2
            while i+1 < L and not (source[i]=='*' and source[i+1]=='/'): i += 1
            i += 2; continue
        if source[i:i+3] == '"""':
            i += 3; start = i
            while i+2 < L:
                if source[i] == '"' and source[i+1] == '"' and source[i+2] == '"': break
                i += 1
            out.append(('STR', source[start:i])); i += 3; continue
        if c == '"':
            i += 1; start = i
            while i < L:
                if source[i] == '\\': i += 2; continue
                if source[i] == '"': break
                i += 1
            out.append(('STR', source[start:i])); i += 1; continue
        if c == "'":
            i += 1
            while i < L:
                if source[i] == '\\': i += 2; continue
                if source[i] == "'": break
                i += 1
            out.append(('STR', "'c'")); i += 1; continue
        if c.isdigit() or (c == '.' and i+1 < L and source[i+1].isdigit()):
            j = i
            if source[i:i+2].lower() in ('0x', '0b'):
                j = i + 2
                while j < L and (source[j].isalnum() or source[j] == '_'): j += 1
            else:
                while j < L and (source[j].isdigit() or source[j] in '._eE'): j += 1
            while j < L and source[j] in 'fFLlDd': j += 1
            out.append(('NUM', source[i:j])); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < L and (source[j].isalnum() or source[j] == '_'): j += 1
            w = source[i:j]
            out.append(('KW', w) if w in KW else ('ID', w))
            i = j; continue
        for sym in SYM:
            if source.startswith(sym, i):
                out.append(('SYM', sym)); i += len(sym); break
        else:
            out.append(('UNK', c)); i += 1
    return out


def _try_parse_function(source, fun_pos):
    n = len(source)
    j = fun_pos + 3
    while j < n and source[j].isspace(): j += 1
    if j < n and source[j] == '<':
        depth = 0
        while j < n:
            if source[j] == '<': depth += 1
            elif source[j] == '>':
                depth -= 1
                if depth == 0:
                    j += 1; break
            j += 1
        while j < n and source[j].isspace(): j += 1
    name_start = j
    while j < n and (source[j].isalnum() or source[j] == '_'): j += 1
    if j == name_start: return None
    while j < n and source[j] == '.':
        j += 1
        while j < n and (source[j].isalnum() or source[j] == '_'): j += 1
    name_end = j
    while j < n and source[j].isspace(): j += 1
    if j >= n or source[j] != '(': return None
    close = _match_paren(source, j)
    if close <= j: return None
    k = close
    lookahead = min(n, close + 1000)
    while k < lookahead:
        c = source[k]
        if c.isspace(): k += 1; continue
        if source[k:k+3] == '"""':
            k = _skip_triple(source, k); continue
        if c in '"\'':
            k = _skip_string(source, k); continue
        if c == '/' and k+1 < n:
            if source[k+1] == '/': k = _skip_line(source, k); continue
            if source[k+1] == '*': k = _skip_block(source, k); continue
        if c == '{':
            end = _match_brace(source, k)
            name = source[name_start:name_end]
            return ({'name': name, 'body': source[name_start:end],
                     'start': name_start, 'end': end}, end)
        if c == '=':
            k += 1; depth = 0
            while k < n:
                ch = source[k]
                if source[k:k+3] == '"""':
                    k = _skip_triple(source, k); continue
                if ch in '"\'':
                    k = _skip_string(source, k); continue
                if ch in '([{': depth += 1
                elif ch in ')]}':
                    if depth == 0: break
                    depth -= 1
                elif ch == '\n' and depth == 0:
                    k2 = k + 1
                    while k2 < n and source[k2].isspace(): k2 += 1
                    if not (k2 < n and source[k2] in '.+-*/%?:&|!<>=,'):
                        break
                k += 1
            name = source[name_start:name_end]
            return ({'name': name, 'body': source[name_start:k],
                     'start': name_start, 'end': k}, k)
        if c == ';': break
        k += 1
    return None


def scan_units(source):
    out = []
    i, n = 0, len(source)
    while i < n:
        c = source[i]
        if source[i:i+3] == '"""':
            i = _skip_triple(source, i); continue
        if c in '"\'':
            i = _skip_string(source, i); continue
        if c == '/' and i+1 < n:
            if source[i+1] == '/': i = _skip_line(source, i); continue
            if source[i+1] == '*': i = _skip_block(source, i); continue
        if source.startswith('fun', i):
            prev_ok = i == 0 or not (source[i-1].isalnum() or source[i-1] == '_')
            next_ok = i + 3 >= n or not (source[i+3].isalnum() or source[i+3] == '_')
            if prev_ok and next_ok:
                result = _try_parse_function(source, i)
                if result:
                    out.append(result[0]); i = result[1]; continue
        i += 1
    return out
