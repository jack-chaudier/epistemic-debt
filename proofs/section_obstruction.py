#!/usr/bin/env python3
"""Section obstruction — the mirage shelf as a contextuality class (exact check).

CLAIM UNDER TEST (theory doc section 5.3): justifications form a presheaf over the
cover of observation contexts; a global justification is a section; the mirage is
local consistency WITHOUT a global section — an Abramsky-Brandenburger contextuality
class — and Vorob'ev's acyclicity criterion says exactly when the shelf CANNOT form.

MINI-MODEL (possibilistic / relational empirical models):
  - variables X = {0..n-1}, each with a finite outcome alphabet (binary in the sweeps);
  - a cover: contexts C_i subseteq X (subsets jointly observable), union = X;
  - local valuations: a nonempty relation R_i of local sections over C_i;
  - local consistency (pairwise compatibility / possibilistic no-signalling):
    for all i,j the projections of R_i and R_j onto C_i n C_j are EQUAL;
  - global witness section: g: X -> outcomes with g|C_i in R_i for every i.

GRADES OF OBSTRUCTION (both counted exhaustively):
  LOGICAL  some local section extends to no global section
           (equivalently: the family is not "globally consistent" in the
           Beeri-Fagin-Maier-Yannakakis sense);
  STRONG   no global section exists at all ("strong contextuality");
  ANSWER-DETERMINED SHELF (the mirage, with its answer layer made explicit):
           STRONG, and additionally every context locally *determines the verdict*
           under fail-closed OR semantics (global answer DENY iff some variable = 1;
           a context determines DENY iff every one of its local sections contains a
           failing bit). Every context confidently answers DENIED, all contexts agree,
           local data are pairwise consistent — yet no global witness assignment
           exists. Verdict everywhere, witness nowhere.

ACYCLICITY: alpha-acyclicity via GYO reduction, independently cross-checked against a
brute-force running-intersection-property (RIP) ordering search on every swept cover.

KNOWN THEOREM BEING INSTANTIATED (this script does NOT claim novelty for it):
Vorob'ev 1962 (probabilistic) / Beeri-Fagin-Maier-Yannakakis 1983 (relational):
a cover is alpha-acyclic iff EVERY pairwise-consistent family of relations over it is
globally consistent. The acyclic direction holds over every alphabet; the cyclic
converse guarantees a counterexample over SOME alphabet (not necessarily binary).

WHAT IS VERIFIED, EXHAUSTIVELY (binary outcomes unless stated):
  V1  GYO == RIP on every swept cover (two independent acyclicity implementations).
  V2  Vorob'ev direction: on every acyclic cover in the sweep — ALL edge-covers of
      3 and 4 variables (45 covers), curated 5/6-variable graph covers, and curated
      hypergraph covers — ZERO logical obstructions among ALL compatible families.
      On an acyclic cover the shelf cannot form. Zero parameters, no exceptions.
  V3  Converse, all swept covers (graph AND hypergraph): every cyclic cover admits
      STRONG shelf instances (counted exactly); every acyclic cover admits none.
      The obstruction is available exactly on cyclic covers — zero exceptions.
  V4  The tetrahedron cover {ABC,ABD,ACD,BCD} (cyclic, non-graph): 720 binary
      strong shelves and 102 binary answer-determined shelves exist (the author's
      hand-derivation had guessed binary might not suffice here — the exhaustive
      run refuted that guess; binary parity relations alone cannot obstruct it
      since J-I is invertible mod 2, so the 720 are non-parity families).
      Additionally a canonical algebraic instance — mod-3 parity relations with
      defect vector (1,0,0,0), unsolvable because J-I is SINGULAR mod 3 — is
      verified pairwise-compatible with zero global sections over ternary.
  V5  Canonical instances cell-by-cell: Specker triangle on C3 (the minimal
      answer-determined shelf), PR box on C4 (witness shelf), triangle embedding on
      {ABC,CD,DA}.
  V6  Cutting the cycle repays the debt: dropping one context from the PR-box cover
      leaves an acyclic path on which the SAME residual family is globally consistent.
  V7  Joint observation dissolves the shelf: adjoining the total context ABC to the
      cyclic triangle gives an alpha-acyclic cover (GYO) whose 1-skeleton still
      contains the 3-cycle; all 255 compatible families are obstruction-free. The
      criterion is hypergraph acyclicity, not graph-drawing intuition.
  V8  Holonomy = the first epistemic-debt inequality, in miniature: on the k-cycle
      (k = 3..6) with constant-parity relations, a global section exists iff the sum
      of edge parities around the cycle is EVEN; exactly 2^(k-1) of the 2^k parity
      patterns are shelves. "Sum of local parities is even" is a behavioral linear
      inequality whose violation certifies the shelf with no interpretability access.
      COMPLETENESS (found by the sweep, not designed in): the exhaustive strong-shelf
      counts on C3/C4/C5/C6 are exactly 4/8/16/32 = 2^(k-1) — every strong shelf on
      a pure cycle cover IS a holonomy violation. On cycles the parity inequality is
      a complete certificate, not merely a sufficient one.
  V9  The answer layer has its own, finer topology: across every swept graph cover,
      answer-determined shelves exist iff the cover is NON-BIPARTITE (odd cycle),
      while witness shelves exist iff the cover is merely CYCLIC. Two grades of
      obstruction, two different zero-parameter structural criteria — the exact shape
      section 5.3 conjectured when it noted static and dynamic obstructions first
      fail on structurally different families.
  V10 Pinned exact counts (regression): all curated-cover counts below.

HONEST SCOPE — what this does NOT show:
  - It instantiates and cross-checks a KNOWN theorem (Vorob'ev/BFMY) on finite
    families, plus new exact counts for the answer-determined layer; the general
    theorem is cited, not re-proved here.
  - Exhaustive only within the box: binary outcomes, <= 6 contexts, <= 6 variables
    (the tetrahedron ternary check is a single verified instance, not a sweep).
  - NOTHING here shows that LLM compaction artifacts realize cyclic observation
    covers, or that measured compaction debt is contextuality. That bridge needs an
    experiment mapping (artifact, probe) pairs to contexts and testing V8-style
    inequalities behaviorally. This script supplies the exact target and the
    inequality template; the empirical bridge is future work.

Exit code 0 iff every check passes. Stdlib only, deterministic, no arguments.
"""
import itertools
import sys
import time

