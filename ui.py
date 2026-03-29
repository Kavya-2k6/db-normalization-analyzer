import streamlit as st
from normalization import check_1nf, check_2nf, check_3nf, check_bcnf, minimal_cover
def render_relation_card(name: str, attrs, pk):
    pk_set = set(pk)
    rows_html = ""
    for a in sorted(attrs):
        if a in pk_set:
            rows_html += f'<div class="rel-attr-row pk-row">{a}<span class="pk-marker">PK</span></div>'
        else:
            rows_html += f'<div class="rel-attr-row">{a}</div>'
    pk_str = ", ".join(sorted(pk))
    st.markdown(f"""
<div class="card-flush">
  <div class="rel-table-header">
    <span>{name}</span>
    <span style="font-size:11px;color:var(--text-3);font-weight:400">{len(attrs)} attrs</span>
  </div>
  {rows_html}
  <div class="rel-pk-footer">PK: {pk_str}</div>
</div>""", unsafe_allow_html=True)


def render_fd_list(fds):
    rows = "".join(
        f'<div class="fd-row"><span class="fd-lhs">{", ".join(sorted(lhs))}</span>'
        f'<span class="fd-arrow">→</span>'
        f'<span style="color:var(--text-2)">{", ".join(sorted(rhs))}</span></div>'
        for lhs, rhs in fds
    )
    return f'<div class="fd-list">{rows}</div>'


def alert_box(msg, kind="info"):
    icons = {"ok": "✓", "err": "✕", "info": "ℹ", "warn": "⚠"}
    cls   = {"ok": "alert-ok", "err": "alert-err", "info": "alert-info", "warn": "alert-warn"}
    st.markdown(
        f'<div class="alert {cls[kind]}">'
        f'<span class="alert-icon">{icons[kind]}</span>'
        f'<span class="alert-body">{msg}</span></div>',
        unsafe_allow_html=True
    )


