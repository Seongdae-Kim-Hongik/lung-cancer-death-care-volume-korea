# check_jto_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
import os, re, subprocess, zipfile
from docx import Document
from docx.oxml.ns import qn
from PIL import Image
import content_lcad as C
from build_jto_lcad import read_draft, TITLE, ORCID, KEYS, FUNDING, CONTRIB, IRB, COI, CONSENT
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out")
N = C.N; R = []
def ok(c, m): R.append(("ok  " if c else "FAIL") + " " + m)
W = dict(l.split("=") for l in open(os.path.join(OUT, "wordcount_jto.txt")).read().split())
D = read_draft(); AB = D["Abstract"]; ab = " ".join(AB)
MSF, SUPF, CLF = "Manuscript_JTO_LCAD.docx", "Supplemental_Data_1.docx", "Cover_Letter_JTO_LCAD.docx"
for f in (MSF, SUPF, "Supplemental_Data_1.pdf", CLF, "Figures/Figure1.tif", "Figures/Figure2.tif"): ok(os.path.exists(os.path.join(OUT, f)), f"파일 {f}")
aw = sum(len(re.sub(r"<[^>]+>|\s*\[@[^\]]+\]", "", p).split()) for p in AB); ok(150 <= aw <= 250 and aw == int(W["abstract_words"]), f"초록 {aw}단어 ≤250")
ok([re.match(r"^(\w+):", p).group(1) for p in AB] == ["Introduction", "Methods", "Results", "Conclusions"], "구조화 초록 Introduction·Methods·Results·Conclusions")
ok("2011" in ab and "2024" in ab, "초록에 자료 기간"); ok(not re.search(r"\[@", ab), "초록 인용 없음")
ok(not re.search(r"\b(SD|SMR|CrI|BYM2|WAIC|ICD|RR|MTR)\b", re.sub(r"<[^>]+>", "", ab)), "초록에 정의 안 된 약어 없음")
ok(":" not in TITLE and "229" not in TITLE and "standardi" not in TITLE.lower() and not re.search(r"\b[A-Z]{2,}\b", TITLE), f"제목 쌍점·약어·시리즈 틀 없음")
ok(int(W["body_words"]) <= 4000, f"본문 {W['body_words']}단어 ≤ 4,000(Introduction~Discussion)")
KW = [k.strip() for k in C.KEYWORDS.split(";")]; ok(3 <= len(KW) <= 5, f"키워드 {len(KW)}개 3-5")
ok(int(W["refs"]) == len(KEYS) <= 50, f"참고문헌 {len(KEYS)} ≤50")
d = Document(os.path.join(OUT, MSF)); _ps = [p.text.strip() for p in d.paragraphs]; _dx = "\n".join(_ps)
ok(len(d.tables) == 2 and int(W["tables"]) + int(W["figures"]) <= 6, "표 2 + 그림 2 ≤ 6")
head = "\n".join(_ps[:_ps.index("Abstract")])
for t in ("Seongdae Kim, PhD", "kimsd@hongik.ac.kr", ORCID, "Hongik University", "Republic of Korea", "Corresponding author", "Funding", "Conflict of interest statement", "Keywords", "Abbreviations", f"abstract {W['abstract_words']} words", f"text {int(W['body_words']):,} words"): ok(t in head, f"제목면 '{t}'")
_ord = ["Abstract", "Introduction", "Materials and Methods", "Results", "Discussion", "Conclusions", "Declaration of Generative AI and AI-assisted Technologies in the Writing Process", "References", "Figure Legends", "List of Supplemental Material"]; pos = [_ps.index(k) if k in _ps else -1 for k in _ord]
ok(all(p >= 0 for p in pos) and pos == sorted(pos), f"원고 순서(제목면→초록→본문→결론→참고문헌→표→범례) {pos}")
ok(all(t in _dx for t in (IRB, FUNDING, CONTRIB, COI, CONSENT)), "IRB·연구비·기여(CRediT)·이해충돌·동의 정본 문장")
ok("Declaration of Helsinki" in IRB and "7002340-202611-HR-040" in IRB, "윤리 문장 헬싱키·승인 번호")
from build_jto_lcad import AI_DECL
ok(AI_DECL in _dx and _dx.count("Claude (Anthropic)") == 1 and "only for translation and English-language editing" in AI_DECL, "AI 고지 = 참고문헌 앞 절(JTO 규정), 번역·첨삭만, 1회")
iT1 = next(i for i, p in enumerate(_ps) if p.startswith("Table 1. ")); iT2 = next(i for i, p in enumerate(_ps) if p.startswith("Table 2. ")); ok(pos[7] < iT1 < iT2 < pos[8], "표 1·2가 참고문헌 뒤·범례 앞")
ok(not any(":" in p for p in _ps if p.startswith(("Table 1. ", "Table 2. "))), "표 제목 쌍점 없음")
caps = [p for p in _ps if re.match(r"^Figure \d\. ", p)]; ok(len(caps) == 4, "그림 범례(범례 절 2 + 그림 아래 2)")
z = zipfile.ZipFile(os.path.join(OUT, MSF)); ok(z.read("word/document.xml").decode().count("<w:drawing") == 2, "본문 안 그림 2(초투고 허용)")
for k in (1, 2):
    im = Image.open(os.path.join(OUT, "Figures", f"Figure{k}.tif")); dpi = round(im.info.get("dpi", (0, 0))[0])
    ok(im.mode == "RGB" and dpi >= (600 if k == 1 else 1200) and getattr(im, "n_frames", 1) == 1 and abs(im.size[0] / dpi * 25.4 - 174) < 2, f"Figure{k}.tif RGB 컬러·{dpi} dpi·폭 {im.size[0]/dpi*25.4:.0f} mm")
