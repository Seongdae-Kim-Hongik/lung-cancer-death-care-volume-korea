#!/usr/bin/env python3
# 99R_next5b-mort — 2차 후보 사망 세부 사인 시군구 사망자 수(2026-11-12; 99R_alld_extra_causes.py 복제·사인 코드만 교체, 원본 수정 없음).
#  원표 DT_1B34E13 정리본(02_패널/사망원인_시군구_연도_사인_성_long.parquet) → 50.load_source(일반구 합산, 코드표 결합) → 시군구 마스터키. 검산: 계(코드 0) = 기준 SQLite mort__전체사망_deaths 3,206칸.
#  산출: 02_패널/next5b_mort_counts_261112.csv
import os, sqlite3, unicodedata, importlib.util, numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); PAN = os.path.join(os.path.dirname(HERE), "02_패널")
DB = os.environ.get("ST_DB", "02_체육건강_시공간.sqlite")
CODES = {"0": "total_chk", "11": "c11", "12": "c12", "I": "cI", "E": "cE", "25": "c25", "29": "c29", "2B": "c2B", "6": "c6", "61": "c61", "5": "c5", "B": "cB", "B1": "cB1", "26": "c26", "24": "c24"}
L = pd.read_parquet(os.path.join(PAN, "사망원인_시군구_연도_사인_성_long.parquet"), columns=["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note", "cause_code", "sex", "deaths"],
                    filters=[("sex", "==", "계"), ("year", ">=", 2011), ("year", "<=", 2024), ("cause_code", "in", list(CODES))])
L = L[(L.sex == "계") & L.year.between(2011, 2024) & L.cause_code.isin(list(CODES))]; L["v"] = L.cause_code.map(CODES)
IDX = ["year", "sido", "sigungu", "sgg_code", "sgg_code_std", "level", "parent_code", "code_note"]
for c in IDX[1:]: L[c] = L[c].fillna("").astype(str)
W = L.pivot_table(index=IDX, columns="v", values="deaths", aggfunc="sum").reset_index().replace({"": np.nan}); W = W[W.level.notna()]
tmpf = "_tmp_next5b_mort_wide.csv"; W.to_csv(os.path.join(PAN, tmpf), index=False, encoding="utf-8-sig")
spec = importlib.util.spec_from_file_location("m50", os.path.join(HERE, "50_build_master_panel.py")); m50 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m50)
mk = pd.read_csv(os.path.join(PAN, "시군구_마스터키.csv"), dtype=str); mk = mk[mk.fbd_sido.notna()].drop_duplicates("key")
log = dict(missing_files=[], level_filter={}, unmatched=[], special=[], overlap=[], sources={})
src = dict(name="mortn5b", prefix="", files=[tmpf], sido="sido", sgg="sigungu", merge_counts=True, level="시군구", ratio=lambda c: False, label="사망원인통계")
agg, meta = m50.load_source(src, set(mk.key), log); os.remove(os.path.join(PAN, tmpf))
agg = agg.merge(mk[["key", "fbd_region"]], on="key", how="left"); agg["fbd_region"] = agg.fbd_region.map(NFC); agg["year"] = agg.year.astype(int)
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
R = pd.read_sql('select year, fbd_region, "mort__전체사망_deaths" as total from region_year where year between 2011 and 2024', c); R["fbd_region"] = R.fbd_region.map(NFC)
M = R.merge(agg[["year", "fbd_region"] + ["total_chk"] + [v for v in CODES.values() if v != "total_chk"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
print("[99R5b-mort] 결측 칸:", M[["total_chk"] + [v for v in CODES.values() if v != "total_chk"]].isna().sum().to_dict())
assert M.total_chk.notna().all() and (M.total_chk == M.total).all(), "원표 계 ≠ 기준 SQLite 전체 사망"
VV = [v for v in CODES.values() if v != "total_chk"]; M[VV] = M[VV].fillna(0)
print("[99R5b-mort] 계 = 기준 SQLite 3,206칸 일치. 연도 합:", M.groupby("year")[VV].sum().astype(int).loc[[2011, 2024]].to_dict("index"))
M[["year", "fbd_region"] + VV + ["total_chk"]].to_csv(os.path.join(PAN, "next5b_mort_counts_261112.csv"), index=False, encoding="utf-8-sig")
