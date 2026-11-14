#!/usr/bin/env python3
# 99E — LCAD 주 offset(2026-11-12): '진료 대비 사망' 기대 수. E_mtr = E_sexage(성×18연령 사망 E) × sir_treat(폐암 진료 연령표준화비, 같은 지역·연도)
#  → 연도별 ΣE = Σ사망 재척도(80이 다시 함). RR>1 = 그 지역의 연령·성 구조와 진료 인원으로 기대되는 것보다 사망이 많음.
#  민감도 열: E_mtr_ma3(진료 SIR 3년 이동평균), E_mtr_c10(10구간 연령 E × sir_treat, s8), E_sexage(진료 보정 없는 사망 SMR, 'smr'), E_std2.
import os, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); PAN = os.path.join(os.path.dirname(HERE), "02_패널")
rd = lambda f: (lambda d: d.assign(fbd_region=d.fbd_region.map(NFC)))(pd.read_csv(os.path.join(PAN, f), encoding="utf-8-sig"))
S = rd("LCAD_Esex.csv"); A = rd("LCAD_Estd2.csv")[["year", "fbd_region", "E_std_c10"]]; X = rd("EXT_canonical_pool_LCAD_261112.csv")[["year", "fbd_region", "sir_treat", "sir_treat_ma3", "lcad_deaths"]]
D = S.merge(A, on=["year", "fbd_region"], validate="one_to_one").merge(X, on=["year", "fbd_region"], validate="one_to_one"); assert len(D) == 3206
D["cases"] = D.lcad_deaths; assert np.allclose(D.groupby("year").E_sexage.sum(), D.groupby("year").cases.sum()), "E_sexage 연도 합 ≠ 사망 합"
rs = lambda v: v * D.groupby("year").cases.transform("sum") / v.groupby(D.year).transform("sum")
D["E_mtr"] = rs(D.E_sexage * D.sir_treat); D["E_mtr_ma3"] = rs(D.E_sexage * D.sir_treat_ma3); D["E_mtr_c10"] = rs(D.E_std_c10 * D.sir_treat)
r = D.cases.sum() / D.E_mtr.sum(); assert abs(r - 1) < 1e-9
print("[99E] E_mtr/E_sexage:", (D.E_mtr / D.E_sexage).describe()[["min", "50%", "max"]].round(3).to_dict())
D[["year", "fbd_region", "E_mtr", "E_mtr_ma3", "E_mtr_c10", "E_sexage", "E_std2", "pop80_share_raw"]].sort_values(["year", "fbd_region"]).to_csv(os.path.join(PAN, "LCAD_Emtr.csv"), index=False, encoding="utf-8-sig")
print("[99E] 저장 02_패널/LCAD_Emtr.csv")
