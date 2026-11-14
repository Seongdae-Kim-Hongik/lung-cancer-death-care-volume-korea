# numbers_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
import os, glob, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.path.join(ROOT, "02_패널")
WIN = [("W1_2011-15", 2011, 2015), ("W2_2016-19", 2016, 2019), ("W3_2020-24", 2020, 2024)]
rd = lambda f, **k: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", **k)
EDU, OUTC, CSR = "tertiary_educated_share", "outside_care_share", "ext__cancer_screen_rate"
ROB = [OUTC, CSR, EDU]   # S7 robust 집합(다중우주 ≥75%·부호 ≥95%)
SENS = ["smr", "ma3", "s577", "s2", "s8"]
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))
COVS = ["pop80_share", "urban_population_share", "ext__genhosp_per100k", "outside_care_share", "ext__cancer_screen_rate", "current_smoking_rate", "prior_tb_share", "coal_plant_host",
        "factory_land_share", "detached_house_households", "walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k", "basic_livelihood_rate", "tertiary_educated_share"]
SIDO_EN = {"11": "Seoul", "21": "Busan", "22": "Daegu", "23": "Incheon", "24": "Gwangju", "25": "Daejeon", "26": "Ulsan", "29": "Sejong", "31": "Gyeonggi", "32": "Gangwon",
           "33": "North Chungcheong", "34": "South Chungcheong", "35": "North Jeolla", "36": "South Jeolla", "37": "North Gyeongsang", "38": "South Gyeongsang", "39": "Jeju"}

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_LCAD_std3.csv")); N["n_rows"] = len(P); N["n_districts"] = P.fbd_region.nunique()
    assert (N["n_rows"], N["n_districts"]) == (3206, 229)
    Em = pd.read_csv(os.path.join(PAN, "LCAD_Emtr.csv")); Xt = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_LCAD_261112.csv"))
    X = P[["year", "fbd_region", "cases", "E", "offset"]].merge(Em[["year", "fbd_region", "E_mtr", "E_sexage"]], on=["year", "fbd_region"], validate="one_to_one") \
        .merge(Xt[["year", "fbd_region", "lcad_deaths", "treated_n", "treated_E", "sir_treat"]], on=["year", "fbd_region"], validate="one_to_one")
    assert (X.cases == X.lcad_deaths).all() and np.allclose(X.E, X.E_mtr)
    X = X.rename(columns={"treated_n": "care", "treated_E": "E_care", "E_sexage": "E_death"})
    N["cases_total"] = int(P.cases.sum()); N["py"] = float(P.offset.sum()); N["care_total"] = int(X.care.sum())
    y = X.groupby("year")[["cases", "offset", "care"]].sum(); N["cases_2011"], N["cases_2024"] = int(y.cases[2011]), int(y.cases[2024])
    N["care_2011"], N["care_2024"] = int(y.care[2011]), int(y.care[2024])
    N["ratio_y"] = (100 * y.cases / y.care).to_dict(); N["ratio_2011"], N["ratio_2024"] = N["ratio_y"][2011], N["ratio_y"][2024]
    N["crude_y"] = (1e5 * y.cases / y.offset).to_dict()
    A = pd.read_csv(os.path.join(PAN, "LCAD_national_agerates_mort.csv"), encoding="utf-8-sig")
    _d = {yr: y.cases[yr] - A[A.year == yr].deaths.sum() for yr in y.index}; N["age_unknown"] = int(round(sum(_d.values()))); assert all(-0.5 <= v <= 5 for v in _d.values()), _d
    w = A[A.year == 2015].set_index("age").denom_nat; w = w / w.sum(); asr = {}
    for yr, g in A.groupby("year"): asr[yr] = 1e5 * float((g.set_index("age").rate * w).sum())
    N["asr"] = asr; N["asr_2011"], N["asr_2024"] = asr[2011], asr[2024]
    Q = X.groupby("fbd_region")[["cases", "E_death", "care", "E_care", "E"]].sum()
    Q["smr"] = Q.cases / Q.E_death; Q["sir_care"] = Q.care / Q.E_care; Q["mtr"] = Q.cases / Q.E
    N["dist"] = {k: (Q[k].quantile(.1), Q[k].median(), Q[k].quantile(.9)) for k in ("smr", "sir_care", "mtr")}
    N["mtr_min"] = (Q.mtr.idxmin(), Q.mtr.min()); N["mtr_max"] = (Q.mtr.idxmax(), Q.mtr.max())
    N["rho_smr_care"] = spearmanr(Q.smr, Q.sir_care).correlation; N["rho_mtr_care"] = spearmanr(Q.mtr, Q.sir_care).correlation; N["rho_mtr_smr"] = spearmanr(Q.mtr, Q.smr).correlation
    N["Q"] = Q
    T1 = {}
    for wn, a, b in WIN + [("2011-2024", 2011, 2024)]:
        q = P[(P.year >= a) & (P.year <= b)]; xq = X[(X.year >= a) & (X.year <= b)]
        g = xq.groupby("fbd_region")[["cases", "E", "E_death", "care", "E_care"]].sum()
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), care=int(xq.care.sum()), py=float(q.offset.sum()), ratio=100 * xq.cases.sum() / xq.care.sum(),
                      asr=np.mean([asr[t] for t in range(a, b + 1)]), mtr=(g.cases / g.E).quantile([.1, .5, .9]).tolist(), smr=(g.cases / g.E_death).quantile([.1, .5, .9]).tolist(),
                      care_sir=(g.care / g.E_care).quantile([.1, .5, .9]).tolist(), cov={v: (q[f"{v}_raw"].mean(), q[f"{v}_raw"].std()) for v in COVS})
    N["T1"] = T1
    # 공간
    s6m = rd("S6_moran_year.csv"); N["moran_year_min"], N["moran_year_max"] = s6m.moran_I.min(), s6m.moran_I.max(); N["moran_y"] = s6m.set_index("year").moran_I.to_dict()
    N["moran_year_p_max"] = s6m.p_perm.max()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"] = r8.loc["pearson_residual_area_mean", "moran_I"]; N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv", dtype={"sigungu_cd": str}); N["rr_min"], N["rr_max"] = s6.RR.min(), s6.RR.max(); N["s6"] = s6
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    N["n_hot_rr110"] = int(((s6["class"] == "hotspot") & (s6.RR >= 1.10)).sum()); N["n_cold_rr090"] = int(((s6["class"] == "coldspot") & (s6.RR <= 0.90)).sum())
    s6["sido"] = s6.sigungu_cd.str[:2]; N["n_sido"] = s6.groupby("sido").size().to_dict()
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby("sido").size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby("sido").size().sort_values(ascending=False).to_dict()
    N["hot_top"] = s6.sort_values("RR", ascending=False).head(5)[["fbd_region", "RR"]].values.tolist(); N["cold_top"] = s6.sort_values("RR").head(5)[["fbd_region", "RR"]].values.tolist()
    typ = s6.fbd_region.map(lambda r: "county" if r.endswith("군") else ("ward" if r.endswith("구") else "city"))
    N["type_class"] = pd.crosstab(typ, s6["class"]).to_dict()
    wm = rd("S4b_window_spatialRR.csv"); hs = {w: set(wm[(wm.window == w) & (wm["class"] == "hotspot")].fbd_region) for w in wm.window.unique()}; N["hot_all_windows"] = len(set.intersection(*hs.values()))
    cs = {w: set(wm[(wm.window == w) & (wm["class"] == "coldspot")].fbd_region) for w in wm.window.unique()}; N["cold_all_windows"] = len(set.intersection(*cs.values()))
    _pv = wm.pivot_table(index="fbd_region", columns="window", values="RR").corr(method="spearman"); N["win_rr_rho"] = float(_pv.loc["W1_2011-15", "W3_2020-24"])
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    N["ehsa"] = rd("S11_ehsa_summary.csv").set_index("category").n.to_dict()
    vp = rd("S42_variance_partition.csv"); N["varpart"] = vp
    # 주모형·다중우주
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role", "label_en"]].to_dict("index")
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); N["n_cred_hyp"] = int(((m3.role == "hypothesis") & m3.cred).sum())
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust", "IRR_min", "IRR_max"]].to_dict("index")
    assert set(s7.index[s7.robust]) == set(ROB), s7.index[s7.robust].tolist()
    fit = rd("S3_main_fit.csv").iloc[0]; N["waic_main"] = float(fit.WAIC); N["family"] = fit.family
    LK = rd("S1_likelihood.csv"); LK = LK[LK.set == "REF_forced_only"].set_index("family").WAIC; N["waic_pois"], N["waic_nb"] = float(LK["poisson"]), float(LK["nbinomial"]); N["waic_forced"] = min(N["waic_pois"], N["waic_nb"])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = nc[["IRR", "lo", "hi", "cred"]].to_dict("index")
    wi = rd("S4_window_IRR.csv"); N["win_irr"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in wi.itertuples()}
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict(); N["s43_analyses"] = sorted(S43.analysis.unique())
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    N["alt"] = sorted({a for a in S41.analysis.unique() if not a.startswith(("F1_", "F2_", "G2_", "H1_", "bw_"))})
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["retention"] = rd("S41_retention_by_cov.csv").set_index("cov").to_dict("index"); N["rubin"] = rd("S41_noise_rubin.csv").set_index("cov").to_dict("index")
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index"); N["oos"] = rd("S41_oos2024.csv").iloc[0].to_dict(); N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict()
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in rd("S41_nco_detail.csv").itertuples()}
    lo = rd("S41_leaveout_ranges.csv"); N["leaveout"] = {(r.set, r.cov): (int(r.n), int(r.n_cred_same_sign)) for r in lo.itertuples() if not str(r.cov).startswith("__")}
    cv = rd("S5_covid.csv"); N["covid_main"] = tuple(cv[cv["cov"] == "post"][["IRR", "lo", "hi"]].iloc[0])
    rs = rd("S50_region_slopes.csv"); N["s50_region"] = {tuple(r.cov.split("__")): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in rs.itertuples()}
    N["s50_region_dwaic"] = rs.groupby(rs["cov"].str.split("__").str[0]).dWAIC_vs_common.first().to_dict()
    N["within_sd"] = {}
    for v in ROB:
        x = P[f"{v}_raw"]; mi = P.groupby("fbd_region")[f"{v}_raw"].transform("mean"); mt = P.groupby("year")[f"{v}_raw"].transform("mean")
        N["within_sd"][v] = (float((x - mi - mt + x.mean()).std()), float(mi.std()), float(x.std()))
    # 사전지정 민감도
    s6i = s6.set_index("sigungu_cd"); h0 = set(s6i.index[s6i["class"] == "hotspot"]); c0 = set(s6i.index[s6i["class"] == "coldspot"])
    N["sens_main"] = {}; N["sens_hot"] = {}; N["sens_waic"] = {}
    for v in SENS:
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens_main"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
        N["sens_waic"][v] = float(pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_fit.csv")).WAIC.iloc[0])
        sv = pd.read_csv(os.path.join(B, f"results_{v}", "S6_spatial_RR.csv"), dtype={"sigungu_cd": str}).set_index("sigungu_cd")
        hv = set(sv.index[sv["class"] == "hotspot"]); cv_ = set(sv.index[sv["class"] == "coldspot"])
        N["sens_hot"][v] = dict(n_hot=len(hv), n_cold=len(cv_), jac=len(hv & h0) / len(hv | h0), overlap=len(hv & h0), rho=spearmanr(sv.RR.reindex(s6i.index), s6i.RR).correlation,
                                hot_sido={SIDO_EN[k]: n for k, n in pd.Series([c[:2] for c in hv]).value_counts().items()}, cold_sido={SIDO_EN[k]: n for k, n in pd.Series([c[:2] for c in cv_]).value_counts().items()},
                                busan_cold=len([c for c in cv_ if c[:2] == "21"]))
    N["busan_hot_smr"] = len([c for c in h0 if c[:2] == "21" and c in set(pd.read_csv(os.path.join(B, "results_smr", "S6_spatial_RR.csv"), dtype={"sigungu_cd": str}).query("`class`=='hotspot'").sigungu_cd)])
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame))})
    print("dist", N["dist"], N["mtr_min"], N["mtr_max"]); print("hot", N["hot_by_sido"]); print("cold", N["cold_by_sido"]); print("ehsa", {k: v for k, v in N["ehsa"].items() if v})
    print("ratio", {k: round(v, 2) for k, v in N["ratio_y"].items()}); print("asr", {k: round(v, 2) for k, v in N["asr"].items()})
    print("sens_hot", N["sens_hot"]); print("hot_top", N["hot_top"], "cold_top", N["cold_top"]); print(N["varpart"]); print("type", N["type_class"])
    for v in ROB: print(v, N["main"][v], N["mv"][v], {k: N["s43"].get((k, v)) for k in ("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV")}, N["bw"].get(v + "__between"), N["bw"].get(v + "__within"),
                        N["nco"].get(("TRANS", v)), N["nco"].get(("FALL", v)), N["evalue"].get(v), N["retention"].get(v), N["rubin"].get(v), N["leaveout"].get(("province", v)), N["leaveout"].get(("year", v)),
                        {s: N["sens_main"][s].get(v) for s in SENS}, {r: N["s50_region"].get((v, r)) for r in ("Capital", "Yeongnam", "Honam", "Chungcheong", "Gangwon_Jeju")}, N["within_sd"][v],
                        {w: N["win_irr"].get((v, w)) for w, _, _ in WIN})
    print("waic", N["waic_main"], N["waic_pois"], N["waic_nb"], {k: N["s43_waic"][k] for k in sorted(N["s43_waic"])}); print("negctl", N["negctl"]); print("alt", N["alt"], len(N["alt"]))
    print("smk", N["main"]["current_smoking_rate"], "bls smr", N["sens_main"]["smr"]["basic_livelihood_rate"]); print("covid", N["covid_main"]); print("busan_hot_smr", N["busan_hot_smr"])
    print("forced smr", {c: N["sens_main"]["smr"][c] for c in ("urban_population_share", "pop80_share", "sex_ratio", "fiscal_independence", "physicians_per_1000")})
    print("ppc", N["ppc"], "oos", N["oos"], "phi", N["phi"], "moran", N["moran_pooled"], N["moran_year_min"], N["moran_year_max"], N["moran_resid"], N["moran_resid_p"], N["moran_year_p_max"])
