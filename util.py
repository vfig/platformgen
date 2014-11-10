__all__ = ('contains_subsequence,')

def contains_subsequence(seq, subseq):
    for i in range(len(seq) - len(subseq)):
        if seq[i:i + len(subseq)] == subseq:
            return True
    return False

def shortest_subsequence(seq, value):
    in_subseq = False
    subseq_len = 0
    subseq_len_min = len(seq) + 1
    for seq_value in seq:
        if seq_value == value:
            if in_subseq:
                subseq_len += 1
            else:
                in_subseq = True
                subseq_len = 1
        else:
            if in_subseq:
                in_subseq = False
                if subseq_len < subseq_len_min:
                    subseq_len_min = subseq_len
    if subseq_len_min == len(seq) + 1:
        return 0
    else:
        return subseq_len_min