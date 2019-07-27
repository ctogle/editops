# cython: language_level=3, boundscheck=False, wraparound=False
from numpy import int32
from numpy cimport ndarray


cdef str op_delete = 'delete'
cdef str op_insert = 'insert'
cdef str op_replace = 'replace'


cdef int [:, :] cost_matrix_c(str s, str t, int m, int n, int substitution_cost):
    """Compute the cost matrix to transform string s into string t"""
    cdef int i, j, x
    cdef int [:, :] cost = ndarray((m + 1, n + 1), dtype=int32)
    cost[0, 0] = 0
    for i in range(1, m + 1):
        cost[i, 0] = i
    for j in range(1, n + 1):
        cost[0, j] = j
    for j in range(1, n + 1):
        for i in range(1, m + 1):
            x = 0 if s[i - 1] == t[j - 1] else substitution_cost
            cost[i, j] = min(cost[i - 1, j]     + 1,
                             cost[i, j - 1]     + 1,
                             cost[i - 1, j - 1] + x)
    return cost


cdef list editops_c(str s, str t, int substitution_cost):
    """Compute an optimal set of edit operations to transform string s into string t"""
    # remove common prefix/suffix of s and t resulting in u and v
    cdef int i = len(s)
    cdef int j = len(t)
    cdef int offset = 0
    while (i > 0 and j > 0 and s[offset] == t[offset]):
        i -= 1
        j -= 1
        offset += 1
    while (i > 0 and j > 0 and s[i - 1 + offset] == t[j - 1 + offset]):
        i -= 1
        j -= 1
    cdef str u = s[offset:offset + i]
    cdef str v = t[offset:offset + j]
    # compute the cost matrix of transforming u to v
    cdef int [:, :] d = cost_matrix_c(u, v, i, j, substitution_cost)
    # decode the cost matrix into an optimal set of edit operations
    cdef int k = 0
    cdef list ops = []
    while i > 0 or j > 0:        
        if k < 0 and j > 0 and d[i, j] == d[i, j - 1] + 1:
            j -= 1
            k = -1
            ops.append((op_insert, i + offset, j + offset))
        elif k > 0 and i > 0 and d[i, j] == d[i - 1, j] + 1:
            i -= 1
            k = 1
            ops.append((op_delete, i + offset, j + offset))
        elif i > 0 and j > 0 and u[i - 1] == v[j - 1] and d[i, j] == d[i - 1, j - 1]:
            i -= 1
            j -= 1
            k = 0
        elif i > 0 and j > 0 and d[i, j] == d[i - 1, j - 1] + substitution_cost:
            i -= 1
            j -= 1
            k = 0
            ops.append((op_replace, i + offset, j + offset))
        elif j > 0 and d[i, j] == d[i, j - 1] + 1:
            j -= 1
            k = -1
            ops.append((op_insert, i + offset, j + offset))
        elif i > 0 and d[i, j] == d[i - 1, j] + 1:
            i -= 1
            k = 1
            ops.append((op_delete, i + offset, j + offset))
    ops.reverse()
    return ops


cpdef editops(str s, str t, int substitution_cost=1):
    """Exposed python wrapper for editops_c"""
    return editops_c(s, t, substitution_cost)


cpdef editdistance(str s, str t, int substitution_cost=1):
    """Exposed python wrapper to compute cost matrix and return edit distance"""
    # remove common prefix/suffix of s and t resulting in u and v
    cdef int i = len(s)
    cdef int j = len(t)
    cdef int offset = 0
    while (i > 0 and j > 0 and s[offset] == t[offset]):
        i -= 1
        j -= 1
        offset += 1
    while (i > 0 and j > 0 and s[i - 1 + offset] == t[j - 1 + offset]):
        i -= 1
        j -= 1
    cdef str u = s[offset:offset + i]
    cdef str v = t[offset:offset + j]
    # compute the cost matrix of transforming u to v
    cdef int [:, :] d = cost_matrix_c(u, v, i, j, substitution_cost)
    # edit distance is the bottom right corner of the cost matrix (no need to decode)
    return d[i, j]