EQ2 = 0b1001   # {00, 11} on a 2-variable context
NEQ2 = 0b0110  # {01, 10} on a 2-variable context


# ---------------------------------------------------------------------------
# acyclicity: GYO reduction and an independent RIP-ordering search
# ---------------------------------------------------------------------------

def gyo_acyclic(contexts) -> bool:
    """Graham-Yu-Ozsoyoglu reduction empties the hypergraph iff alpha-acyclic."""
    edges = [set(c) for c in contexts]
    changed = True
    while changed:
        changed = False
        counts: dict = {}
        for e in edges:
            for v in e:
                counts[v] = counts.get(v, 0) + 1
        for e in edges:
            isolated = {v for v in e if counts[v] == 1}
            if isolated:
                e -= isolated
                changed = True
        keep = []
        for i, e in enumerate(edges):
            if not e:
                changed = True
                continue
            subsumed = any(
                j != i and e <= edges[j] and (e < edges[j] or j < i)
                for j in range(len(edges))
            )
            if subsumed:
                changed = True
            else:
                keep.append(e)
        edges = keep
    return not edges


def rip_ordering_exists(contexts) -> bool:
    """Running intersection property, by brute force over context orderings."""
    sets = [set(c) for c in contexts]
    for order in itertools.permutations(range(len(sets))):
        ok = True
        for i in range(1, len(sets)):
            seen = set().union(*(sets[order[j]] for j in range(i)))
            inter = sets[order[i]] & seen
            if not any(inter <= sets[order[j]] for j in range(i)):
                ok = False
                break
        if ok:
            return True
    return False


# ---------------------------------------------------------------------------
# binary cover machinery: relations as bitmasks over local sections
# ---------------------------------------------------------------------------

def proj_table(ctx, sub):
    """Map each local section of ctx (bit i = value of ctx[i]) to its sub-section."""
    positions = [ctx.index(v) for v in sub]
    return tuple(
        sum(((s >> p) & 1) << i for i, p in enumerate(positions))
        for s in range(1 << len(ctx))
    )


def rel_proj_array(n_sections, table):
    """Array: relation bitmask -> projected relation bitmask, via the section table."""
    arr = [0] * (1 << n_sections)
    for r in range(1, 1 << n_sections):
        low = r & -r
        arr[r] = arr[r ^ low] | (1 << table[low.bit_length() - 1])
    return arr


