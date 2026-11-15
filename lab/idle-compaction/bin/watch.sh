#!/bin/bash
: "${LAB_ROOT:?LAB_ROOT에 실험 상태를 둘 폴더를 정한다}"
tm=$1; seconds=$2; shift 2
state() {
  local out=""
  for name in "$@"; do
    local hooks=$(wc -l <"$LAB_ROOT/out/$name/hook-input.jsonl" 2>/dev/null || echo 0)
    local sources=$(python3 -c "
import json,sys
print(','.join(json.loads(l)['input'].get('source','?') for l in open(sys.argv[1], encoding='utf-8')))" "$LAB_ROOT/out/$name/hook-input.jsonl" 2>/dev/null)
    local notice=$("$tm" cap "$name" 200 2>/dev/null | grep -c 'Compacted')
    local requests=$(grep -c '"type":"api-request"' "$(cat "$LAB_ROOT/out/$name/transcript")" 2>/dev/null)
    out="$out $name[hook=$hooks:$sources compacted줄=$notice 요청=$requests]"
  done
  echo "$out"
}
first=$(state "$@")
deadline=$(( $(date +%s) + seconds ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  now=$(state "$@")
  if [ "$now" != "$first" ]; then echo "바뀜 $(date +%H:%M:%S) uptime=$(cut -d' ' -f1 /proc/uptime):$now"; exit 0; fi
  sleep 10
done
echo "그대로 $(date +%H:%M:%S) wall=$(date +%s) uptime=$(cut -d' ' -f1 /proc/uptime):$first"
