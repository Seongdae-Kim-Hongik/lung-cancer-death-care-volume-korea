# esm_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
import os, re, json, subprocess, pandas as pd
from docx.shared import Cm
import content_lcad as C
from build_jto_lcad import LABEL, GROUPS, TX, TITLE as DTITLE, AFFIL, foot_row, read_draft
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.path.join(MSD, "out"); B = os.path.dirname(MSD)
N = C.N; EDU, OUTC, CSR = C.EDU, C.OUTC, C.CSR
st = lambda t: f"{t[0]:.3f} ({t[1]:.3f}-{t[2]:.3f})"
J = TX(cite="bracket")
def TF(title, header, rows, foot="", fs=8):
    J.page_break(); J.table_fit(title, header, rows, "", fs_max=fs, title_bold=False)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Supplemental Data 1</b>")
J.para(f"Article title: {DTITLE}")
J.para("Journal: Journal of Thoracic Oncology")
J.para(f"Author: Seongdae Kim, PhD, {AFFIL}. Corresponding author e-mail: kimsd@hongik.ac.kr")
J.para("Contents: Supplementary Methods and additional results; Tables S1-S7 (Table S2 in two parts); Figure S1; STROBE checklist.")
_MT = pd.read_csv(os.path.join(B, "panel_META_LCAD_std3.csv"), encoding="utf-8-sig").set_index("variable")
_imp = lambda v: int(_MT.loc[v, "n_imputed_interp"] + _MT.loc[v, "n_imputed_sgg_mean"] + _MT.loc[v, "n_imputed_year_mean"])
gate = open(os.path.join(B, "data_gate_LCAD_std3_261112.txt"), encoding="utf-8").read(); nwarn = int(re.search(r"경고 (\d+)건", gate).group(1))
X = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(B)), "02_패널", "EXT_canonical_pool_LCAD_261112.csv"))
_care_min = int(X.treated_n.min()); _zero_d = int((X.lcad_deaths == 0).sum())
J.page_break(); J.head("Supplementary Methods and additional results", 2)
SM = [("Outcome selection and districts.", f"Lung cancer mortality was one of several candidate outcomes screened with fixed rules for spatial structure (Moran's I before and after forced controls, persistence of district rankings, spatial fraction and dispersion); because deaths and persons treated were both available by district, the ratio of deaths to treated persons was defined as the outcome before the principal model was fitted. All data were joined by district code; districts merged or split during 2011-2024 (for example, Cheongju and Cheongwon in 2014 and Gunwi, which moved to Daegu in 2023) were aggregated to the {N['n_districts']} units of the 2024 boundaries."),
      ("Deaths.", "Annual deaths with malignant neoplasms of the trachea, bronchus and lung (International Classification of Diseases, 10th revision, C33-C34) as the underlying cause by district of residence came from the cause-of-death statistics of Statistics Korea (deaths by cause, sex and district, 50-item list). Deaths are attributed to the district of the registered address at death. District totals summed exactly to the national totals in every year."),
      ("Treated persons.", f"The number of persons treated for lung cancer (C33-C34) by district of residence came from the regional medical care utilization statistics of the National Health Insurance Service, which count each person with at least one claim for the disease in a year once, whether for a new diagnosis, continuing treatment or follow-up. The smallest annual district count was {_care_min}, and {_zero_d} district-years had no deaths."),
      ("Expected counts.", f"National lung cancer deaths by sex and 5-year age group (0-4 to 80-84 years and 85 years or older) came from the national cause-of-death table by cause, sex and age; deaths with unknown age ({N['age_unknown']} in 14 years) were excluded from the age-specific rates. National treated persons by age group (ten groups, the oldest 75 years or older) gave the treatment rates. District populations by sex and age came from resident registration statistics. In the 2023 resident registration file, the age block of Changwon duplicated the 2022 block; a corrected 2023 file matching the official total (1,009,038) was used. Expected deaths and expected treated persons were each rescaled so that their national sums equaled the observed national totals each year. The offset of the principal model was log(expected deaths × treatment ratio), rescaled again so that it summed to the observed national deaths each year. The 3-year sensitivity analysis replaced the treatment ratio with its moving average over the current and two previous years."),
      ("Covariates.", "Current smoking, walking practice and moderate-to-vigorous physical activity (any domain) are district age-standardized estimates from the Community Health Survey. Previous pulmonary tuberculosis is the share of national health screening participants reporting a history of pulmonary tuberculosis. The out-of-district outpatient share is the number of residents treated as outpatients by institutions outside the district divided by the sum of residents treated as outpatients inside and outside the district (all conditions; National Health Insurance Service regional medical care utilization statistics). A person treated both inside and outside the district is counted in both categories, so the share is not the proportion of unique outpatients treated elsewhere. Cancer screening uptake is the number of people screened per person invited in the national cancer screening program (all program cancers; lung cancer screening for heavy smokers from 2019). Coal-fired power plant is a time-invariant indicator of districts in which a coal-fired steam generator operated in 2011-2024 (Korea Power Exchange generator capacity); factory land is the share of district area designated as factory land (national land-use statistics); households in detached houses is the 2015-2024 mean share of general households living in detached houses (register-based census), an indicator of indoor radon exposure, held constant within district because earlier years were not published. General hospitals per 100,000 residents, the share of basic livelihood security recipients and the share of adults with tertiary education came from a harmonized public district panel built from local statistics; three implausible values of the recipient share in each of 2021-2023 for ten districts and Changwon (33 cells) were set to missing and interpolated within the district. Public sports facilities per 100,000 residents came from the national register of public sports facilities. District-level data on stage at diagnosis, histologic type, treatment, travel for lung cancer care, ambient fine particulate matter and measured radon were not available or not used."),
      ("Panel checks before modeling.", f"An automated gate run on the analytic panel reported {nwarn} flags, mostly standardized columns whose yearly means were near 0 (a ratio artifact), the post-2020 indicator (constant by design), time-invariant indicators, the sex ratio expressed as men per 100 women and districts without a general hospital or a coal-fired plant (true zeros). Missing years were interpolated within districts, then filled with district means and, for districts never observed, with yearly national means; filled cells are listed in Table S1. Flags by rule, threshold and handling are given in Table S7."),
      ("Models.", f"Software: R 4.6.0 with R-INLA; Python 3.9 for data preparation and figures. The Poisson likelihood was chosen because its widely applicable information criterion (WAIC) for the forced-controls model was lower than that of a negative binomial likelihood ({N['waic_pois']:,.1f} vs {N['waic_nb']:,.1f}). Fixed effects had normal priors with mean 0 and precision 4 (intercept precision 0.001). The Besag-York-Mollié 2 district effect used penalized-complexity priors (P(σ>0.5)=0.01; P(φ<0.5)=2/3) on a 593-edge district adjacency graph with Jeju Island as a separate connected component; the random-walk and independent year effects used penalized-complexity priors (P(σ>0.5)=0.01). Covariate subsets for the multiverse were drawn with a fixed seed, each characteristic entering with probability 0.5. Knorr-Held interactions used Kronecker-product structures (type I: independent; II: random walk in time by independent districts; III: independent years by intrinsic conditional autoregressive districts; IV: random walk by intrinsic conditional autoregressive districts). The queen-contiguity sensitivity graph (577 edges) omits the 16 contact links of the principal graph. Estimates from the 20 perturbations of filled values were pooled with Rubin's rules. Between- and within-district components were the district mean and the deviation from district and year means. Region-specific slopes interacted each characteristic with five regions (capital region: Seoul, Incheon, Gyeonggi; Chungcheong; Honam; Yeongnam; Gangwon-Jeju). Comparison outcomes (transport-accident and fall deaths) were fitted with the same covariates and their own age-standardized expected deaths. The mortality-level analysis used sex- and age-standardized expected deaths alone as the offset; its likelihood (negative binomial) was chosen by the same WAIC rule."),
      ]
