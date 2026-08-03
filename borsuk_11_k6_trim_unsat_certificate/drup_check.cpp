#include <algorithm>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

struct VecHash {
    size_t operator()(const vector<int>& v) const noexcept {
        uint64_t h = 1469598103934665603ULL;
        for (int x : v) {
            uint64_t z = static_cast<uint32_t>(x) * 0x9e3779b185ebca87ULL;
            h ^= z + (h << 6) + (h >> 2);
            h *= 1099511628211ULL;
        }
        return static_cast<size_t>(h);
    }
};

struct Clause {
    vector<int> lits;       // watcher positions may mutate
    vector<int> canonical;  // stable deletion key
    bool active = true;
    bool learned = false;
};

class DRUPChecker {
public:
    explicit DRUPChecker(int nvars)
        : nvars_(nvars), value_(nvars + 1, -1),
          binary_imp_(2 * nvars), watches_(2 * nvars) {}

    bool add_original(vector<int> c) {
        return add_clause(move(c), false);
    }

    bool verify_add(vector<int> c, size_t step) {
        if (dirty_) rebuild();
        canonicalize(c);

        size_t root = trail_.size();
        bool conflict = root_conflict_;
        if (!conflict) {
            for (int lit : c) {
                if (!enqueue(-lit)) {
                    conflict = true;
                    break;
                }
            }
            if (!conflict) conflict = !propagate();
        }
        backtrack(root);

        if (!conflict) {
            cerr << "INVALID: addition step " << step
                 << " is not RUP (length " << c.size() << ")\n";
            return false;
        }
        if (c.empty()) {
            saw_empty_ = true;
            return true;
        }
        if (!add_clause(move(c), true)) root_conflict_ = true;
        return true;
    }

    void delete_clause(vector<int> c) {
        canonicalize(c);
        auto it = learned_index_.find(c);
        if (it == learned_index_.end()) return;
        auto& ids = it->second;
        while (!ids.empty() && !clauses_[ids.back()].active) ids.pop_back();
        if (ids.empty()) return;
        clauses_[ids.back()].active = false;
        ids.pop_back();
        dirty_ = true;
        ++pending_deletions_;
    }

    bool saw_empty() const { return saw_empty_; }
    size_t active_learned() const {
        size_t n = 0;
        for (const auto& c : clauses_) if (c.active && c.learned) ++n;
        return n;
    }

private:
    int nvars_;
    vector<int8_t> value_;
    vector<int> trail_;
    size_t qhead_ = 0;
    vector<vector<pair<int,int>>> binary_imp_; // assigned literal -> (implied,cid)
    vector<vector<int>> watches_;              // watched literal -> clause ids
    vector<Clause> clauses_;
    vector<int> unit_clause_lits_;             // unit deletions are absent/ignored
    unordered_map<vector<int>, vector<int>, VecHash> learned_index_;
    bool root_conflict_ = false;
    bool saw_empty_ = false;
    bool dirty_ = false;
    size_t pending_deletions_ = 0;

    static void canonicalize(vector<int>& c) {
        sort(c.begin(), c.end());
        c.erase(unique(c.begin(), c.end()), c.end());
    }

    int idx(int lit) const {
        return 2 * (abs(lit) - 1) + (lit < 0 ? 1 : 0);
    }

    int lit_value(int lit) const {
        int8_t a = value_[abs(lit)];
        if (a < 0) return -1;
        return lit > 0 ? a : 1 - a;
    }

    bool enqueue(int lit) {
        int v = abs(lit);
        int want = lit > 0 ? 1 : 0;
        if (value_[v] >= 0) return value_[v] == want;
        value_[v] = static_cast<int8_t>(want);
        trail_.push_back(lit);
        return true;
    }

