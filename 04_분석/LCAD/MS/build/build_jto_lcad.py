# build_jto_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm
from jkms_engine import JKMS
import content_lcad as C
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_lcad.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "01_manuscript.md")
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "[ZENODO DOI]"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
IRB = "This study was performed in line with the principles of the Declaration of Helsinki. The Institutional Review Board of Hongik University approved the study on November 4, 2025 (Approval No. 7002340-202511-HR-012) and its continuing review on November 3, 2026 (Approval No. 7002340-202611-HR-040)."
CONSENT = "The Institutional Review Board of Hongik University waived informed consent because only published aggregate statistics were used."
FUNDING = "No specific funding was disclosed."
CONTRIB = "Seongdae Kim: Conceptualization, data curation, formal analysis, investigation, methodology, software, visualization, writing - original draft, and writing - review and editing."
COI = "The author declares no conflict of interest."
AI_DECL = "During the preparation of this work the author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing. After using these tools, the author reviewed and edited the content as needed and takes full responsibility for the content of the publication."
ABBREV = "BYM2, Besag-York-Mollié 2; CrI, credible interval; KH, Knorr-Held; RR, rate ratio; SD, standard deviation; WAIC, widely applicable information criterion."
def data_statement(): return "All source data are publicly available from the national statistics cited in the Materials and Methods. The processed analytic data are available from the author on reasonable request."
def code_statement(): return f"The analysis code and the scripts that generate every number, table and figure are openly available on Zenodo under the MIT license (https://doi.org/{ZENODO})."
def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t):   # JTO(AMA): 위첨자 번호, 마침표·쉼표 밖(뒤), 쌍점·쌍반점 안(앞)
    t = re.sub(r"\s*\[(@[^\]]+)\]", lambda m: "{{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
    return re.sub(r"(\{\{[^}]+\}\})([.,])", r"\2\1", t)
def strip(t): return re.sub(r"\{\{[^}]+\}\}|<[^>]+>", "", re.sub(r"\s*\[@[^\]]+\]", "", t))
def all_keys():
    src = open(os.path.join(HERE, "content_lcad.py"), encoding="utf-8").read() + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()

KEEP = {"South", "Republic", "Korea", "Korean", "Bayesian", "United", "States", "US", "Gaussian", "Laplace", "Poisson", "England", "Seoul", "Busan", "Organization", "Economic", "Co-operation",
        "Development", "OECD", "GLOBOCAN", "STROBE", "Statement", "E-Value", "CT", "Lung-RADS", "Korean", "Beijing", "Taiwan", "Victoria", "Australia"}
def sent(t):   # 참고문헌 제목 문장형 통일: 첫 단어·고유명사·약어 유지
    w = t.split(" "); caps = sum(1 for x in w[1:] if x[:1].isupper())
    if len(w) < 4 or caps < 0.5 * (len(w) - 1): return t
    out = [w[0]]
    for x in w[1:]:
        core = x.strip("(),:;.?")
        keep = core in KEEP or core.isupper() or any(c.isdigit() for c in core) or out[-1].endswith((":", "?")) or (core.split("-")[0] in KEEP)
        if not keep: x = x[:1].lower() + x[1:]
        x = "-".join([x.split("-")[0]] + [y if (y in KEEP or y.isupper()) else y[:1].lower() + y[1:] for y in x.split("-")[1:]])
        out.append(x)
    t2 = " ".join(out)
    for ph in ("Community Health Survey", "E-value", "Korean Lung Cancer Screening"): t2 = re.sub(re.escape(ph), ph, t2, flags=re.I)
    return t2.replace("E-Value", "E-value")
def ref(k):   # AMA 11판: 저자 6명 이하 전원, 7명 이상 3명 + et al. 제목. 약어 학술지. 연도;권(호):쪽. doi:
    r = REFS[k]
    if r["type"] == "web": return f"{r['authors']}. {r['title']}. Published {r['year']}. Accessed {r['accessed']}. {r['url']}"
    au = [re.sub(r"^([A-Z][a-z]+) ([A-Z])([a-z])$", lambda m: f"{m.group(1)} {m.group(2)}{m.group(3).upper()}", x) for x in r["authors"]]
    a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:3]) + ", et al"
    t = sent(r["title"].rstrip(".")); t = t + ("" if t.endswith(("?", "!")) else ".")
    s_ = f"{a}. {t} {r['journal']}. {r['year']}"
    if r.get("vol"): s_ += f";{r['vol']}" + (f"({r['issue']})" if r.get("issue") else "")
    if r.get("pages"): s_ += f":{r['pages']}"
    return s_ + (f". doi:{r['doi']}" if r.get("doi") else "")

