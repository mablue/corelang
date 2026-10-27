"""Worth criterion: L > C * n/(n-1)."""

C_DEFAULT = 15

def worth_extracting(avg_length, size, lang=None, C=None):
    if size < 2: return False
    if C is None: C = C_DEFAULT
    return avg_length > C * size / (size - 1)

def project_savings(avg_length, size, lang=None, C=None):
    if C is None: C = C_DEFAULT
    return int(round((avg_length + C * size) - (avg_length * size)))