for h, t in SM: J.para(f"<b>{h}</b> {t}")
_eh = N["ehsa"]; _tc = N["type_class"]; _vp = N["varpart"].set_index("component").share_of_linear_predictor_var
J.para("<b>Additional results.</b> " + f"Emerging hot spot analysis of smoothed ratios classified {_eh['Sporadic hot']} districts as sporadic and {_eh['New hot']} as new hot spots, and {_eh['Intensifying cold']} as intensifying, {_eh['Persistent cold']} as persistent and {_eh['Consecutive cold']} as consecutive cold spots (Figure S1). "
       f"Hot spots comprised {_tc['hotspot'].get('ward', 0)} urban wards, {_tc['hotspot'].get('city', 0)} cities and {_tc['hotspot'].get('county', 0)} counties. Of the variance of the linear predictor, covariates accounted for {100*_vp['fixed_covariates']:.0f}%, the structured district effect for {100*_vp['spatial_structured']:.0f}% and the unstructured district effect for {100*_vp['spatial_unstructured']:.0f}%. "
       f"The out-of-district outpatient share was not credible within any single calendar window ({', '.join(st(N['win_irr'][(OUTC, w)]) for w in C.WN)}), whereas tertiary education was credible in all three windows. "
       f"Basic livelihood recipients were credibly associated only in the mortality-level analysis ({st(C.SC('smr', C.BLS))}). The traffic culture index, a negative-control exposure, was credibly associated in the principal model. "
       f"In a model adding an indicator for 2020-2024, the indicator was {st(N['covid_main'])}; because expected counts were rescaled to the national total each year, it reflects relative rather than national change.")
