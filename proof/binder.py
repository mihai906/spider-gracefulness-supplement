#!/usr/bin/env python3
"""Bind a CPC proof's global assumption to the original SMT2, without a solver.

An iterative S-expression reader and lexical let evaluator expand aliases
into exact interned structural DAG identifiers. Only syntactic abbreviation expansion
is performed; neither Boolean rewriting nor arithmetic simplification is
trusted. Definitions and declarations before the CPC assumption must be
fresh. The check is intentionally stricter than logical equivalence.
"""
from hashlib import sha256
from pathlib import Path
import argparse,json,re,time

ROOT=Path(__file__).resolve().parents[1]
TOKEN=re.compile(r';[^\n]*|[()]|[^\s();]+')
INTEGER=re.compile(r'0|[1-9][0-9]*')


def commands(stream):
    stack=[]
    for line in stream:
        for match in TOKEN.finditer(line):
            token=match.group()
            if token.startswith(';'):break
            assert '"' not in token and '|' not in token, 'quoted symbols unsupported'
            if token=='(':
                stack.append([])
            elif token==')':
                assert stack,'unbalanced closing parenthesis'
                term=stack.pop()
                if stack:stack[-1].append(term)
                else:yield term
            else:
                assert stack,'unexpected top-level atom'
                stack[-1].append(token)
    assert not stack,'unfinished S-expression'


class Terms:
    """Exact structural equality: Python dictionaries resolve hash collisions."""
    def __init__(self):
        self.ids={};self.digests=[]

    def intern(self,key,payload):
        if key not in self.ids:
            self.ids[key]=len(self.ids)
            self.digests.append(sha256(payload).digest())
        return self.ids[key]

    def atom(self,name):
        assert isinstance(name,str)
        tag='number'if INTEGER.fullmatch(name)else'symbol'
        return self.intern((tag,name),(tag+'\0'+name).encode())

    def application(self,operator,arguments):
        assert isinstance(operator,str)and '\0'not in operator
        arguments=tuple(arguments)
        assert all(isinstance(a,int)and 0<=a<len(self.ids)for a in arguments)
        payload=b'application\0'+operator.encode()+b'\0'+str(len(arguments)).encode()+b'\0'
        payload+=b''.join(self.digests[a]for a in arguments)
        return self.intern(('application',operator,arguments),payload)


def evaluate(term,environment,terms):
    """Expand SMT simultaneous lexical lets, without recursion or DAG expansion."""
    # Lexical bindings are restored on return. CPC definitions contain no
    # lets, so the large alias environment never needs to be copied.
    sentinel=object();env=environment;values=[];todo=[('eval',term)]
    while todo:
        op,item=todo.pop()
        if op=='eval':
            if isinstance(item,str):
                values.append(env[item] if item in env else terms.atom(item))
                continue
            assert isinstance(item,list) and item and isinstance(item[0],str)
            if item[0]=='let':
                assert len(item)==3 and isinstance(item[1],list)
                bindings=item[1]
                assert all(isinstance(p,list) and len(p)==2 and isinstance(p[0],str) for p in bindings)
                names=[p[0]for p in bindings];assert len(names)==len(set(names))
                todo.append(('bind',(names,item[2])))
                for _,expression in reversed(bindings):todo.append(('eval',expression))
            else:
                todo.append(('combine',(item[0],len(item)-1)))
                for child in reversed(item[1:]):todo.append(('eval',child))
        elif op=='combine':
            operator,n=item
            args=values[-n:] if n else []
            if n:del values[-n:]
            values.append(terms.application(operator,args))
        elif op=='bind':
            names,body=item;n=len(names)
            assigned=values[-n:] if n else []
            if n:del values[-n:]
            old=[(name,env.get(name,sentinel))for name in names]
            env.update(zip(names,assigned))
            todo.append(('restore',old));todo.append(('eval',body))
        elif op=='restore':
            for name,old in item:
                if old is sentinel:del env[name]
                else:env[name]=old
        else:raise AssertionError(op)
    assert len(values)==1
    return values[0]


def bind(source,proof):
    terms=Terms();declared={};assertions=[]
    with source.open()as stream:
        for command in commands(stream):
            head=command[0]
            if head=='declare-fun':
                assert len(command)==4 and command[2]==[] and command[3]=='Int'
                name=command[1];assert name not in declared
                declared[name]='Int'
            elif head=='assert':
                assert len(command)==2
                assertions.append(evaluate(command[1],{},terms))
            else:assert head in('set-info','set-logic','check-sat','set-option','exit'),head
    assert len(assertions)==1,'this checker targets the frozen single-assertion queries'
    aliases={};proof_declared={};global_assumptions=[];definitions=0
    with proof.open()as stream:
        for command in commands(stream):
            head=command[0]
            if global_assumptions:
                assert head!='assume','additional global CPC assumption'
                continue
            if head=='declare-const':
                assert len(command)==3 and command[2]=='Int'
                name=command[1];assert name not in proof_declared and name not in aliases
                proof_declared[name]='Int'
            elif head=='define':
                assert len(command)==4 and command[2]==[]
                name=command[1];assert name.startswith('@t')
                assert name not in aliases and name not in proof_declared
                # CPC aliases are acyclic by construction; reject references
                # to an unresolved @t identifier rather than treating one as
                # a free variable.
                work=[command[3]]
                while work:
                    node=work.pop()
                    if isinstance(node,list):work.extend(node)
                    elif node.startswith('@t'):assert node in aliases,('unbound CPC alias',node)
                aliases[name]=evaluate(command[3],aliases,terms);definitions+=1
            elif head=='assume':
                assert len(command)==3
                global_assumptions.append(evaluate(command[2],aliases,terms))
            else:raise AssertionError(('unexpected pre-assumption CPC command',head))
        assert global_assumptions,'no global CPC assumption'
    assert declared==proof_declared,'input variable declarations differ'
    assert assertions==global_assumptions,'CPC global premise differs from original SMT2 assertion'
    return dict(status='identical',method='Exact shared structural DAG interning after lexical let and definition expansion',
        input_assertions=1,CPC_global_assumptions=1,expanded_CPC_definitions=definitions,
        declared_integer_variables=sorted(declared),structural_digest=terms.digests[assertions[0]].hex(),
        structural_equality_uses_digest_collision_assumption=False,
        interned_terms=len(terms.ids),
        external_solver_imported=False,logical_simplification_used=False,
        files={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest()for p in(source,proof,Path(__file__).resolve())})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('proof',type=Path)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();start=time.monotonic()
    result=bind(args.input.resolve(),args.proof.resolve());result['seconds']=time.monotonic()-start
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='files'},indent=2),flush=True)

if __name__=='__main__':main()
