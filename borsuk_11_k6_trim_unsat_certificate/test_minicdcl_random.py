import itertools,random,subprocess,tempfile,os,sys
random.seed(20260802)
solver='/mnt/data/minicdcl'

def brute(n,clauses):
    for mask in range(1<<n):
        ok=True
        for cl in clauses:
            if not any(((mask>>(abs(x)-1))&1)==(x>0) for x in cl):
                ok=False;break
        if ok:return True
    return False

for t in range(400):
    n=random.randint(1,14)
    m=random.randint(0, min(100,5*n+20))
    clauses=[]
    for _ in range(m):
        k=random.randint(1,min(6,n))
        vs=random.sample(range(1,n+1),k)
        clauses.append([v if random.getrandbits(1) else -v for v in vs])
    expected=brute(n,clauses)
    path=f'/mnt/data/rand_{os.getpid()}.cnf'
    with open(path,'w') as f:
        f.write(f'p cnf {n} {len(clauses)}\n')
        for c in clauses:f.write(' '.join(map(str,c))+' 0\n')
    p=subprocess.run([solver,path,'5','/mnt/data/rand.model'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    got='SATISFIABLE' in p.stdout and 'UNSATISFIABLE' not in p.stdout
    if got!=expected:
        print('MISMATCH',t,n,m,expected,p.returncode,p.stdout)
        print(clauses)
        sys.exit(1)
    os.remove(path)
print('PASS 400 randomized CNFs against brute force')