class Cover:
    def __init__(self, name, n, contexts):
        self.name = name
        self.n = n
        self.contexts = [tuple(sorted(c)) for c in contexts]
        assert set().union(*(set(c) for c in self.contexts)) == set(range(n))
        m = len(self.contexts)
        self.loc_of_glob = []   # per context: global assignment -> local section
        self.rel_glob = []      # per context: relation mask -> mask of allowed globals
        for ctx in self.contexts:
            loc = [
                sum(((g >> v) & 1) << i for i, v in enumerate(ctx))
                for g in range(1 << n)
            ]
            self.loc_of_glob.append(loc)
            sec_glob = [0] * (1 << len(ctx))
            for g, s in enumerate(loc):
                sec_glob[s] |= 1 << g
            arr = [0] * (1 << (1 << len(ctx)))
            for r in range(1, len(arr)):
                low = r & -r
                arr[r] = arr[r ^ low] | sec_glob[low.bit_length() - 1]
            self.rel_glob.append(arr)
        # deps[i]: for each earlier overlapping context j, projection arrays onto
        # the overlap from the i side (for candidates) and the j side (for chosen).
        self.deps = [[] for _ in range(m)]
        for i in range(m):
            for j in range(i):
                ov = tuple(sorted(set(self.contexts[i]) & set(self.contexts[j])))
                if not ov:
                    continue
                ti = rel_proj_array(1 << len(self.contexts[i]),
                                    proj_table(self.contexts[i], ov))
                tj = rel_proj_array(1 << len(self.contexts[j]),
                                    proj_table(self.contexts[j], ov))
                self.deps[i].append((j, ti, tj))

    def sweep(self):
        """Exhaustively enumerate ALL pairwise-compatible families of nonempty
        relations; count logical obstructions, strong shelves, and
        answer-determined shelves. Exact, deterministic."""
        m = len(self.contexts)
        full = (1 << (1 << self.n)) - 1
        buckets = []
        for i in range(m):
            cands = range(1, 1 << (1 << len(self.contexts[i])))
            b: dict = {}
            for r in cands:
                key = tuple(ti[r] for (_, ti, _) in self.deps[i])
                b.setdefault(key, []).append(r)
            buckets.append(b)
        counts = {"families": 0, "logical": 0, "strong": 0, "strong_deny": 0}
        chosen = [0] * m
        loc_of_glob = self.loc_of_glob
        rel_glob = self.rel_glob

        def rec(i, G, deny):
            if i == m:
                counts["families"] += 1
                if G == 0:
                    counts["strong"] += 1
                    counts["logical"] += 1
                    if deny:
                        counts["strong_deny"] += 1
                    return
                projs = [0] * m
                gg = G
                while gg:
                    g = (gg & -gg).bit_length() - 1
                    gg &= gg - 1
                    for t in range(m):
                        projs[t] |= 1 << loc_of_glob[t][g]
                if any(projs[t] != chosen[t] for t in range(m)):
                    counts["logical"] += 1
                return
            key = tuple(tj[chosen[j]] for (j, _, tj) in self.deps[i])
            for r in buckets[i].get(key, ()):
                chosen[i] = r
                rec(i + 1, G & rel_glob[i][r], deny and (r & 1) == 0)
            chosen[i] = 0

        rec(0, full, True)
        return counts


def analyze_family(cov: Cover, family):
    """Exact analysis of one explicit family (canonical-instance verification)."""
    m = len(family)
    nonempty = all(r > 0 for r in family)
    compatible = all(
        ti[family[i]] == tj[family[j]]
        for i in range(m)
        for (j, ti, tj) in cov.deps[i]
    )
    G = (1 << (1 << cov.n)) - 1
    for i, r in enumerate(family):
        G &= cov.rel_glob[i][r]
    strong = G == 0
    globally_consistent = not strong
    if not strong:
        projs = [0] * m
        gg = G
        while gg:
            g = (gg & -gg).bit_length() - 1
            gg &= gg - 1
            for t in range(m):
                projs[t] |= 1 << cov.loc_of_glob[t][g]
        globally_consistent = all(projs[t] == family[t] for t in range(m))
    return {
        "nonempty": nonempty,
        "compatible": compatible,
        "n_global": bin(G).count("1"),
        "strong": strong,
        "logical": not globally_consistent,
        "deny_determined": all((r & 1) == 0 for r in family),
    }