# Table S1
DIR = {C.GHP: "−", OUTC: "+", CSR: "−", C.SMK: "+", C.TB: "+", C.COAL: "+", C.FAC_L: "+", C.DET: "+", C.WALK: "−", C.MPA: "−", C.FAC: "−", C.BLS: "+", EDU: "−"}
_sj = json.load(open(os.path.join(B, "sets_LCAD_std3.json"))); _ed = _sj["expected_direction"]
_src2var = {str(_MT.loc[v, "source_column"]): v for v in _MT.index}
assert all(_ed[c][0] == DIR[_src2var[c]].replace("−", "-") for c in _ed if c in _src2var), "기대 방향 불일치"
SRC = {"kchs": "Survey", "chk": "Screening", "eloc": "KOSIS", "fac": "Registry", "nhis": "NHIS"}
EXT = {"ext__pop80_share": "Registry", "ext__basic_livelihood_rate": "Panel", "ext__tertiary_educated_share": "Panel", "ext__genhosp_per100k": "Panel", "ext__cancer_screen_rate": "NHIS",
       "ext__outside_care_share": "NHIS", "ext__coal_host": "KPX", "ext__factory_land_share": "Land use", "ext__detached_hh_share": "Census"}
UNIT = {C.GHP: "per 100,000", OUTC: "%", CSR: "%", C.SMK: "%", C.TB: "%", C.COAL: "0/1", C.FAC_L: "% of area", C.DET: "%", C.WALK: "%", C.MPA: "%", C.FAC: "per 100,000", C.BLS: "%", EDU: "%",
        "urban_population_share": "%", "physicians_per_1000": "per 1,000", "sex_ratio": "ratio", "fiscal_independence": "%", "pop80_share": "%"}
YRS = {C.COAL: "2011-2024<sup>a</sup>", C.DET: "2015-2024<sup>a</sup>"}
PREFILL = {C.BLS: 33}
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs:
        m = _MT.loc[v]; sc = str(m.source_column); src = EXT.get(sc, SRC.get(sc.split("__")[0], sc.split("__")[0]))
        rows.append([f"  {LABEL[v]}", UNIT[v], src, YRS.get(v, f"{int(m.obs_year_min)}-{int(m.obs_year_max)}"), ("Forced" if m.role == "forced" else DIR[v]), f"{_imp(v) + PREFILL.get(v, 0):,}"])
TF("Table S1. Source, unit, observed years, expected direction and filled cells for each district characteristic, Korea, 2011-2024", ["Characteristic", "Unit", "Source", "Years", "Direction", "Filled cells"], rows,
   "Survey, Community Health Survey (district age-standardized rates); screening, National Health Insurance Service health screening statistics; NHIS, National Health Insurance Service regional and cancer screening program statistics; KOSIS, Korean Statistical Information Service local indicators; KPX, Korea Power Exchange generator capacity; land use, national land-use statistics; census, register-based census; registry, resident registration or public sports facility register; panel, harmonized public district panel; ratio, men per 100 women; forced, in every model. Filled cells of 3,206 district-years (interpolation, district means or yearly means). Direction, expected direction of association with the mortality-to-treatment ratio. <sup>a</sup>Time-invariant within district. Basic livelihood recipients: 33 implausible cells (2021-2023) set to missing and interpolated.")
