# cover_jto_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).

import os, re, sys, datetime, subprocess
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import content_lcad as C
from build_jto_lcad import TITLE as DTITLE, ZENODO, ADDRESS
brit = lambda t: t
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "out"); DRAFT = "--draft" in sys.argv
N = C.N; W = dict(l.split("=") for l in open(os.path.join(OUT, "wordcount_jto.txt")).read().split()); M = N["main"]
assert M[C.OUTC]["cred"] and M[C.EDU]["cred"] and not M[C.SMK]["cred"] and C.NCO("TRANS", C.EDU)[3]
_d = datetime.date.today(); cl = [f"{_d:%B} {_d.day}, {_d.year}", "The Editor-in-Chief", "Journal of Thoracic Oncology", "",
      "Dear Editor,",
      f"Please find enclosed the manuscript entitled \"{DTITLE}\" by Seongdae Kim, for consideration as an Original Article in the Journal of Thoracic Oncology.",
      f"Lung cancer death rates mix how often the disease arises with how often patients die of it. Using complete death registration and national insurance counts of persons treated for lung cancer in all {N['n_districts']} Korean districts over 14 years, this study maps the age-standardized ratio of deaths to treated persons as a screening measure of where deaths are high relative to the volume of care. The ratio was strongly clustered: {N['n_hot']} residual hot spots lay mainly in South Gyeongsang, Busan, North Gyeongsang and Gangwon, and Busan stood out only when deaths were compared with treatment. Smoking, coal power plants, industrial land, detached housing, tuberculosis and physical activity showed no credible association with the ratio, whereas a rising share of residents treated as outpatients outside their district accompanied a small increase, and tertiary education accompanied a lower ratio, an association also present for transport and fall deaths.",
      "The study speaks to the journal's epidemiology and prevention readership: it separates the geography of lung cancer deaths from the geography of the disease in care, identifies districts where stage, treatment and place of care should be examined with linked records, and reports the results of a broad set of robustness and negative-control analyses. The study used only published aggregate statistics with approval of the Institutional Review Board of Hongik University.",
      "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. This manuscript has not been published and is not under consideration for publication elsewhere. The sole author meets the authorship criteria of the journal and agrees with the content of the manuscript. The work received no funding from the tobacco industry or any other source.",
      f"The text contains {int(W['body_words']):,} words, with a structured abstract of {int(W['abstract_words'])} words, two tables, two figures and {W['refs']} references. Supplemental Data 1 (supplementary methods, tables, figure and the STROBE checklist) is provided as one PDF file.",
      f"The analysis code is openly available on Zenodo under the MIT license (https://doi.org/{ZENODO}).",
      "Thank you for considering this manuscript.", "", "Sincerely,", "",
      "Seongdae Kim, PhD (corresponding author)", ADDRESS, "Email: kimsd@hongik.ac.kr"]
d = Document(); st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11); st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.0
for s in d.sections: s.page_width, s.page_height = Cm(21), Cm(29.7); s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
assert "[ZENODO DOI]" not in ZENODO or DRAFT, "Zenodo 공개 DOI 없음(투고 전 게이트)"   # 11/12 새 규칙: 공개 DOI만, 심사 토큰 링크 없음
def _add_link(p, url, text):
    rid = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rid); r = OxmlElement("w:r"); rp = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), "0563C1"); u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rp.append(c); rp.append(u); r.append(rp)
    tt = OxmlElement("w:t"); tt.text = text; r.append(tt); h.append(r); p._p.append(h)
gap = False
for t in cl:
    if t == "": gap = True; continue
    t = brit(t)
    p = d.add_paragraph(t)
    if gap: p.paragraph_format.space_before = Pt(10); gap = False
d.core_properties.author = "Seongdae Kim"; d.core_properties.last_modified_by = "Seongdae Kim"; d.core_properties.title = "Cover Letter"; d.core_properties.comments = ""
fp = os.path.join(OUT, "Cover_Letter_JTO_LCAD.docx"); d.save(fp)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_lcad_jcl", "--convert-to", "pdf", "--outdir", OUT, fp], capture_output=True)
txt = subprocess.run(["pdftotext", fp.replace(".docx", ".pdf"), "-"], capture_output=True, text=True).stdout
assert not re.search(r"\b(we|our|us|I)\b", txt) and "—" not in txt and not re.search(r"7002340", txt) and not re.search(r"(?i)competing", txt), "문체·IRB·금지 항목"
pages = subprocess.run(["pdfinfo", fp.replace(".docx", ".pdf")], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0]
assert pages == "1", pages; print("cover pages", pages, "draft" if DRAFT else "")