# ---------------------------------------------------------------------------
# sweeps
# ---------------------------------------------------------------------------

def covering_edge_subsets(n):
    edges = list(itertools.combinations(range(n), 2))
    for bits in range(1, 1 << len(edges)):
        sel = [edges[k] for k in range(len(edges)) if (bits >> k) & 1]
        if set().union(*(set(e) for e in sel)) == set(range(n)):
            yield sel


def is_bipartite(n, edges):
    color = [-1] * n
    for start in range(n):
        if color[start] != -1:
            continue
        color[start] = 0
        stack = [start]
        while stack:
            u = stack.pop()
            for a, b in edges:
                v = b if a == u else (a if b == u else None)
                if v is None:
                    continue
                if color[v] == -1:
                    color[v] = color[u] ^ 1
                    stack.append(v)
                elif color[v] == color[u]:
                    return False
    return True


def ctx_letters(contexts):
    return "|".join("".join("ABCDEF"[v] for v in c) for c in contexts)


def run_cover(name, n, contexts, graph):
    cov = Cover(name, n, contexts)
    rec = {
        "name": name, "n": n, "contexts": cov.contexts,
        "gyo": gyo_acyclic(cov.contexts), "rip": rip_ordering_exists(cov.contexts),
        "graph": graph,
        "bipartite": is_bipartite(n, cov.contexts) if graph else None,
    }
    rec.update(cov.sweep())
    return rec


def check_tetra_ternary():
    """Canonical strong instance on the tetrahedron cover over a TERNARY alphabet:
    R_i = { s : sum(s) = b_i mod 3 } with b = (1,0,0,0). Pairwise marginals are all
    full (given any two coordinates the third is determined), and a global section
    needs (J-I)x = b mod 3, which is unsolvable because rank(J-I) = 3 mod 3 and
    achievable b-vectors satisfy sum(b) = 0 mod 3 while sum((1,0,0,0)) = 1."""
    q = 3
    contexts = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    bvec = (1, 0, 0, 0)
    rels = [
        {s for s in itertools.product(range(q), repeat=3) if sum(s) % q == b}
        for b in bvec
    ]
    compatible = True
    for i in range(4):
        for j in range(i):
            ov = sorted(set(contexts[i]) & set(contexts[j]))
            pi = {tuple(s[contexts[i].index(v)] for v in ov) for s in rels[i]}
            pj = {tuple(s[contexts[j].index(v)] for v in ov) for s in rels[j]}
            compatible &= pi == pj
    n_global = sum(
        1
        for g in itertools.product(range(q), repeat=4)
        if all(tuple(g[v] for v in contexts[i]) in rels[i] for i in range(4))
    )
    return all(rels) and compatible and n_global == 0


def cycle_holonomy(k):
    """On the k-cycle with constant-parity relations (EQ2 / NEQ2), a global section
    exists iff the edge-parity sum is even. Returns (law_holds, violation_count)."""
    contexts = [tuple(sorted((i, (i + 1) % k))) for i in range(k)]
    cov = Cover(f"C{k}-parity", k, contexts)
    law = True
    violations = 0
    for pattern in range(1 << k):
        family = [NEQ2 if (pattern >> e) & 1 else EQ2 for e in range(k)]
        res = analyze_family(cov, family)
        assert res["nonempty"] and res["compatible"]
        odd = bin(pattern).count("1") % 2 == 1
        law &= res["strong"] == odd
        violations += res["strong"]
    return law, violations


# pinned exact counts for the curated covers: (families, logical, strong, strong_deny)
PINNED = {
    "C3 triangle": (405, 240, 4, 1),
    "P4 path": (711, 0, 0, 0),
    "C4 cycle": (2961, 1240, 8, 0),
    "C5 cycle": (21789, 6048, 16, 1),
    "P5 path": (5211, 0, 0, 0),
    "star4": (6723, 0, 0, 0),
    "C5+chord": (136539, 109240, 2964, 15),
    "C6 cycle": (160569, 28448, 32, 0),
    "filled triangle {AB,BC,CA,ABC}": (255, 0, 0, 0),
    "hyper acyclic {ABC,ACD}": (9999, 0, 0, 0),
    "hyper cyclic {ABC,CD,DA}": (10917, 6480, 36, 9),
    "hyper acyclic matched {ABC,CD,DE}": (15975, 0, 0, 0),
    "tetrahedron {ABC,ABD,ACD,BCD}": (1893897, 1850752, 720, 102),
}
# Independent hand-derived cross-checks of the enumerator (closed forms):
# triangle compatible-family count = sum_k C(3,k) 2^(3-k) 7^C(k,2) = 405
# (choose which vertex marginals are free; 7 = # binary pair relations with both
# projections full, 1 otherwise); {ABC,ACD} pair count = 81^2+4*27^2+6*9^2+4*3^2
# = 9999 (bucket the 255 nonempty triple relations by their AC-marginal).
TRIANGLE_CLOSED_FORM = 405
ABC_ACD_CLOSED_FORM = 81 ** 2 + 4 * 27 ** 2 + 6 * 9 ** 2 + 4 * 3 ** 2


