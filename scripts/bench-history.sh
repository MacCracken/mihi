#!/usr/bin/env bash
set -euo pipefail

# Build + run every benches/*.bcyr, parse the cyrius stdlib's
# bench_report output (group/name: <avg><unit> avg (min=… max=…)
# [N iters]), append per-bench rows to docs/benchmarks/history.csv,
# and regenerate docs/benchmarks/results.md with the 3 most recent
# runs side-by-side.
#
# Three-tier convention matches the yukti sibling:
#   1. benches/*.bcyr       — bench definitions in Cyrius
#   2. docs/benchmarks/history.csv  — full append-only history
#   3. docs/benchmarks/results.md   — auto-regenerated 3-run summary
#
# Usage:
#   ./scripts/bench-history.sh                              # default paths
#   ./scripts/bench-history.sh path/to/history.csv          # custom CSV

HISTORY_FILE="${1:-docs/benchmarks/history.csv}"
RESULTS_MD="docs/benchmarks/results.md"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
CYRIUS_VER=$(cyrius --version 2>/dev/null || echo unknown)

mkdir -p "$(dirname "$HISTORY_FILE")"
if [ ! -f "$HISTORY_FILE" ]; then
    echo "timestamp,commit,branch,benchmark,avg_ns,min_ns,max_ns,iters" > "$HISTORY_FILE"
fi

echo "┌─────────────────────────────────────────────┐"
echo "│  mihi benchmark suite (cyrius)              │"
echo "├─────────────────────────────────────────────┤"
echo "│  commit : $COMMIT"
echo "│  branch : $BRANCH"
echo "│  cyrius : $CYRIUS_VER"
echo "│  date   : $TIMESTAMP"
echo "└─────────────────────────────────────────────┘"
echo ""

# unit_to_ns "<value><unit>" → integer nanoseconds
# Handles: "48ns", "2us", "1.263ms", "1.005s"
unit_to_ns() {
    local raw="$1"
    awk -v v="$raw" 'BEGIN {
        if (match(v, /^([0-9.]+)(ns|us|ms|s)$/, m)) {
            n = m[1] + 0
            if      (m[2] == "ns") printf "%.0f", n
            else if (m[2] == "us") printf "%.0f", n * 1000
            else if (m[2] == "ms") printf "%.0f", n * 1000000
            else if (m[2] == "s")  printf "%.0f", n * 1000000000
        } else { print "0" }
    }'
}

declare -a BENCH_NAMES=()
declare -a BENCH_AVG=()
declare -a BENCH_DISPLAY=()

