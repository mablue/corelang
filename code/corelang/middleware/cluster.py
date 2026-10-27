"""Clustering via union-find."""

from collections import defaultdict
from .distance import d_lambda, levenshtein, jaccard_bigrams

class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb: return
        if self.rank[ra] < self.rank[rb]: ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]: self.rank[ra] += 1

def cluster_exact(units, lang, threshold=2):
    by_len = defaultdict(list)
    for i, u in enumerate(units):
        by_len[len(u['tokens'])].append(i)
    dsu = DSU(len(units))
    pc = pm = 0
    for L, idxs in by_len.items():
        if len(idxs) < 2: continue
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                a, b = idxs[i], idxs[j]
                pc += 1
                r = d_lambda(units[a]['tokens'], units[b]['tokens'], lang)
                if r is None: continue
                if r['d_lambda'] <= threshold:
                    pm += 1
                    dsu.union(a, b)
    groups = defaultdict(list)
    for i in range(len(units)): groups[dsu.find(i)].append(i)
    return {k: v for k, v in groups.items() if len(v) >= 2}, pc, pm

def cluster_fuzzy(units, lang, threshold=0.6):
    n = len(units); dsu = DSU(n); comps = levis = 0
    for i in range(n):
        a = units[i]['norm_tokens']
        for j in range(i + 1, n):
            b = units[j]['norm_tokens']
            la, lb = len(a), len(b)
            if la == 0 or lb == 0: continue
            ml = max(la, lb)
            if min(la, lb) / ml < threshold - 0.1: continue
            comps += 1
            if jaccard_bigrams(a, b) < threshold - 0.2: continue
            levis += 1
            d = levenshtein(a, b)
            if 1 - d / ml >= threshold: dsu.union(i, j)
    groups = defaultdict(list)
    for i in range(n): groups[dsu.find(i)].append(i)
    return {k: v for k, v in groups.items() if len(v) >= 2}, comps, levis
