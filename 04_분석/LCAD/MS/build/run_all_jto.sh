#!/bin/bash
# run_all_jto.sh: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
set -e; cd "$(dirname "$0")"
[ -n "$REFS" ] && python3 build_refs_lcad.py || true
python3 figs_lcad.py 2>&1 | grep -v Warning
python3 build_jto_lcad.py
python3 esm_lcad.py
python3 cover_jto_lcad.py ${COVER_DRAFT:+--draft}
python3 sanitize_docx.py --no-anon ../out/Manuscript_JTO_LCAD.docx ../out/Supplemental_Data_1.docx ../out/Cover_Letter_JTO_LCAD.docx
for f in ../out/Supplemental_Data_1.docx ../out/Manuscript_JTO_LCAD.docx ../out/Cover_Letter_JTO_LCAD.docx; do /opt/homebrew/bin/soffice --headless -env:UserInstallation=file:///tmp/lo_lcad_pdf --convert-to pdf --outdir ../out "$f" >/dev/null 2>&1; done
python3 check_jto_lcad.py