    bool propagate() {
        while (qhead_ < trail_.size()) {
            int p = trail_[qhead_++];

            auto& bs = binary_imp_[idx(p)];
            for (const auto& edge : bs) {
                int q = edge.first;
                int cid = edge.second;
                if (!clauses_[cid].active) continue;
                if (!enqueue(q)) return false;
            }

            int false_lit = -p;
            auto& ws = watches_[idx(false_lit)];
            size_t i = 0, j = 0;
            while (i < ws.size()) {
                int cid = ws[i++];
                Clause& cl = clauses_[cid];
                if (!cl.active) continue;

                if (cl.lits[0] == false_lit) swap(cl.lits[0], cl.lits[1]);
                if (cl.lits[1] != false_lit) {
                    cerr << "internal watcher mismatch\n";
                    return false;
                }
                int other = cl.lits[0];
                if (lit_value(other) == 1) {
                    ws[j++] = cid;
                    continue;
                }

                bool moved = false;
                for (size_t k = 2; k < cl.lits.size(); ++k) {
                    if (lit_value(cl.lits[k]) != 0) {
                        cl.lits[1] = cl.lits[k];
                        cl.lits[k] = false_lit;
                        watches_[idx(cl.lits[1])].push_back(cid);
                        moved = true;
                        break;
                    }
                }
                if (moved) continue;

                ws[j++] = cid;
                int ov = lit_value(other);
                if (ov == 0 || !enqueue(other)) {
                    while (i < ws.size()) {
                        int rest = ws[i++];
                        if (clauses_[rest].active) ws[j++] = rest;
                    }
                    ws.resize(j);
                    return false;
                }
            }
            ws.resize(j);
        }
        return true;
    }

    void backtrack(size_t root) {
        while (trail_.size() > root) {
            value_[abs(trail_.back())] = -1;
            trail_.pop_back();
        }
        qhead_ = trail_.size();
    }

    static bool tautological(const vector<int>& c) {
        for (int lit : c) {
            if (binary_search(c.begin(), c.end(), -lit)) return true;
        }
        return false;
    }

    void arrange_watches(Clause& cl) {
        size_t next = 0;
        for (size_t i = 0; i < cl.lits.size() && next < 2; ++i) {
            if (lit_value(cl.lits[i]) != 0) {
                swap(cl.lits[next], cl.lits[i]);
                ++next;
            }
        }
        while (next < 2) {
            swap(cl.lits[next], cl.lits[next]);
            ++next;
        }
    }

    void attach(int cid) {
        Clause& cl = clauses_[cid];
        if (cl.lits.size() == 2) {
            binary_imp_[idx(-cl.lits[0])].push_back({cl.lits[1], cid});
            binary_imp_[idx(-cl.lits[1])].push_back({cl.lits[0], cid});
        } else {
            arrange_watches(cl);
            watches_[idx(cl.lits[0])].push_back(cid);
            watches_[idx(cl.lits[1])].push_back(cid);
        }
    }

    bool add_clause(vector<int> c, bool learned) {
        canonicalize(c);
        if (tautological(c)) return true;
        if (c.empty()) return false;
        if (c.size() == 1) {
            unit_clause_lits_.push_back(c[0]);
            if (!enqueue(c[0])) return false;
            return propagate();
        }

        Clause cl;
        cl.lits = c;
        cl.canonical = c;
        cl.learned = learned;
        int cid = static_cast<int>(clauses_.size());
        clauses_.push_back(move(cl));
        if (learned) learned_index_[clauses_[cid].canonical].push_back(cid);
        attach(cid);

        bool sat = false;
        int nonfalse = 0, sole = 0;
        for (int lit : clauses_[cid].lits) {
            int v = lit_value(lit);
            if (v == 1) sat = true;
            if (v != 0) { ++nonfalse; sole = lit; }
        }
        if (!sat) {
            if (nonfalse == 0) return false;
            if (nonfalse == 1 && !enqueue(sole)) return false;
        }
        return propagate();
    }

