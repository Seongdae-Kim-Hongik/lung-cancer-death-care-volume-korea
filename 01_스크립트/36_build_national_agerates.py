#!/usr/bin/env python3
# 36 — 전국 연령별 정신 및 행동장애(F00-F99) 진료실인원 → 연령별 전국 진료율 (간접 연령표준화용, PLAN R10)
#  출처: 건강보험통계 「298 질병분류별 연령별 급여현황(총계)」 — 298분류 112(치매)·113(알코올)·114(기타 정신활성물질)·115(조현병 등)·116(기분장애)
#        ·117(신경증·스트레스)·118(정신지연)·119(기타 정신 및 행동장애), 진료형태 '계'(입원+외래), 항목 '진료실인원'
#   2011~2017 KOSIS 350/TX_35001_A061(연령 12구간) · 2018 KOSIS 350/DT_35001_A0611(5세 구간) · 2019~2024 엑셀 00_원천/NHIS_전국_질병분류_연령/<연도>_298 질병분류.xlsx
#   엑셀 배치: 2019 = 시트 1개, 코드가 세로로 이어지고 연령 블록이 가로로(블록 사이 '구분 Division' 열 반복);
#             2020~2024 = 시트 90개(17열), 한 시트에 연령 블록 3개 → 같은 코드 구간이 6개 시트에 걸쳐 연령 블록 18개(총계+17 연령)로 반복
#             → 두 경우 모두 '행5가 진료실인원으로 시작하는 열'을 블록 시작으로 보고, 블록 5열의 행4 글자를 이어 붙여 연령 이름을 읽음
#  검증(assert): 2019 코드 104 계 = 3,224,207 · 112 = 553,461 · 116 = 962,882; 모든 연도·코드에서 연령 블록 합 = 총계
#  연령: 10세 8구간(0~9 … 60~69, 70세 이상)으로 통일 — 시군구 인구 ST_agepop 과 같은 구간
#  전국 인구: 패널 시군구(panel_MENTAL.csv)의 연령별 인구 합(ST_agepop 연령 비율 × 패널 인구; 누락 시군구-연도는 같은 시군구 가장 가까운 연도 비율)
#  산출: 02_패널/MENTAL_national_agerates.csv (+ 열 설명 MENTAL_national_agerates_변수설명.csv)
import os, re, sys, glob, unicodedata
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
NFC = lambda s: unicodedata.normalize("NFC", str(s))
AGEPOP = os.path.expandvars("$ST_DATA_ROOT") + "/G.Downloads/FBD_SpatioTemporal/data_cache/ST_agepop.csv"
AGES = ["0~9세", "10~19세", "20~29세", "30~39세", "40~49세", "50~59세", "60~69세", "70세 이상"]
CODES = list(range(112, 120)); CHECK = 104

