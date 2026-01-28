import itertools

def slist(num):
    return [x for x in range(num)]

# with python itertools
def _combinations(lst):
    return list(itertools.combinations(lst, 2))

for i in range(100):
    l = slist(i)
    print(f"list: {i} elements {len(l)**2:10} combinations: {len(_combinations(l))}")