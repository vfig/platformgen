__all__ = ('contains_subsequence,')

def contains_subsequence(seq, subseq):
    for i in range(len(seq) - len(subseq)):
        if seq[i:i + len(subseq)] == subseq:
            return True
    return False
