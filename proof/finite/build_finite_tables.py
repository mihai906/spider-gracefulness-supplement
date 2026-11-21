#!/usr/bin/env python3
"""Print and independently verify the finite bases used by the manuscripts."""
from hashlib import sha256
from itertools import combinations_with_replacement
from pathlib import Path
import json
import sys
HERE=Path(__file__).resolve().parent
DATA=HERE/'data'

def verify(paths,hub=0,cut=None):
    n=sum(map(len,paths));values=[hub]+sum(paths,[]);colors=[]
    assert sorted(values)==list(range(n+1))
    for path in paths:
        old=hub
        for value in path:
            colors.append(abs(value-old))
            if cut is not None:assert (value<=cut)!=(old<=cut)
            old=value
    assert sorted(colors)==list(range(1,n+1))
    return n

def words(row):
    out=[];at=0
    for length in row['order']:
        out.append(row['labels'][at:at+length]);at+=length
    assert at==len(row['labels'])
    assert sorted(map(len,out))==row['arms']
    return out

def word(values):return '('+',\\allowbreak '.join(map(str,values))+')'
def profile(values):return '('+','.join(map(str,values))+')'
def paths_cell(paths):return r'\(\begin{array}{l}'+r'\\'.join(word(p) for p in paths)+r'\end{array}\)'
def table_begin(columns,head,caption,label):
    n=len(columns);gaps=r'@{\hspace{.02\linewidth}}'
    spec='@{}'+gaps.join('p{'+str(w)+r'\linewidth}' for w in columns)+'@{}'
    return [r'\small',r'\begin{longtable}{'+spec+'}',r'\caption{'+caption+r'}\label{'+label+r'}\\',
       r'\toprule',head+r'\\\midrule',r'\endfirsthead',
       r'\toprule',head+r'\\\midrule',r'\endhead',
       r'\midrule\multicolumn{'+str(n)+r'}{r}{\footnotesize Continued on the next page}\\\endfoot',
       r'\bottomrule\endlastfoot']
def table_end():return [r'\end{longtable}',r'\normalsize']