class TX(JKMS):
    raw = False
    def save(self, path):   # 줄번호 유지, 머리·바닥글 문단은 줄번호 제외
        for s_ in self.doc.sections:
            for part in (s_.header, s_.footer, s_.first_page_header, s_.first_page_footer):
                for p in part.paragraphs:
                    pPr = p._p.get_or_add_pPr()
                    if pPr.find(qn("w:suppressLineNumbers")) is None: pPr.append(OxmlElement("w:suppressLineNumbers"))
        return super().save(path)
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)   # 음수는 U+2212
        return super()._emit(p, text, sz, bold, italic)

TAB1_COV = [("pop80_share", "Population aged 80 years or older, %"), ("urban_population_share", "Urban population share, %"),
            ("ext__genhosp_per100k", "General hospitals per 100,000"), ("outside_care_share", "Out-of-district outpatient share, %"), ("ext__cancer_screen_rate", "Cancer screening uptake, %"),
            ("current_smoking_rate", "Current smoking, %"), ("coal_plant_host", "Coal-fired power plant in district, %<sup>d</sup>"), ("factory_land_share", "Factory land, % of area"),
            ("detached_house_households", "Households in detached houses, %<sup>e</sup>"), ("prior_tb_share", "Previous tuberculosis at screening, %"),
            ("walking_practice_rate", "Walking practice, %"), ("moderate_pa_rate", "Moderate-to-vigorous physical activity, %"), ("public_sports_facilities_per_100k", "Public sports facilities per 100,000"),
            ("basic_livelihood_rate", "Basic livelihood recipients, %"), ("tertiary_educated_share", "Tertiary education, %")]
