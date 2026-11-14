#!/usr/bin/env python3
# 99R_next5b-mortE — 2차 후보 사망 세부 사인 E(2026-11-12; 99Q_build_E_next5.py 복제·사망 대상만 교체, 원본 수정 없음).
#  분자 = 02_패널/next5b_mort_counts_261112.csv(원표 DT_1B34E13, 코드표 결합, 계 = 기준 SQLite 3,206칸 일치). 검산: 알츠하이머(G30)·간질환(K70-K76) = 기준 SQLite.
#  E = Σ_s Σ_a pop(성×18연령, 창원 2023 정정) × 전국 율(DT_1B34E01, 연령미상 제외), 연도별 ΣE = Σcases. 산출: 02_패널/<TAG>_Estd3r.csv
import os, sys, sqlite3, importlib.util, unicodedata
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석"); PAN = os.path.join(ROOT, "02_패널")
SRC = os.path.join(ROOT, "00_원천", "C_NHIS_검진보험")
DB = os.environ.get("ST_DB", "02_체육건강_시공간.sqlite")
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m38 = _load("m38", "38_build_Estd_all.py"); cw = _load("cw", "40_region_crosswalk.py"); m50 = _load("m50", "50_build_master_panel.py")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
assert os.environ.get("ST_FBDZIP"), "ST_FBDZIP(창원 2023 교정 인구 폴더)를 지정"
YEARS = list(range(2011, 2025)); SEXES = ["남자", "여자"]
SCR = {}
HI, CB, HT, IH = "허혈성 심장 질환 (I20-I25)", "뇌혈관 질환 (I60-I69)", "고혈압성 질환 (I10-I13)", "기타 심장 질환 (I26-I51)"
MORT = {"SEPS": (["c12"], ["패혈증 (A40-A41)"], []), "TBD": (["c11"], ["호흡기 결핵 (A15-A16)"], []),
        "ILLD": (["cI"], ["달리 분류되지 않은 증상 징후 (R00-R99)"], []), "GUD": (["cE"], ["비뇨생식계통의 질환 (N00-N98)"], []),
        "PANC": (["c25"], ["췌장의 악성신생물 (C25)"], []), "PRCA": (["c29"], ["전립선의 악성신생물 (C61)"], []), "LEUK": (["c2B"], ["백혈병 (C91-C95)"], []),
        "NEUX": (["c6", "-c61"], ["신경계통의 질환 (G00-G98)"], ["알츠하이머병 (G30)"]), "MNTL": (["c5"], ["정신 및 행동장애 (F01-F99)"], []),
        "DIGX": (["cB", "-cB1"], ["소화계통의 질환 (K00-K92)"], ["간 질환 (K70-K76)"]), "LCAD": (["c26"], ["기관 기관지 및 폐의 악성신생물 (C33-C34)"], []),
        "HCCD": (["c24"], ["간 및 간내 담관의 악성신생물 (C22)"], [])}
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cols = ["mort__알츠하이머_deaths", "mort__간질환_deaths"]
RY = pd.read_sql("select year, fbd_region, " + ", ".join(f'"{c}"' for c in cols) + " from region_year where year between 2011 and 2024", con); RY["fbd_region"] = RY.fbd_region.map(NFC)
MC = pd.read_csv(os.path.join(PAN, "next5b_mort_counts_261112.csv"), encoding="utf-8-sig"); MC["fbd_region"] = MC.fbd_region.map(NFC)
RY = RY.merge(MC, on=["year", "fbd_region"], how="left", validate="one_to_one"); assert RY.c12.notna().all()
assert (RY.c61 == RY["mort__알츠하이머_deaths"]).all() and (RY.cB1 == RY["mort__간질환_deaths"]).all(), "원표 결합 검산 실패"; print("[99R5b-mortE] 알츠하이머·간질환 = 기준 SQLite 3,206칸 일치")
base = pd.read_sql("select year, key, fbd_region from disease_panel where tag='PERIO'", con); base["fbd_region"] = base.fbd_region.map(NFC); base["key"] = base.key.map(NFC)
PKEYS = set(base.key); assert len(base) == 3206
# ── 시군구 성×연령 인구(99U2 규칙) ──
BANDS16 = ["0-19"] + [f"{lo}-{lo+4}" for lo in range(20, 85, 5)] + ["85+"]; BANDS18 = [f"{lo}-{lo+4}" for lo in range(0, 85, 5)] + ["85+"]
SIDO_HDR = {k for k in cw.SIDO_STD if len(k) >= 3 and (k.endswith("시") or k.endswith("도"))}
FIVE = [f"{lo}-{lo+4}세" for lo in range(0, 85, 5)]; OLD85 = ["85-89세", "90-94세", "95-99세", "100세 이상"]
EXTRA = {("충청북도", "청원군"): "충청북도|청주시"}; rows = []
for y in YEARS:
    d = pd.read_csv(os.path.join(m38.FBDZIP, f"{y}.csv"), encoding="cp949", dtype=str)
    d["행정구역별"] = d["행정구역별"].map(NFC).str.strip(); d["연령별"] = d["연령별"].map(NFC).str.strip()
    for s in SEXES: d[s] = pd.to_numeric(d[s].str.replace(",", ""), errors="coerce")
    sido = None; city = None; blocks = (d["행정구역별"] != d["행정구역별"].shift()).cumsum()
    for _, g in d.groupby(blocks, sort=False):
        nm = g["행정구역별"].iat[0]
        if nm == "전국": continue
        if nm in SIDO_HDR:
            sido = nm; city = None
            if nm != "세종특별자치시": continue
            g = g.drop_duplicates("연령별")
        sg = nm.split("-")[-1]
        if sg.endswith("시"): city = sg
        elif sg.endswith("구") and city is not None and cw.sido_std(sido) not in ("서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시"): continue
        else: city = None
        key = EXTRA.get((cw.sido_std(sido), sg), cw.make_key(sido, sg))
        if key not in PKEYS and key.endswith("군") and key[:-1] + "시" in PKEYS: key = key[:-1] + "시"
        for s in SEXES:
            a = g.set_index("연령별")[s]
            if pd.isna(a.get("계", np.nan)): continue
            f = a.reindex(FIVE); o = a.reindex(OLD85).fillna(0); assert f.notna().all(), (y, nm, s)
            r = {"year": y, "sex": s, "key": NFC(key), **{b: f[b + "세"] for b in BANDS18[:-1]}, "85+": o.sum()}
            r["0-19"] = f["0-4세"] + f["5-9세"] + f["10-14세"] + f["15-19세"]; r["s0-19_adult"] = f["15-19세"]; rows.append(r)