# Table S2
NAMES = [("principal", "Principal model"), ("KH_typeI", "Knorr-Held type I"), ("KH_typeII", "Knorr-Held type II"), ("KH_typeIII", "Knorr-Held type III"), ("KH_typeIV", "Knorr-Held type IV"),
         ("icar_besag", "ICAR district effect"), ("iid_only", "IID district effect"), ("no_spatial", "No district effect"), ("knn3", "3 nearest neighbors"), ("knn4", "4 nearest neighbors"), ("knn5", "5 nearest neighbors"),
         ("B3_smooth_forced", "Smoothed sex ratio"), ("C1_poisson_lognormal", "Poisson, observation effect"), ("C2_rw2_year", "RW2 year effect"), ("C3_ar1_year", "AR1 year effect"), ("C4_sido_year_iid", "Province-by-year effect"), ("D1_spatial_plus", "Spatial+-type adjustment"),
         ("E0_nolag_from2012", "No lag, from 2012"), ("E1_lag1", "Lag 1 year"), ("E0_nolag_from2013", "No lag, from 2013"), ("E2_lag2", "Lag 2 years"), ("F3_extreme_R7", "Extreme values refilled"), ("G1_kchs_ma3", "Survey 3-year averages"), ("H4_odd_years", "Odd years only"), ("H4_even_years", "Even years only"),
         ("F1_drop_sido_11", "Seoul left out"), ("F1_drop_sido_21", "Busan left out"), ("F1_drop_sido_38", "South Gyeongsang left out"), ("F1_drop_sido_37", "North Gyeongsang left out"),
         ("H1_nco_TRANS", "Transport deaths (comparison)"), ("H1_nco_FALL", "Fall deaths (comparison)")]
SS = {**N["s43"], **N["s41"]}; WA = {**N["s43_waic"], **N["s41_waic"]}; WA["principal"] = N["waic_main"]
SS.update({("principal", c): (r["IRR"], r["lo"], r["hi"], r["cred"]) for c, r in N["main"].items()})
def cell(a, v): t = SS.get((a, v)); return "–" if t is None else st(t)
ALT = set(N["alt"]); assert ALT <= {a for a, _ in NAMES}, sorted(ALT - {a for a, _ in NAMES})
FOOT2 = "Values are rate ratios (95% credible intervals) per 1 standard deviation; –, not computed. For the Spatial+-type model, rate ratios are per 1 standard deviation of the residualized covariate. <sup>a</sup>One of the 14 alternative specifications counted in the main text. Transport and fall models use outcome-specific age-standardized expected deaths without a treatment adjustment, so their estimates are mortality rate ratios. ICAR, intrinsic conditional autoregressive; IID, independent; RW2, second-order random walk; AR1, first-order autoregressive."
for part, cols in (("A", [OUTC, EDU]), ("B", [CSR, C.SMK, C.BLS])):
    rows = [[lab + ("<sup>a</sup>" if a in ALT else "")] + ([f"{WA[a]:,.0f}" if a in WA and not a.startswith(("H1_", "F1_")) else "–"] if part == "A" else []) + [cell(a, v) for v in cols] for a, lab in NAMES]
    TF(f"Table S2{part.lower()}. Rate ratios per 1 standard deviation increase in each characteristic for the mortality-to-treatment ratio of lung cancer across alternative specifications and for comparison mortality outcomes, Korea, 2011-2024 (part {part})", ["Specification"] + (["WAIC"] if part == "A" else []) + [LABEL[v] for v in cols], rows, FOOT2)
# Table S3
SL = [("smr", "Mortality level (no treatment adjustment)"), ("ma3", "3-year treatment ratio"), ("s577", "Queen graph, 577 edges"), ("s2", "Share aged 80+ omitted"), ("s8", "Expected deaths from ten age groups")]
hyp = [v for g, vs in GROUPS[:-1] for v in vs]
rows = [["Principal model", f"{N['waic_main']:,.0f}", str(N["n_hot"]), "1.00", st((N['main'][OUTC]['IRR'], N['main'][OUTC]['lo'], N['main'][OUTC]['hi'])), st((N['main'][EDU]['IRR'], N['main'][EDU]['lo'], N['main'][EDU]['hi'])), ", ".join(LABEL[v] for v in hyp if N["main"][v]["cred"])]]
for v, lab in SL:
    hs = N["sens_hot"][v]; cr = [LABEL[c] for c in hyp if N["sens_main"][v][c][3]]
    rows.append([lab, f"{N['sens_waic'][v]:,.0f}", str(hs["n_hot"]), f"{hs['jac']:.2f}", st(N["sens_main"][v][OUTC]), st(N["sens_main"][v][EDU]), ", ".join(cr) if cr else "None"])
