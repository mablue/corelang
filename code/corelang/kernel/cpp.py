"""Pure C/C++ tokenizer and unit scanner.

The kernel knows ONLY syntax: strings, comments, braces, keywords.
It does NOT know what a function call means, what `.` means, or what
to infer. All semantic interpretation lives in middleware/.
"""

KW = {
    # C++11/14 keywords (harmless if unused in v0.1.5)
    'alignas','alignof','and','and_eq','asm','auto','bitand','bitor',
    'bool','break','case','catch','char','char16_t','char32_t','class',
    'compl','const','constexpr','const_cast','continue','decltype',
    'default','delete','do','double','dynamic_cast','else','enum',
    'explicit','export','extern','false','float','for','friend','goto',
    'if','inline','int','long','mutable','namespace','new','noexcept',
    'not','not_eq','nullptr','operator','or','or_eq','private','protected',
    'public','register','reinterpret_cast','return','short','signed',
    'sizeof','static','static_assert','static_cast','struct','switch',
    'template','this','thread_local','throw','true','try','typedef',
    'typeid','typename','union','unsigned','using','virtual','void',
    'volatile','wchar_t','while','xor','xor_eq',
}

SYM = sorted([
    '>>=', '<<=', '->*', '...',
    '<<', '>>', '<=', '>=', '==', '!=', '&&', '||', '++', '--',
    '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=',
    '->', '::',
    '{', '}', '(', ')', '[', ']', ';', ',', '.', ':',
    '+', '-', '*', '/', '%', '=', '<', '>', '&', '|', '^', '~', '!', '?',
], key=len, reverse=True)

# Keywords that cannot be function names (their `(...)` is control flow)
_CONTROL = {'if', 'while', 'for', 'switch', 'catch', 'do', 'return',
            'sizeof', 'new', 'delete', 'throw', 'not', 'and', 'or'}


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
    while i + 1 < len(s) and not (s[i] == '*' and s[i+1] == '/'): i += 1
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


def tokenize(source):
    """Token stream: list of (type, value).

    Preprocessor lines (`# ...`) are skipped entirely.
    """
    i, L, out = 0, len(source), []
    while i < L:
        c = source[i]
        if c.isspace(): i += 1; continue
        # Preprocessor directive
        if c == '#' and (i == 0 or source[i-1] == '\n'):
            i = _skip_line(source, i); continue
        if c == '/' and i+1 < L and source[i+1] == '/':
            while i < L and source[i] != '\n': i += 1
            continue
        if c == '/' and i+1 < L and source[i+1] == '*':
            i += 2
            while i+1 < L and not (source[i]=='*' and source[i+1]=='/'): i += 1
            i += 2; continue
        if c in '"\'':
            q = c; i += 1; start = i
            while i < L:
                if source[i] == '\\': i += 2; continue
                if source[i] == q: break
                i += 1
            out.append(('STR', source[start:i])); i += 1; continue
        if c.isdigit() or (c == '.' and i+1 < L and source[i+1].isdigit()):
            j = i
            if source[i:i+2].lower() in ('0x', '0b'):
                j = i + 2
                while j < L and (source[j].isalnum() or source[j] == '_'): j += 1
            else:
                while j < L and (source[j].isalnum() or source[j] in '._'): j += 1
            # numeric suffix (u, l, f, ul, etc.)
            while j < L and source[j] in 'ulfULF': j += 1
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


def scan_units(source):
    """Extract function-level units from C/C++ source.

    Heuristic: find `(` ... `)`, then look ahead for `{` (skipping
    modifiers like const/noexcept and initializer lists). The identifier
    chain before `(` (e.g. `Foo::bar`) is the function name.

    Works for v0.1.5 style code (no lambdas, no nested named functions).
    Operator overloads (`operator+`) are skipped.
    """
    out = []
    i, n = 0, len(source)
    while i < n:
        c = source[i]
        if c in '"\'':
            i = _skip_string(source, i); continue
        if c == '/' and i+1 < n:
            if source[i+1] == '/': i = _skip_line(source, i); continue
            if source[i+1] == '*': i = _skip_block(source, i); continue
        if c == '#' and (i == 0 or source[i-1] == '\n'):
            i = _skip_line(source, i); continue
        if c != '(':
            i += 1; continue
        close = _match_paren(source, i)
        if close <= i:
            i += 1; continue
        # Look ahead for `{`
        j = close
        lookahead_end = min(n, close + 2000)
        found_body = False
        while j < lookahead_end:
            c2 = source[j]
            if c2.isspace(): j += 1; continue
            if c2 == '{':
                found_body = True; break
            if c2 == ';':
                break  # declaration only
            if c2 in '"\'':
                j = _skip_string(source, j); continue
            if c2 == '/' and j+1 < n:
                if source[j+1] == '/': j = _skip_line(source, j); continue
                if source[j+1] == '*': j = _skip_block(source, j); continue
            j += 1
        if not found_body:
            i = close; continue
        end = _match_brace(source, j)
        if end <= j:
            i = close; continue
        # Extract name before `(`
        start = i
        while start > 0 and source[start-1].isspace(): start -= 1
        name_end = start
        while start > 0 and (source[start-1].isalnum() or source[start-1] in '_:'):
            start -= 1
        if start > 0 and source[start-1] == '~':
            start -= 1
        name = source[start:name_end]
        last_part = name.split('::')[-1] if name else ''
        if name and last_part not in _CONTROL:
            out.append({'name': name, 'body': source[start:end],
                        'start': start, 'end': end})
        i = end
    return out
