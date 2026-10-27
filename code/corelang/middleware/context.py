"""Context inference: alpha vs semantic classification."""

def infer_context(tokens, pos, lang):
    prev  = tokens[pos-1][1] if pos > 0 else None
    nxt   = tokens[pos+1][1] if pos+1 < len(tokens) else None
    prev2 = tokens[pos-2][1] if pos > 1 else None
    prev3 = tokens[pos-3][1] if pos > 2 else None

    if prev == '.':
        return 'field_access'
    if lang == 'js' and prev == 'function':
        return 'function_name'
    if lang == 'py' and prev == 'def':
        return 'function_name'

    if prev == '(' and prev2 in ('function', 'def'):
        return 'parameter_name'
    if prev == '(' and prev3 in ('function', 'def'):
        return 'parameter_name'

    if prev == ',':
        depth = 0
        for j in range(pos - 1, -1, -1):
            s = tokens[j][1]
            if s == ')':
                depth += 1
            elif s == '(':
                if depth == 0:
                    if j > 0 and tokens[j-1][1] in ('function', 'def'):
                        return 'parameter_name'
                    if j > 1 and tokens[j-2][1] in ('function', 'def'):
                        return 'parameter_name'
                    return 'call_argument'
                depth -= 1
        return 'unknown'

    if prev == '(' and nxt in (')', ','):
        return 'call_argument'
    if prev == '[' and nxt == ']':
        return 'index_key'

    # C++ specific heuristics (added in F1)
    if lang == 'cpp':
        if prev == '->':
            return 'field_access'
        if prev == '::':
            return 'function_name'      # class::member
        if nxt == '::':
            return 'function_name'      # class/namespace qualifier
        if nxt == '(':
            return 'function_name'      # function/method call
        return 'alpha_local'            # local variable, parameter, type

    # Kotlin specific heuristics (added in F2)
    if lang == 'kotlin':
        if prev in ('.', '?.'):
            return 'field_access'
        if prev in ('fun', '::'):
            return 'function_name'
        if prev in ('class', 'object', 'interface', 'typealias'):
            return 'function_name'
        if prev == '@':
            return 'function_name'
        if prev in ('val', 'var'):
            return 'alpha_local'
        if nxt == '(':
            return 'function_name'
        if nxt == '::':
            return 'function_name'
        return 'alpha_local'

    return 'unknown'
