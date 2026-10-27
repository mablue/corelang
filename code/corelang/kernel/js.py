"""Pure JavaScript tokenizer and unit scanner. No semantic interpretation."""

KW = {
    'if','else','for','while','do','switch','case','default','break',
    'continue','return','throw','try','catch','finally','var','function',
    'new','delete','typeof','instanceof','in','of','this','true','false',
    'null','undefined','void','with',
}
SYM = sorted([
    '>>>=','===','!==','>>>','<<=','>>=','==','!=','<=','>=','&&','||',
    '++','--','+=','-=','*=','/=','%=','&=','|=','^=','<<','>>',
    '{','}','(',')','[',']',';',',','.',':',
    '+','-','*','/','%','=','<','>','&','|','^','~','!','?',
], key=len, reverse=True)

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
        if c in '"\'':
            q = c; i += 1; start = i
            while i < L:
                if source[i] == '\\': i += 2; continue
                if source[i] == q: break
                i += 1
            out.append(('STR', source[start:i])); i += 1; continue
        if c.isdigit() or (c == '.' and i+1 < L and source[i+1].isdigit()):
            j = i
            while j < L and (source[j].isalnum() or source[j] in '._'): j += 1
            out.append(('NUM', source[i:j])); i = j; continue
        if c.isalpha() or c in '_$':
            j = i
            while j < L and (source[j].isalnum() or source[j] in '_$'): j += 1
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
    out, i, n = [], 0, len(source)
    while i < n:
        c = source[i]
        if c in '"\'':
            i = _skip_string(source, i); continue
        if c == '/' and i+1 < n:
            if source[i+1] == '/': i = _skip_line(source, i); continue
            if source[i+1] == '*': i = _skip_block(source, i); continue
        if source.startswith('function', i):
            prev_ok = i == 0 or not (source[i-1].isalnum() or source[i-1] in '_$')
            next_ok = i + 8 >= n or not (source[i+8].isalnum() or source[i+8] in '_$')
            if prev_ok and next_ok:
                j = i + 8
                while j < n and source[j].isspace(): j += 1
                if j < n and (source[j].isalnum() or source[j] in '_$'):
                    while j < n and (source[j].isalnum() or source[j] in '_$'): j += 1
                    while j < n and source[j].isspace(): j += 1
                if j < n and source[j] == '(':
                    j = _match_paren(source, j)
                    while j < n and source[j].isspace(): j += 1
                    if j < n and source[j] == '{':
                        end = _match_brace(source, j)
                        out.append({'name': f'fn@{i}', 'body': source[i:end],
                                    'start': i, 'end': end})
                i += 8; continue
        i += 1
    return out
