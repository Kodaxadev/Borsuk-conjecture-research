#include <bits/stdc++.h>
using namespace std;

struct Clause {
    vector<int> lits;
    bool learnt=false;
    bool deleted=false;
    double activity=0.0;
    Clause(vector<int>&& xs, bool l=false): lits(move(xs)), learnt(l) {}
};

struct Solver {
    int nvars=0;
    vector<Clause*> clauses;
    vector<Clause*> learnts;
    vector<vector<Clause*>> watches;
    vector<vector<pair<int,Clause*>>> binImp;
    vector<int8_t> assigns; // -1 undef, 0 false, 1 true
    vector<int> levels;
    vector<Clause*> reasons;
    vector<int> trail, trail_lim;
    size_t qhead=0;
    vector<double> activity;
    vector<int8_t> polarity; // saved assignment, default false
    vector<uint8_t> seen;
    priority_queue<pair<double,int>> order;
    double var_inc=1.0, var_decay=0.95;
    double cla_inc=1.0, cla_decay=0.999;
    uint64_t conflicts=0, decisions=0, propagations=0, starts=0;
    chrono::steady_clock::time_point started;
    double timeout_sec=0;
    ofstream proof;

    static inline int var(int lit){return lit>>1;}
    static inline int neg(int lit){return lit^1;}
    static inline int sign(int lit){return lit&1;}
    int value(int lit) const {
        int8_t a=assigns[var(lit)];
        if(a<0) return -1;
        return int(a)^sign(lit);
    }
    int decisionLevel() const {return (int)trail_lim.size();}

    void init(int n){
        nvars=n; watches.assign(2*n,{}); binImp.assign(2*n,{}); assigns.assign(n,-1); levels.assign(n,0);
        reasons.assign(n,nullptr); activity.assign(n,0.0); polarity.assign(n,0); seen.assign(n,0);
        for(int v=0;v<n;v++) order.push({0.0,v});
    }

    bool enqueue(int lit, Clause* reason){
        int v=var(lit); int want=sign(lit)?0:1;
        if(assigns[v]>=0) return assigns[v]==want;
        assigns[v]=want; levels[v]=decisionLevel(); reasons[v]=reason; polarity[v]=want;
        trail.push_back(lit); return true;
    }

    void attach(Clause* c){
        if(c->lits.size()==2){
            binImp[neg(c->lits[0])].push_back({c->lits[1],c});
            binImp[neg(c->lits[1])].push_back({c->lits[0],c});
        }else if(c->lits.size()>2){
            watches[c->lits[0]].push_back(c);
            watches[c->lits[1]].push_back(c);
        }
    }

    bool addClause(vector<int> ps, bool learnt=false){
        sort(ps.begin(),ps.end());
        vector<int> q; q.reserve(ps.size());
        int last=-2;
        for(int l:ps){
            if(last==neg(l)) return true; // tautology
            if(l!=last) q.push_back(l);
            last=l;
        }
        if(q.empty()) return false;
        if(q.size()==1) return enqueue(q[0],nullptr);
        Clause* c=new Clause(move(q),learnt);
        clauses.push_back(c); if(learnt) learnts.push_back(c); attach(c); return true;
    }

    Clause* propagate(){
        while(qhead<trail.size()){
            int p=trail[qhead++]; propagations++;
            // Binary clauses are an implication graph: p -> q.
            for(auto [q,c]:binImp[p]){
                if(c->deleted) continue;
                int val=value(q);
                if(val==0) return c;
                if(val<0 && !enqueue(q,c)) return c;
            }
            int falselit=neg(p);
            auto &ws=watches[falselit];
            size_t i=0,j=0;
            while(i<ws.size()){
                Clause* c=ws[i++];
                if(c->deleted) continue;
                if(c->lits[0]==falselit) swap(c->lits[0],c->lits[1]);
                if(c->lits[1]!=falselit){
                    // stale watcher (should be rare after lazy deletion/moves)
                    ws[j++]=c; continue;
                }
                int other=c->lits[0];
                if(value(other)==1){ws[j++]=c; continue;}
                bool moved=false;
                for(size_t k=2;k<c->lits.size();k++){
                    if(value(c->lits[k])!=0){
                        c->lits[1]=c->lits[k]; c->lits[k]=falselit;
                        watches[c->lits[1]].push_back(c); moved=true; break;
                    }
                }
                if(moved) continue;
                ws[j++]=c;
                if(value(other)==0){
                    while(i<ws.size()) ws[j++]=ws[i++];
                    ws.resize(j); return c;
                }
                if(!enqueue(other,c)){
                    while(i<ws.size()) ws[j++]=ws[i++];
                    ws.resize(j); return c;
                }
            }
            ws.resize(j);
        }
        return nullptr;
    }

