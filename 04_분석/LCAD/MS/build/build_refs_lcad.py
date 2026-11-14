# build_refs_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
import os, re, json, time, urllib.request, urllib.parse, glob
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE)
man = pd.read_csv(os.path.join(MS, "refs", "manifest", "ALL_refs.csv"), dtype=str).fillna("")
man["pmid"] = man.pmid.str.replace(r"\.0$", "", regex=True); M = man.set_index("key")
src = open(os.path.join(HERE, "content_lcad.py"), encoding="utf-8").read() + "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(MS, "draft", "*.md")))
src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
keys = sorted({k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")})
keys = [k for k in keys if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k)]
WEB = {
 "web:kostat2026cause": dict(type="web", authors="Statistics Korea", title="Causes of death statistics: deaths by cause (50-item list), sex and administrative district (DT_1B34E13) and by cause, sex and 5-year age group (DT_1B34E01), 2011-2024. Korean Statistical Information Service", url="https://kosis.kr", year=2026, accessed="November 12, 2026"),
 "web:mois2026population": dict(type="web", authors="Ministry of the Interior and Safety", title="Resident registration population by district, sex and 5-year age group, 2011-2024", url="https://jumin.mois.go.kr", year=2026, accessed="October 20, 2026"),
 "web:nhis2026regional": dict(type="web", authors="National Health Insurance Service", title="Regional medical care utilization statistics: number of persons treated for major diseases by district of residence and age group, lung cancer (C33-C34), 2011-2024", url="https://kosis.kr", year=2026, accessed="November 8, 2026"),
 "web:rcore2026": dict(type="web", authors="R Core Team", title="R: a language and environment for statistical computing. Version 4.6.0. Vienna: R Foundation for Statistical Computing", url="https://www.R-project.org/", year=2026, accessed="October 20, 2026"),
}
out = {}
miss = [k for k in keys if not k.startswith("web:") and k not in M.index]; assert not miss, miss
pm = [k for k in keys if not k.startswith("web:") and M.loc[k, "pmid"]]
for i in range(0, len(pm), 150):
    ids = ",".join(M.loc[k, "pmid"] for k in pm[i:i + 150])
    d = json.load(urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ids, timeout=60))["result"]
    for k in pm[i:i + 150]:
        r = d[M.loc[k, "pmid"]]
        au = [a["name"] for a in r["authors"] if a.get("authtype", "Author") == "Author"] or [a["name"] for a in r["authors"]]
        doi = next((a["value"] for a in r["articleids"] if a["idtype"] == "doi"), "") or M.loc[k, "doi"]
        pages = r.get("pages", "") or (r.get("elocationid", "").replace("pii: ", "").split(" doi")[0] if r.get("elocationid", "").startswith("pii:") else "")
        out[k] = dict(type="journal", authors=au, title=r["title"].rstrip("."), journal=r["source"], year=int(r["pubdate"][:4]), vol=r.get("volume", ""), issue=r.get("issue", ""), pages=pages, doi=doi, pmid=M.loc[k, "pmid"], verified="PubMed esummary " + time.strftime("%Y-%m-%d"))
    time.sleep(0.4)
JABBR = {"Political Science Research and Methods": "Polit Sci Res Methods", "Geographical Analysis": "Geogr Anal", "Econometrica": "Econometrica", "Statistical Science": "Stat Sci"}
for k in keys:
    if k.startswith("web:"): out[k] = WEB[k]; continue
    if k in out: continue
    doi = M.loc[k, "doi"]; assert doi, k
    m = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(doi), headers={"User-Agent": "research-client"}), timeout=60))["message"]
    au = [f"{a.get('family','')} {''.join(x[0] for x in re.split(r'[ -]', a.get('given','')) if x)}".strip() for a in m.get("author", [])]
    ct = (m.get("container-title") or [""])[0]; jt = JABBR.get(ct, (m.get("short-container-title") or [ct])[0])
    yr = (m.get("published-print") or m.get("published-online") or m.get("issued"))["date-parts"][0][0]
    out[k] = dict(type="journal", authors=au, title=re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0]), journal=jt, year=int(yr), vol=m.get("volume", ""), issue=m.get("issue", ""), pages=m.get("page", "") or m.get("article-number", ""), doi=doi, verified="Crossref " + time.strftime("%Y-%m-%d"))
    time.sleep(0.3)
# 서식 통일: 학술지 MEDLINE 약어(마침표 없음), 쪽 범위 전체 표기, 대문자 제목 문장형
JN = {"Polit. Sci. Res. Methods": "Polit Sci Res Methods", "Geogr. Anal.": "Geogr Anal", "Stat. Sci.": "Stat Sci", "J R Stat Soc Series B Stat Methodol": "J R Stat Soc Series B Stat Methodol",
      "Journal of the Royal Statistical Society Series B: Statistical Methodology": "J R Stat Soc Series B Stat Methodol"}