for f in benches/*.bcyr; do
    name=$(basename "$f" .bcyr)
    echo "--- Building $name ---"
    mkdir -p build
    cyrius build "$f" "build/bench_${name}" >/dev/null 2>&1
    echo "--- Running $name ---"
    raw=$("build/bench_${name}" 2>&1)
    echo "$raw"
    echo ""

    while IFS= read -r line; do
        # Line shape: "  group/bench: <avg><unit> avg (min=<min><unit> max=<max><unit>) [<iters> iters]"
        if [[ "$line" =~ ^[[:space:]]+([a-zA-Z0-9_/]+):[[:space:]]+([0-9.]+(ns|us|ms|s))[[:space:]]+avg[[:space:]]+\(min=([0-9.]+(ns|us|ms|s))[[:space:]]+max=([0-9.]+(ns|us|ms|s))\)[[:space:]]+\[([0-9]+)[[:space:]]+iters\] ]]; then
            bname="${BASH_REMATCH[1]}"
            avg_raw="${BASH_REMATCH[2]}"
            min_raw="${BASH_REMATCH[4]}"
            max_raw="${BASH_REMATCH[6]}"
            iters="${BASH_REMATCH[8]}"
            avg_ns=$(unit_to_ns "$avg_raw")
            min_ns=$(unit_to_ns "$min_raw")
            max_ns=$(unit_to_ns "$max_raw")
            BENCH_NAMES+=("$bname")
            BENCH_AVG+=("$avg_ns")
            BENCH_DISPLAY+=("$avg_raw")
            echo "${TIMESTAMP},${COMMIT},${BRANCH},${bname},${avg_ns},${min_ns},${max_ns},${iters}" >> "$HISTORY_FILE"
        fi
    done <<< "$raw"
done

TOTAL=${#BENCH_NAMES[@]}

if [ "$TOTAL" -eq 0 ]; then
    echo "ERROR: no benchmark lines parsed. Check bench_report format." >&2
    exit 1
fi

echo ""
echo "┌──────────────────────────────────────────────────────────────┐"
echo "│  Results — this run                                          │"
echo "├────────────────────────────────────────────┬─────────────────┤"
printf "│ %-42s │ %15s │\n" "Benchmark" "Avg"
echo "├────────────────────────────────────────────┼─────────────────┤"

CURRENT_GROUP=""
for i in $(seq 0 $((TOTAL - 1))); do
    NAME="${BENCH_NAMES[$i]}"
    DISPLAY="${BENCH_DISPLAY[$i]}"
    GROUP="${NAME%%/*}"
    if [ "$GROUP" != "$CURRENT_GROUP" ]; then
        if [ -n "$CURRENT_GROUP" ]; then
            echo "├────────────────────────────────────────────┼─────────────────┤"
        fi
        CURRENT_GROUP="$GROUP"
    fi
    printf "│ %-42s │ %15s │\n" "$NAME" "$DISPLAY"
done
echo "└────────────────────────────────────────────┴─────────────────┘"
echo ""
echo "Appended ${TOTAL} rows to ${HISTORY_FILE}"

# ── Regenerate docs/benchmarks/results.md (3 most recent runs) ────────

mapfile -t RUNS < <(awk -F, 'NR>1 {print $1","$2}' "$HISTORY_FILE" | sort -u | tail -3)
NUM_RUNS=${#RUNS[@]}

declare -a RUN_TS=()
declare -a RUN_COMMIT=()
for run in "${RUNS[@]}"; do
    RUN_TS+=("${run%%,*}")
    RUN_COMMIT+=("${run#*,}")
done

lookup_ns() {
    local commit="$1" bench="$2"
    awk -F, -v c="$commit" -v b="$bench" '$2 == c && $4 == b {print $5}' "$HISTORY_FILE" | tail -1
}

format_ns() {
    local ns="$1"
    if [ -z "$ns" ]; then echo "—"; return; fi
    awk -v v="$ns" 'BEGIN {
        if (v < 1000)               printf "%d ns", v
        else if (v < 1000000)        printf "%.2f µs", v / 1000
        else if (v < 1000000000)     printf "%.2f ms", v / 1000000
        else                          printf "%.2f s", v / 1000000000
    }'
}

{
    echo "# mihi benchmarks"
    echo ""
    echo "> Auto-regenerated by [\`scripts/bench-history.sh\`](../../scripts/bench-history.sh) — do not edit manually."
    echo "> Full history in [\`history.csv\`](history.csv)."
    echo ""
    echo "## Run History"
    echo ""
    printf "| | "
    for i in $(seq 0 $((NUM_RUNS - 1))); do printf "Run %d | " "$((i + 1))"; done
    echo ""
    printf "|---|"
    for _ in $(seq 1 "$NUM_RUNS"); do printf -- "---|"; done
    echo ""
    printf "| **Date** | "
    for i in $(seq 0 $((NUM_RUNS - 1))); do printf "\`%s\` | " "${RUN_TS[$i]}"; done
    echo ""
    printf "| **Commit** | "
    for i in $(seq 0 $((NUM_RUNS - 1))); do printf "\`%s\` | " "${RUN_COMMIT[$i]}"; done
    echo ""
    echo ""
    echo "## Results"
    echo ""

    CURRENT_GROUP=""
    for i in $(seq 0 $((TOTAL - 1))); do
        NAME="${BENCH_NAMES[$i]}"
        GROUP="${NAME%%/*}"
        BENCH="${NAME#*/}"

        if [ "$GROUP" != "$CURRENT_GROUP" ]; then
            if [ -n "$CURRENT_GROUP" ]; then echo ""; fi
            echo "### ${GROUP}"
            echo ""
            printf "| Benchmark |"
            for r in $(seq 0 $((NUM_RUNS - 1))); do printf " \`%s\` |" "${RUN_COMMIT[$r]}"; done
            echo " Δ first→last |"
            printf "|-----------|"
            for _ in $(seq 1 "$NUM_RUNS"); do printf -- "------|"; done
            echo "------|"
            CURRENT_GROUP="$GROUP"
        fi

        printf "| %s |" "$BENCH"
        FIRST_NS=""
        LAST_NS=""
        for r in $(seq 0 $((NUM_RUNS - 1))); do
            VAL=$(lookup_ns "${RUN_COMMIT[$r]}" "$NAME")
            FORMATTED=$(format_ns "$VAL")
            printf " %s |" "$FORMATTED"
            if [ -n "$VAL" ]; then
                [ -z "$FIRST_NS" ] && FIRST_NS="$VAL"
                LAST_NS="$VAL"
            fi
        done
        if [ -n "$FIRST_NS" ] && [ -n "$LAST_NS" ] && [ "$FIRST_NS" != "$LAST_NS" ] && [ "$FIRST_NS" != "0" ]; then
            DELTA=$(awk -v f="$FIRST_NS" -v l="$LAST_NS" 'BEGIN { printf "%+.1f%%", (l - f) / f * 100 }')
        else
            DELTA="—"
        fi
        printf " %s |" "$DELTA"
        echo ""
    done

    echo ""
    echo "---"
    echo ""
    echo "Run: \`./scripts/bench-history.sh\` — appends to history, regenerates this file."
} > "$RESULTS_MD"

echo "Regenerated ${RESULTS_MD}"
