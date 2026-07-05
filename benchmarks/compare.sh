#!/bin/sh
# Runs the ClingOWL and DLVHEX benchmarks, each in its own container, on the
# same machine, and prints a combined table (plus each system's raw CSV).
#
# Usage, from the repository root:
#   sh benchmarks/compare.sh [family|snomed]
#
# Note: ClingOWL's benchmark reports phase times (parsing/translation/
# reasoning); DLVHEX does not expose comparable phases, so the combined table
# uses total wall-clock time. Currently the ClingOWL benchmark runs on the
# family ontology only, so the combined table is meaningful for `family`.
set -e

ONTO="${1:-family}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/.." && pwd)

echo "== Building images (cached after the first time) =="
docker build -q -t dlvhex250 "$HERE/dlvhex"
docker build -q -f "$HERE/clingowl/Dockerfile" -t clingowl-bench "$REPO"

echo
echo "== ClingOWL ($ONTO) =="
CW_OUT=$(docker run --rm clingowl-bench)
echo "$CW_OUT" | grep -E '^(theory_atoms|[0-9]+,)'

echo
echo "== DLVHEX ($ONTO) =="
DL_OUT=$(docker run --rm dlvhex250 bench "$ONTO")
echo "$DL_OUT" | grep -E '^(theory_atoms|[0-9]+,)'

echo
echo "== Combined (total wall-clock time per run, ms) =="
echo "theory_atoms,clingowl_mean_ms,clingowl_stdev_ms,dlvhex_mean_ms,dlvhex_stdev_ms"
CW_CSV=$(echo "$CW_OUT" | grep -E '^[0-9]+,')
DL_CSV=$(echo "$DL_OUT" | grep -E '^[0-9]+,')
for N in 10 50 100 500; do
    CW=$(echo "$CW_CSV" | awk -F, -v n="$N" '$1==n {printf "%s,%s", $8, $9}')
    DL=$(echo "$DL_CSV" | awk -F, -v n="$N" '$1==n {printf "%s,%s", $2, $3}')
    echo "$N,$CW,$DL"
done