    void rebuild() {
        // Deletions weaken the formula, so recompute root closure from permanent units.
        fill(value_.begin(), value_.end(), static_cast<int8_t>(-1));
        trail_.clear();
        qhead_ = 0;
        root_conflict_ = false;
        for (auto& v : binary_imp_) v.clear();
        for (auto& v : watches_) v.clear();

        for (size_t cid = 0; cid < clauses_.size(); ++cid) {
            if (!clauses_[cid].active) continue;
            // With no assignments yet, any two literals form valid watches.
            watches_dummy_attach(static_cast<int>(cid));
        }
        for (int lit : unit_clause_lits_) {
            if (!enqueue(lit)) { root_conflict_ = true; break; }
        }
        if (!root_conflict_ && !propagate()) root_conflict_ = true;
        dirty_ = false;
        pending_deletions_ = 0;
    }

    void watches_dummy_attach(int cid) {
        Clause& cl = clauses_[cid];
        if (cl.lits.size() == 2) {
            binary_imp_[idx(-cl.lits[0])].push_back({cl.lits[1], cid});
            binary_imp_[idx(-cl.lits[1])].push_back({cl.lits[0], cid});
        } else {
            watches_[idx(cl.lits[0])].push_back(cid);
            watches_[idx(cl.lits[1])].push_back(cid);
        }
    }
};

static bool parse_cnf_header(ifstream& in, int& vars, long long& clauses) {
    string line;
    while (getline(in, line)) {
        if (line.empty() || line[0] == 'c') continue;
        if (line[0] == 'p') {
            string p, kind;
            istringstream ss(line);
            ss >> p >> kind >> vars >> clauses;
            return p == "p" && kind == "cnf";
        }
    }
    return false;
}

static bool read_dimacs_clause(istream& in, vector<int>& c) {
    c.clear();
    int x;
    while (in >> x) {
        if (x == 0) return true;
        c.push_back(x);
    }
    return false;
}

int main(int argc, char** argv) {
    if (argc != 3) {
        cerr << "usage: drup_check formula.cnf proof.drat\n";
        return 2;
    }
    ifstream cnf(argv[1]);
    ifstream proof(argv[2]);
    if (!cnf || !proof) { cerr << "cannot open input\n"; return 2; }

    int vars = 0;
    long long declared = 0;
    if (!parse_cnf_header(cnf, vars, declared)) { cerr << "bad CNF header\n"; return 2; }
    DRUPChecker checker(vars);
    vector<int> clause;
    long long loaded = 0;
    while (read_dimacs_clause(cnf, clause)) {
        for (int lit : clause) if (abs(lit) > vars) { cerr << "CNF literal range\n"; return 2; }
        checker.add_original(clause);
        ++loaded;
    }
    if (loaded != declared) { cerr << "CNF clause count mismatch\n"; return 2; }

    auto started = chrono::steady_clock::now();
    string line;
    size_t step = 0, additions = 0, deletions = 0;
    while (getline(proof, line)) {
        if (line.empty() || line[0] == 'c') continue;
        ++step;
        istringstream ss(line);
        bool del = false;
        if (ss.peek() == 'd') { char d; ss >> d; del = true; }
        clause.clear();
        int x;
        while (ss >> x && x != 0) clause.push_back(x);
        for (int lit : clause) if (abs(lit) > vars) { cerr << "proof literal range at step " << step << "\n"; return 2; }

        if (del) {
            checker.delete_clause(clause);
            ++deletions;
        } else {
            if (!checker.verify_add(clause, step)) return 1;
            ++additions;
            if (clause.empty()) break;
        }
        if (step % 25000 == 0) {
            double sec = chrono::duration<double>(chrono::steady_clock::now() - started).count();
            cerr << "c steps " << step << " additions " << additions
                 << " deletions " << deletions << " active_learned "
                 << checker.active_learned() << " sec " << sec << "\n";
        }
    }

    if (!checker.saw_empty()) { cerr << "proof lacks verified empty clause\n"; return 1; }
    double sec = chrono::duration<double>(chrono::steady_clock::now() - started).count();
    cout << "s VERIFIED UNSAT\n";
    cout << "c original " << loaded << " additions " << additions
         << " deletions " << deletions << " steps " << step
         << " seconds " << sec << "\n";
    return 0;
}
