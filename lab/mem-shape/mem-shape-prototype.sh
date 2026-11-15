#!/usr/bin/env bash
set -euo pipefail

lab=${1:?"쓸 폴더 경로를 준다. 이미 있는 폴더면 멈춘다"}
mkdir "$lab"

use_candidate_one_root() {
  candidate="후보 1: 뿌리 하나 안에서 layer tree와 도구 파일이 나란히 놓인다"
  home="$lab/1-one-root/home"
  global="$home/.mem/layers"
  log="$home/.mem/log.md"
  retired="$home/.mem/retired"
  machine_values="$home/.config/mem-hook/contexts"
  moved_to_other_machine="$home/.mem"
}

use_candidate_tool_files_outside() {
  candidate="후보 2: 뿌리가 전역이고 도구 파일은 전부 뿌리 밖에 놓인다"
  home="$lab/2-tool-files-outside/home"
  global="$home/.mem"
  log="$home/.mem-hook/log.md"
  retired="$home/.mem-hook/retired"
  machine_values="$home/.mem-hook/contexts"
  moved_to_other_machine="$home/.mem"
}

use_candidate_reserved_name() {
  candidate="후보 3: 뿌리가 전역이고 도구 파일은 뿌리 안 예약한 이름 아래에 놓인다"
  home="$lab/3-reserved-name/home"
  global="$home/.mem"
  log="$home/.mem/.hook/log.md"
  retired="$home/.mem/.hook/retired"
  machine_values="$home/.config/mem-hook/contexts"
  moved_to_other_machine="$home/.mem"
}

layers_from_global_to() {
  local target=$1 path_so_far="" segment
  local -a segments
  echo "."
  [ "$target" = "." ] && return
  IFS=/ read -ra segments <<< "$target"
  for segment in "${segments[@]}"; do
    path_so_far="${path_so_far:+$path_so_far/}$segment"
    echo "$path_so_far"
  done
}

files_directly_in() {
  ls -A -p "$1" | grep -v '/$' || true
}

folders_directly_in() {
  ls -A -p "$1" | grep '/$' | sed 's|/$||' || true
}

show_session() {
  local target=$1 shown_target=$1 layer file
  local -a loaded=()
  [ "$target" = "." ] && shown_target="전역"
  while read -r layer; do
    while read -r file; do
      loaded+=("$layer/$file")
    done < <(files_directly_in "$global/$layer")
  done < <(layers_from_global_to "$target")
  printf '    target layer가 %s 인 세션:' "$shown_target"
  printf ' %s' "${loaded[@]#./}"
  echo
}

show_files_as_home() {
  sort | sed "s|^$1|    ~|"
}

show_state() {
  local target
  echo "  파일:"
  find "$home" -type f | show_files_as_home "$home"
  echo "  세션이 받는 것(전역부터 target layer까지 layer마다 ls):"
  for target in "$@"; do
    show_session "$target"
  done
}

stage_load() {
  mkdir -p "$global/work/api" "$global/work/web" "$(dirname "$machine_values")"
  echo "어디서나 맞는 사실" > "$global/a.md"
  echo "work 전체에 맞는 사실" > "$global/work/b.md"
  echo "api에 맞는 decision" > "$global/work/api/c.md"
  echo "web에 맞는 사실" > "$global/work/web/d.md"
  echo "이 기기에서 work 저장소들이 놓인 절대 경로 → work" > "$machine_values"
}

stage_save() {
  echo "에이전트가 save한 사실" > "$global/work/api/e.md"
  mkdir -p "$(dirname "$log")"
  echo "save work/api/e.md" >> "$log"
}

stage_decision() {
  mkdir -p "$retired/work/api"
  mv "$global/work/api/c.md" "$retired/work/api/c.md"
  echo "c.md를 대체한 decision" > "$global/work/api/c2.md"
  echo "retire work/api/c.md" >> "$log"
}

stage_split() {
  mkdir "$global/work/api/billing"
  mv "$global/work/api/e.md" "$global/work/api/billing/e.md"
  echo "move work/api/e.md work/api/billing/e.md" >> "$log"
}

check_tool_names_among_layers() {
  local folder
  echo "  전역 바로 아래 폴더:" $(folders_directly_in "$global")
  echo "  그 폴더마다 target layer로 삼은 세션:"
  while read -r folder; do
    show_session "$folder"
  done < <(folders_directly_in "$global")
}

check_move_to_other_machine() {
  local other_home
  other_home="$(dirname "$home")/other-machine-home"
  mkdir "$other_home"
  cp -r "$moved_to_other_machine" "$other_home/"
  echo "  다른 기기에 놓인 것:"
  find "$other_home" -type f | show_files_as_home "$other_home"
  echo "  이 기기에만 남은 것:"
  find "$home" -type f | grep -v "^$moved_to_other_machine/" | show_files_as_home "$home"
}

check_files_that_are_not_items() {
  echo "*.swp" > "$moved_to_other_machine/.gitignore"
  printf 'PNG' > "$global/work/api/diagram.png"
  show_state "." "work/api"
}

check_moved_folder_as_git_repository() {
  git init -q "$moved_to_other_machine"
  echo "  전역 바로 아래 폴더:" $(folders_directly_in "$global")
  show_session "."
}

walk() {
  echo
  echo "================================================================"
  echo "$candidate"
  echo "================================================================"
  mkdir -p "$home"

  echo "[1단계 load] 항목 넷과 맥락 규칙 파일을 둔다"
  stage_load
  show_state "." "work" "work/api"

  echo "[2단계 save] 에이전트가 work/api에 e.md를 save하고 hook이 log에 한 줄 덧붙인다"
  stage_save
  show_state "." "work" "work/api"

  echo "[3단계 decision] c.md를 c2.md가 대체하고, c.md는 load하지 않는 자리로 옮긴다"
  stage_decision
  show_state "." "work" "work/api"

  echo "[4단계 split] work/api 안에 billing layer를 두고 e.md를 옮긴다"
  stage_split
  show_state "." "work" "work/api" "work/api/billing"

  echo "[이름] 도구가 정한 이름이 layer 이름 자리에 끼어 있는가"
  check_tool_names_among_layers

  echo "[옮기기] 옮길 폴더 하나를 다른 기기에 복사한다"
  check_move_to_other_machine

  echo "[항목이 아닌 파일] 옮길 폴더의 뿌리에 .gitignore, work/api에 diagram.png가 놓인다"
  check_files_that_are_not_items

  echo "[옮기는 도구] 옮길 폴더를 git 저장소로 만든다"
  check_moved_folder_as_git_repository
}

use_candidate_one_root
walk
use_candidate_tool_files_outside
walk
use_candidate_reserved_name
walk
