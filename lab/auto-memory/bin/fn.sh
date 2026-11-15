: "${LAB_ROOT:?LAB_ROOT에 실험 상태를 둘 폴더를 정한다}"
lab_bin=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

run() {
  local label=$1 dir=$2 prompt=$3
  shift 3
  LAB_CLIP=200 "$lab_bin/case" "$label" "$dir" "$prompt" "$@" >/dev/null
  echo "## $label"
  python3 "$lab_bin/calls.py" "$(sed -n 's/^exit=.* stream=//p' "$LAB_ROOT/out/$label/last-run.txt")"
  echo "   작업 폴더 변경: $(cd "$dir" && git status --porcelain 2>/dev/null | tr '\n' ' ')"
  (cd "$dir" && git checkout -q . 2>/dev/null && git clean -fdq 2>/dev/null)
}

memory_path() {
  local label=$1 dir=$2
  shift 2
  LAB_CLIP=200 "$lab_bin/case" "$label" "$dir" '한 줄로 인사해 줘.' --model haiku "$@" | grep '^memory_paths' | sed "s/^/$label: /"
}

reset_memory() {
  local memory_dir=$1 tag=$2
  mkdir -p "$memory_dir"
  find "$memory_dir" -mindepth 1 -delete
  "$lab_bin/memfix" "$memory_dir" "$tag" >/dev/null
}
