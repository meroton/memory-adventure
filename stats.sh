#!/usr/bin/env bash

# TODO: extract memory limit from the profile itself,
# so it does not need to be sent out-of-band.

test $# -lt 1 && {
    echo >&2 "Usage: $0 <directory>"
    echo "Example: 250m"
    exit 1
}

set -eu

trap '{ echo >&2 $basename; }' ERR

dir=$1; shift
basename=$(basename "$dir" | sed 's|/$||')
mem=$(echo "$basename" | cut -d- -f1)
attempt=$(echo "$basename" | cut -d- -f2)

status=ok

grep -q "Build completed successfully" "$dir"/console || status=crash
# The more principled approach is below, though it does not work well for
# truncated profiles
#     acat "$dir"/profile.gz 2>/dev/null | jq '.' >/dev/null 2>&1 || status=crash

gc_count=$(acat "$dir"/profile.gz 2>/dev/null | grep -c GC)
timestamps="$(acat 2>/dev/null "$dir"/profile.gz \
    | awk -F, '/"ts":/ {
        for(i=0; i<NF; i++) {
            if($i ~ /^"ts":/) {
                print $i
            } } }
    ' | cut -d: -f2)"
# The more principled approach is below, though it does not work well for
# truncated profiles
#     timestamps=$(acat "$dir"/profile.gz | jq '.traceEvents[] | .ts' | sort -n)

first=$(echo "$timestamps" | head -1)
last=$(echo "$timestamps" | tail -1)
duration=$((last - first))

echo "$mem, $attempt, $gc_count, $duration, $status"
