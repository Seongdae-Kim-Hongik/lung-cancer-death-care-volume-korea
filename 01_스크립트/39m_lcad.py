#!/usr/bin/env python3
# 39m_lcad — 폐암 사망(LCAD, C33-C34) E(2026-11-12). 공유 원본 39m_build_Estd_mort.py 불변, 사인 표에 한 줄 더해 실행.
#  사용: ST_FBDZIP=<창원 교정 인구> ST_E2_PANEL_SUF=_std3 python3 39m_lcad.py
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "39m_build_Estd_mort.py"), encoding="utf-8").read()
a = 'TAG = sys.argv[1]; assert TAG in CAUSES, TAG; NC = CAUSES[TAG]'
assert src.count(a) == 1
src = src.replace(a, 'CAUSES["LCAD"] = "기관 기관지 및 폐의 악성신생물 (C33-C34)"\n' + a)
sys.argv = ["39m_build_Estd_mort.py", "LCAD"]
exec(compile(src, os.path.join(HERE, "39m_build_Estd_mort.py"), "exec"), {"__file__": os.path.join(HERE, "39m_build_Estd_mort.py"), "__name__": "__main__"})