def age10(lo):   # 구간 하한 → 10세 구간
    return AGES[min(int(lo) // 10, 7)]

def agepop_panel(panel_csv):
    """패널 시군구-연도별 10세 연령 인구 = 패널 population × ST_agepop 연령 비율(누락 시군구-연도는 같은 시군구의 가장 가까운 연도 비율). 반환 long + 대체 기록."""
    a = pd.read_csv(AGEPOP); a["region"] = a.region.map(NFC); a["age10"] = a.age10.map(NFC)
    assert set(a.age10) == set(AGES)
    a["share"] = a["pop"] / a.groupby(["region", "year"])["pop"].transform("sum")
    p = pd.read_csv(panel_csv, encoding="utf-8-sig", usecols=["year", "fbd_region", "population"]); p["fbd_region"] = p.fbd_region.map(NFC)
    W = a.pivot_table(index=["region", "year"], columns="age10", values="share")[AGES]
    rows, fb = [], []
    for (r, y), pop in p.set_index(["fbd_region", "year"]).population.items():
        if (r, y) in W.index: s = W.loc[(r, y)].values; src = y
        else:
            ys = W.loc[r].index.values if r in W.index.get_level_values(0) else None
            assert ys is not None, f"ST_agepop 에 시군구 없음: {r}"
            src = int(ys[np.argmin(np.abs(ys - y))]); s = W.loc[(r, src)].values; fb.append((r, y, src))
        rows += [(y, r, ag, pop * sh) for ag, sh in zip(AGES, s)]
    out = pd.DataFrame(rows, columns=["year", "fbd_region", "age10", "pop"])
    return out, fb

# ── KOSIS 2011~2018 ──
KDIFF = []
def kosis_part():
    import kosis_api as K
    items, objs = K.meta_codes("350", "TX_35001_A061"); dz = objs["15350AF5"]; codes = [dz[c] for c in CODES + [CHECK]]
    cmap = {dz[c]: c for c in CODES + [CHECK]}
    def get(tbl, y0, y1):
        p = {"method": "getList", "orgId": "350", "tblId": tbl, "itmId": "16350AAB1", "prdSe": "Y", "startPrdDe": str(y0), "endPrdDe": str(y1), "format": "json", "jsonVD": "Y",
             "objL1": "+".join(codes), "objL2": "15350AB300", "objL3": "ALL"}
        d = pd.DataFrame(K._get(K.BASE + "/Param/statisticsParameterData.do", p)); assert (d.ITM_ID == "16350AAB1").all() and (d.C2 == "15350AB300").all()
        d["code"] = d.C1.map(cmap); d["DT"] = pd.to_numeric(d.DT.replace("-", 0)); return d
    out = []
    for tbl, y0, y1 in (("TX_35001_A061", 2011, 2017), ("DT_35001_A0611", 2018, 2018)):
        d = get(tbl, y0, y1)
        assert sorted(d.PRD_DE.astype(int).unique()) == list(range(y0, y1 + 1)), (tbl, d.PRD_DE.unique())
        for (yr, code), g in d.groupby(["PRD_DE", "code"]):
            tot = g.loc[g.C3_NM.str.replace(" ", "").isin(["합계", "계"]), "DT"]; assert len(tot) == 1
            ag = g[~g.C3_NM.str.replace(" ", "").isin(["합계", "계"])]
            dif = ag.DT.sum() - tot.iloc[0]   # KOSIS 2011~18: 실인원 집계라 연령 합이 총계와 ±몇 명 다를 수 있음(예 2014 치매 +1) → 상대오차 1e-4 이내 허용·기록
            assert abs(dif) <= max(2, 1e-4 * tot.iloc[0]), f"KOSIS {tbl} {yr} {code}: 연령 합 {ag.DT.sum()} ≠ 총계 {tot.iloc[0]}"
            if dif: KDIFF.append((int(yr), code, int(dif)))
            for nm, v in zip(ag.C3_NM, ag.DT):
                lo = int(re.findall(r"\d+", nm)[0]); out.append((int(yr), code, age10(lo), float(v)))
            out.append((int(yr), code, "TOTAL", float(tot.iloc[0])))
        print(f"[36] KOSIS {tbl} {y0}-{y1}: {d.C3_NM.nunique()-1} 연령 구간 · 코드 {d.code.nunique()}개")
    return out

# ── 엑셀 2019~2024 ──
def _code(v):
    s = NFC(v).strip()
    if re.fullmatch(r"\d{1,3}(\.0)?", s): return int(float(s))
    return None
def _agelabel(cells):
    t = re.sub(r"\s+", "", "".join(NFC(c) for c in cells if pd.notna(c)))
    if t.startswith("총") or "G.T" in t or "Total" in t: return "TOTAL"
    n = re.findall(r"\d+", t); assert n, f"연령 이름 해석 실패: {t}"
    return int(n[0])
def excel_year(f):
    X = pd.read_excel(f, sheet_name=None, header=None); vals = {}; nblk = 0
    for sn, d in X.items():
        hdr5 = d.iloc[5].map(lambda v: NFC(v).replace("\n", "") if pd.notna(v) else "")
        pcols = [j for j, v in hdr5.items() if v.startswith("진료실인원")]
        assert pcols, f"{f} {sn}: 진료실인원 열 없음"
        labels = {j: _agelabel(d.iloc[4, j:j + 5].tolist()) for j in pcols}
        for i in range(6, len(d)):
            c = _code(d.iat[i, 0]); kind = NFC(d.iat[i, 1]).replace(" ", "").replace("　", "") if pd.notna(d.iat[i, 1]) else ""
            if c is None or not kind.startswith("계"): continue
            for j in pcols:
                k = (c, labels[j]); v = float(str(d.iat[i, j]).replace(",", "").replace("-", "0"))
                assert k not in vals or vals[k] == v, f"{f}: 중복 값 불일치 {k}"
                vals[k] = v
        nblk += len(pcols)
    return vals
def excel_part():
    out = []; D = os.path.join(ROOT, "00_원천", "NHIS_전국_질병분류_연령")
    for f in sorted(glob.glob(os.path.join(D, "*_298 질병분류.xlsx"))):
        yr = int(os.path.basename(f)[:4]); vals = excel_year(f)
        codes = sorted({c for c, _ in vals}); assert codes == list(range(1, 299)), f"{yr}: 코드 {len(codes)}개 ({codes[:3]}…{codes[-3:]})"
        ages = sorted({a for _, a in vals if a != "TOTAL"}); assert len(ages) == 17 and ages[0] == 0 and ages[-1] == 75, f"{yr}: 연령 {ages}"
        for c in codes:   # 모든 코드 연령 합 = 총계
            s = sum(vals[(c, a)] for a in ages); assert s == vals[(c, "TOTAL")], f"{yr} code {c}: 연령 합 {s} ≠ 총계 {vals[(c, 'TOTAL')]}"
        if yr == 2019:
            assert vals[(104, "TOTAL")] == 3224207 and vals[(112, "TOTAL")] == 553461 and vals[(116, "TOTAL")] == 962882, "2019 검증값 불일치"
            print(f"[36] 2019 검증 통과: 104={vals[(104,'TOTAL')]:,.0f} · 112={vals[(112,'TOTAL')]:,.0f} · 116={vals[(116,'TOTAL')]:,.0f}")
        for c in CODES + [CHECK]:
            for a in ages: out.append((yr, c, age10(a), vals[(c, a)]))
            out.append((yr, c, "TOTAL", vals[(c, "TOTAL")]))
        print(f"[36] {yr} 엑셀: 코드 298개 · 연령 17구간 · 연령 합=총계 298/298")
    return out

if __name__ == "__main__":
    L = pd.DataFrame(kosis_part() + excel_part(), columns=["year", "code", "age10", "patients"])
    L = L.groupby(["year", "code", "age10"], as_index=False).patients.sum()
    T = L[L.age10 == "TOTAL"].pivot(index="year", columns="code", values="patients")
    A = L[L.age10 != "TOTAL"]
    chk = A.groupby(["year", "code"]).patients.sum().unstack(); assert ((chk - T).abs() <= np.maximum(2, 1e-4 * T)).all().all(), "10세 통합 후 합 ≠ 총계"
    assert (chk.loc[2019:] == T.loc[2019:]).all().all(), "엑셀 연도 10세 통합 후 합 ≠ 총계"
    print(f"[36] KOSIS 연령 합-총계 차이(허용·기록): {KDIFF if KDIFF else '없음'}")
    assert sorted(A.year.unique()) == list(range(2011, 2025))
    W = A.pivot_table(index=["year", "age10"], columns="code", values="patients").reset_index()
    out = pd.DataFrame({"year": W.year, "age10": W.age10})
    out["patients_all"] = W[CODES].sum(axis=1); out["patients_dementia"] = W[112]; out["patients_nondementia"] = W[list(range(113, 120))].sum(axis=1)
    ap, fb = agepop_panel(os.path.join(ROOT, "04_분석", "MENTAL", "panel_MENTAL.csv"))
    pn = ap.groupby(["year", "age10"])["pop"].sum()
    out["pop_nat"] = [pn.loc[(y, a)] for y, a in zip(out.year, out.age10)]
    out["rate_all"] = out.patients_all / out.pop_nat; out["rate_nondem"] = out.patients_nondementia / out.pop_nat
    out["age10"] = pd.Categorical(out.age10, AGES, ordered=True); out = out.sort_values(["year", "age10"]).reset_index(drop=True)
    P = os.path.join(ROOT, "02_패널"); out.to_csv(os.path.join(P, "MENTAL_national_agerates.csv"), index=False, encoding="utf-8-sig")
    desc = pd.DataFrame([
        ("year", "연도(2011~2024)"), ("age10", "10세 연령 구간(ST_agepop 과 같은 8구간; 2011~17의 60-64+65-69→60~69, 70-74+75+→70세 이상)"),
        ("patients_all", "298분류 112~119 진료실인원 합(입원+외래 계). 한 사람이 둘 이상 분류로 진료받으면 중복 계산 → 실인원이 아니라 '연령 프로파일' 용도"),
        ("patients_dementia", "298분류 112(치매) 진료실인원"), ("patients_nondementia", "298분류 113~119 진료실인원 합(중복 계산 가능, 연령 프로파일 용도)"),
        ("pop_nat", "전국 연령별 인구 = 패널 시군구 연령별 인구 합(ST_agepop 연령 비율 × 패널 population)"),
        ("rate_all", "patients_all / pop_nat (간접 연령표준화 E_std 의 연령별 기준율, 중복 포함 프로파일)"), ("rate_nondem", "patients_nondementia / pop_nat (치매 제외 민감도 E_std_nondem 기준율)")], columns=["column", "description"])
    desc.to_csv(os.path.join(P, "MENTAL_national_agerates_변수설명.csv"), index=False, encoding="utf-8-sig")
    print(f"[36] 저장: 02_패널/MENTAL_national_agerates.csv ({len(out)}행) · 연령 비율 대체 시군구-연도 {len(fb)}건: {sorted(set((r, s) for r, _, s in fb))}")
    print("[36] 코드 104 총계:", T[CHECK].astype(int).to_dict()); print("[36] 코드 112 총계:", T[112].astype(int).to_dict())
    print(out.pivot(index="age10", columns="year", values="rate_all").mul(1e3).round(1).to_string())