def table1():
    T = N["T1"]; cols = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "2011-2024"]
    q = lambda t: f"{t[1]:.2f} ({t[0]:.2f}-{t[2]:.2f})"
    rows = [["__H__", "Deaths and treated persons"],
            ["  District-years, n"] + [f"{T[c]['n']:,}" for c in cols],
            ["  Deaths, n"] + [f"{T[c]['cases']:,}" for c in cols],
            ["  Persons treated, sum of annual counts<sup>a</sup>"] + [f"{T[c]['care']:,}" for c in cols],
            ["  Age-standardized death rate per 100,000<sup>b</sup>"] + [f"{T[c]['asr']:.1f}" for c in cols],
            ["  Deaths per 100 persons treated"] + [f"{T[c]['ratio']:.1f}" for c in cols],
            ["__H__", "District ratios, median (10th-90th percentile)<sup>c</sup>"],
            ["  Standardized mortality ratio"] + [q(T[c]['smr']) for c in cols],
            ["  Treatment ratio"] + [q(T[c]['care_sir']) for c in cols],
            ["  Mortality-to-treatment ratio"] + [q(T[c]['mtr']) for c in cols],
            ["__H__", "District characteristics, mean (standard deviation)"]]
    for v, lab in TAB1_COV:
        sc = 100 if v == "coal_plant_host" else 1
        mx = max(abs(sc * T[c]['cov'][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 5 else 1)
        rows.append([f"  {lab}"] + [f"{sc*T[c]['cov'][v][0]:,.{dp}f} ({sc*T[c]['cov'][v][1]:,.{dp}f})" for c in cols])
    foot = ("<sup>a</sup>Sum of annual persons treated for lung cancer under national health insurance; a person treated in several years is counted in each year. "
            f"<sup>b</sup>Direct standardization to the 2015 national population; window values are means of annual rates ({N['asr_2011']:.1f} in 2011 and {N['asr_2024']:.1f} in 2024). "
            "<sup>c</sup>Observed over indirectly age-standardized expected counts summed over the window; for the mortality-to-treatment ratio, expected deaths were multiplied by the treatment ratio and rescaled to national deaths separately in each year before summation. "
            "<sup>d</sup>Share of district-years in districts hosting a coal-fired power plant in 2011-2024 (time-invariant indicator). <sup>e</sup>Mean of 2015-2024, held constant within district. "
            "Lung cancer, International Classification of Diseases, 10th revision, C33-C34.")
    return ("Table 1. Lung cancer deaths, treated persons and district characteristics by calendar window, 3,206 district-years in Korea, 2011-2024", ["Characteristic", "2011-2015", "2016-2019", "2020-2024", "2011-2024"], rows, foot)

GROUPS = [("Care access and detection", ["ext__genhosp_per100k", "outside_care_share", "ext__cancer_screen_rate"]),
          ("Smoking", ["current_smoking_rate"]),
          ("Air and residential exposure", ["coal_plant_host", "factory_land_share", "detached_house_households"]),
          ("Previous lung disease", ["prior_tb_share"]),
          ("Physical activity", ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]),
          ("Socioeconomic position", ["basic_livelihood_rate", "tertiary_educated_share"]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {"ext__genhosp_per100k": "General hospitals", "outside_care_share": "Out-of-district outpatient share", "ext__cancer_screen_rate": "Cancer screening uptake",
         "current_smoking_rate": "Current smoking", "coal_plant_host": "Coal-fired power plant", "factory_land_share": "Factory land", "detached_house_households": "Detached-house households",
         "prior_tb_share": "Previous tuberculosis", "walking_practice_rate": "Walking practice", "moderate_pa_rate": "Moderate-to-vigorous activity", "public_sports_facilities_per_100k": "Public sports facilities",
         "basic_livelihood_rate": "Basic livelihood recipients", "tertiary_educated_share": "Tertiary education", "urban_population_share": "Urban population share",
         "physicians_per_1000": "Physicians per 1,000", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Population aged 80 years or older"}
BEST_KH = min(("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV"), key=lambda a: N["s43_waic"][a]); assert BEST_KH == "KH_typeIV"
from decimal import Decimal, ROUND_HALF_UP
_pct = lambda f: str(int(Decimal(str(round(100 * f, 6))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
def table2():
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    f = lambda t: f"{t[0]:.3f} ({t[1]:.3f}-{t[2]:.3f})"
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); k = N["s43"][(BEST_KH, v)]; sm = N["sens_main"]["smr"][v]
            rows.append([f"  {LABEL[v]}", f((m["IRR"], m["lo"], m["hi"])), _pct(mv["cred_frac"]) if mv else "–", f(k), f(sm)])
    foot = (f"RR, rate ratio of the age-standardized ratio of lung cancer deaths to treated persons per 1 standard deviation increase in the characteristic; CrI, credible interval. Principal model, Poisson with a Besag-York-Mollié 2 district effect, random-walk and independent year effects and an offset of log expected deaths multiplied by the treatment ratio (n={N['n_rows']:,} district-years); all 13 district characteristics and five forced controls are shown. "
            f"<sup>a</sup>Share of the 200 covariate-subset fits containing the characteristic in which the CrI excluded 1; –, forced into every fit. "
            f"<sup>b</sup>Principal model plus a Knorr-Held type IV space-time interaction, which had the lowest widely applicable information criterion of the four interaction types, {N['waic_main'] - N['s43_waic'][BEST_KH]:,.0f} lower than the principal model. "
            "<sup>c</sup>Same covariates with sex- and age-standardized expected deaths alone as the offset (negative binomial), so that rate ratios refer to the standardized mortality ratio.")
    return ("Table 2. District characteristics and the mortality-to-treatment ratio of lung cancer in Korea, 2011-2024, in the principal, type IV space-time interaction and mortality-level models",
            ["Characteristic", "Principal RR\n(95% CrI)", "Subsets\ncredible, %<sup>a</sup>", "Type IV RR\n(95% CrI)<sup>b</sup>", "Mortality-level\nRR (95% CrI)<sup>c</sup>"], rows, foot)

FIGCAP = {
 1: "Lung cancer deaths relative to treated persons in 229 Korean districts, 2011-2024. (A) Standardized mortality ratio and (B) treatment ratio (observed over age-standardized expected treated persons), each pooled over 2011-2024. (C) Residual spatial rate ratio of the mortality-to-treatment ratio, the exponential of the posterior mean of the Besag-York-Mollié 2 district log effect from the principal model; solid outlines, hot spots (posterior probability of a residual rate ratio above 1 greater than 0.95); dashed outlines, cold spots (probability below 0.05). Map lines delineate study areas and do not necessarily depict accepted national boundaries. (D) National directly age-standardized death rate (2015 population) and deaths per 100 persons treated.",
 2: "Rate ratios per 1 standard deviation, with 95% credible intervals, of (A) the out-of-district outpatient share and (B) the share of adults with tertiary education across models of the mortality-to-treatment ratio of lung cancer, for mortality without the treatment adjustment and for the comparison outcomes (deaths from transport accidents and falls), Korea, 2011-2024. Principal, principal model; KH I-IV, Knorr-Held space-time interactions; between and within, district-mean and two-way-centered components; 3-year treatment ratio, queen graph, without age 80+ control and ten age groups, sensitivity analyses defined with the outcome.",
}
def foot_row(J, text, sz=9, ls=15):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=False); foot_row(J, t[3], 8); J.counting = c
def put_fig(J, k, width_cm=16.0):
    from docx.enum.text import WD_BREAK
    p = J.doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE); p.add_run().add_picture(os.path.join(HERE, "figs", f"JTO_Fig{k}.png"), width=Cm(width_cm))
    J.para(f"<b>Figure {k}.</b> {FIGCAP[k]}", before=6)

def build(bw=0, aw=0):
    D = read_draft(); J = TX(cite="sup")
    J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae Kim, PhD<sup>a</sup>", before=6)
    J.para(f"<sup>a</sup>{ADDRESS}. E-mail: kimsd@hongik.ac.kr")
    J.para(f"<b>Corresponding author:</b> Seongdae Kim, PhD, {ADDRESS}. Telephone: +82-2-320-1114. E-mail: kimsd@hongik.ac.kr. ORCID: {ORCID}", before=6)
    J.para(f"<b>Funding:</b> {FUNDING}", before=6)
    J.para(f"<b>Conflict of interest statement:</b> {COI}")
    J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6)
    J.para(f"<b>Abbreviations:</b> {ABBREV}", before=6)
    J.para(f"<b>Word counts:</b> abstract {aw} words; text {bw:,} words (Introduction to Discussion). <b>References:</b> {len(KEYS)}. <b>Tables and figures:</b> 2 tables and 2 figures. <b>Supplemental Data:</b> 1 PDF file.", before=6)
    J.page_break(); J.head("Abstract", 1)
    for p in D["Abstract"]:
        m = re.match(r"^(Introduction|Methods|Results|Conclusions):\s*(.*)$", p, flags=re.S); assert m, p[:30]
        J.para(f"<b>{m.group(1)}:</b> {m.group(2)}")
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Materials and Methods", 1)
    for h, p in C.METHODS: J.head(h, 2); J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for h, p in C.RESULTS:
        if h: J.head(h, 2)
        J.para(pandoc_cites(p), indent=True)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.head("Conclusions", 2)
    for p in D["Conclusion"]: J.para(pandoc_cites(p), indent=True)
    J.counting = False
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.head("CRediT Authorship Contribution Statement", 1); J.para(CONTRIB)
    J.head("Ethics Approval and Consent", 1); J.para(f"{IRB} {CONSENT}")
    J.head("Data Availability", 1); J.para(f"{data_statement()} {code_statement()}")
    J.head("Acknowledgments", 1); J.para("None.")
    J.head("Declaration of Generative AI and AI-assisted Technologies in the Writing Process", 1); J.para(AI_DECL)
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k in enumerate(J.cites, 1): s_ = f"{i}. " + ref(k); rl.append(s_); J.para(s_)
    J.raw = False
    J.page_break(); put_table(J, table1(), fs=8)
    J.page_break(); put_table(J, table2(), fs=8)
    J.page_break(); J.head("Figure Legends", 1)
    for k in (1, 2): J.para(f"<b>Figure {k}.</b> {FIGCAP[k]}", before=6)
    put_fig(J, 1, 12.0); put_fig(J, 2, 15.0)
    J.page_break(); J.head("List of Supplemental Material", 1); J.para("Supplemental Data 1. pdf (Supplementary Methods and additional results; Tables S1-S7; Figure S1; STROBE checklist)")
    return J, rl, D

def docx_bw(path):   # JTO: 본문 단어 수 = Introduction ~ Discussion(Conclusions 포함) 끝(제목면·초록·참고문헌·표·그림 제외)
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    a = t.find("\nIntroduction\n"); b = t.find("\nCRediT Authorship Contribution Statement\n"); assert a > 0 and b > a
    return len(t[a:b].split())
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_lcad_jto", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads: orphan = ls[-1]; break
        if orphan is None: return
        d = Document(path)
        for p in d.paragraphs:
            if p.text.strip() == orphan:
                r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); p._p.insert(1 if p._p.pPr is not None else 0, r); break
        d.save(path); print("orphan fixed:", orphan)

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript_JTO_LCAD.docx"); D = read_draft()
    aw = sum(len(strip(x).split()) for x in D["Abstract"]); assert aw <= 250, aw
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p); assert bw <= 4000, bw
    J, rl, D = build(bw, aw); J.doc_title = "Manuscript"; J.save(p); assert docx_bw(p) == bw
    heads = {"Abstract", "Introduction", "Materials and Methods", "Results", "Discussion", "Conclusions", "References", "Figure Legends", "CRediT Authorship Contribution Statement", "Data Availability", "Ethics Approval and Consent", "Acknowledgments", "List of Supplemental Material", "Declaration of Generative AI and AI-assisted Technologies in the Writing Process"}
    heads |= {x[4:].strip() for x in D["Discussion"] if x.startswith("### ")} | {h for h, _ in C.METHODS + C.RESULTS if h}
    fix_orphans(p, heads)
    open(os.path.join(OUT, "wordcount_jto.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=2\ntitle_words={len(TITLE.split())}\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | title words {len(TITLE.split())}")