    void cancelUntil(int lev){
        if(decisionLevel()<=lev) return;
        int target=trail_lim[lev];
        for(int i=(int)trail.size()-1;i>=target;i--){
            int v=var(trail[i]); assigns[v]=-1; reasons[v]=nullptr; levels[v]=0;
        }
        trail.resize(target); qhead=trail.size(); trail_lim.resize(lev);
    }

    void varBump(int v){
        activity[v]+=var_inc;
        if(activity[v]>1e100){
            for(double &x:activity)x*=1e-100;
            var_inc*=1e-100;
        }
    }
    void varDecay(){var_inc*=1.0/var_decay;}
    void claBump(Clause* c){
        c->activity+=cla_inc;
        if(c->activity>1e20){for(Clause* d:learnts) if(!d->deleted)d->activity*=1e-20; cla_inc*=1e-20;}
    }
    void claDecay(){cla_inc*=1.0/cla_decay;}

    bool locked(Clause* c) const {
        if(c->lits.empty()) return false;
        int v=var(c->lits[0]);
        return assigns[v]>=0 && reasons[v]==c;
    }

    void reduceDB(){
        double t0=chrono::duration<double>(chrono::steady_clock::now()-started).count();
        cerr<<"c REDUCE begin conflict "<<conflicts<<" active "<<learnts.size()<<" clauses "<<clauses.size()<<" level "<<decisionLevel()<<" trail "<<trail.size()<<" sec "<<t0<<"\n";
        // Rebuild only at root.  Reattaching watchers under a non-root partial
        // assignment can miss already-false watched literals.
        cancelUntil(0);
        qhead=0;
        unordered_set<Clause*> locked_set;
        locked_set.reserve(trail.size()*2+1);
        for(int v=0;v<nvars;v++) if(assigns[v]>=0 && reasons[v]) locked_set.insert(reasons[v]);
        vector<Clause*> cand;
        cand.reserve(learnts.size());
        for(Clause* c:learnts) if(!c->deleted && c->lits.size()>2 && !locked_set.count(c)) cand.push_back(c);
        sort(cand.begin(),cand.end(),[](Clause* a,Clause* b){
            if(a->lits.size()!=b->lits.size()) return a->lits.size()>b->lits.size();
            return a->activity<b->activity;
        });
        size_t kill=cand.size()/2;
        for(size_t i=0;i<kill;i++){ logProofDelete(cand[i]->lits); cand[i]->deleted=true; }
        vector<Clause*> keep; keep.reserve(learnts.size()-kill);
        for(Clause* c:learnts) if(!c->deleted) keep.push_back(c);
        learnts.swap(keep);
        // Physically purge dead clauses and reconstruct watcher lists.  Lazy
        // deletion alone makes dense instances progressively slower.
        for(auto &w:watches) w.clear();
        for(auto &b:binImp) b.clear();
        vector<Clause*> live; live.reserve(clauses.size()-kill);
        for(Clause* c:clauses){
            if(c->deleted) delete c;
            else {live.push_back(c); attach(c);}
        }
        clauses.swap(live);
        double t1=chrono::duration<double>(chrono::steady_clock::now()-started).count();
        cerr<<"c REDUCE end conflict "<<conflicts<<" active "<<learnts.size()<<" clauses "<<clauses.size()<<" trail "<<trail.size()<<" sec "<<t1<<"\n";
    }