legs = "\n".join(caps); ok("Map lines delineate study areas" in legs, "지도 경계 면책 문구")
ok(not re.search(r"\b(red|blue|green|orange|colou?r)\b", legs, re.I), "그림 설명에 색 의존 표현 없음")
ok(all(f"({ch})" in legs for ch in "ABCD") and not re.search(r"\([a-d]\)", legs), "패널 문자 대문자 A-D")
sec = d.sections[0]._sectPr; ok(sec.find(qn("w:lnNumType")) is not None, "연속 줄번호")
for nm, f in (("원고", MSF), ("보충", SUPF), ("커버", CLF)):
    dd = Document(os.path.join(OUT, f))
    for i, t in enumerate(dd.tables):
        tpr = t._tbl.tblPr; b = tpr.find(qn("w:tblBorders"))
        ok(b is not None and all(b.find(qn(f"w:{s}")).get(qn("w:val")) == "nil" for s in ("insideV", "insideH", "left", "right")), f"{nm} 표{i+1} 3선")
        _rows = [row for k_, row in enumerate(t.rows) if k_ > 0 and len({id(c._tc) for c in row.cells}) > 1]
        bad = [r.text for row in _rows for c in row.cells for p in c.paragraphs for r in p.runs if r.bold and r.text.strip()]
        ok(not bad, f"{nm} 표{i+1} 데이터 칸 볼드 없음 {bad[:2]}")
        ok(not [c.text for r in t.rows for c in r.cells if re.fullmatch(r"[\d.()\- ]+\*+", c.text.strip())], f"{nm} 표{i+1} 유의성 별표 없음")
    x = subprocess.run(["unzip", "-p", os.path.join(OUT, f), "word/*.xml"], capture_output=True, text=True).stdout
    ok(len(re.findall(r"<w:keepNext[ />]|<w:keepLines[ />]|<w:pageBreakBefore[ />]", x)) == 0, f"{nm} Word 검은 네모 0건")
    zz = zipfile.ZipFile(os.path.join(OUT, f)); core = zz.read("docProps/core.xml").decode(); app = zz.read("docProps/app.xml").decode()
    ok("2013-12-23" not in core and not any(n.startswith("customXml/") for n in zz.namelist()) and "<Words>0<" not in app and "python-docx" not in core, f"{nm} python-docx 지문 없음(sanitize 후)")
    ok("<dc:creator>Seongdae Kim</dc:creator>" in core, f"{nm} 작성자 메타")