def main() -> int:
    t0 = time.time()

    # -- sweeps: ALL edge-covers of 3 and 4 variables, plus curated covers --------
    graph_sweep = []
    for n in (3, 4):
        for sel in covering_edge_subsets(n):
            graph_sweep.append(run_cover(f"n{n}:{ctx_letters(sel)}", n, sel, True))

    C5 = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4)]
    C6 = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)]
    curated_specs = [
        ("C3 triangle", 3, [(0, 1), (1, 2), (0, 2)], True),
        ("P4 path", 4, [(0, 1), (1, 2), (2, 3)], True),
        ("C4 cycle", 4, [(0, 1), (1, 2), (2, 3), (0, 3)], True),
        ("C5 cycle", 5, C5, True),
        ("P5 path", 5, [(0, 1), (1, 2), (2, 3), (3, 4)], True),
        ("star4", 5, [(0, 1), (0, 2), (0, 3), (0, 4)], True),
        ("C5+chord", 5, C5 + [(0, 2)], True),
        ("C6 cycle", 6, C6, True),
        ("filled triangle {AB,BC,CA,ABC}", 3,
         [(0, 1), (1, 2), (0, 2), (0, 1, 2)], False),
        ("hyper acyclic {ABC,ACD}", 4, [(0, 1, 2), (0, 2, 3)], False),
        ("hyper cyclic {ABC,CD,DA}", 4, [(0, 1, 2), (2, 3), (0, 3)], False),
        ("hyper acyclic matched {ABC,CD,DE}", 5, [(0, 1, 2), (2, 3), (3, 4)], False),
        ("tetrahedron {ABC,ABD,ACD,BCD}", 4,
         [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)], False),
    ]
    curated = [run_cover(name, n, ctxs, graph)
               for name, n, ctxs, graph in curated_specs]
    everything = graph_sweep + curated

    print("curated covers (exhaustive over all pairwise-compatible families, binary):")
    print(f"{'cover':38}{'acyclic':>8}{'families':>10}{'logical':>9}"
          f"{'strong':>8}{'ans-det':>8}")
    for r in curated:
        print(f"{r['name']:38}{str(r['gyo']):>8}{r['families']:>10}"
              f"{r['logical']:>9}{r['strong']:>8}{r['strong_deny']:>8}")
    n_acyc = sum(1 for r in graph_sweep if r["gyo"])
    print(f"\ngraph sweep: {len(graph_sweep)} covers over 3-4 variables "
          f"({n_acyc} acyclic, {len(graph_sweep) - n_acyc} cyclic), "
          f"{sum(r['families'] for r in graph_sweep)} families enumerated")

    # -- canonical instances ------------------------------------------------------
    c3 = Cover("C3", 3, [(0, 1), (1, 2), (0, 2)])
    specker = analyze_family(c3, [NEQ2, NEQ2, NEQ2])

    c4 = Cover("C4", 4, [(0, 1), (1, 2), (2, 3), (0, 3)])
    prbox = analyze_family(c4, [EQ2, EQ2, EQ2, NEQ2])

    path = Cover("P4", 4, [(0, 1), (1, 2), (2, 3)])
    prbox_cut = analyze_family(path, [EQ2, EQ2, EQ2])  # drop the DA context

    mixed = Cover("ABC|CD|DA", 4, [(0, 1, 2), (2, 3), (0, 3)])
    # R_ABC = {a == c, b free} = sections {000,010,101,111} = mask 165
    mixed_inst = analyze_family(mixed, [165, EQ2, NEQ2])

    holonomy = {k: cycle_holonomy(k) for k in (3, 4, 5, 6)}

    by_name = {r["name"]: r for r in curated}
    tetra = by_name["tetrahedron {ABC,ABD,ACD,BCD}"]
    filled = by_name["filled triangle {AB,BC,CA,ABC}"]
    tri = by_name["C3 triangle"]

    checks = [
        ("V1 GYO == RIP on every swept cover (independent implementations)",
         all(r["gyo"] == r["rip"] for r in everything)),
        ("V2 Vorob'ev direction: every acyclic cover has ZERO logical obstructions"
         " (exhaustive)",
         all(r["logical"] == 0 for r in everything if r["gyo"])),
        ("V3 converse on ALL swept covers (graph and hypergraph): strong shelves"
         " exist iff the cover is cyclic",
         all((r["strong"] > 0) == (not r["gyo"]) for r in everything)),
        ("V4 tetrahedron: cyclic, binary-obstructed (720 strong / 102 answer-det),"
         " plus verified canonical ternary mod-3 strong instance",
         not tetra["gyo"] and tetra["strong"] == 720
         and tetra["strong_deny"] == 102 and check_tetra_ternary()),
        ("V5 canonical instances: Specker C3 (answer-determined shelf), PR box C4"
         " (witness shelf), triangle embedding on {ABC,CD,DA}",
         specker["compatible"] and specker["strong"] and specker["deny_determined"]
         and prbox["compatible"] and prbox["strong"]
         and not prbox["deny_determined"]
         and mixed_inst["compatible"] and mixed_inst["strong"]),
        ("V6 cutting the cycle repays the debt: PR box minus one context is acyclic"
         " and globally consistent",
         gyo_acyclic(path.contexts) and prbox_cut["compatible"]
         and not prbox_cut["logical"] and prbox_cut["n_global"] == 2),
        ("V7 joint observation dissolves the shelf: triangle+ABC is alpha-acyclic"
         " with 0 obstructions; bare triangle is cyclic with strong shelves",
         filled["gyo"] and filled["logical"] == 0 and filled["families"] == 255
         and not tri["gyo"] and tri["strong"] > 0),
        ("V8 holonomy inequality on C_k (k=3..6): global section iff even parity"
         " sum; 2^(k-1) violations; COMPLETE on cycles (sweep strong count ="
         " violation count, so every cycle-cover shelf is a parity violation)",
         all(holonomy[k][0] and holonomy[k][1] == 1 << (k - 1)
             for k in (3, 4, 5, 6))
         and by_name["C3 triangle"]["strong"] == 4
         and by_name["C4 cycle"]["strong"] == 8
         and by_name["C5 cycle"]["strong"] == 16
         and by_name["C6 cycle"]["strong"] == 32),
        ("V9 answer layer is finer: answer-determined shelves iff NON-BIPARTITE;"
         " witness shelves iff CYCLIC (all swept graph covers)",
         all((r["strong_deny"] > 0) == (not r["bipartite"])
             for r in everything if r["graph"])),
        ("V10 pinned exact counts on all curated covers, plus two hand-derived"
         " closed-form family counts (enumerator cross-validation)",
         all(
             (by_name[k]["families"], by_name[k]["logical"],
              by_name[k]["strong"], by_name[k]["strong_deny"]) == v
             for k, v in PINNED.items()
         )
         and tri["families"] == TRIANGLE_CLOSED_FORM
         and by_name["hyper acyclic {ABC,ACD}"]["families"] == ABC_ACD_CLOSED_FORM
         and len(graph_sweep) == 45
         and sum(1 for r in graph_sweep if r["gyo"]) == 22),
    ]

    print()
    for name, passed in checks:
        print(f"  [{'ok' if passed else 'FAIL'}] {name}")

    ok = all(passed for _, passed in checks)
    print(f"\nruntime: {time.time() - t0:.1f}s")
    if ok:
        print(
            "\nConclusion: EXACT on the swept finite families — the section"
            " obstruction (mirage shelf) exists only on cyclic covers; on acyclic"
            " (running-intersection) covers Vorob'ev/BFMY forces a global section"
            " through every locally consistent family, with zero exceptions in"
            " exhaustive enumeration. The answer-determined shelf obeys a strictly"
            " finer criterion (odd cycles) than the witness shelf (any cycle), and"
            " the k-cycle parity inequality is a working Bell-type epistemic-debt"
            " inequality in miniature — sufficient AND complete on cycle covers."
            " Known theorem instantiated, not re-proved; no claim about LLM"
            " artifacts is made here."
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
