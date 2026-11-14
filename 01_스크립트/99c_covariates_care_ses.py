# 99c_covariates_care_ses.py: builds district-year covariates used in the lung cancer deaths analysis (see README).
#!/usr/bin/env python3
import os, sys, json, unicodedata, importlib.util
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
PAN = os.path.join(ROOT, "02_패널")

C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
out = pd.DataFrame({"year": C.year, "fbd_region": C.region.map(NFC),
                    "basic_livelihood_rate": C.basic_livelihood_recipient_rate.astype(float),
                    "tertiary_educated_share": C.tertiary_educated_share.astype(float),
                    "genhosp_per100k": C.general_hospitals.astype(float) / C["pop"].astype(float) * 1e5,
                    "factory_land_share": C.factory_land_area.astype(float)})
out = out[(out.year >= 2011) & (out.year <= 2024)].copy().sort_values(["fbd_region", "year"])
_ref = out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean()
bad = out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * out.fbd_region.map(_ref)) | (out.basic_livelihood_rate > 5 * out.fbd_region.map(_ref)) | (out.fbd_region == NFC("경상남도창원시")))
print("[99c-cov-care] 수급률 결함 칸", int(bad.sum()), sorted(out.loc[bad, "fbd_region"].unique()), "→ 결측 후 보간")
assert bad.sum() == 33 and NFC("경상남도창원시") in set(out.loc[bad, "fbd_region"])
out.loc[bad, "basic_livelihood_rate"] = np.nan
out["basic_livelihood_rate"] = out.groupby("fbd_region").basic_livelihood_rate.transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
assert out.basic_livelihood_rate.notna().all() and out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229
D19 = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_DMD_261108.csv"), encoding="utf-8-sig"); D19["fbd_region"] = D19.fbd_region.map(NFC)
chk = out.merge(D19[["year", "fbd_region", "basic_livelihood_rate", "ill_defined_share"]], on=["year", "fbd_region"], suffixes=("", "_dmd"), validate="one_to_one")
assert np.allclose(chk.basic_livelihood_rate, chk.basic_livelihood_rate_dmd), "정정판과 수급률 불일치"
out = out.merge(D19[["year", "fbd_region", "ill_defined_share"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
L16 = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_LIVD_261108.csv"), encoding="utf-8-sig"); L16["fbd_region"] = L16.fbd_region.map(NFC)
out = out.merge(L16[["year", "fbd_region", "hcv_notif_rate_log"]], on=["year", "fbd_region"], how="left", validate="one_to_one")

s32 = open(os.path.join(HERE, "32_build_nhis_checkup_panel.py"), encoding="utf-8").read(); s32 = s32[:s32.index("def load_table")]
g32 = {"__file__": os.path.join(HERE, "32_build_nhis_checkup_panel.py"), "__name__": "m32"}; exec(compile(s32, "m32", "exec"), g32)
N = pd.read_csv(os.path.join(ROOT, "00_원천", "C_NHIS_검진보험", "암검진_N009", "DT_35007_N009_long.csv"), encoding="utf-8-sig", dtype={"C1": str, "C2": str, "C3": str})
N = N[N.C2 == "001"].copy(); N["DT"] = pd.to_numeric(N.DT, errors="coerce")
sido, sgg, level = g32["parse_region"](N, "NHIS", "C1"); N["sido"], N["sigungu"], N["level"] = sido, sgg, level
N["v"] = N.C3.map({"001_1": "all", "002": "gastric", "003": "crc"}) + "_" + N.ITM_NM.map({"대상인원": "elig", "수검인원": "scr"})
N["year"] = N.PRD_DE.astype(int)
W = N[N.level == "시군구"].pivot_table(index=["year", "sido", "sigungu", "level"], columns="v", values="DT", aggfunc="sum").reset_index()
tmpf = "_tmp_cov_screen_wide.csv"; W.to_csv(os.path.join(PAN, tmpf), index=False, encoding="utf-8-sig")
spec = importlib.util.spec_from_file_location("m50", os.path.join(HERE, "50_build_master_panel.py")); m50 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m50)
mk = pd.read_csv(os.path.join(PAN, "시군구_마스터키.csv"), dtype=str); mk = mk[mk.fbd_sido.notna()].drop_duplicates("key")
log = dict(missing_files=[], level_filter={}, unmatched=[], special=[], overlap=[], sources={})
src = dict(name="canscr", prefix="", files=[tmpf], sido="sido", sgg="sigungu", merge_counts=True, level="시군구", ratio=lambda c: False, label="암검진")
agg, meta = m50.load_source(src, set(mk.key), log)
os.remove(os.path.join(PAN, tmpf))
um = pd.concat(log["unmatched"]) if log["unmatched"] else pd.DataFrame()
if len(um): print("[99c-cov-care] 암검진 미결합 지역:", um[["_sido", "_sgg", "years", "n_rows_with_values"]].to_string())
agg = agg.merge(mk[["key", "fbd_region"]], on="key", how="left"); agg["fbd_region"] = agg.fbd_region.map(NFC); agg["year"] = agg.year.astype(int)
agg = agg[agg.year.between(2011, 2024)]
for k in ("all", "gastric", "crc"):
    agg[{"all": "cancer_screen_rate", "gastric": "gastric_screen_rate", "crc": "crc_screen_rate"}[k]] = 100 * agg[f"{k}_scr"] / agg[f"{k}_elig"]
SJ = N[(N.level == "시도") & (N.sido.astype(str).str.startswith("세종"))].pivot_table(index="year", columns="v", values="DT", aggfunc="sum").reset_index()
assert len(SJ) >= 13, SJ
SJ["fbd_region"] = NFC("세종시세종시"); SJ = SJ[SJ.year.between(2012, 2024)]
assert set(agg.loc[agg.fbd_region == NFC("세종시세종시"), "year"]) <= {2011}
agg = pd.concat([agg[~((agg.fbd_region == NFC("세종시세종시")) & agg.year.isin(SJ.year))], SJ], ignore_index=True)
for k in ("all", "gastric", "crc"):
    agg[{"all": "cancer_screen_rate", "gastric": "gastric_screen_rate", "crc": "crc_screen_rate"}[k]] = 100 * agg[f"{k}_scr"] / agg[f"{k}_elig"]
out = out.merge(agg[["year", "fbd_region", "cancer_screen_rate", "gastric_screen_rate", "crc_screen_rate"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
print("[99c-cov-care] 결측 칸:", out.isna().sum()[lambda s: s > 0].to_dict())
print("[99c-cov-care] 암검진 수검률 연도 중앙값:", out.groupby("year").cancer_screen_rate.median().round(1).to_dict())
nat = N[(N.level == "전국") & (N.C3 == "001_1")].pivot_table(index="year", columns="ITM_NM", values="DT", aggfunc="sum")
s229 = agg.groupby("year")[["all_elig", "all_scr"]].sum()
print("[99c-cov-care] 229 합/전국(대상·수검):", (s229.all_elig / nat["대상인원"]).round(4).to_dict(), (s229.all_scr / nat["수검인원"]).round(4).to_dict())
for c in ["cancer_screen_rate", "tertiary_educated_share", "genhosp_per100k", "factory_land_share", "basic_livelihood_rate"]:
    s = out.sort_values(["fbd_region", "year"]).groupby("fbd_region")[c]
    nb = (s.shift(1) + s.shift(-1)) / 2; v = out.sort_values(["fbd_region", "year"])[c]
    n = int(((v < 0.2 * nb) | (v > 5 * nb)).sum()); print(f"[99c-cov-care] 게이트 {c}: 이웃 평균 대비 <20%·>5배 칸 {n}")
out.to_csv(os.path.join(PAN, "EXT_covariates_care_ses.csv"), index=False, encoding="utf-8-sig")
print("[99c-cov-care] 저장 02_패널/EXT_covariates_care_ses.csv", out.shape)
