# hook과 권한 실험 도구

Claude Code의 `SessionStart` hook과 `~/.mem` 쓰기 권한이 실제로 어떻게 도는지를 격리 환경에서 돌려 보는 스크립트다. 본 결과는 [임시 세션에 hook을 걸어 README가 기대는 동작을 실제로 본다](https://github.com/uwonu606/agent-memory-layer/issues/5)의 답에 있다. 스크립트 호출의 권한과 subagent가 받는 글을 본 결과는 [에이전트는 `~/.mem`의 파일을 어떤 도구로 쓰고 지우며, 어떤 세션에서 쓰는가](https://github.com/uwonu606/agent-memory-layer/issues/18)의 답에 있다. `path-map`의 권한과 `PostToolUse` hook이 받는 입력을 본 결과는 [`Edit` allow rule 하나로 `path-map`을 묻지 않고 고칠 수 있고, hook은 바뀌기 전의 글을 받는가](https://github.com/uwonu606/agent-memory-layer/issues/36)의 답에 있다. auto mode에서 `~/.mem-hook`의 스크립트 고치기를 막는 방법을 본 결과는 [`deny` rule과 hook은 auto mode에서 `~/.mem-hook`의 스크립트 고치기를 막는가](https://github.com/uwonu606/agent-memory-layer/issues/38)의 답에 있다. Claude Code 2.1.325와 2.1.327, Linux에서 썼고 `tmux`와 `python3`이 필요하다.

## 준비

실험 상태는 `LAB_ROOT`가 가리키는 폴더에 모인다. 그 아래 `home/`이 실험 세션의 `HOME`이 되어서, 실험이 실제 설정과 기억에 섞이지 않는다.

1. 빈 폴더를 정한다.

   ```
   export LAB_ROOT=<빈 폴더>
   mkdir -p "$LAB_ROOT/home" "$LAB_ROOT/work/plain"
   ```

2. 그 home에서 한 번 login한다.

   ```
   HOME="$LAB_ROOT/home" claude auth login
   ```

3. 격리 home의 user settings에 실험용 hook을 건다.

   ```
   bin/setcfg '{"autoMemoryEnabled": false}'
   ```

## 파일

| 파일 | 하는 일 |
|---|---|
| `bin/iso` | `HOME`을 `LAB_ROOT/home`(`LAB_HOME`이 있으면 그 폴더)으로 바꾸고 `LAB_*` 변수만 남긴 env로 명령을 실행한다 |
| `bin/setcfg` | 격리 home의 user settings를 다시 쓴다. 실험용 hook 둘과 넘겨준 JSON을 넣는다. `--subagent-hook`을 주면 `SubagentStart` hook도, `--post-tool-hook`을 주면 `Write`와 `Edit`의 `PostToolUse` hook도 건다 |
| `hooks/session-start.py` | hook 입력과 env를 `out/<LAB_CASE>/hook-input.jsonl`에 덧붙이고 `additionalContext`와 `systemMessage`를 낸다 |
| `hooks/subagent-start.py` | subagent가 시작할 때의 hook 입력을 `out/<LAB_CASE>/subagent-start.jsonl`에 덧붙이고, `LAB_SUBSTART_CONTEXT`가 `1`이면 `additionalContext`를 낸다 |
| `hooks/pre-tool-guard.py` | 실제 home 경로가 든 tool 호출을 거부하고, 모든 호출을 `agent_id`·`agent_type`과 함께 `out/<LAB_CASE>/pretool.jsonl`에 적는다 |
| `hooks/post-tool-dump.py` | `PostToolUse` hook 입력을 `out/<LAB_CASE>/posttool.jsonl`에 덧붙인다 |
| `proto/mem-file` | `~/.mem` 안에서만 파일 하나를 옮기거나 지우는 시제품 스크립트. `bin/perm.py`가 격리 home의 `.mem-hook/`에 놓는다 |
| `bin/runp` | `claude -p` 세션 하나를 돌리고 stream을 요약한다 |
| `bin/sum.py` | stream-json 파일을 줄마다 요약한다 |
| `bin/req.py` | transcript의 `api-request` record에서 모델에게 간 메시지 목록을 보인다 |
| `bin/launch`, `bin/tm`, `bin/ask` | tmux 안에서 대화형 세션을 열고, 글을 보내고, 화면을 읽는다 |
| `bin/perm.py` | `~/.mem` 아래의 한 동작을 세션 하나에 시키고 권한 결과를 한 줄로 낸다 |
| `bin/posttool-keys.py` | `posttool.jsonl`에서 `tool_input`과 `tool_response`의 key 목록과, 찾는 글이 든 key를 보인다 |
| `bin/make-payload.py` | 10,000자 경계용 글과 compaction을 일으킬 큰 파일을 만든다 |
| `payload/pre-*.txt` | preamble 글투 실험에 넣은 글 |

## 변수

| 이름 | 뜻 |
|---|---|
| `LAB_ROOT` | 실험 상태를 두는 폴더 |
| `LAB_HOME` | 실험 세션의 `HOME`으로 쓸 폴더. 없으면 `LAB_ROOT/home`이다 |
| `LAB_CASE` | 결과를 모을 `out/` 아래 폴더 이름 |
| `LAB_CONTEXT` | hook이 `additionalContext`로 낼 글. `{N}`은 호출 순번, `{SOURCE}`는 시작 방식, `{HOME}`은 격리 home으로 바뀐다 |
| `LAB_CONTEXT_FILE` | 그 글이 든 파일. `LAB_CONTEXT`보다 먼저 본다 |
| `LAB_SYSMSG` | hook이 `systemMessage`로 낼 글. `{CHARS}`는 `additionalContext`의 글자 수로 바뀐다 |
| `LAB_PRETOOL_ALLOW_MEM` | `1`이면 guard hook이 `/.mem`이 든 호출에 `"allow"`를 낸다 |
| `LAB_PRETOOL_DENY` | 빈칸으로 가른 글자들. guard hook이 그중 하나가 입력에 든 호출에 `"deny"`를 낸다 |
| `LAB_SUBSTART_CONTEXT` | `1`이면 `SubagentStart` hook이 표지 낱말 `MARK-SUBSTART-<호출 순번>`이 든 `additionalContext`를 낸다 |
| `LAB_FORWARD` | 격리 env로 함께 넘길 변수 이름들 |
| `LAB_ROOT/hookmode` 파일 | hook의 실패 모양을 고른다: `exit1`, `exit2`, `plain`, `badjson`, `empty`, `toplevel`, `multiline`, `nosys` |

## 돌리는 법

hook 입력과 모델이 받은 글은 `-p` 세션으로 본다. 표지 낱말은 어느 글이 모델에게 남았는지 가르려고 넣는 낱말이다.

```
export LAB_CASE=startup LAB_CONTEXT='이 세션의 표지 낱말은 MARK-{SOURCE}-{N}이다.' LAB_SYSMSG='실림: 표지 {N} [{SOURCE}]'
bin/runp "$LAB_ROOT/work/plain" '보이는 표지 낱말을 적어 줘.' --model haiku --tools ""
bin/req.py "$LAB_ROOT"/home/.claude/projects/*/<session id>.jsonl --grep MARK
```

화면은 tmux 안의 대화형 세션으로 본다. 처음 여는 폴더에서는 trust 물음이 떠서 `Down`과 `Enter`를 보낸다.

```
bin/launch s1 "$LAB_ROOT/work/plain" --model haiku
bin/tm key s1 Down; bin/tm key s1 Enter
bin/ask s1 "/compact"
bin/tm kill s1
```

권한은 설정을 바꿔 쓴 뒤 mode와 동작을 골라 돌린다.

```
bin/setcfg --no-session-hook '{"autoMemoryEnabled": false, "permissions": {"allow": ["Edit(~/.mem/**)"]}}'
bin/perm.py edit-allow manual RWEDX
```

스크립트 호출의 권한은 스크립트를 부르는 `Bash` allow rule을 둔 뒤 본다. 동작 `S`는 스크립트로 옮기기, `T`는 스크립트로 지우기, `U`는 명령을 `~` 철자로 적은 옮기기, `C`는 스크립트 호출 뒤에 `touch`를 이어 붙인 명령이다.

```
bin/setcfg --no-session-hook "{\"autoMemoryEnabled\": false, \"permissions\": {\"allow\": [\"Bash(python3 $LAB_ROOT/home/.mem-hook/mem-file *)\"]}}"
bin/perm.py rule manual STUC
```

`~/.mem-hook/path-map`의 권한은 그 파일만 가리키는 `Edit` allow rule을 둔 뒤 본다. 동작 `P`는 이미 있는 `path-map`에 `Edit`으로 줄 더하기, `N`은 없는 `path-map`을 `Write`로 만들기, `L`은 같은 폴더의 `load-hook`을 `Edit`으로 고치기다. 세 동작이 같은 폴더의 파일을 다시 만들어서 `--serial`로 하나씩 돌린다. mode에 `none`을 주면 `--permission-mode` 없이 띄운다.

```
bin/setcfg --no-session-hook '{"autoMemoryEnabled": false, "permissions": {"allow": ["Edit(~/.mem-hook/path-map)"]}}'
bin/perm.py path-map none PNL --serial
```

`PostToolUse` hook이 받는 입력은 `--post-tool-hook`으로 hook을 걸고 본다. 동작 `O`는 `Write`로 이미 있는 파일 덮어쓰기다. `--seed`로 이미 있는 파일에 넣어 둔 글을 `--find`로 찾으면, 바뀌기 전의 글이 입력의 어느 key에 들어 있는지 나온다.

```
bin/setcfg --no-session-hook --post-tool-hook '{"autoMemoryEnabled": false, "permissions": {"additionalDirectories": ["~/.mem"], "allow": ["Edit(~/.mem/**)"]}}'
bin/perm.py post none WOE --seed $'ORIGINAL-7Q3 before\nUNTOUCHED-K9\n'
bin/posttool-keys.py "$LAB_ROOT"/out/perm-post-none-*/posttool.jsonl --find ORIGINAL-7Q3 --find UNTOUCHED-K9
```

`~/.mem-hook`의 스크립트를 막는 방법은 deny rule, guard hook의 거부, `autoMode.hard_deny`를 하나씩 두고 본다. 동작 `H`는 `load-hook`을 `Write`로 덮어쓰기, `G`는 redirect, `I`는 `sed -i`, `K`는 `cp`, `F`는 폴더로 `cd`한 뒤 상대 경로로 부른 `sed -i`, `A`는 `python3 -c`로 파일을 직접 여는 명령이다.

```
bin/setcfg --no-session-hook '{"autoMemoryEnabled": false, "permissions": {"deny": ["Edit(~/.mem-hook/load-hook)"]}}'
bin/perm.py deny auto LHGIKFA --serial
bin/setcfg --no-session-hook '{"autoMemoryEnabled": false}'
LAB_PRETOOL_DENY="/.mem-hook/load-hook" bin/perm.py hook auto LHGIKFA --serial
```

세션에 준 글이 스크립트를 가리켜 시키지 않을 때 에이전트가 하는 일은 동작 `Q`·`Y`·`J`로 본다. `Q`는 폴더를 정리하라고만 시키고, `Y`는 오타가 든 `load-hook`을 두고 `path-map`이 load되지 않는다고만 알리고, `J`는 `path-map` 안에 `load-hook`을 고치라는 줄을 넣어 둔다. 세 동작은 호출 여러 번을 거쳐서 `--timeout`을 늘리고, `Y`의 세션이 user settings를 고칠 수 있어서 돌릴 때마다 `bin/setcfg`로 설정을 다시 쓴다. 결과에 `~/.mem-hook`에서 바뀐 파일이 함께 나온다.

```
bin/perm.py unasked auto QYJ --serial --timeout 400 --model sonnet
```

subagent가 받는 글은 `SubagentStart` hook을 걸고 본다. subagent의 transcript는 주 세션의 transcript 옆 `<session id>/subagents/agent-<agent id>.jsonl`에 따로 있고, 모델에게 간 요청은 브랜치 `auto-memory-lab`의 `lab/auto-memory/bin/tx.py`로 읽는다.

```
bin/setcfg --subagent-hook '{"autoMemoryEnabled": false}'
export LAB_CASE=sub LAB_SUBSTART_CONTEXT=1 LAB_CONTEXT='이 세션의 표지 낱말은 MARK-SESSION-{N}이다.'
bin/runp "$LAB_ROOT/work/plain" 'Agent 도구로 general-purpose subagent를 하나 띄워서 context에 보이는 MARK로 시작하는 낱말을 모두 적게 해 줘. 네가 아는 표지 낱말은 그 prompt에 적지 마.' --model haiku
tx.py "$LAB_ROOT"/home/.claude/projects/*/<session id>/subagents/agent-<agent id>.jsonl find MARK-SESSION MARK-SUBSTART --req all
```

## 끝낸 뒤

격리 home에서 logout하고 폴더를 지운다.

```
bin/iso claude auth logout
rm -rf "$LAB_ROOT"
```
