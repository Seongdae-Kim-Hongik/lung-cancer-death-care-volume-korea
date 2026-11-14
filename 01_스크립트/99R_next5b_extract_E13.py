#!/usr/bin/env python3
# 99R_next5b — 시군구 사망원인 50항목(KOSIS DT_1B34E13 원천 CSV) 2011-2024 사망자수(성 계)만 뽑는다(2026-11-12, 2차 후보 풀 = 기준 SQLite 17사인 밖 세부 사인 확인용).
#  원천 읽기 전용. 산출: 02_패널/DT_1B34E13_사인50_시군구_2011_2024.csv (C1 시군구 코드, C1_NM, C2 사인 코드, C2_NM, year, deaths)
import os, pyarrow.csv as pc, pyarrow.compute as pcm, pyarrow as pa
R = os.environ.get("ST_ROOT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")); f = f"{R}/00_원천/D_사망_인구_암/DT_1B34E13.csv"
cols = ["C1", "C1_NM", "C2", "C2_NM", "C3_NM", "ITM_ID", "PRD_DE", "DT"]
opt = pc.ConvertOptions(include_columns=cols, column_types={c: pa.string() for c in cols})
rd = pc.open_csv(f, convert_options=opt, read_options=pc.ReadOptions(block_size=1 << 26))
out = []
for b in rd:
    t = pa.Table.from_batches([b]); y = pcm.cast(t["PRD_DE"], pa.int32(), safe=False)
    m = pcm.and_(pcm.and_(pcm.equal(t["ITM_ID"], "T1"), pcm.equal(t["C3_NM"], "계")), pcm.and_(pcm.greater_equal(y, 2011), pcm.less_equal(y, 2024)))
    out.append(t.filter(m))
T = pa.concat_tables(out).to_pandas(); T["year"] = T.PRD_DE.astype(int); T["deaths"] = pd_num = __import__("pandas").to_numeric(T.DT, errors="coerce")
T[["C1", "C1_NM", "C2", "C2_NM", "year", "deaths"]].to_csv(f"{R}/02_패널/DT_1B34E13_사인50_시군구_2011_2024.csv", index=False, encoding="utf-8-sig")
print(len(T), T.C1.nunique(), T.C2.nunique(), T.year.min(), T.year.max())
print(T[["C2", "C2_NM"]].drop_duplicates().to_string())
