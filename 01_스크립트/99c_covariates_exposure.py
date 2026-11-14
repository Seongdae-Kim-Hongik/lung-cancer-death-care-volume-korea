# 99c_covariates_exposure.py: builds district-year covariates used in the lung cancer deaths analysis (see README).
#!/usr/bin/env python3
import os, json, unicodedata
import pandas as pd, numpy as np
NFC = lambda s: unicodedata.normalize("NFC", str(s))
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
RAW = os.path.join(ROOT, "00_원천", "G_석탄발전_LCA")
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
assert (C.factory_land_area == C.factory_land).all()
out = pd.DataFrame({"year": C.year, "sigungu_cd": C.sigungu_cd, "fbd_region": C.region.map(NFC), "factory_land_share": C.factory_land_area})
out = out[(out.year >= 2011) & (out.year <= 2024)].copy()

rows = []
for y in range(2015, 2025):
    for r in json.load(open(os.path.join(RAW, f"DT_1JC1503_{y}.json"), encoding="utf-8")):
        cd = r["C1"]
        if len(cd) == 5 and cd[2:] not in ("003", "004", "005"): rows.append((y, cd, r["ITM_ID"], float(r["DT"])))
H = pd.DataFrame(rows, columns=["year", "cd", "itm", "v"]).pivot_table(index=["year", "cd"], columns="itm", values="v").reset_index()
def census_code(cd, y):
    codes = set(H[H.year == y].cd)
    cand = [cd]
    if cd[2] in "34": cand.append(cd[:2] + str(int(cd[2]) + 2) + cd[3:])
    if cd == "23030": cand.append("23090")
    if cd == "37310": cand += ["22520"]
    if cd == "33010": cand += ["33040"]
    for c in cand:
        if c in codes: return c
    return None
hh = []
for y in range(2015, 2025):
    Hy = H[H.year == y].set_index("cd")
    for cd in K.sigungu_cd:
        c = census_code(cd, y)
        if c is None:
            kids = [k for k in Hy.index if k[:4] == cd[:4] and k != cd and k[4] != "0"]
            assert kids, (y, cd)
            t00, t101 = Hy.loc[kids, "T00"].sum(), Hy.loc[kids, "T101"].sum()
        else:
            t00, t101 = Hy.loc[c, "T00"], Hy.loc[c, "T101"]
        hh.append((y, cd, 100 * t101 / t00))
HH = pd.DataFrame(hh, columns=["year", "sigungu_cd", "detached"])
assert HH.groupby("sigungu_cd").year.nunique().eq(10).all() and HH.detached.between(1, 100).all()
ti = HH.groupby("sigungu_cd").detached.mean().rename("detached_hh_share")
out = out.merge(ti, left_on="sigungu_cd", right_index=True, how="left", validate="many_to_one"); assert out.detached_hh_share.notna().all()

G = pd.DataFrame(json.load(open(os.path.join(RAW, "TX_38803_A004_raw.json"), encoding="utf-8")))
G = G[(G.ITM_NM == "용량합계") & (G.C1.str.startswith("15388AE1ABAAAC") | G.C1.str.startswith("15388AE1ABAAAD")) & (G.C1.str.len() > 14)].copy()  # 기력 무연탄(AC)·유연탄(AD) 아래 발전기
G["kw"] = pd.to_numeric(G.DT.replace("-", np.nan), errors="coerce").fillna(0); G["year"] = G.PRD_DE.astype(int)
PLANT2CD = {"영동": "32030", "강릉안인": "32030", "서천": "34340", "신서천": "34340", "동해": "32040", "북평": "32040", "호남": "36020", "여수": "36020",
            "삼천포": "38340", "고성": "38340", "보령": "34030", "신보령": "34030", "태안": "34380", "하동": "38360", "당진": "34080", "영흥": "23320",
            "삼척그린": "32070", "삼척화력": "32070"}
def plant_cd(nm):
    for k in sorted(PLANT2CD, key=len, reverse=True):
        if nm.startswith(k): return PLANT2CD[k]
    raise KeyError(nm)
G["sigungu_cd"] = G.C1_NM.map(plant_cd)
print("[99c-cov-exp] 석탄 발전기:", sorted(G.C1_NM.unique()))
cap = G[G.year.between(2011, 2024)].groupby(["sigungu_cd", "year"]).kw.sum().div(1e6).rename("coal_gw").reset_index()
out = out.merge(cap, on=["sigungu_cd", "year"], how="left"); out["coal_gw"] = out.coal_gw.fillna(0.0)
host = set(cap[cap.coal_gw > 0].sigungu_cd); out["coal_host"] = out.sigungu_cd.isin(host).astype(float)
print("[99c-cov-exp] 석탄 소재 시군구:", sorted(K[K.sigungu_cd.isin(host)].region))
P = pd.read_csv(os.path.join(ROOT, "04_분석", "TREATED", "panel_LCA.csv"), encoding="utf-8-sig", usecols=["year", "fbd_region"]); P["fbd_region"] = P.fbd_region.map(NFC)
assert set(P.fbd_region) == set(out.fbd_region), "체육 패널 지역과 불일치"
import geopandas as gpd  # 81·88k와 같은 final.shp 레코드 순서 = 그래프 노드 순서
SHP = os.environ.get("ST_SHP", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/final.shp"))
REG = [NFC(r) for r in gpd.read_file(SHP).region]; assert set(REG) == set(P.fbd_region) and len(REG) == 229
GR = os.environ.get("ST_GRAPH", os.path.join(ROOT, "04_분석", "CRC", "graph_593.graph"))
lines = open(GR).read().split("\n"); n = int(lines[0]); assert n == 229 == len(REG)
nbr = {}
for ln in lines[1:n + 1]:
    t = list(map(int, ln.split())); nbr[t[0]] = t[2:2 + t[1]]
cd_of = dict(zip(out.fbd_region, out.sigungu_cd)); idx_of = {cd_of[r]: i + 1 for i, r in enumerate(REG)}; cd_at = {v: k for k, v in idx_of.items()}
near = set(host)
for h in host: near |= {cd_at[j] for j in nbr[idx_of[h]]}
out["coal_near"] = out.sigungu_cd.isin(near).astype(float)
print("[99c-cov-exp] 소재+이웃 시군구 수:", len(near))
out = out.drop(columns=["sigungu_cd"])
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any() and out.notna().all().all()
fp = os.path.join(ROOT, "02_패널", "EXT_covariates_exposure.csv"); out.to_csv(fp, index=False, encoding="utf-8-sig")
print(f"[99c-cov-exp] 저장 {fp} {out.shape}; 단독주택 가구 비율 {out.detached_hh_share.describe()[['min','50%','max']].round(1).to_dict()}")
