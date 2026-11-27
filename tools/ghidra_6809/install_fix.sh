#!/bin/sh
# Apply (or revert) the 6809 fix to a Ghidra install, then rebuild 6809.sla.
# usage: install_fix.sh GHIDRA_DIR [full|sleigh|revert]
#   full   (default) 6x09_pull.sinc (PULS/PULU ...PC = return) + 6809.cspec (A,B parameters replaced by D)
#   sleigh           only the PULS/PULU fix, calling convention untouched (fewer changes in already-working output)
#   revert           restore the files saved as *.before_fix
# Spec files are those of Ghidra 11.2.1 (spec/*.ghidra_11.2.1 = the originals for diffing).
set -e
G=${1:?GHIDRA_DIR}; MODE=${2:-full}
L=$G/Ghidra/Processors/MC6800/data/languages; H=$(cd "$(dirname "$0")" && pwd)/spec
[ -d "$L" ] || { echo "no 6809 language dir in $G" >&2; exit 1; }
grep -q 'application.version=11\.2\.1' "$G/Ghidra/application.properties" 2>/dev/null || echo "warning: tested on Ghidra 11.2.1 only" >&2
save() { [ -f "$1.before_fix" ] || cp "$1" "$1.before_fix"; }
case $MODE in
  revert) for f in 6x09_pull.sinc 6809.cspec; do [ -f "$L/$f.before_fix" ] && cp "$L/$f.before_fix" "$L/$f"; done ;;
  sleigh) save "$L/6x09_pull.sinc"; cp "$H/6x09_pull.sinc" "$L/"; [ -f "$L/6809.cspec.before_fix" ] && cp "$L/6809.cspec.before_fix" "$L/6809.cspec" ;;
  full)   save "$L/6x09_pull.sinc"; save "$L/6809.cspec"; cp "$H/6x09_pull.sinc" "$H/6809.cspec" "$L/" ;;
  *) echo "mode: full|sleigh|revert" >&2; exit 1 ;;
esac
"$G/support/sleigh" "$L/6809.slaspec" >/dev/null 2>&1
echo "6809 spec: $MODE applied, 6809.sla rebuilt in $L"