TF("Table S3. Sensitivity analyses defined with the outcome, Korea, 2011-2024", ["Analysis", "WAIC", "Hot spots", "Jaccard", "Out-of-district outpatient share", "Tertiary education", "Credible characteristics"], rows,
   "Rate ratios per 1 standard deviation (95% credible intervals). Jaccard, similarity of the hot-spot set with the principal model. WAIC values are comparable only between models with the same outcome and offset. The mortality-level analysis uses sex- and age-standardized expected deaths alone as the offset (negative binomial likelihood).")


R3 = os.path.join(B, "results_std3"); rd3 = lambda f: pd.read_csv(os.path.join(R3, f))
RG = [("Capital", "Capital region"), ("Chungcheong", "Chungcheong"), ("Honam", "Honam"), ("Yeongnam", "Yeongnam"), ("Gangwon_Jeju", "Gangwon-Jeju")]
_rs = rd3("S50_region_slopes.csv"); _V3 = [OUTC, CSR, EDU]
_g = {v: _rs[_rs.covariate == v].set_index("region") for v in _V3}
rows = [["Common slope", f"{N['n_rows']:,}"] + [st((_g[v].common_IRR.iloc[0], N["main"][v]["lo"], N["main"][v]["hi"])) for v in _V3]]
rows += [[lab, f"{int(_g[OUTC].loc[r, 'n_district_years']):,}"] + [st((_g[v].loc[r, "IRR"], _g[v].loc[r, "lo"], _g[v].loc[r, "hi"])) for v in _V3] for r, lab in RG]
TF("Table S4. Region-specific rate ratios per 1 standard deviation for the characteristics retained in all principal-model subsets, Korea, 2011-2024", ["Region", "District-years"] + [LABEL[v] for v in _V3], rows,
   "Values are rate ratios (95% credible intervals). Each model interacted one characteristic with five regions (capital region: Seoul, Incheon, Gyeonggi). WAIC of the region-specific model minus that of the common-slope model: " + "; ".join(f"{LABEL[v]} {_g[v].dWAIC_vs_common.iloc[0]:.1f}" for v in _V3) + ".")
SPN = {"principal": "Principal model", "forced_only": "Forced controls only", "parsimonious": "Parsimonious model", "no_spatial": "No district effect", "iid_district": "Independent district effect", "icar_district": "ICAR district effect", "typeI_interaction": "Knorr-Held type I interaction"}
_rm = rd3("S50_resid_moran_by_spec.csv")
rows = [[SPN[r.spec], str(int(r.n_cov)), f"{r.WAIC:,.1f}", f"{r.resid_moran_I:.3f}", f"{r.p_perm:.3f}"] for r in _rm.itertuples()]
TF("Table S5. Residual spatial autocorrelation by model specification, Korea, 2011-2024", ["Specification", "Characteristics", "WAIC", "Residual Moran's I", "Permutation P"], rows,
   "Moran's I of district mean residuals with the principal adjacency graph; P from permutation. ICAR, intrinsic conditional autoregressive.")
_pm = rd3("S50_parsimonious.csv")
rows = [[LABEL.get(r.cov, r.cov), "Retained characteristic" if r.role == "robust" else "Forced control", st((r.IRR, r.lo, r.hi))] for r in _pm.itertuples()]
TF(f"Table S6. Parsimonious model with the three characteristics retained in all subsets and the five forced controls, Korea, 2011-2024 (WAIC {_pm.WAIC.iloc[0]:,.1f})", ["Variable", "Role", "Rate ratio (95% CrI)"], rows,
   f"Rate ratios per 1 standard deviation. The principal model with all thirteen characteristics had WAIC {N['waic_main']:,.1f}. CrI, credible interval.")
