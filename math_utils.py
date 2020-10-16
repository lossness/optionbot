def percent_difference(a, b) -> int:
    '''
    Calculates the difference between prices. Always returns positive number.
    '''
    if a < b:
        result = int(((b - a) * 100) / a)
    else:
        result = int(((a - b) * 100) / b)
    return result