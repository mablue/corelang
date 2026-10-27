"""Pure Python tokenizer and unit scanner."""

import ast
import io
import tokenize as pytok

KW = {
    'False','None','True','and','as','assert','async','await','break',
    'class','continue','def','del','elif','else','except','finally','for',
    'from','global','if','import','in','is','lambda','nonlocal','not','or',
    'pass','raise','return','try','while','with','yield',
}

def tokenize(source):
    out = []
    try:
        for t in pytok.generate_tokens(io.StringIO(source).readline):
            if t.type == pytok.NAME:
                out.append(('KW' if t.string in KW else 'ID', t.string))
            elif t.type == pytok.NUMBER:
                out.append(('NUM', t.string))
            elif t.type == pytok.STRING:
                out.append(('STR', t.string))
            elif t.type == pytok.OP:
                out.append(('SYM', t.string))
    except (pytok.TokenError, IndentationError):
        pass
    return out

def scan_units(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    lines = source.splitlines()
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                start = node.lineno - 1
                end = node.end_lineno
                body = '\n'.join(lines[start:end])
                out.append({'name': node.name, 'body': body,
                            'start': start, 'end': end})
            except Exception:
                pass
    return out