    void analyze(Clause* confl, vector<int>& out, int& btlevel){
        out.clear(); out.push_back(-1);
        int pathC=0, p=-1, idx=(int)trail.size()-1;
        vector<int> touched; touched.reserve(64);
        do{
            Clause* c=confl;
            if(c->learnt) claBump(c);
            for(int q:c->lits){
                int v=var(q);
                if(p!=-1 && v==var(p)) continue;
                if(!seen[v] && levels[v]>0){
                    seen[v]=1; touched.push_back(v); varBump(v);
                    if(levels[v]==decisionLevel()) pathC++;
                    else out.push_back(q);
                }
            }
            while(idx>=0 && !seen[var(trail[idx])]) idx--;
            if(idx<0){cerr<<"c INTERNAL analyze exhausted trail\n"; exit(3);} 
            p=trail[idx--];
            confl=reasons[var(p)];
            seen[var(p)]=0;
            pathC--;
        }while(pathC>0);
        out[0]=neg(p);
        // Basic MiniSat-style clause minimization: a literal is redundant when
        // its reason mentions only root variables or variables already in the learnt clause.
        for(int q:out) seen[var(q)]=1;
        size_t wr=1;
        for(size_t i=1;i<out.size();i++){
            int v=var(out[i]); Clause* r=reasons[v]; bool redundant=(r!=nullptr);
            if(r){
                for(int z:r->lits){int w=var(z); if(w==v) continue; if(levels[w]>0 && !seen[w]){redundant=false;break;}}
            }
            if(!redundant) out[wr++]=out[i];
        }
        out.resize(wr);
        btlevel=0;
        if(out.size()>1){
            size_t best=1;
            for(size_t i=1;i<out.size();i++) if(levels[var(out[i])]>levels[var(out[best])]) best=i;
            swap(out[1],out[best]); btlevel=levels[var(out[1])];
        }
        for(int v:touched) seen[v]=0;
        for(int q:out) seen[var(q)]=0;
    }

    int pickBranchLit(){
        int best=-1; double bestAct=-1.0;
        for(int v=0;v<nvars;v++) if(assigns[v]<0 && (best<0 || activity[v]>bestAct)){
            best=v; bestAct=activity[v];
        }
        if(best<0) return -1;
        decisions++;
        int want=polarity[best];
        return 2*best + (want?0:1);
    }

    static double luby(double y, int x){
        int size=1,seq=0;
        while(size<x+1){seq++;size=2*size+1;}
        while(size-1!=x){size=(size-1)>>1;seq--;x%=size;}
        return pow(y,seq);
    }


    void logProofClause(const vector<int>& lits){
        if(!proof.is_open()) return;
        for(int l:lits){
            int z=var(l)+1;
            if(sign(l)) z=-z;
            proof<<z<<' ';
        }
        proof<<"0\n";
    }
    void logProofDelete(const vector<int>& lits){
        if(!proof.is_open()) return;
        proof<<"d ";
        for(int l:lits){
            int z=var(l)+1;
            if(sign(l)) z=-z;
            proof<<z<<' ';
        }
        proof<<"0\n";
    }
    void logProofEmpty(){ if(proof.is_open()) proof<<"0\n"; }

    bool timedOut() const {
        if(timeout_sec<=0) return false;
        return chrono::duration<double>(chrono::steady_clock::now()-started).count()>=timeout_sec;
    }