def main():
    seven_name='seven_closure_finite_base_792.jsonl'
    four_name='seven_closure_hubzero4_all_m6.jsonl'
    seven=[json.loads(s) for s in (DATA/seven_name).read_text().splitlines()]
    seven=[r for r in seven if min(r['arms'])>=2]
    assert len(seven)==330
    assert {tuple(r['arms']) for r in seven}==set(combinations_with_replacement(range(2,7),7))
    alpha={};hub={};splits=[];direct=[]
    for row in seven:
        pp=words(row);verify(pp,row['hub'])
        if row['construction']=='explicit direct rooted certificate':
            assert row['hub']==0;direct.append(row);continue
        assert row['construction']=='reverse-alpha plus hub-zero amalgamation'
        g,h=pp[:3],pp[3:];ng=sum(map(len,g));nh=sum(map(len,h))
        k=sum(len(p)//2 for p in g);assert k==row['hub']
        gg=[[k-v if v<=k else ng+k+nh+1-v for v in p] for p in g]
        hh=[[v-k for v in p] for p in h]
        verify(gg,cut=k);verify(hh)
        gg.sort(key=len);hh.sort(key=len)
        akey=tuple(map(len,gg));hkey=tuple(map(len,hh))
        assert sorted(akey)==sorted(row['alpha_arms'])
        assert sorted(hkey)==sorted(row['hubzero_arms'])
        alpha.setdefault(akey,gg);hub.setdefault(hkey,hh)
        splits.append((tuple(row['arms']),akey,hkey))
    assert len(direct)==19 and len(splits)==311 and len(alpha)==24 and len(hub)==70
    four=[json.loads(s) for s in (DATA/four_name).read_text().splitlines()]
    four=[r for r in four if min(r['arms'])>=2]
    assert len(four)==70
    assert {tuple(r['arms']) for r in four}==set(combinations_with_replacement(range(2,7),4))
    for row in four:
        pp=words(row);pp.sort(key=len);verify(pp,row.get('hub',0))
        hub[tuple(row['arms'])]=pp
    ak={key:i+1 for i,key in enumerate(sorted(alpha))}
    hk={key:i+1 for i,key in enumerate(sorted(hub))}
    for prof,a,b in splits:
        assert sorted(a+b)==list(prof)
        # Rebuild every claimed decomposition using the exact bases printed
        # below, rather than relying on the original seven-arm labeling.
        gg=alpha[a];hh=hub[b];ng=sum(a);nh=sum(b);k=sum(x//2 for x in a)
        joined=[[k-v if v<=k else ng+k+nh+1-v for v in p] for p in gg]
        joined += [[v+k for v in p] for p in hh]
        verify(joined,k)
    out=[r'\chapter{Explicit finite construction certificates}\label{app:finite-bases}',
        r'All words below run outward from a common hub of label zero, unless a different hub is stated. Lengths count edges. A semicolon separates arms; it is not an additional vertex. Every printed labeling is checked by the elementary inventory algorithm of Appendix~\ref{app:template-certificates}.',
        r'\section{Small root-zero alpha bases}\label{app:small-finite-alpha}',
        r'These 24 bases suffice for every alpha component in the 311 seven-core decompositions. They also contain the 23 small positive alpha profiles required in the short-arm case analysis. The cut is the sum of the half-lengths. The printed words themselves, rather than an existence inference from bounded searching, are finite proof inputs.']
    out+=table_begin([.10,.24,.10,.50],r'ID & Lengths & Cut & Arm words',
        'Literal root-zero alpha labelings used by the small-core proof.','tab:finite-alpha')
    for key in sorted(alpha):
        out.append(r'\(A_{'+str(ak[key])+r'}\) & \('+profile(key)+r'\) & \('+str(sum(x//2 for x in key))+r'\) & '+paths_cell(alpha[key])+r'\\[.5em]')
    out+=table_end()
    out += [r'\section{Four-arm hub-zero bases}\label{app:four-finite-hubzero}',
        r'The following table covers exactly the 70 sorted four-tuples in $\{2,3,4,5,6\}$. A four-arm spider with a unit arm is obtained by appending a unit leaf to a hub-zero three-arm spider, so no additional finite table with a unit entry is needed.']
    out+=table_begin([.10,.24,.62],r'ID & Lengths & Arm words',
        'Complete hub-zero four-arm catalog for nonunit lengths at most six.','tab:finite-four')
    for key in sorted(hub):
        out.append(r'\(H_{'+str(hk[key])+r'}\) & \('+profile(key)+r'\) & '+paths_cell(hub[key])+r'\\[.5em]')
    out+=table_end()
    out += [r'\ifSevenVolume',r'\section{The 311 alpha/hub-zero decompositions}\label{app:seven-finite-decompositions}',
        r'For each row, take the alpha basis $A_i$ and the hub-zero basis $H_j$ from the preceding tables. Their arm multisets combine to the displayed seven-tuple. Apply ordinary alpha amalgamation; add any unit arms to $H_j$ first. Thus each row proves an entire unbounded unit-arm family. Together with the next section these are exactly all $\binom{11}{7}=330$ sorted nonunit seven-tuples with maximum at most six.']
    out+=table_begin([.48,.15,.15,.16],r'Lengths & Alpha base & Hub-zero base & Final hub',
        'Complete small seven-core decomposition table.','tab:finite-seven')
    for prof,a,b in sorted(splits):
        out.append(r'\('+profile(prof)+r'\) & \(A_{'+str(ak[a])+r'}\) & \(H_{'+str(hk[b])+r'}\) & \('+str(sum(x//2 for x in a))+r'\)\\')
    out+=table_end()
    out += [r'\section{The 19 direct hub-zero cores}\label{app:seven-direct-finite}',
        r'These remaining profiles are not negative alpha assertions. The direct hub-zero words displayed here suffice, and arbitrary unit leaves receive successive new maximum labels.']
    out+=table_begin([.30,.68],r'Lengths & Arm words',
        'Direct hub-zero seven-core certificates.','tab:finite-direct-seven')
    for row in sorted(direct,key=lambda r:r['arms']):
        pp=words(row);pp.sort(key=len)
        out.append(r'\('+profile(row['arms'])+r'\) & '+paths_cell(pp)+r'\\[.5em]')
    out+=table_end();out+=[r'\fi']
    out_dir=Path(sys.argv[1]) if len(sys.argv)>1 else HERE
    (out_dir/'finite_tables.tex').write_text('\n'.join(out)+'\n')
    print(json.dumps(dict(status='all_printed_finite_bases_and_decompositions_verified',alpha_bases=24,
        hubzero_four_bases=70,seven_core_profiles=330,alpha_hubzero_decompositions=311,
        direct_hubzero_seven_cores=19),indent=2))

if __name__=='__main__':main()
