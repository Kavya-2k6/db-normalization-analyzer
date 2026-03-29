from itertools import combinations


def parse_attributes(attr_str: str) -> list:
    return [a.strip() for a in attr_str.replace(";", ",").split(",") if a.strip()]


def parse_fds(fd_str: str) -> list:
    fds = []
    for line in fd_str.strip().splitlines():
        line = line.strip()
        if not line or "->" not in line:
            continue
        lhs, rhs = line.split("->", 1)
        lhs_set = set(parse_attributes(lhs))
        rhs_set = set(parse_attributes(rhs))
        if lhs_set and rhs_set:
            fds.append((lhs_set, rhs_set))
    return fds


def closure(attrs: set, fds: list) -> set:
    result = set(attrs)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in fds:
            if lhs <= result and not rhs <= result:
                result.update(rhs)
                changed = True
    return result


def find_candidate_keys(attrs: set, fds: list) -> list:
    cks = []
    for size in range(1, len(attrs) + 1):
        for combo in combinations(sorted(attrs), size):
            s = set(combo)
            if closure(s, fds) == attrs and not any(ck < s for ck in cks):
                cks.append(s)
    return cks


def prime_attributes(cks: list) -> set:
    return {a for ck in cks for a in ck}


def minimal_cover(fds):
    single = [(set(lhs), {r}) for lhs, rhs in fds for r in rhs]
    reduced = []
    for lhs, rhs in single:
        min_lhs = set(lhs)
        for attr in lhs:
            candidate = lhs - {attr}
            if candidate and closure(candidate, single) >= rhs:
                min_lhs = candidate
        reduced.append((min_lhs, rhs))
    seen, mc = [], []
    for lhs, rhs in reduced:
        key = (frozenset(lhs), frozenset(rhs))
        if key not in seen:
            seen.append(key)
            mc.append((set(lhs), set(rhs)))
    return mc


def check_1nf(multivalued, composite, has_pk):
    violations, fixes = [], []
    if multivalued:
        violations.append(f"Multi-valued attributes: <code>{', '.join(multivalued)}</code>")
        fixes.extend(f"Move <code>{mv}</code> into a separate relation with the PK as foreign key." for mv in multivalued)
    if composite:
        violations.append(f"Composite attributes: <code>{', '.join(composite)}</code>")
        fixes.extend(f"Decompose <code>{ca}</code> into atomic sub-attributes." for ca in composite)
    if not has_pk:
        violations.append("No primary key — each tuple must be uniquely identifiable.")
        fixes.append("Add a surrogate or natural primary key.")
    return {"violations": violations, "fixes": fixes, "ok": not violations}


def check_2nf(attrs, fds, cks, pk):
    primes = prime_attributes(cks)
    non_primes = attrs - primes
    if len(pk) == 1:
        return {"violations": [], "decomposed": {}, "relations": {}, "ok": True,
                "note": "Single-attribute primary key — partial dependencies are impossible — already satisfies 2NF."}
    violations, decomposed = [], {}
    for lhs, rhs in fds:
        partial_np = rhs & non_primes
        if lhs < pk and partial_np:
            violations.append(
                f"<code>{{{', '.join(sorted(lhs))}}}</code> → <code>{{{', '.join(sorted(partial_np))}}}</code> — partial dependency"
            )
            key = tuple(sorted(lhs))
            if key not in decomposed:
                decomposed[key] = set()
            decomposed[key].update(partial_np)
    relations = {}  # type: ignore
    if violations:
        partial_attrs = set()
        for v in decomposed.values():
            partial_attrs |= v
        main_rel_attrs = pk | (non_primes - partial_attrs) | primes
        relations["Main Relation"] = (pk, main_rel_attrs)
        for det, dep in decomposed.items():
            det_set = set(det)
            relations[f"Decomposed ({', '.join(sorted(det))})"] = (det_set, det_set | dep)
    return {"violations": violations, "decomposed": decomposed, "relations": relations, "ok": not violations}


def synthesis_3nf(attrs, fds, cks):
    mc = minimal_cover(fds)
    relations, covered = [], set()
    for lhs, rhs in mc:
        rel_attrs = lhs | rhs
        ck_for_rel = find_candidate_keys(rel_attrs, [(l, r) for l, r in mc if l <= rel_attrs])
        relations.append({"name": f"R_{', '.join(sorted(lhs))}", "attrs": rel_attrs, "pk": ck_for_rel[0] if ck_for_rel else set(lhs)})
        covered |= rel_attrs
    if cks and not any(ck <= covered for ck in cks):
        relations.append({"name": "R_KEY", "attrs": cks[0], "pk": cks[0]})
    return relations


def check_3nf(attrs, fds, cks):
    primes = prime_attributes(cks)
    violations = []
    for lhs, rhs in fds:
        non_prime_rhs = rhs - primes
        if non_prime_rhs and closure(lhs, fds) != attrs:
            violations.extend({"fd": f"{{{', '.join(sorted(lhs))}}} → {a}", "reason": "LHS is not a superkey and RHS is non-prime (transitive dependency)"} for a in non_prime_rhs)
    return {"violations": violations, "relations": synthesis_3nf(attrs, fds, cks), "ok": not violations}


def check_bcnf(attrs, fds, cks):
    violations = []
    for lhs, rhs in fds:
        non_trivial = rhs - lhs
        if non_trivial and closure(lhs, fds) != attrs:
            violations.append({"fd": f"{{{', '.join(sorted(lhs))}}} → {{{', '.join(sorted(non_trivial))}}}", "reason": "LHS is not a superkey"})
    return {"violations": violations, "relations": decompose_bcnf(attrs, fds), "ok": not violations}


def decompose_bcnf(attrs, fds, depth=0):
    if depth > 15:
        return [{"name": "R", "attrs": attrs, "pk": attrs}]
    cks = find_candidate_keys(attrs, fds)
    for lhs, rhs in fds:
        non_trivial = rhs - lhs
        if not non_trivial or not (lhs <= attrs and non_trivial <= attrs):
            continue
        local_fds = [(l, r) for l, r in fds if l <= attrs and r <= attrs]
        if closure(lhs, local_fds) != attrs:
            r1_attrs = closure(lhs, local_fds) & attrs
            r2_attrs = attrs - (r1_attrs - lhs)
            result = []
            for ra, rf in [(r1_attrs, fds), (r2_attrs, fds)]:
                sub_fds = [(l, r & ra) for l, r in rf if l <= ra and r & ra]
                result.extend(decompose_bcnf(ra, sub_fds, depth + 1))
            return result
    return [{"name": "R", "attrs": attrs, "pk": cks[0] if cks else attrs}]