#!/bin/bash
: "${LAB_ROOT:?LAB_ROOT에 실험 상태를 둘 폴더를 정한다}"
iso=$1; seconds=${2:-165}
cd "$LAB_ROOT" || exit 2
deadline=$(( $(date +%s) + seconds ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  if "$iso" claude auth status 2>/dev/null | grep -q '"loggedIn": true'; then echo "logged in $(date +%H:%M:%S)"; exit 0; fi
  sleep 10
done
echo "아직 $(date +%H:%M:%S)"; exit 1