def fullp(p):
    m = re.match(r"^(\d+)-(\d+)$", str(p))
    if not m: return p
    a, b = m.groups(); return p if len(b) >= len(a) else f"{a}-{a[:len(a)-len(b)]+b}"
FIXP = {"jeong2024income": "2923", "jung2023deprivation": "3171"}   # 전자 논문 번호(PubMed esummary pages 없음·마침표 붙음)
AHEAD = set()
for k, v in out.items():
    if v.get("type") != "journal": continue
    if k in FIXP: v["pages"] = FIXP[k]
    if k == "lee2016garbage": v["vol"] = "31"
    if k in AHEAD: v["pages"] = ""; v["vol"] = ""; v["ahead"] = True
    v["journal"] = JN.get(v["journal"], v["journal"]).replace(".", "")
    v["pages"] = fullp(v.get("pages", "")) if k not in AHEAD else ""
    if v["title"].isupper(): v["title"] = v["title"].capitalize()
    v["authors"] = [a.title() if a.isupper() else a for a in v["authors"]]
# 문장형 제목(제목형 대소문자 문헌만 직접 지정, 고유명사 유지)
SENT = {
 "ambroggi2015distance": "Distance as a barrier to cancer diagnosis and treatment: review of the literature",
 "caini2022quitting": "Quitting smoking at or around diagnosis improves the overall survival of lung cancer patients: a systematic review and meta-analysis",
 "cho2019tertiary": "Cancer patients' utilization of tertiary hospitals in Seoul before and after the benefit expansion policy",
 "choi2025screening": "Changes in uptake, participant disparities, and screening outcomes of the Korean National Lung Cancer Screening Program: a five-year experience",
 "ellis2019mir": "The mortality-to-incidence ratio is not a valid proxy for cancer survival",
 "howlader2020treatment": "The effect of advances in lung-cancer treatment on population mortality",
 "jeong2024income": "Disparities in overall survival rates for cancers across income levels in the Republic of Korea",
 "jung2023deprivation": "The impact of neighborhood deprivation on the survival rates of patients with cancer in Korea",
 "kim2018radon": "The disease burden of lung cancer attributable to residential radon exposure in Korean homes",
 "kim2025overdiagnosis": "Screening for lung cancer, overdiagnosis, and healthcare utilization: a nationwide population-based study",
 "kim2025pa": "Association of pre- and postdiagnosis physical activity, promotion and maintenance with lung cancer survival: a nationwide cohort study",
 "kwak2017busan": "Disparities by age, sex, tumor stage, diagnosis path, and area-level socioeconomic status in survival time for major cancers: results from the Busan Cancer Registry",
 "lee2016garbage": "Application of a modified garbage code algorithm to estimate cause-specific mortality and years of life lost in Korea",
 "lee2020state": "State-level disparity in lung cancer survival in the United States",
 "lee2021trends": "Recent trends of lung cancer in Korea",
 "lee2024ses": "Socioeconomic disparities in six common cancer survival rates in South Korea: population-wide retrospective cohort study",
 "shin2017epi": "Lung cancer epidemiology in Korea",
 "won2018geographic": "Geographical variations and trends in major cancer incidences throughout Korea during 1999-2013",
 "han2023fatty": "Fatty liver & diabetes statistics in Korea: nationwide data 2009 to 2017",
 "ufere2022rural": "Rural-urban disparities in mortality from cirrhosis in the United States from 1999 to 2019",
 "askgaard2024population": "Population-based study of alcohol-related liver disease in England in 2001-2018: influence of socioeconomic position",
 "blanc2019occupational": "The occupational burden of nonmalignant respiratory diseases. An official American Thoracic Society and European Respiratory Society statement",
 "choi2020regional": "Regional variation of suicide mortality in South Korea",
 "dwyerlindgren2017trends": "Trends and patterns of differences in chronic respiratory disease mortality among US counties, 1980-2014",
 "hwang2017recent": "Recent trends in the prevalence of chronic obstructive pulmonary disease in Korea",
 "kim2022trends": "Trends in regional disparity in cardiovascular mortality in Korea, 1983-2019",
 "lee2016risk": "The risk factors and characteristics of COPD among nonsmokers in Korea: an analysis of KNHANES IV and V",
 "raju2019rural": "Rural residence and poverty are independent risk factors for chronic obstructive pulmonary disease in the United States",
 "luo2026copd": "COPD burden across 48 Asian locations, 2009-2023: demographic drivers and socioeconomic inequality",
 "kim2017income": "Income differences in smoking prevalences in 245 districts of South Korea: patterns by area deprivation and urbanity, 2008-2014",
 "cheolseong2017data": "Data resource profile: the National Health Information Database of the National Health Insurance Service in South Korea",
 "steegen2016increasing": "Increasing transparency through a multiverse analysis",
 "vanderweele2017sensitivity": "Sensitivity analysis in observational research: introducing the E-value",
 "bell2015explaining": "Explaining fixed effects: random effects modeling of time-series cross-sectional and panel data",
 "rue2009approximate": "Approximate Bayesian inference for latent Gaussian models by using integrated nested Laplace approximations",
 "morgenstern1995ecologic": "Ecologic studies in epidemiology: concepts, principles, and methods",
 "inskip1983methods": "Methods for age-adjustment of rates",
 "knorrheld2000bayesian": "Bayesian modelling of inseparable space-time variation in disease risk",
 "dupont2022spatial": "Spatial+: a novel approach to spatial confounding",
 "lipsitch2010negative": "Negative controls: a tool for detecting confounding and bias in observational studies",
 "vonelm2007strengthening": "The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies",
 "kim2019executive": "Executive summary of stroke statistics in Korea 2018: a report from the Epidemiology Research Council of the Korean Stroke Society",
 "lee2018geographic": "Geographic variation in morbidity and mortality of cerebrovascular diseases in Korea during 2011-2015",
 "simpson2017penalising": "Penalising model component complexity: a principled, practical approach to constructing priors",
 "stockwell2016moderate": "Do \"moderate\" drinkers have reduced mortality risk? A systematic review and meta-analysis of alcohol consumption and all-cause mortality",
 "kang2015korea": "Korea Community Health Survey data profiles",
 "kim2024korea": "Korea hypertension fact sheet 2023: analysis of nationwide population-based data with a particular focus on hypertension in special populations",
 "holmes2014association": "Association between alcohol and cardiovascular disease: Mendelian randomisation analysis based on individual participant data",
 "lederer2019control": "Control of confounding and reporting of results in causal inference studies. Guidance for authors from editors of respiratory, sleep, and critical care journals",
}
for k, t in SENT.items():
    if k in out: out[k]["title"] = t
