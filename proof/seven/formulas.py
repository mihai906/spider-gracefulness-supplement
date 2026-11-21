#!/usr/bin/env python3
"""Definition of the 128 seven-arm failure formulas (Article, eq. (4.2)).

For a parity word p in {0,1}^7, L_i = 2*q_i + p_i with q_i unbounded integers.
The formula asserts the ordered domain L_0 >= 6 and the failure of all fifteen
routes, using the ten alpha families of Article Table 1 and the four hub-zero
rules. The saved inputs in inputs/ were produced from query(p) with the
z3 Python API; the CPC proofs are bound to those saved files.

  python3 formulas.py 0110101     print the SMT-LIB formula for one parity word
"""
from functools import lru_cache
from itertools import combinations
import z3
ENABLED={'long', 'equal', 'EEE_repeat', 'EEO_central', 'OEE_repeat', 'OEE_central', 'EEE_central', 'EEO_near', 'EOO_central', 'OOO_central'}
OUTER=((0, 1, 2), (0, 1, 4), (0, 1, 6), (0, 2, 6), (0, 5, 6), (1, 2, 3), (1, 2, 4), (1, 4, 6), (2, 3, 4), (2, 3, 6), (2, 4, 5), (2, 5, 6), (3, 4, 5), (3, 4, 6), (4, 5, 6))

def alpha_rules(L,q,p,ids):
    a,b,c=(L[i] for i in ids)
    aa,bb,cc=(p[i] for i in ids)
    k=sum(q[i] for i in ids[:2])
    out={'equal':a==c, 'long':z3.And(c>2*k,c!=4*k+1)}
    if aa==bb==cc==1:
        out.update(OOO_central=c<=2*a-1, OOO_repeat=b==c)
    if aa==0 and bb==cc==1:
        out.update(EOO_central=c<=2*a+1, EOO_repeat=b==c)
    if aa==1 and bb==0 and cc==1:
        out['OEO_central']=c<=2*a-3
    if aa==bb==0 and cc==1:
        out.update(EEO_central=z3.And(a<b,c<=2*a-1),
                   EEO_near=z3.And(a==b,c==a+1))
    if aa==1 and bb==cc==0:
        out.update(OEE_central=z3.And(a<b,b<c,c<=2*a),
                   OEE_repeat=z3.And(a<b,b==c))
    if aa==bb==cc==0:
        out.update(EEE_central=z3.And(a<b,b<c,c<=2*a+2),
                   EEE_repeat=z3.And(b==c,b>=a+4))
    return out


def build(bits):
    q=z3.Ints('or0 or1 or2 or3 or4 or5 or6')
    L=tuple(2*x+p for x,p in zip(q,bits))
    def split(ids,n):
        for t in combinations(ids,n):yield t,tuple(i for i in ids if i not in t)
    def K(ids):return sum(q[i] for i in ids)
    @lru_cache(None)
    def A(ids):return z3.Or(*[v for n,v in alpha_rules(L,q,bits,ids).items() if n in ENABLED])
    @lru_cache(None)
    def H(ids):
        terms=[]
        for triple,single in split(ids,3):
            h=single[0]
            terms.extend([z3.And(A(triple),L[h]>K(triple)),
                          z3.And(L[triple[0]]==L[triple[2]],q[h]<L[triple[0]])])
        for pair,other in split(ids,2):
            i,j=other;y,z=L[i],L[j];k=K(pair)
            terms.extend([z3.And(q[j]<=k,k<=y-1,4*k!=4*y-z-3),z3.And(y==z,k<y)])
        return z3.Or(*terms)
    domain=z3.And(L[0]>=6,*[L[i]<=L[i+1] for i in range(6)])
    routes={t:z3.simplify(z3.And(A(t),H(rest))) for t,rest in split(tuple(range(7)),3)}
    return L,domain,routes


def query(bits):
    L,domain,routes=build(bits)
    formula=z3.simplify(z3.And(domain,*[z3.Not(routes[t]) for t in OUTER]))
    return z3.Ints('or0 or1 or2 or3 or4 or5 or6'),L,formula


if __name__ == '__main__':
    import sys
    bits = tuple(int(ch) for ch in sys.argv[1])
    assert len(bits) == 7 and set(bits) <= {0, 1}
    solver = z3.Solver()
    solver.add(query(bits)[2])
    print(solver.to_smt2())