POP = pd.DataFrame(rows).groupby(["year", "key", "sex"], as_index=False).sum(numeric_only=True)
cwn = POP[(POP.key == NFC(base[base.fbd_region == NFC("경상남도창원시")].key.iat[0])) & (POP.year == 2023)][BANDS18].sum().sum()
print(f"[99R5b-mortE] 창원 2023 인구 {cwn:,.0f} (정답 1,009,038)")
out = {}
# ── 사망 ──
N = pd.read_csv(os.path.join(ROOT, "00_원천", "D_사망_인구_암", "DT_1B34E01_national_long.csv"), encoding="utf-8-sig")
N = N[N.sex.isin(SEXES) & (N.item == "사망자수") & N.year.between(2011, 2024)]
def nat_band(a):
    a = a.replace(" ", "")
    if a in ("0세", "1-4세"): return "0-4"
    if a in ("85-89세", "90세이상"): return "85+"
    if a.endswith("세") and "-" in a:
        lo, hi = a[:-1].split("-")
        if int(hi) - int(lo) == 4 and int(lo) <= 80: return f"{lo}-{hi}"
    return None
N["band"] = N.age.map(nat_band)
NATPOP18 = POP.groupby(["year", "sex"])[BANDS18].sum()
for T, (cl, plus, minus) in MORT.items():
    Z = N[N.band.notna()].groupby(["cause", "year", "sex", "band"]).value.sum()
    x = sum(Z.loc[c].unstack()[BANDS18] for c in plus) - (sum(Z.loc[c].unstack()[BANDS18] for c in minus) if minus else 0)
    rate = x / NATPOP18
    RY["_c"] = sum((-1 if c.startswith("-") else 1) * RY[c.lstrip("-")] for c in cl)
    P = base.merge(RY[["year", "fbd_region", "_c"]], on=["year", "fbd_region"], how="left", validate="one_to_one").rename(columns={"_c": "cases"}); assert P.cases.notna().all() and (P.cases >= 0).all(), T
    E = np.zeros(len(P)); off = np.zeros(len(P))
    for s in SEXES:
        X = P[["year", "key"]].merge(POP[POP.sex == s], on=["year", "key"], how="left", validate="one_to_one"); assert X[BANDS18].notna().all().all()
        E += (X[BANDS18].values * rate.xs(s, level="sex").loc[X.year.values].values).sum(1); off += X[BANDS18].values.sum(1)
    P["offset"] = off; P["E_std"] = E * P.year.map(P.groupby("year").cases.sum()) / pd.Series(E).groupby(P.year.values).transform("sum").values
    P["E_crude"] = P.offset * P.year.map(P.groupby("year").cases.sum() / P.groupby("year").offset.sum())
    NT = N[N.age == "계"].groupby(["cause", "year"]).value.sum()
    nat = sum(NT.loc[c] for c in plus) - (sum(NT.loc[c] for c in minus) if minus else 0)
    print(f"[99R5b-mortE] {T}: 시군구 합/전국 사망 {(P.groupby('year').cases.sum()/nat).round(3).min()}~{(P.groupby('year').cases.sum()/nat).round(3).max()}, 합 {int(P.cases.sum()):,}, 0칸 {(P.cases==0).sum()}")
    out[T] = P
for T, P in out.items():
    P[["year", "fbd_region", "offset", "cases", "E_std", "E_crude"]].to_csv(os.path.join(PAN, f"{T}_Estd3r.csv"), index=False, encoding="utf-8-sig")