import html
for k, v in out.items():
    if v.get("type") == "journal": v["title"] = html.unescape(html.unescape(v["title"]))
for k, v in out.items():   # 콜론 뒤 첫 글자 소문자(고유명사·약어 제외)
    if v.get("type") == "journal":
        v["title"] = re.sub(r":\s+([A-Z][a-z]*)\b", lambda m: ": " + (m.group(1) if m.group(1) in ("Korea", "Korean", "South", "Bayesian", "Spatial", "E", "GLOBOCAN", "COPD", "Mendelian") else m.group(1).lower()), v["title"])
# PubMed 저자명 뒤집힘 교정(2026-11-06 조테로 검증에서 발견: PubMed 27794523이 "Cheol Seong S", "Heon Park J"로 색인 — 원문 Sang Cheol Seong, Jong Heon Park)
AUTHOR_FIX = {"Molli\ufffd A": "Molli\u00e9 A", "Cheol Seong S": "Seong SC", "Heon Park J": "Park JH", "Hyon Bang J": "Bang JH", "Ae Shin S": "Shin SA"}
for _k, _v in out.items():
    if isinstance(_v.get("authors"), list): _v["authors"] = [AUTHOR_FIX.get(a, a) for a in _v["authors"]]
assert not any("Cheol Seong" in a for v in out.values() if isinstance(v.get("authors"), list) for a in v["authors"])
json.dump(out, open(os.path.join(HERE, "refs_lcad.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
import re as _re
for _k, _v in out.items():   # 부터: 한국인 이름 뒤집힘 검사(두 음절 이름 + 한 글자 이니셜)
    if isinstance(_v.get("authors"), list): assert not [a for a in _v["authors"][:3] if a not in ("Tchetgen Tchetgen E", "Di Napoli M", "De Villiers A", "Asadzadeh Vostakolaei F", "Del Giovane C", "Rees Punia E", "De Koning HJ") and a.split()[0] not in ("Del", "De", "Di", "Van", "Von", "Da", "Dos", "La", "Le") and _re.fullmatch(r"[A-Z][a-z]+ [A-Z][a-z]+ [A-Z]", a)], (_k, _v["authors"])
print(len(keys), "keys;", sum(v["type"] == "journal" for v in out.values()), "journal,", sum(v["type"] == "web" for v in out.values()), "web")
