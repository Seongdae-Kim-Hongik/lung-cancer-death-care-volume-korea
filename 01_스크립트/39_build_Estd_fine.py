#!/usr/bin/env python3
# 39 — 세분 연령 구간 간접 연령표준화 기대건수 E_std2 (버전 std2, PLAYBOOK §3-B 7)
#  사용: python3 39_build_Estd_fine.py <TAG>      (MENTAL 부터; BRCA 는 여성 분모가 필요해 미지원)
#  왜: 37·38 의 E_std 는 10세 8구간(맨 위 70세 이상)이라 70+ 안의 초고령 구성 차이를 offset 이 못 거름 → 80+ 비율 추가 시 강건 8개 중 2개만 유지.
#  ① 연령 구간(전 기간 공통 최세분) AGES2 = 0-9, 10-19, 20-29, 30-39, 40-49, 50-59, 60-64, 65-69, 70-74, 75+
#     2011-17 KOSIS TX_35001_A061 의 구간(0세·1-9세·…·60-64·65-69·70-74·75세 이상)이 이것까지. 2018 DT_35001_A0611(5세) 와 2019-24 엑셀(17구간)도 맨 위가 75세 이상
#     → ★2018-24 도 전국 진료 원자료의 최상위 구간이 75+ 라 75-79·80-84·85+ 로 나눈 E_std2_85 는 만들 수 없음(아래 assert 로 확인·출력).
#  ② 전국 연령별 진료실인원: 38 의 kosis_codes·excel_codes 재사용(연령 매핑 함수만 m36.age10 ← fine_bin 으로 교체, 연령 합 = 총계 assert 유지)
#     코드: 04_분석/00_298코드_질환매핑.csv 의 포함 코드. MENTAL 은 112~119(전체), 113~119(비치매 민감도 E_std2_nondem)
#  ③ 시군구 연령별 인구: FBD_DATA_ZIP/<연도>.csv(주민등록, 행정구역별·5세·성별, cp949) '전체' 열 — 88b_mental_sens333_prep.py 매칭 규칙 그대로
#     (시도 머리행 문맥, 통합시는 시 합계행·하위 구 건너뜀, 청원군 → 청주시 합산, 군→시 승격 당진·여주, 세종 시도행=시군구행 중복 제거, 40_region_crosswalk.make_key)
#     75+ = 계 − Σ(0-4 … 70-74); 검증 75+ = Σ(75-79 … 100세 이상). 총인구 대조: FBD 계 / 패널 population 를 출력, |비−1| ≤ 1% assert(청주 2011-13 청원 포함 등 경계 사례 제외 없음 확인용)
#     분모 = 패널 offset × FBD 연령 비율(crude E 와 같은 총량 유지)
#  ④ rate[y,a] = 진료실인원 합 / Σ_d 분모[d,y,a] ; E_raw[d,y] = Σ_a 분모 × rate ; 연도별 Σ_d E = Σ_d cases 재척도
#  ⑤ 검증: 14년 통합 시군구 SIR 의 고령(65+)·80+·85+ 비율 Spearman — crude·std(02_패널/<TAG>_Estd.csv)·std2·std2_nondem 나란히
#  산출: 02_패널/<TAG>_Estd2.csv (year, fbd_region, E_std2[, E_std2_nondem], SIR_crude, SIR_std, SIR_std2, pop65/80/85_share_raw)
#        02_패널/<TAG>_national_agerates_std2.csv, 04_분석/<TAG>/results_std2/S00_Estd2_validation.csv   (기존 std 산출은 읽기만)
import os, sys, importlib.util, unicodedata
import numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m36 = _load("m36", "36_build_national_agerates.py"); m38 = _load("m38", "38_build_Estd_all.py"); cw = _load("cw", "40_region_crosswalk.py")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
TAG = sys.argv[1] if len(sys.argv) > 1 else "MENTAL"; assert TAG != "BRCA", "BRCA 는 여성 분모 필요 — 미지원"
ZIP = m38.FBDZIP
AGES2 = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-64", "65-69", "70-74", "75+"]
def fine_bin(lo):
    lo = int(lo)
    if lo < 60: return AGES2[lo // 10]
    if lo < 65: return "60-64"
    if lo < 70: return "65-69"
    if lo < 75: return "70-74"
    return "75+"
m36.age10 = fine_bin; m38.m36.age10 = fine_bin   # 38 의 kosis_codes·excel_codes 가 m36.age10 을 호출 → 세분 구간으로 매핑

# ── 코드 ──
M = pd.read_csv(os.path.join(ROOT, "04_분석", "00_298코드_질환매핑.csv"), encoding="utf-8-sig")
CODES = M[(M.TAG == TAG) & (M["포함"].astype(str) == "True")].code298.astype(int).tolist(); assert CODES, TAG
PROF = {"all": CODES}
if TAG == "MENTAL": assert CODES == list(range(112, 120)); PROF["nondem"] = list(range(113, 120))

# ── 전국 연령별 진료실인원 ──
ko, kdiff = m38.kosis_codes(CODES); ex = m38.excel_codes(CODES)
L = pd.DataFrame(ko + ex, columns=["year", "code", "age", "patients"]).groupby(["year", "code", "age"], as_index=False).patients.sum()
A = L[L.age != "TOTAL"]; T = L[L.age == "TOTAL"].set_index(["year", "code"]).patients
assert sorted(A.year.unique()) == list(range(2011, 2025))
for y in range(2011, 2025): assert set(A[A.year == y].age) == set(AGES2), (y, sorted(set(A[A.year == y].age)))
chk = A.groupby(["year", "code"]).patients.sum(); assert ((chk - T).abs() <= np.maximum(20, 1e-3 * T)).all()
print(f"[39] {TAG}: 코드 {CODES[0]}~{CODES[-1]} ({len(CODES)}개) · 14년 모두 세분 10구간 확보 · KOSIS 연령 합-총계 차이 {kdiff if kdiff else '없음'}")
print("[39] ★E_std2_85(75-79·80-84·85+) 불가: 2011-17 KOSIS 맨 위 '75세 이상', 2018 KOSIS 5세 표 맨 위 '75세이상', 2019-24 엑셀 17구간 맨 위 75(+) — 전국 진료 원자료에 75세 초과 구분 없음")

# ── 시군구 5세 인구(FBD_DATA_ZIP) — 88b prep 매칭 규칙 ──
PAN = os.path.join(ROOT, "04_분석", TAG, f"panel_{TAG}{os.environ.get('ST_E2_PANEL_SUF', '')}.csv")   # 2026-11-04: ST_E2_PANEL_SUF=_std3 → 인구 교정된 판의 패널 인구 사용
P = pd.read_csv(PAN, encoding="utf-8-sig"); P["key"] = P.key.map(NFC); P["fbd_region"] = P.fbd_region.map(NFC)
PKEYS = set(P.key)
SIDO_HDR = {k for k in cw.SIDO_STD if len(k) >= 3 and (k.endswith("시") or k.endswith("도"))}
FIVE = [f"{lo}-{lo+4}세" for lo in range(0, 75, 5)]; OLD = ["75-79세", "80-84세", "85-89세", "90-94세", "95-99세", "100세 이상"]
EXTRA = {("충청북도", "청원군"): "충청북도|청주시"}
rows = []
for y in range(2011, 2025):
    d = pd.read_csv(os.path.join(ZIP, f"{y}.csv"), encoding="cp949", dtype=str)
    d["행정구역별"] = d["행정구역별"].map(NFC).str.strip(); d["연령별"] = d["연령별"].map(NFC).str.strip()
    d["v"] = pd.to_numeric(d["전체"].str.replace(",", ""), errors="coerce")
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
        a = g.set_index("연령별")["v"]; tot = a.get("계", np.nan)
        if pd.isna(tot): continue
        f = a.reindex(FIVE); o = a.reindex(OLD); assert f.notna().all() and o.notna().all(), (y, nm)
        r = {"year": y, "src": f"{sido}/{nm}", "tot": tot}
        for lo in range(0, 60, 10): r[AGES2[lo // 10]] = f[f"{lo}-{lo+4}세"] + f[f"{lo+5}-{lo+9}세"]
        r["60-64"] = f["60-64세"]; r["65-69"] = f["65-69세"]; r["70-74"] = f["70-74세"]; r["75+"] = tot - f.sum()
        assert abs(r["75+"] - o.sum()) < 0.5, (y, nm, r["75+"], o.sum())
        r["p80"] = o.iloc[1:].sum(); r["p85"] = o.iloc[2:].sum(); r["p65"] = r["65-69"] + r["70-74"] + r["75+"]
        key = EXTRA.get((cw.sido_std(sido), sg), cw.make_key(sido, sg))
        if key not in PKEYS and key.endswith("군") and key[:-1] + "시" in PKEYS: key = key[:-1] + "시"
        r["key"] = NFC(key); rows.append(r)
R = pd.DataFrame(rows); NUM = ["tot"] + AGES2 + ["p80", "p85", "p65"]
G = R.groupby(["year", "key"], as_index=False).agg({**{c: "sum" for c in NUM}, "src": lambda s: ";".join(s)})
if "older_adult_share_raw" not in P:   # 2026-11-04: std3 판은 65+ 강제통제를 뺐으므로 검증용 65+ 비율을 v1 패널에서 가져옴
    _o = pd.read_csv(os.path.join(ROOT, "04_분석", TAG, f"panel_{TAG}.csv"), encoding="utf-8-sig", usecols=["year", "key", "older_adult_share_raw"]); _o["key"] = _o.key.map(NFC)
    P = P.merge(_o, on=["year", "key"], how="left", validate="one_to_one")
X = P[["year", "key", "fbd_region", "offset", "population", "cases", "E", "older_adult_share_raw"]].merge(G, on=["year", "key"], how="left", validate="one_to_one")
assert X.tot.notna().all(), X[X.tot.isna()][["year", "key"]].to_string()
X["pop_ratio"] = X.tot / X.population
print(f"[39] FBD_DATA_ZIP 매칭 {len(X)}행 / {X.key.nunique()} 시군구 · 총인구 비(FBD 계 / 패널 population):", X.pop_ratio.describe()[["min", "50%", "max"]].round(4).to_dict())
assert ((X.pop_ratio - 1).abs() <= 0.01).all(), X[(X.pop_ratio - 1).abs() > 0.01][["year", "key", "population", "tot"]].to_string()
assert (X[AGES2].sum(axis=1) - X.tot).abs().max() < 0.5
for c in ("p65", "p80", "p85"): X[c.replace("p", "pop") + "_share_raw"] = 100 * X[c] / X.tot
r65 = spearmanr(X.pop65_share_raw, X.older_adult_share_raw)[0]; print(f"[39] FBD 65+ 비율 vs 패널 older_adult_share_raw Spearman {r65:.4f}")

# ── rate·E ──
DEN = pd.DataFrame({a: X.offset * X[a] / X.tot for a in AGES2}); DEN["year"] = X.year.values
den_nat = DEN.groupby("year")[AGES2].sum().stack().rename("denom_nat"); den_nat.index.names = ["year", "age"]
RATES = []; OUT = X[["year", "fbd_region", "cases", "E", "older_adult_share_raw", "pop65_share_raw", "pop80_share_raw", "pop85_share_raw"]].copy()
for nm, cs in PROF.items():
    num = A[A.code.isin(cs)].groupby(["year", "age"]).patients.sum().rename("patients_sum")
    rt = pd.concat([num, den_nat], axis=1); rt["rate"] = rt.patients_sum / rt.denom_nat; rt["profile"] = nm; RATES.append(rt.reset_index())
    W = rt.rate.unstack()[AGES2]
    e = (DEN[AGES2].values * W.loc[X.year.values].values).sum(axis=1)
    col = "E_std2" if nm == "all" else f"E_std2_{nm}"
    OUT[col] = e * OUT.groupby("year").cases.transform("sum") / pd.Series(e, index=OUT.index).groupby(OUT.year).transform("sum")
    assert (OUT.groupby("year")[col].sum() - OUT.groupby("year").cases.sum()).abs().max() < 1e-6 * OUT.cases.sum()
OLDF = pd.read_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd.csv"), encoding="utf-8-sig"); OLDF["fbd_region"] = OLDF.fbd_region.map(NFC)
OUT = OUT.merge(OLDF[["year", "fbd_region", "E_std"] + (["E_std_nondem"] if "E_std_nondem" in OLDF else [])], on=["year", "fbd_region"], how="left", validate="one_to_one"); assert OUT.E_std.notna().all()
OUT["SIR_crude"] = OUT.cases / OUT.E; OUT["SIR_std"] = OUT.cases / OUT.E_std; OUT["SIR_std2"] = OUT.cases / OUT.E_std2
ecols = ["E_std2"] + [c for c in OUT if c.startswith("E_std2_")]
save = OUT[["year", "fbd_region"] + ecols + ["SIR_crude", "SIR_std", "SIR_std2", "pop65_share_raw", "pop80_share_raw", "pop85_share_raw"]].sort_values(["year", "fbd_region"])
save.to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd2.csv"), index=False, encoding="utf-8-sig")
RT = pd.concat(RATES); RT["age"] = pd.Categorical(RT.age, AGES2, ordered=True)
RT.sort_values(["profile", "year", "age"])[["profile", "year", "age", "patients_sum", "denom_nat", "rate"]].to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_national_agerates_std2.csv"), index=False, encoding="utf-8-sig")

# ── 검증 ──
Gs = OUT.groupby("fbd_region").agg(cases=("cases", "sum"), E=("E", "sum"), Es=("E_std", "sum"), Es2=("E_std2", "sum"), o65=("pop65_share_raw", "mean"), o80=("pop80_share_raw", "mean"), o85=("pop85_share_raw", "mean"), old=("older_adult_share_raw", "mean"),
                                    **({"Es2n": ("E_std2_nondem", "sum"), "Esn": ("E_std_nondem", "sum")} if "E_std2_nondem" in OUT and "E_std_nondem" in OUT else {}))
VAL = []
for nm, col in (("crude", "E"), ("std", "Es"), ("std_nondem", "Esn"), ("std2", "Es2"), ("std2_nondem", "Es2n")):
    if col not in Gs: continue
    sir = Gs.cases / Gs[col]
    VAL.append(dict(version=nm, rho_old_panel=spearmanr(sir, Gs.old)[0], rho_65=spearmanr(sir, Gs.o65)[0], rho_80=spearmanr(sir, Gs.o80)[0], rho_85=spearmanr(sir, Gs.o85)[0], SIR_P90_P10=sir.quantile(.9) / sir.quantile(.1)))
V = pd.DataFrame(VAL).round(3); os.makedirs(os.path.join(ROOT, "04_분석", TAG, "results_std2"), exist_ok=True)
V.to_csv(os.path.join(ROOT, "04_분석", TAG, "results_std2", "S00_Estd2_validation.csv"), index=False, encoding="utf-8-sig")
print("[39] 14년 통합 시군구 SIR – 고령 비율(14년 평균) Spearman:\n" + V.to_string(index=False))
yr = OUT.groupby("year").apply(lambda d: pd.Series({"std_80": spearmanr(d.SIR_std, d.pop80_share_raw)[0], "std2_80": spearmanr(d.SIR_std2, d.pop80_share_raw)[0]}))
print("[39] 연도별 SIR–80+ rho (std → std2):", " ".join(f"{y}:{a:+.2f}→{b:+.2f}" for y, (a, b) in yr.iterrows()))
print("[39] E_std2/E_std 분포:", (OUT.E_std2 / OUT.E_std).describe()[["min", "25%", "50%", "75%", "max"]].round(3).to_dict())
print(f"[39] 저장: 02_패널/{TAG}_Estd2.csv ({len(save)}행, 열 {ecols}) · 02_패널/{TAG}_national_agerates_std2.csv · results_std2/S00_Estd2_validation.csv")
print(RT[RT.profile == "all"].pivot(index="age", columns="year", values="rate").mul(1e3).round(1).to_string())
