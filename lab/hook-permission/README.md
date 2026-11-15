# hook과 권한 실험 도구

Claude Code의 `SessionStart` hook과 `~/.mem` 쓰기 권한이 실제로 어떻게 도는지를 격리 환경에서 돌려 보는 스크립트다. 본 결과는 [임시 세션에 hook을 걸어 README가 기대는 동작을 실제로 본다](https://github.com/uwonu606/agent-memory-layer/issues/5)의 답에 있다. 스크립트 호출의 권한과 subagent가 받는 글을 본 결과는 [에이전트는 `~/.mem`의 파일을 어떤 도구로 쓰고 지우며, 어떤 세션에서 쓰는가](https://github.com/uwonu606/agent-memory-layer/issues/18)의 답에 있다. Claude Code 2.1.325, Linux에서 썼고 `tmux`와 `python3`이 필요하다.

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
| `bin/iso` | `HOME`을 `LAB_ROOT/home`으로 바꾸고 `LAB_*` 변수만 남긴 env로 명령을 실행한다 |
| `bin/setcfg` | 격리 home의 user settings를 다시 쓴다. 실험용 hook 둘과 넘겨준 JSON을 넣는다. `--subagent-hook`을 주면 `SubagentStart` hook도 건다 |
| `hooks/session-start.py` | hook 입력과 env를 `out/<LAB_CASE>/hook-input.jsonl`에 덧붙이고 `additionalContext`와 `systemMessage`를 낸다 |
| `hooks/subagent-start.py` | subagent가 시작할 때의 hook 입력을 `out/<LAB_CASE>/subagent-start.jsonl`에 덧붙이고, `LAB_SUBSTART_CONTEXT`가 `1`이면 `additionalContext`를 낸다 |
| `hooks/pre-tool-guard.py` | 실제 home 경로가 든 tool 호출을 거부하고, 모든 호출을 `agent_id`·`agent_type`과 함께 `out/<LAB_CASE>/pretool.jsonl`에 적는다 |
| `proto/mem-file` | `~/.mem` 안에서만 파일 하나를 옮기거나 지우는 시제품 스크립트. `bin/perm.py`가 격리 home의 `.mem-hook/`에 놓는다 |
| `bin/runp` | `claude -p` 세션 하나를 돌리고 stream을 요약한다 |
| `bin/sum.py` | stream-json 파일을 줄마다 요약한다 |
| `bin/req.py` | transcript의 `api-request` record에서 모델에게 간 메시지 목록을 보인다 |
| `bin/launch`, `bin/tm`, `bin/ask` | tmux 안에서 대화형 세션을 열고, 글을 보내고, 화면을 읽는다 |
| `bin/perm.py` | `~/.mem` 아래의 한 동작을 세션 하나에 시키고 권한 결과를 한 줄로 낸다 |
| `bin/make-payload.py` | 10,000자 경계용 글과 compaction을 일으킬 큰 파일을 만든다 |
| `payload/pre-*.txt` | preamble 글투 실험에 넣은 글 |

## 변수

| 이름 | 뜻 |
|---|---|
| `LAB_ROOT` | 실험 상태를 두는 폴더 |
| `LAB_CASE` | 결과를 모을 `out/` 아래 폴더 이름 |
| `LAB_CONTEXT` | hook이 `additionalContext`로 낼 글. `{N}`은 호출 순번, `{SOURCE}`는 시작 방식, `{HOME}`은 격리 home으로 바뀐다 |
| `LAB_CONTEXT_FILE` | 그 글이 든 파일. `LAB_CONTEXT`보다 먼저 본다 |
| `LAB_SYSMSG` | hook이 `systemMessage`로 낼 글. `{CHARS}`는 `additionalContext`의 글자 수로 바뀐다 |
| `LAB_PRETOOL_ALLOW_MEM` | `1`이면 guard hook이 `/.mem`이 든 호출에 `"allow"`를 낸다 |
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