def attr_table(attrs, pk_set=None, prime_set=None):
    pk_set    = pk_set    or set()
    prime_set = prime_set or set()
    rows = ""
    for a in sorted(attrs):
        if a in pk_set:
            role = '<span class="role-label pk">Primary Key</span>'
            row_cls = ' class="attr-pk"'
        elif a in prime_set:
            role = '<span class="role-label">Prime</span>'
            row_cls = ''
        else:
            role = '<span class="role-label">Non-prime</span>'
            row_cls = ''
        rows += f'<tr{row_cls}><td>{a}</td><td style="color:var(--text-3);font-size:12px">—</td><td>{role}</td></tr>'
    return (
        '<table class="attr-table">'
        '<thead><tr><th>Attribute</th><th>Type</th><th>Key Role</th></tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )
def render_onboarding():
    st.markdown("""
<div class="how-to">
  <h3>Getting started</h3>
  <div class="step-list">
    <div class="step-item"><span class="step-num">1</span><span>Enter your relation name, attributes (comma-separated), and primary key in the sidebar — or click <strong>Load demo schema</strong> to try the AI Research Conference example.</span></div>
    <div class="step-item"><span class="step-num">2</span><span>Add functional dependencies one per line using the format <code style="font-family:var(--mono);font-size:12px;background:rgba(0,0,0,0.05);padding:1px 5px;border-radius:3px">A, B -&gt; C, D</code>.</span></div>
    <div class="step-item"><span class="step-num">3</span><span>Optionally flag multi-valued or composite attributes for 1NF analysis.</span></div>
    <div class="step-item"><span class="step-num">4</span><span>Click <strong>Run normalization →</strong> to generate the full step-by-step report.</span></div>
  </div>
</div>

<p class="section-title">Normal forms covered</p>
<div class="onboard-grid">
  <div class="onboard-card">
    <div class="nf-label">1NF</div>
    <div class="nf-name">First Normal Form</div>
    <div class="nf-desc">Atomic values, no multi-valued or composite attributes, defined primary key.</div>
  </div>
  <div class="onboard-card">
    <div class="nf-label">2NF</div>
    <div class="nf-name">Second Normal Form</div>
    <div class="nf-desc">1NF + no partial dependencies on a proper subset of the primary key.</div>
  </div>
  <div class="onboard-card">
    <div class="nf-label">3NF</div>
    <div class="nf-name">Third Normal Form</div>
    <div class="nf-desc">2NF + no transitive dependencies through non-prime attributes.</div>
  </div>
  <div class="onboard-card">
    <div class="nf-label">BCNF</div>
    <div class="nf-name">Boyce-Codd NF</div>
    <div class="nf-desc">Stricter than 3NF — every non-trivial FD determinant must be a superkey.</div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_1nf(mv_list, comp_list, pk, attrs, rname):
    st.markdown("")
    st.markdown('<p class="section-title">First Normal Form</p>', unsafe_allow_html=True)
    st.markdown("""<div class="def-block">
A relation is in <strong>1NF</strong> if all attribute domains contain only <strong>atomic values</strong>
(no sets or lists), each column has a unique name, there are no repeating groups,
and a <strong>primary key</strong> is defined.
</div>""", unsafe_allow_html=True)

    result_1nf = check_1nf(mv_list, comp_list, bool(pk))
    st.markdown('<p class="section-title">Violation check</p>', unsafe_allow_html=True)
    if result_1nf["ok"]:
        alert_box("No 1NF violations detected — the relation satisfies First Normal Form.", "ok")
    else:
        for v in result_1nf["violations"]:
            alert_box(v, "err")

    if result_1nf["fixes"]:
        st.markdown('<p class="section-title" style="margin-top:1rem">Remediation</p>', unsafe_allow_html=True)
        steps_html = "".join(
            f'<div class="step-item"><span class="step-num">{i}</span><span>{fix}</span></div>'
            for i, fix in enumerate(result_1nf["fixes"], 1)
        )
        st.markdown(f'<div class="card"><div class="step-list">{steps_html}</div></div>', unsafe_allow_html=True)

    st.markdown('<p class="section-title" style="margin-top:1rem">Resulting schema after 1NF</p>', unsafe_allow_html=True)
    clean_attrs = attrs - frozenset(mv_list) - frozenset(comp_list)
    for ca in comp_list:
        clean_attrs = clean_attrs | frozenset([f"{ca}_Part1", f"{ca}_Part2"])
    c1, c2, c3 = st.columns(3)
    with c1:
        render_relation_card(rname, clean_attrs, pk)
    if mv_list:
        for i, mv in enumerate(mv_list):
            with [c2, c3][i % 2]:
                render_relation_card(f"{mv} (separated)", pk | frozenset([mv]), pk)


def render_2nf(attrs, fds, cks, pk, rname):
    st.markdown("")
    st.markdown('<p class="section-title">Second Normal Form</p>', unsafe_allow_html=True)
    st.markdown("""<div class="def-block">
A relation is in <strong>2NF</strong> if it is in 1NF and every <strong>non-prime attribute</strong>
is <strong>fully functionally dependent</strong> on the entire primary key —
i.e., no non-prime attribute depends on a <em>proper subset</em> of the PK.
</div>""", unsafe_allow_html=True)

    result_2nf = check_2nf(attrs, fds, cks, pk)
    st.markdown('<p class="section-title">Partial dependency analysis</p>', unsafe_allow_html=True)
    if result_2nf.get("note"):
        alert_box(result_2nf["note"], "info")
    elif result_2nf["ok"]:
        alert_box("No partial dependencies found — the relation satisfies 2NF.", "ok")
    else:
        for v in result_2nf["violations"]:
            alert_box(v, "err")

    st.markdown('<p class="section-title" style="margin-top:1rem">Decomposed relations</p>', unsafe_allow_html=True)
    relations = result_2nf.get("relations", {})
    if result_2nf["ok"] or result_2nf.get("note") or not relations:
        c1, _, _ = st.columns(3)
        with c1:
            render_relation_card(f"{rname} (no change)", attrs, pk)
    else:
        cols = st.columns(min(len(relations), 3))
        for i, (rn, (rpk, rattrs)) in enumerate(relations.items()):
            with cols[i % len(cols)]:
                render_relation_card(rn, rattrs, rpk)
        st.markdown('<p class="section-title" style="margin-top:1rem">Explanation</p>', unsafe_allow_html=True)
        for rn, (rpk, rattrs) in relations.items():
            non_key = rattrs - rpk
            alert_box(
                f"<strong>{rn}</strong> · PK: <code>{', '.join(sorted(rpk))}</code> · "
                f"Non-key: <code>{', '.join(sorted(non_key)) or '—'}</code>",
                "info"
            )


def render_3nf(attrs, fds, cks, rname):
    st.markdown("")
    st.markdown('<p class="section-title">Third Normal Form</p>', unsafe_allow_html=True)
    st.markdown("""<div class="def-block">
A relation is in <strong>3NF</strong> if it is in 2NF and for every non-trivial FD <strong>X → A</strong>,
either (1) X is a <strong>superkey</strong>, or (2) A is a <strong>prime attribute</strong>.
This eliminates <strong>transitive dependencies</strong>.
</div>""", unsafe_allow_html=True)

    result_3nf = check_3nf(attrs, fds, cks)
    st.markdown('<p class="section-title">Transitive dependency analysis</p>', unsafe_allow_html=True)
    if result_3nf["ok"]:
        alert_box("No transitive dependencies — the relation satisfies 3NF.", "ok")
    else:
        for v in result_3nf["violations"]:
            alert_box(f"<code>{v['fd']}</code> — {v['reason']}", "err")

    mc = minimal_cover(fds)
    st.markdown('<p class="section-title" style="margin-top:1rem">Minimal cover</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="card" style="padding:0.75rem 1.1rem">{render_fd_list(mc)}</div>', unsafe_allow_html=True)

    st.markdown('<p class="section-title" style="margin-top:1rem">3NF decomposition (synthesis algorithm)</p>', unsafe_allow_html=True)
    relations_3nf = result_3nf["relations"]
    if relations_3nf:
        cols = st.columns(min(len(relations_3nf), 3))
        for i, rel in enumerate(relations_3nf):
            with cols[i % len(cols)]:
                render_relation_card(rel["name"], rel["attrs"], rel["pk"])

    st.markdown('<p class="section-title" style="margin-top:1rem">Algorithm steps</p>', unsafe_allow_html=True)
    st.markdown("""<div class="card"><div class="step-list">
  <div class="step-item"><span class="step-num">1</span><span><strong>Minimal cover</strong> — decompose RHS to singletons, remove redundant LHS attributes, remove redundant FDs.</span></div>
  <div class="step-item"><span class="step-num">2</span><span><strong>Create one relation per FD group</strong> — for each FD X → Y in the minimal cover, create R(X ∪ Y) with X as key.</span></div>
  <div class="step-item"><span class="step-num">3</span><span><strong>Preserve a candidate key</strong> — if no resulting relation contains a CK of the original schema, add one.</span></div>
  <div class="step-item"><span class="step-num">4</span><span><strong>Eliminate subsumed relations</strong> — remove any relation whose attribute set is a subset of another's.</span></div>
</div></div>""", unsafe_allow_html=True)


def render_bcnf(attrs, fds, cks, rname):
    st.markdown("")
    st.markdown('<p class="section-title">Boyce-Codd Normal Form</p>', unsafe_allow_html=True)
    st.markdown("""<div class="def-block">
A relation is in <strong>BCNF</strong> if for every non-trivial FD <strong>X → Y</strong>,
X is a <strong>superkey</strong>. BCNF is strictly stronger than 3NF — it eliminates all
remaining redundancy but may not preserve every functional dependency.
</div>""", unsafe_allow_html=True)

    result_bcnf = check_bcnf(attrs, fds, cks)
    st.markdown('<p class="section-title">Superkey violation analysis</p>', unsafe_allow_html=True)
    if result_bcnf["ok"]:
        alert_box("No BCNF violations — the relation already satisfies BCNF.", "ok")
    else:
        for v in result_bcnf["violations"]:
            alert_box(f"<code>{v['fd']}</code> — {v['reason']}", "err")

    st.markdown('<p class="section-title" style="margin-top:1rem">BCNF decomposition</p>', unsafe_allow_html=True)
    relations_bcnf = result_bcnf["relations"]
    for i, rel in enumerate(relations_bcnf):
        rel["name"] = f"{rname}{i + 1}"
    if relations_bcnf:
        cols = st.columns(min(len(relations_bcnf), 3))
        for i, rel in enumerate(relations_bcnf):
            with cols[i % len(cols)]:
                render_relation_card(rel["name"], rel["attrs"], rel["pk"])

    st.markdown('<p class="section-title" style="margin-top:1rem">Decomposition algorithm</p>', unsafe_allow_html=True)
    st.markdown("""<div class="card"><div class="step-list">
  <div class="step-item"><span class="step-num">1</span><span>Find a violating FD <strong>X → Y</strong> where X is not a superkey of R.</span></div>
  <div class="step-item"><span class="step-num">2</span><span>Compute <strong>X⁺</strong> (closure of X under all FDs applicable to R).</span></div>
  <div class="step-item"><span class="step-num">3</span><span>Decompose: <strong>R₁ = X⁺</strong> (key is X) and <strong>R₂ = (R − X⁺) ∪ X</strong> (X serves as FK).</span></div>
  <div class="step-item"><span class="step-num">4</span><span>Recurse on R₁ and R₂ until all resulting relations satisfy BCNF.</span></div>
</div></div>""", unsafe_allow_html=True)

    alert_box(
        "BCNF guarantees <strong>lossless joins</strong> but may not preserve all functional dependencies — "
        "a known trade-off compared to 3NF synthesis.", "warn"
    )

    st.markdown('<p class="section-title" style="margin-top:1rem">3NF vs BCNF comparison</p>', unsafe_allow_html=True)
    st.markdown("""
<div class="card-flush">
  <table class="cmp-table">
    <thead><tr><th>Property</th><th>3NF</th><th>BCNF</th></tr></thead>
    <tbody>
      <tr><td>Lossless decomposition</td><td>Always</td><td>Always</td></tr>
      <tr><td>Dependency preservation</td><td>Always</td><td>Not always</td></tr>
      <tr><td>Redundancy elimination</td><td>Partial</td><td>Complete</td></tr>
      <tr><td>Condition on X → Y</td><td>X is superkey <em>or</em> Y is prime</td><td>X must be superkey</td></tr>
      <tr><td>Strictness</td><td>Less strict</td><td>Stricter</td></tr>
    </tbody>
  </table>
</div>""", unsafe_allow_html=True)
