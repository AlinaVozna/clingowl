#!/bin/sh
# DLVHEX benchmark runner. Mirrors examples/family/benchmark_family.py:
# starts Racer once (outside the timer, like the global reasoner there),
# generates HEX programs with 10/50/100/500 DL atoms, one warm-up run,
# then times each dlvhex2 execution. Prints CSV (mean, stdev).
#
# Usage: bench.sh <family|snomed> [repetitions]
set -u

ONTO="${1:-family}"
REPEATS="${2:-10}"

HERE=$(cd "$(dirname "$0")" && pwd)
PLUGINDIR=/usr/local/lib/dlvhex2/plugins
WORK=/tmp/dlvhex-bench
mkdir -p "$WORK"

# Racer takes a few seconds to open its socket, so poll the actual port
# instead of just checking the process
racer_ready() {
    python -c "import socket; socket.create_connection(('127.0.0.1',8088),1).close()" 2>/dev/null
}
if ! racer_ready; then
    nohup RacerPro > /tmp/racer.log 2>&1 &
    i=0
    while [ "$i" -lt 30 ] && ! racer_ready; do sleep 1; i=$((i+1)); done
fi
if ! racer_ready; then
    echo "ERROR: Racer did not start (see /tmp/racer.log)" >&2
    exit 1
fi

python "$HERE/generate_hex.py" "$ONTO" "$WORK" || exit 1

echo
echo "theory_atoms,total_mean_ms,total_stdev_ms,failures"
for N in 10 50 100 500; do
    F="$WORK/bench_${ONTO}_${N}.hex"
    dlvhex2 --plugindir="$PLUGINDIR" "$F" >/dev/null 2>&1   # warm-up
    TIMES=""; FAILS=0; i=0
    while [ "$i" -lt "$REPEATS" ]; do
        S=$(date +%s%N)
        dlvhex2 --plugindir="$PLUGINDIR" "$F" >/dev/null 2>&1 || FAILS=$((FAILS+1))
        E=$(date +%s%N)
        TIMES="$TIMES $(( (E-S)/1000000 ))"
        i=$((i+1))
    done
    echo "$N $FAILS $TIMES" | awk '{
        n=NF-2; s=0;
        for (i=3;i<=NF;i++) s+=$i; m=s/n;
        ss=0; for (i=3;i<=NF;i++) ss+=($i-m)^2;
        sd=(n>1)?sqrt(ss/(n-1)):0;
        printf "%d,%.1f,%.1f,%d\n", $1, m, sd, $2
    }'
done