_GR = {"연도 전체 0/결측": ("All districts 0 or missing in a year", "Any year", "Post-2020 indicator by design"),
       "연도 전체 상수": ("Same value in all districts in a year", "Any year", "Post-2020 indicator by design"),
       "연도가 분산 대부분 설명": ("Year explains most variance", "R² ≥ 0.9", "Post-2020 indicator by design"),
       "연도 간 평균 2배 이상 차이": ("Yearly means differ twofold", "Max/min ≥ 2", "Ratio artifact or real trend"),
       "비율형인데 100 초과": ("Proportion above 100", "Max > 100", "Men per 100 women"),
       "전 연도 0인 지역": ("Districts with 0 in all years", "Any district", "True zeros")}
_cnt = {}
for l in gate.splitlines():
    m = re.match(r"\s+\[([^\]]+)\]\s+(\S+):", l)
    if m: _cnt.setdefault(m.group(1), []).append(m.group(2))
assert set(_cnt) <= set(_GR) and sum(len(v) for v in _cnt.values()) == nwarn, _cnt
rows = [[_GR[k][0], _GR[k][1], str(len(v)), _GR[k][2]] for k, v in _cnt.items()]
_ncol = re.search(r'점검 열 (\d+)', gate).group(1)
TF("Table S7. Automated panel checks before modeling, by rule, Korea, 2011-2024", ["Rule", "Threshold", "Flags", "Reason"], rows,
   f"The gate checked {_ncol} columns of the {N['n_rows']:,}-row analytic panel. Every flag was checked against the source and kept; no value was changed as a result of these flags; implausible recipient shares (33 cells) were set to missing beforehand (Supplementary Methods).")
# Figure S1
J.page_break(); _pp = J.para(""); _pp.add_run().add_picture(os.path.join(HERE, "figs", "JTO_FigS1.png"), width=Cm(16))
J.para("<b>Figure S1.</b> Persistence of the district pattern of the mortality-to-treatment ratio of lung cancer, Korea, 2011-2024. (A) Emerging hot spot analysis (Getis-Ord Gi* with Mann-Kendall trend) of empirical Bayes-smoothed ratios; numbers of districts in parentheses. (B) Number of calendar windows (2011-2015, 2016-2019, 2020-2024) in which each district was a residual hot or cold spot. Map lines delineate study areas and do not necessarily depict accepted national boundaries.")
# STROBE
DS = [x[4:].strip() for x in read_draft()["Discussion"] if x.startswith("### ")]; MH = [h for h, _ in C.METHODS]; RH = [h for h, _ in C.RESULTS if h]
CK = [("Title and abstract", "1", "Title page; Abstract"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"), ("Study design", "4", f"Materials and Methods, {MH[0]}"), ("Setting", "5", f"Materials and Methods, {MH[0]}"),
      ("Participants", "6", f"Materials and Methods, {MH[0]} (district populations; ecological)"), ("Variables", "7", f"Materials and Methods, {MH[1]} and {MH[2]}; Table S1"), ("Data sources/measurement", "8", "Materials and Methods; Supplementary Methods"),
      ("Bias", "9", f"Materials and Methods, {MH[3]}; Tables S2 and S3"), ("Study size", "10", f"Materials and Methods, {MH[0]} (all 229 districts)"), ("Quantitative variables", "11", f"Materials and Methods, {MH[2]}"),
      ("Statistical methods", "12", f"Materials and Methods, {MH[3]}"), ("Participants (flow)", "13", "Not applicable (aggregate district data; no exclusions)"), ("Descriptive data", "14", f"Results, {RH[0]}; Table 1"), ("Outcome data", "15", f"Results, {RH[0]} and {RH[1]}; Figures 1 and S1"),
      ("Main results", "16", f"Results, {RH[2]}; Table 2"), ("Other analyses", "17", f"Results, {RH[3]}; Figure 2; Tables S2 and S3"),
      ("Key results", "18", "Discussion, first paragraph"), ("Limitations", "19", "Discussion, Limitations"), ("Interpretation", "20", "Discussion"), ("Generalizability", "21", "Discussion, Implications and Limitations"),
      ("Funding", "22", "Title page, Funding support")]
assert "Limitations" in DS and "Implications" in DS
J.page_break()
J.table_fit("STROBE checklist for this ecological study", ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK], "", fs_max=8, title_bold=False)
foot_row(J, "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology.", 8, 12)
ps = os.path.join(OUT, "Supplemental_Data_1.docx"); J.doc_title = "Supplemental Data 1"; J.save(ps)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_lcad_esm", "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
