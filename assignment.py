import streamlit as st # type: ignore
import os

from normalization import (
    parse_attributes, parse_fds,
    closure, find_candidate_keys, prime_attributes,
    minimal_cover,
    check_1nf, check_2nf, check_3nf, check_bcnf,
)
from ui import (
    render_relation_card, render_fd_list, alert_box, attr_table,
    render_onboarding, render_1nf, render_2nf, render_3nf, render_bcnf
)

st.set_page_config(
    page_title="NormFlow · DB Normalization",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(css_path, "r", encoding="utf-8") as f:
    CSS = f"<style>\n{f.read()}\n</style>"
st.markdown(CSS, unsafe_allow_html=True)

DEMO = {
    "rel_name":       "ConferencePaperSubmission",
    "attributes_raw": "PaperID, AuthorID, ReviewerID, Title, TrackID, TrackName, ReviewScore, Decision",
    "pk_raw":         "PaperID, AuthorID, ReviewerID",
    "mv_raw":         "",
    "comp_raw":       "",
    "fds_raw":        "PaperID -> Title, TrackID, Decision\nTrackID -> TrackName\nPaperID, ReviewerID -> ReviewScore",
}

with st.sidebar:
    st.markdown("""
<div class="sidebar-brand">
  <div>
    <div class="brand-name">Norm<span class="brand-dot">Flow</span></div>
    <div class="brand-sub">Normalization Engine</div>
  </div>
</div>""", unsafe_allow_html=True)

    def _load_demo():
        st.session_state["rel_name_input"] = DEMO["rel_name"]
        st.session_state["attr_input"]     = DEMO["attributes_raw"]
        st.session_state["pk_input"]       = DEMO["pk_raw"]
        st.session_state["fd_input"]       = DEMO["fds_raw"]
        st.session_state["mv_input"]       = DEMO["mv_raw"]
        st.session_state["comp_input"]     = DEMO["comp_raw"]

    st.button("Load demo schema", use_container_width=True, on_click=_load_demo)

    st.markdown('<span class="sidebar-label">Relation name</span>', unsafe_allow_html=True)
    st.text_input("r", placeholder="e.g. ConferencePaperSubmission",
                  label_visibility="collapsed", key="rel_name_input")

    st.markdown('<span class="sidebar-label">Attributes</span>', unsafe_allow_html=True)
    st.caption("Comma-separated")
    st.text_area("a", height=100, placeholder="PaperID, Title, AuthorID, ...",
                 label_visibility="collapsed", key="attr_input")

    st.markdown('<span class="sidebar-label">Primary key</span>', unsafe_allow_html=True)
    st.caption("Comma-separated")
    st.text_input("p", placeholder="PaperID, AuthorID",
                  label_visibility="collapsed", key="pk_input")

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-label">Functional dependencies</span>', unsafe_allow_html=True)
    st.caption("One per line · `A, B -> C, D`")
    st.text_area("f", height=160,
                 placeholder="PaperID -> Title, TrackID\nAuthorID -> AuthorName",
                 label_visibility="collapsed", key="fd_input")

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-label">1NF flags</span>', unsafe_allow_html=True)
    st.text_input("Multi-valued attrs", placeholder="e.g. PhoneNumbers", key="mv_input")
    st.text_input("Composite attrs",    placeholder="e.g. FullName",     key="comp_input")

    st.markdown('<div class="sidebar-section"></div>', unsafe_allow_html=True)
    run = st.button("Run normalization →", use_container_width=True)

rel_name       = st.session_state.get("rel_name_input", "")
attributes_raw = st.session_state.get("attr_input", "")
pk_raw         = st.session_state.get("pk_input", "")
fds_raw        = st.session_state.get("fd_input", "")
mv_raw         = st.session_state.get("mv_input", "")
comp_raw       = st.session_state.get("comp_input", "")

st.markdown("""
<div class="page-header">
  <span class="logo">Norm<span>Flow</span></span>
  <span class="tagline">Step-by-step database normalization · 1NF → 2NF → 3NF → BCNF</span>
</div>
""", unsafe_allow_html=True)

if not run:
    render_onboarding()
    st.stop()

attrs     = frozenset(parse_attributes(attributes_raw))
pk        = frozenset(parse_attributes(pk_raw))
fds       = parse_fds(fds_raw)
mv_list   = parse_attributes(mv_raw)  if mv_raw.strip()   else []
comp_list = parse_attributes(comp_raw) if comp_raw.strip() else []

if not attrs: st.error("Please enter at least one attribute."); st.stop()
if not pk:    st.error("Please declare a primary key.");        st.stop()

if pk - attrs:
    attrs = attrs | pk

cks    = find_candidate_keys(attrs, fds) or [pk]
primes = prime_attributes(cks)
rname  = rel_name or "R"

st.markdown(f"### {rname}")
col_l, col_r = st.columns([3, 2])

with col_l:
    st.markdown('<p class="section-title">Attributes</p>', unsafe_allow_html=True)
    st.markdown(f'<div style="margin-bottom:1.25rem">{attr_table(attrs, pk_set=set(pk), prime_set=primes)}</div>',
                unsafe_allow_html=True)
    st.markdown('<p class="section-title">Functional dependencies</p>', unsafe_allow_html=True)
    st.markdown(f'<div style="padding:0.25rem 0">{render_fd_list(fds)}</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<p class="section-title">Keys</p>', unsafe_allow_html=True)
    dot     = " \u00b7 "
    pk_str  = dot.join(sorted(pk))
    ck_rows = "".join(
        f'<div class="rel-attr-row" style="font-size:12.5px">{dot.join(sorted(ck))}</div>'
        for ck in cks
    )
    st.markdown(f"""
<div class="card-flush" style="margin-bottom:0.75rem">
  <div class="card-header"><span class="card-title">Primary key</span></div>
  <div class="card-body" style="padding:0.6rem 1rem">
    <span style="font-family:var(--mono);font-size:13px;color:var(--accent);font-weight:500">{pk_str}</span>
  </div>
</div>
<div class="card-flush">
  <div class="card-header">
    <span class="card-title">Candidate keys</span>
    <span class="badge badge-neutral" style="margin-left:auto;font-size:10px">{len(cks)}</span>
  </div>
  {ck_rows}
</div>""", unsafe_allow_html=True)

    st.markdown('<p class="section-title" style="margin-top:1rem">Prime / Non-prime split</p>', unsafe_allow_html=True)
    non_primes = attrs - primes
    _em = "\u2014"
    st.markdown(f"""
<div style="padding:0.5rem 0">
  <div style="margin-bottom:0.75rem">
    <span style="font-size:10.5px;color:var(--text-3);font-weight:600;letter-spacing:0.04em;text-transform:uppercase">Prime</span><br>
    <span style="font-family:var(--mono);font-size:12.5px;color:var(--text)">{dot.join(sorted(primes)) or _em}</span>
  </div>
  <div>
    <span style="font-size:10.5px;color:var(--text-3);font-weight:600;letter-spacing:0.04em;text-transform:uppercase">Non-prime</span><br>
    <span style="font-family:var(--mono);font-size:12.5px;color:var(--text-2)">{dot.join(sorted(non_primes)) or _em}</span>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["1NF", "2NF", "3NF", "BCNF"])

with tab1:
    render_1nf(mv_list, comp_list, pk, attrs, rname)

with tab2:
    render_2nf(attrs, fds, cks, pk, rname)

with tab3:
    render_3nf(attrs, fds, cks, rname)

with tab4:
    render_bcnf(attrs, fds, cks, rname)


st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<p class="section-title">Normalization summary</p>', unsafe_allow_html=True)

r1 = check_1nf(mv_list, comp_list, bool(pk))
r2 = check_2nf(attrs, fds, cks, pk)
r3 = check_3nf(attrs, fds, cks)
r4 = check_bcnf(attrs, fds, cks)

summary = [
    ("1NF",  r1["ok"],                          "Atomic values, no repeating groups"),
    ("2NF",  r2["ok"] or bool(r2.get("note")),  "No partial dependencies"),
    ("3NF",  r3["ok"],                           "No transitive dependencies"),
    ("BCNF", r4["ok"],                           "Every determinant is a superkey"),
]
cells = ""
for label, ok, desc in summary:
    status_text  = "Satisfied"      if ok else "Violation found"
    status_color = "var(--success)" if ok else "var(--danger)"
    cls  = "ok"  if ok else "err"
    icon = "✓"   if ok else "✕"
    cells += f"""
<div class="summary-cell {cls}">
  <div class="snf">{label}</div>
  <div class="sdesc">{desc}</div>
  <div class="sstatus" style="color:{status_color}">{icon} {status_text}</div>
</div>"""

st.markdown(f'<div class="summary-row">{cells}</div>', unsafe_allow_html=True)