    int solve(double timeout, const string& proofpath){
        timeout_sec=timeout; started=chrono::steady_clock::now();
        if(!proofpath.empty()) proof.open(proofpath, ios::out|ios::trunc);
        Clause* confl=propagate(); if(confl){logProofEmpty();return 20;}
        vector<int> learnt;
        int restart_idx=0;
        uint64_t next_report=10000;
        while(true){
            starts++;
            uint64_t budget=(uint64_t)(100*luby(2,restart_idx++));
            uint64_t local=0;
            while(local<budget){
                if((conflicts%2048)==0 && timedOut()) return 0;
                confl=propagate();
                if(confl){
                    conflicts++; local++;
                    if(decisionLevel()==0){logProofEmpty();return 20;}
                    int bt=0; analyze(confl,learnt,bt); logProofClause(learnt); cancelUntil(bt);
                    Clause* reason=nullptr;
                    if(learnt.size()==1){
                        if(!enqueue(learnt[0],nullptr)){logProofEmpty();return 20;}
                    }else{
                        Clause* c=new Clause(vector<int>(learnt.begin(),learnt.end()),true);
                        clauses.push_back(c); learnts.push_back(c); attach(c); reason=c;
                        if(!enqueue(learnt[0],reason)){logProofEmpty();return 20;}
                    }
                    varDecay(); claDecay();
                    if(conflicts%10000==0 && learnts.size()>12000) reduceDB();
                    if(conflicts>=next_report){
                        double sec=chrono::duration<double>(chrono::steady_clock::now()-started).count();
                        cerr<<"c conflicts "<<conflicts<<" decisions "<<decisions<<" active_learnts "<<this->learnts.size()<<" last_clause "<<learnt.size()<<" level "<<decisionLevel()<<" sec "<<fixed<<setprecision(1)<<sec<<"\n";
                        next_report+=10000;
                    }
                }else{
                    int p=pickBranchLit();
                    if(p<0) return 10;
                    trail_lim.push_back((int)trail.size());
                    enqueue(p,nullptr);
                }
            }
            cancelUntil(0);
        }
    }

    ~Solver(){for(Clause* c:clauses) delete c;}
};

int main(int argc,char**argv){
    if(argc<2){cerr<<"usage: minicdcl_proof file.cnf [timeout_seconds] [model_out] [proof_out]\n";return 2;}
    double timeout=argc>2?stod(argv[2]):300.0;
    string outpath=argc>3?argv[3]:"/mnt/data/minicdcl_model.txt";
    string proofpath=argc>4?argv[4]:"";
    ifstream in(argv[1]); if(!in){cerr<<"cannot open\n";return 2;}
    string tok; int nv=0,nc=0; vector<vector<int>> raw; raw.reserve(400000);
    while(in>>tok){
        if(tok=="c"){string line;getline(in,line);continue;}
        if(tok=="p"){string fmt;in>>fmt>>nv>>nc;break;}
    }
    if(nv<=0){cerr<<"bad header\n";return 2;}
    Solver S;S.init(nv);
    vector<int> clause; clause.reserve(16); int x;
    int readc=0;
    while(in>>x){
        if(x==0){
            vector<int> lits;lits.reserve(clause.size());
            for(int z:clause){int v=abs(z)-1;int sg=z<0; lits.push_back(2*v+sg);} 
            if(!S.addClause(move(lits),false)){cout<<"s UNSATISFIABLE\n";return 20;}
            clause.clear();readc++;
        }else clause.push_back(x);
    }
    cerr<<"c parsed vars "<<nv<<" clauses "<<readc<<" expected "<<nc<<"\n";
    int status=S.solve(timeout,proofpath);
    if(status==10){
        cout<<"s SATISFIABLE\n";
        ofstream out(outpath);
        out<<"s SATISFIABLE\n";
        int col=0;
        for(int v=0;v<nv;v++){
            int z=(S.assigns[v]==1)?v+1:-(v+1);
            out<<z<<' '; if(++col%20==0)out<<"\n";
        }
        out<<"0\n";
        cerr<<"c SAT conflicts "<<S.conflicts<<" decisions "<<S.decisions<<" propagations "<<S.propagations<<"\n";
    }else if(status==20){cout<<"s UNSATISFIABLE\n";cerr<<"c UNSAT conflicts "<<S.conflicts<<"\n";}
    else {cout<<"s UNKNOWN\n";cerr<<"c TIMEOUT conflicts "<<S.conflicts<<" decisions "<<S.decisions<<"\n";}
    return status;
}
