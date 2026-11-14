# 99c_extra_canonical_pool_lcad.py: builds district-year covariates used in the lung cancer deaths analysis (see README).
#!/usr/bin/env python3
#  ③ EXT_covariates_exposure.csv: coal_host, coal_near, coal_gw, detached_hh_share
import os, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PAN = os.path.join(ROOT, "02_패널")
rd = lambda f: (lambda d: d.assign(fbd_region=d.fbd_region.map(NFC)))(pd.read_csv(os.path.join(PAN, f), encoding="utf-8-sig"))
MC = rd("next5b_mort_counts_261112.csv")[["year", "fbd_region", "c26"]].rename(columns={"c26": "lcad_deaths"})
C = rd("EXT_covariates_care_ses.csv")[["year", "fbd_region", "basic_livelihood_rate", "tertiary_educated_share", "genhosp_per100k", "factory_land_share", "cancer_screen_rate", "ill_defined_share"]]
L = rd("EXT_covariates_exposure.csv")[["year", "fbd_region", "coal_host", "coal_near", "coal_gw", "detached_hh_share", "factory_land_share"]].rename(columns={"factory_land_share": "_fl_exp"})
O = rd("EXT_canonical_pool_261106.csv")[["year", "fbd_region", "outside_care_share"]]
T = pd.read_csv(os.path.join(ROOT, "04_분석", "TREATED", "panel_treated_std3.csv"), encoding="utf-8-sig")[["year", "fbd_region", "cases", "E"]]
T["fbd_region"] = T.fbd_region.map(NFC); T = T.rename(columns={"cases": "treated_n", "E": "treated_E"})
out = MC
for X in (C, L, O, T): out = out.merge(X, on=["year", "fbd_region"], how="left", validate="one_to_one")
assert len(out) == 3206 and out.fbd_region.nunique() == 229 and out.notna().all().all(), out.isna().sum()[out.isna().sum() > 0]
assert np.allclose(out.factory_land_share, out._fl_exp), "21·공장용지 정의 불일치"; out = out.drop(columns="_fl_exp")
cw = out[(out.fbd_region == NFC("경상남도창원시")) & out.year.isin([2021, 2022, 2023])].basic_livelihood_rate
assert cw.between(1.5, 3.5).all(), f"창원 수급률 정정 안 됨 {cw.tolist()}"
out["sir_treat"] = out.treated_n / out.treated_E; assert (out.sir_treat > 0).all()
out = out.sort_values(["fbd_region", "year"]).reset_index(drop=True)
out["sir_treat_ma3"] = out.groupby("fbd_region").sir_treat.transform(lambda s: s.rolling(3, center=True, min_periods=2).mean())
N = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig")
N = N[(N.item == "사망자수") & (N.sex == "계") & (N.age == "계") & (N.cause == "기관 기관지 및 폐의 악성신생물 (C33-C34)") & N.year.between(2011, 2024)].groupby("year").value.sum()
r = out.groupby("year").lcad_deaths.sum() / N
print("[99c-lcad] 시군구 합/전국 폐암 사망:", r.round(4).min(), "~", r.round(4).max(), "| 14년 합", int(out.lcad_deaths.sum()), "| 0칸", int((out.lcad_deaths == 0).sum()))
assert ((r > 0.99) & (r <= 1.0001)).all()
print("[99c-lcad] sir_treat:", out.sir_treat.describe()[["min", "50%", "max"]].round(3).to_dict(), "| 진료 최소", int(out.treated_n.min()))
out.to_csv(os.path.join(PAN, "EXT_canonical_pool_LCAD_261112.csv"), index=False, encoding="utf-8-sig"); print("[99c-lcad] 저장 02_패널/EXT_canonical_pool_LCAD_261112.csv", out.shape)
