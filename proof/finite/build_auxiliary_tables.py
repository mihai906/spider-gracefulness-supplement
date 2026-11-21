#!/usr/bin/env python3
"""Print and independently check every auxiliary finite construction word.

Only standard-library integer and list operations are used.
Usage: build_auxiliary_tables.py [output_directory]
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import ast
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE
INPUTS = {
    'minimum_two': 'data/seven_min2_complete_finite_bases.jsonl',
    'minimum_three_small': 'data/seven_general_min3_small_bases_verified.jsonl',
    'minimum_three_pinned': 'data/seven_general_min3_large_pinned_basis.jsonl',
    'minimum_four_remainder': 'data/seven_min4_finite_collected.jsonl',
    'minimum_four_five_small': 'data/seven_general_min45_small_bases.jsonl',
    'endpoint_paths': 'data/seven_min4_endpoint_kernels.json',
    'pair_four_offset_two': 'data/seven_hex_pair_four_offset2_finite.jsonl',
    'pair_four_offset_three': 'data/seven_hex_pair_four_offset3_finite.jsonl',
    'pair_five': 'data/seven_hex_pair_five_finite.jsonl',
    'equal_even': '../../data/affine/Esmall.json',
    'equal_odd_four': 'data/seven_general_extension_equal_four_odd_complete_small.jsonl',
    'offset_two_literal_source': 'data/offset_two_bases.json',
    'minimum_two_odd_rays': '../../data/affine/S2o.jsonl',
    'minimum_two_even_rays': '../../data/affine/S2e.jsonl',
    'minimum_four_rays': '../../data/affine/S4.jsonl',
}


def read_rows(key):
    return [json.loads(line) for line in (ROOT/INPUTS[key]).read_text().splitlines()]


def paths_of(item):
    arms = list(item['arms']); order = list(item.get('order', arms))
    assert sorted(order) == sorted(arms)
    flat = item['labels']; assert len(flat) == sum(order)
    paths = []; cursor = 0
    for length in order:
        paths.append(list(flat[cursor:cursor+length])); cursor += length
    assert cursor == len(flat)
    return paths


def check_spider(paths, hub=0, alpha=False, offset=None):
    assert all(path for path in paths)
    count = sum(map(len, paths)); flat = [x for path in paths for x in path]
    assert all(type(x) is int for x in [hub]+flat)
    if offset is None:
        assert sorted([hub]+flat) == list(range(count+1))
    else:
        assert hub == 0 and offset >= 0
        assert sorted(flat) == list(range(offset+1, offset+count+1))
    cut = sum(len(path)//2 for path in paths)
    colors = []
    for path in paths:
        previous = hub
        for depth, value in enumerate(path, 1):
            colors.append(abs(value-previous))
            if alpha:
                assert hub == 0 and (value > cut) == bool(depth%2)
            previous = value
    assert sorted(colors) == list(range(1,count+1))
    return count, cut


def check_permutation(word, first, alpha=False):
    count = len(word)
    assert word[0] == first and sorted(word) == list(range(count))
    assert sorted(abs(a-b) for a,b in zip(word,word[1:])) == list(range(1,count))
    if alpha:
        cut = (count-1)//2
        assert all((value<=cut) == (i%2==0) for i,value in enumerate(word))


def row_text(paths):
    def word(path):
        return '(' + r',\allowbreak '.join(map(str,path)) + ')'
    return r'{\ttfamily\footnotesize '+r'\par\smallskip '.join(word(path) for path in paths)+'}'


def table(title, label, items, heading='Complete outward words'):
    lines = [r'\section{'+title+'}',r'\label{'+label+'}',
             r'\begingroup\footnotesize',
             r'\begin{longtable}{@{}p{25mm}p{115mm}@{}}',
             'Profile / interface & '+heading+r'\\\hline\endhead']
    for profile, paths, detail in items:
        first = r'{\raggedright\arraybackslash '+profile+r'\par '+detail+'}'
        lines.append(first+' & '+row_text(paths)+r'\tabularnewline[5pt]')
    lines.extend([r'\end{longtable}',r'\endgroup',''])
    return '\n'.join(lines)


def profile_text(profile):
    return r'{\ttfamily\footnotesize ('+r',\allowbreak '.join(map(str,profile))+')}'


def main():
    tex = [r'\chapter{Auxiliary finite path and spider certificates}',
           r'\label{app:auxiliary-finite}',
           'All spider words below are read outward from hub zero. '
           'The word lengths, complete vertex and color inventories, alpha separation, '
           'and the stated controlled interfaces have been checked by the integer-only '
           'procedure of Section~\\ref{templates:finite-check}. '
           'A displayed alpha cut is the sum of the half-lengths. '
           'For an offset record the nonroot interval is $[k+1,k+N]$, not $[1,N]$. '
           'The builder \\file{proof/finite/build_auxiliary_tables.py} rechecks every word '
           'and the equality of every catalog with its required finite domain.']
    summaries = {}; total_colors = 0; inputs = set(INPUTS.values())
    rays2 = read_rows('minimum_two_odd_rays')+read_rows('minimum_two_even_rays')
    rays4 = read_rows('minimum_four_rays')
    expected2 = {(2,3,9),(2,4,13)}
    expected3p = {(2,18,18)}; protected_changes = []
    for cert in rays2:
        r,d = cert['residue'],cert['delta']; v = cert['verification']
        h = v['h_min']; bound = 8*h+r; assert bound == v['b_min']
        for b in range(5 if r%2 else 6,bound):
            if b%8 == r:expected2.add((2,b,b+d))
        assert all(e['arm'] != 0 for e in cert['remove'])
        hp = h
        for edge in cert['remove']:
            if edge['arm'] == 1:
                a,c = edge['depth']; assert a>0
                hp = max(hp,(10-c+a-1)//a)
        if hp != h:protected_changes.append([r,d,bound,8*hp+r])
        for b in range(18,8*hp+r):
            if b%8 == r:expected3p.add((2,b,b+d))
    assert protected_changes == [[5,1,21,29]]
    expected3s = {(3,b,c) for b in range(3,18)
                  for c in list(range(b,b+(2 if b%2 else 3)))+[4*(1+b//2)+1] if c>=7}
    expected4 = set()
    assert {(x['residue'],x['delta']) for x in rays4} == {
        (r,d) for r in range(48) for d in range(4 if r%2 else 5)}
    for cert in rays4:
        r,d = cert['residue'],cert['delta']; v = cert['verification']
        assert v['b_min'] == 48*v['h_min']+r
        for b in range(9,v['b_min']):
            if b%48 == r:expected4.add((4,b,b+d))
    expected45 = {(4,4,c):'alpha only' for c in (7,8,17)}
    expected45.update({(4,5,7):'alpha only',(5,5,7):'alpha only'})
    expected45.update({(4,5,c):'pinned W4' for c in (5,8)})
    for b, values in ((6,range(7,11)),(7,range(7,11)),(8,range(8,13))):
        expected45.update({(4,b,c):'pinned W4' for c in values})

    groups = [
        ('minimum_two','The 55 minimum-two finite cores','aux:min2',expected2),
        ('minimum_three_small','The 44 direct minimum-three cores','aux:min3-small',expected3s),
        ('minimum_three_pinned','The 29 maximum-pinned short-two seeds for minimum three','aux:min3-pinned',expected3p),
        ('minimum_four_remainder','The 139 pinned minimum-four remainder cores','aux:min4',expected4),
        ('minimum_four_five_small','The 20 small minimum-four/five helper cores','aux:min45',set(expected45)),
    ]
    for key,title,label,expected in groups:
        rows = read_rows(key); seen = set(); items = []; edges = 0; interfaces = Counter()
        for item in sorted(rows,key=lambda x:tuple(x['arms'])):
            profile = tuple(item['arms']); assert profile not in seen; seen.add(profile)
            paths = paths_of(item); n,k = check_spider(paths,hub=item.get('hub',0),alpha=True)
            if 'alpha_index' in item:assert item['alpha_index'] == k
            detail = '$K='+str(k)+'$'; b,c = profile[1:]
            if key == 'minimum_two':
                if b%2 and c==b:
                    assert next(p for p in paths if len(p)==2)[-1] == 1
                    detail += r'\par short leaf $1$'; interfaces['short leaf one']+=1
                if b%2==0 and c==b+1:
                    upper = next(p[-1] for p in paths if len(p)%2)
                    assert 2*(upper-k) <= b+4
                    detail += r'\par $2e\le b+4$'; interfaces['upper resonance bound']+=1
            if key == 'minimum_three_pinned':
                assert [n,1] in paths
                detail += r'\par pinned $(N,1)$'; interfaces['pinned maximum']+=1
                if b%2==0 and c==b+1:
                    upper = next(p[-1] for p in paths if len(p)%2)
                    assert 2*(upper-k) <= b+4
                    detail += r'\par $2e\le b+4$'; interfaces['upper resonance bound']+=1
            pinned4 = key == 'minimum_four_remainder' or (
                key == 'minimum_four_five_small' and expected45[profile] == 'pinned W4')
            if pinned4:
                assert [n,1,n-1,2] in paths
                detail += r'\par pinned W4'; interfaces['pinned W4']+=1
                if b%2 and c==b:
                    upper = min(p[-1] for p in paths if len(p)==b)
                    assert 2*(upper-k) <= b+7
                    detail += r'\par $2e\le b+7$'; interfaces['odd resonance bound']+=1
                if b%2==0 and c==b+1:
                    upper = next(p[-1] for p in paths if len(p)==b+1)
                    assert 2*(upper-k) <= b+8
                    detail += r'\par $2e\le b+8$'; interfaces['even resonance bound']+=1
                upgraded = [[n+1,1,n,2,n-1] if p==[n,1,n-1,2] else p[:] for p in paths]
                check_spider(upgraded,alpha=True); interfaces['four to five upgrade checked']+=1
            edges += n; items.append((profile_text(profile),paths,detail))
        assert seen == expected,(key,sorted(seen-expected),sorted(expected-seen))
        summaries[key] = dict(records=len(rows),edge_colors=edges,exact_profile_set=True,interfaces=dict(interfaces))
        total_colors += edges; tex.append(table(title,label,items))

    endpoint_data = json.loads((ROOT/INPUTS['endpoint_paths']).read_text())
    endpoint_one = {3:[1,2,0],4:[1,2,0,3],6:[1,5,0,3,2,4],9:[1,8,0,6,2,7,4,5,3]}
    endpoint_items = []; endpoint_count = 0
    for endpoint in (1,2,3):
        data = {'prefix':[1,2,0,3],'bases':endpoint_one} if endpoint==1 else endpoint_data[str(endpoint)]
        prefix = data['prefix']; check_permutation(prefix,endpoint,alpha=True)
        assert len(prefix)==4*endpoint and prefix[-1]==3*endpoint
        endpoint_items.append(('$e='+str(endpoint)+'$, prefix',[prefix],'$n='+str(len(prefix))+'$'))
        bases = {int(n):word for n,word in data['bases'].items()}
        expected_sizes = set(range(2*endpoint+1,6*endpoint+1))-{4*endpoint+1}|{8*endpoint+1}
        assert set(bases) == expected_sizes
        for n,word in sorted(bases.items()):
            check_permutation(word,endpoint,alpha=True); endpoint_count+=1
            endpoint_items.append(('$e='+str(endpoint)+'$, $n='+str(n)+'$',[word],'alpha path'))
    summaries['endpoint_paths'] = dict(base_words=endpoint_count,prefix_words=3,exact_residue_bases=True)
    tex.append(table('Fixed-endpoint alpha path prefixes and bases','aux:endpoints',endpoint_items,
                     heading='Complete path permutation (no extra hub)'))

    pair_groups = [
        ('pair_four_offset_two','Pairs with minimum four: offset two','aux:pair4-2',{(4,n,2) for n in range(4,18)}),
        ('pair_four_offset_three','Pairs with minimum four: offset three','aux:pair4-3',{(4,n,3) for n in range(4,24)}),
        ('pair_five','Pairs with minimum five: finite offsets','aux:pair5',
         {(5,n,k) for k,stop in ((1,13),(3,21),(4,27)) for n in range(5,stop)}),
    ]
    for key,title,label,expected in pair_groups:
        items = []; seen = set(); edges = 0
        for item in sorted(read_rows(key),key=lambda x:(x['k'],x['arms'])):
            profile = tuple(item['arms']); offset=item['k']; token=(*profile,offset)
            assert token not in seen; seen.add(token)
            paths=paths_of(item); n,k=check_spider(paths,offset=offset); edges+=n
            items.append((profile_text(profile),paths,'offset $k='+str(offset)+'$'))
        assert seen==expected
        summaries[key]=dict(records=len(items),edge_colors=edges,exact_profile_set=True)
        total_colors+=edges; tex.append(table(title,label,items))

    offset_two={int(k):v for k,v in json.loads((ROOT/INPUTS['offset_two_literal_source']).read_text()).items()}
    assert set(offset_two)==set(range(3,15))
    items=[];edges=0
    for n,paths in sorted(offset_two.items()):
        assert list(map(len,paths))==[2,n]
        count,_=check_spider(paths,offset=2);edges+=count
        items.append((profile_text((2,n)),paths,'offset $k=2$'))
    summaries['offset_two_literal_bases']=dict(records=12,edge_colors=edges,
                                              exact_profile_set=True)
    total_colors+=edges
    tex.append(table('The twelve offset-two pairs with a two-arm','aux:offset2-twos',items))

    items=[];edges=0
    equal=json.loads((ROOT/INPUTS['equal_even']).read_text())
    assert set(map(int,equal))=={6,8,10,14,18,22}
    for length,paths in sorted(((int(k),v)for k,v in equal.items())):
        assert list(map(len,paths))==[length]*3
        count,cut=check_spider(paths,alpha=True);edges+=count
        detail='$K='+str(cut)+'$'
        if length in (6,14,22):
            assert any(p[0]+p[-1]==count+1 for p in paths)
            detail+=r'\par complementary arm ends'
        items.append(('$L='+str(length)+'$; $L^3$',paths,detail))
    summaries['equal_even']=dict(records=6,edge_colors=edges,exact_profile_set=True)
    total_colors+=edges
    tex.append(table('Small equal-even alpha sources','aux:equal-even',items))

    rows=read_rows('equal_odd_four'); items=[];seen=set();edges=0
    for item in sorted(rows,key=lambda x:x.get('L',x['arms'][0])):
        length=item.get('L',item['arms'][0]);assert length not in seen;seen.add(length)
        paths=paths_of(item);assert list(map(len,paths))==[length]*4
        count,cut=check_spider(paths,alpha=True);assert item.get('alpha_index',cut)==cut;edges+=count
        items.append(('$L='+str(length)+'$; $L^4$',paths,'$K='+str(cut)+'$'))
    assert seen==set(range(7,49,2))
    summaries['equal_odd_four']=dict(records=21,edge_colors=edges,exact_profile_set=True)
    total_colors+=edges
    tex.append(table('All finite four-equal-odd alpha bases','aux:equal-four-odd',items))

    out_dir=Path(sys.argv[1]) if len(sys.argv)>1 else HERE
    (out_dir/'auxiliary_finite.tex').write_text('\n'.join(tex)+'\n')
    print(json.dumps(dict(status='all_auxiliary_finite_inputs_printed_and_independently_verified',
                          spider_edge_colors_checked=total_colors),indent=2))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