_i0 = _ps.index("Introduction"); _i1 = _ps.index("References")
_bp = d.paragraphs[_i0:_i1]
_nosup = "\n".join("".join(r.text for r in p.runs if not r.font.superscript) for p in _bp)
_supnums = [r.text for p in _bp for r in p.runs if r.font.superscript and r.text.strip()]
body = re.sub(r"\s+", " ", _nosup)
ok(not re.search(r"\b(we|our|us|We|Our)\b|(?<!Moran's )(?<!type )\bI\b(?!-IV)", body), "1인칭 없음")
supd = Document(os.path.join(OUT, SUPF)); supt = "\n".join(p.text for p in supd.paragraphs) + "\n".join(c.text for t in supd.tables for r in t.rows for c in r.cells)
cov = subprocess.run(["pdftotext", os.path.join(OUT, CLF.replace(".docx", ".pdf")), "-"], capture_output=True, text=True).stdout
alltxt = _dx + supt + cov
ok("—" not in alltxt and not re.search(r"[가-힣]", alltxt), "em-dash·한글 없음")
ok(not re.search(r"\bsignifican", _dx + supt, re.I), "'significant' 없음")
UK = r"\b(\w*(standardis|harmonis|summaris|characteris(?=e|ed|ing|ation)|categoris|minimis|randomis|generalis|normalis|prioritis|organis|utilis|penalis)\w*|analys(e|ed|ing)|modelled|modelling|centre(s|d)?|neighbour\w*|behaviour\w*|ageing|colour|favour\w*|labelled|grey|programme|tumour\w*|oesophag\w*|haemorrhag\w*|paediatric)\b"
uk = sorted(set(m.group(0) for m in re.finditer(UK, body + " " + supt + " " + cov + " " + head))); ok(not uk, f"미국식 철자 {uk}")
ok("−" in body or not re.search(r"(^|[\s(])-\d", body), "마이너스 U+2212")
ok(all(re.fullmatch(r"[\d,\-]+", x) for x in _supnums) and not re.search(r"\[(@|web:)", _dx) and "{{" not in _dx and not re.search(r"\{[a-z_]+\(|\{N\[|\{sup\(", alltxt), "미해결 인용·코드 조각 없음")
disc_nc = _nosup[_nosup.find("\nDiscussion\n"):_nosup.find("\nCRediT Authorship Contribution Statement\n")]
_dn = re.findall(r".{15}\d.{8}", disc_nc); _dn = [x for x in _dn if not re.search(r"20(19|11|24)|type (II|IV)|C33|C34|80\+", x)]; ok(not _dn, f"고찰·결론에 통계 숫자 없음 {_dn[:3]}")
ok(not any(":" in h for h, _ in C.METHODS + C.RESULTS if h) and not any(":" in p for p in D["Discussion"] if p.startswith("###")), "소제목 쌍점 없음")
refs = _dx[_dx.find("\nReferences\n"):_dx.find("\nTable 1. ")]
rl = [l for l in refs.split("\n") if re.match(r"^\d+\. ", l)]; ok(len(rl) == len(KEYS), f"참고문헌 목록 {len(rl)}")
ok(not re.search(r"github|zenodo", refs, re.I), "참고문헌에 GitHub·Zenodo 없음")
ok(all(("doi:" in l or "http" in l or int(re.search(r"\. (\d{4})[;.]", l).group(1)) < 2000) for l in rl), "참고문헌마다 DOI·URL(2000년 이전 예외)")
ok(not [l for l in rl if re.search(r"(, [A-Z][a-z]+ [A-Z]{1,3}){6,}", l) and "et al" not in l], "AMA 저자 7명 이상은 3명 + et al")
nums = [int(n) for g in _supnums for part in g.replace("–", "-").split(",") for n in (range(int(part.split("-")[0]), int(part.split("-")[1]) + 1) if "-" in part else [int(part)])]
first = []; [first.append(n) for n in nums if n not in first]; ok(first == list(range(1, len(KEYS) + 1)), "인용 번호 첫 등장 순서 1..n")
for k, lab in C.SUP.items():
    t_ = lab.split(", ", 1)[1]; ok(lab in body and (t_ in supt or t_ + "a" in supt), f"보충 '{t_}' 본문 인용·보충 존재")
ok("STROBE checklist" in supt and "Supplemental Data 1" in supt[:200], "STROBE가 보충 안")
ok("Journal: Journal of Thoracic Oncology" in supt[:600] and "kimsd@hongik.ac.kr" in supt[:600], "보충 첫 쪽 제목·저널·저자·이메일")
ok(not re.search(r"pre-?specified|pre-?registered|before any model|before results were seen", alltxt, re.I), "사전지정 거짓 문구 없음")
ok("[ZENODO DOI]" not in _dx and "[ZENODO DOI]" not in cov, "Zenodo DOI 채움(투고 전 게이트)")
ok(not re.search(r"Byung|Ch[u]n\b", cov), "커버레터 이름 점검")
open(os.path.join(OUT, "check_jto.txt"), "w").write("\n".join(R)); nf = sum(r.startswith("FAIL") for r in R)
print("\n".join(r for r in R if r.startswith("FAIL")) or "", f"\n{len(R)} checks, FAIL {nf}", "PASS" if nf == 0 else "")
