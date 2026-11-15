# auto memory 실험 도구

Claude Code의 auto memory를 켠 세션과 끈 세션에서 모델이 실제로 받는 글, 기억 폴더의 권한, 기억 폴더의 자리를 격리 환경에서 돌려 보는 스크립트다.

본 결과는 [auto memory를 켠 세션과 끈 세션을 실제로 돌려 문서에 없는 동작을 본다](https://github.com/uwonu606/agent-memory-layer/issues/17)의 답에 있다. Claude Code 2.1.325, Linux에서 썼고 `tmux`와 `python3`이 필요하다.

## 준비

실험 상태는 `LAB_ROOT`가 가리키는 폴더에 모인다. 그 아래 `home/`이 실험 세션의 `HOME`이 되어서, 실험이 실제 설정과 기억에 섞이지 않는다.

1. 빈 폴더와 작업 폴더를 만든다.

   ```
   export LAB_ROOT=<빈 폴더>
   mkdir -p "$LAB_ROOT/home" "$LAB_ROOT/work/repoA"
   git -C "$LAB_ROOT/work/repoA" init
   ```

2. 그 home에서 한 번 login한다.

   ```
   HOME="$LAB_ROOT/home" claude auth login
   ```

3. 격리 home의 user settings를 쓴다. 넘긴 JSON이 hook 설정 옆에 합쳐진다.

   ```
   bin/cfg                                   # auto memory를 켠 채
   bin/cfg '{"autoMemoryEnabled": false}'    # 끈 채
   ```

## 파일

| 파일 | 하는 일 |
|---|---|
| `bin/iso` | `HOME`을 `LAB_ROOT/home`으로 바꾸고 `LAB_*` 변수만 남긴 env로 명령을 실행한다 |
| `bin/cfg` | 격리 home의 user settings를 다시 쓴다. guard hook, 기록 hook, 넘겨준 JSON을 넣는다 |
| `hooks/pre-tool-guard.py` | 실제 home 경로가 든 tool 호출을 거부하고, 모든 호출을 `out/<LAB_CASE>/pretool.jsonl`에 적는다 |
| `hooks/log-event.py` | `SessionStart`, `InstructionsLoaded`, `SessionEnd`의 hook 입력을 `out/<LAB_CASE>/events.jsonl`에 덧붙인다 |
| `bin/case` | `claude -p` 세션 하나를 돌리고, 요약과 init 사건의 `memory_paths`를 보이고, transcript 경로를 `out/<이름>/transcript`에 적는다 |
| `bin/runp`, `bin/sum.py` | `bin/case`가 부른다. 세션을 돌리고 stream-json을 줄마다 요약한다 |
| `bin/tx.py` | transcript에서 모델에게 간 요청의 system과 messages를 다시 짜서 보인다 |
| `bin/calls.py` | stream-json에서 tool 호출, 그 결과, 모델의 말을 줄마다 보인다 |
| `bin/memfix` | 기억 폴더에 색인 `MEMORY.md`와 주제 파일 셋을 표지 낱말과 함께 쓴다 |
| `bin/memperm` | 한 폴더의 파일을 읽기, 고치기, 쓰기 세 세션으로 시키고 권한 결과를 한 줄씩 낸다 |
| `bin/bigindex`, `bin/lastline.py` | 줄 수와 줄 길이를 정한 `MEMORY.md`를 만들고, load된 색인이 어디서 끊겼는지 보인다 |
| `bin/fn.sh` | `source`해서 쓰는 함수 셋. `run`, `memory_path`, `reset_memory` |
| `bin/launch`, `bin/tm`, `bin/ask` | tmux 안에서 대화형 세션을 열고, 글을 보내고, 화면을 읽는다 |

## 변수

| 이름 | 뜻 |
|---|---|
| `LAB_ROOT` | 실험 상태를 두는 폴더 |
| `LAB_CASE` | 결과를 모을 `out/` 아래 폴더 이름. `bin/case`는 첫 인자로 정한다 |
| `LAB_FORWARD` | 격리 env로 함께 넘길 변수 이름들 |
| `LAB_CLIP` | `bin/case`가 보이는 요약의 줄 길이 |
| `LAB_TIMEOUT` | `-p` 세션 하나의 제한 시간(초) |

## 돌리는 법

표지 낱말은 어느 글이 모델에게 갔는지 가르려고 기억 파일에 넣는 낱말이다. `bin/memfix`는 색인에 `INDEX-<표지>-LINE`을, 주제 파일에 `TOPIC-<표지>-…`를 넣는다.

모델이 받은 글은 `-p` 세션을 돌린 뒤 transcript에서 본다. 기억 폴더의 경로는 `bin/case`가 보이는 `memory_paths`에서 얻는다. 화면에는 `LAB_ROOT`가 `<LAB>`로 줄어 나오니 실제 경로로 바꿔 쓴다.

```
bin/case probe "$LAB_ROOT/work/repoA" '한 줄로 인사해 줘.' --model haiku
bin/memfix <기억 폴더> A
bin/case on "$LAB_ROOT/work/repoA" '보이는 표지 낱말을 적어 줘.' --model haiku
bin/tx.py "$(cat "$LAB_ROOT/out/on/transcript")" outline
bin/tx.py "$(cat "$LAB_ROOT/out/on/transcript")" find INDEX-A-LINE TOPIC-A "# Memory"
```

`bin/tx.py`의 명령은 넷이다.

| 명령 | 보이는 것 |
|---|---|
| `reqs` | 요청마다 시각, `querySource`, 모델, 메시지 수 |
| `outline` | system block과 메시지마다 길이와 heading |
| `find <글>...` | 그 글이 든 자리와 앞뒤 글 |
| `dump <이름 앞머리>` | `system[2]`나 `messages[0]`의 전문 |

`--req`로 요청을 고른다. 번호, `last`, `all`을 받고 기본은 `last`다.

끈 세션은 설정만 바꿔 같은 명령으로 돌린다. 환경 변수로 끌 때는 `LAB_FORWARD`로 넘긴다.

```
bin/cfg '{"autoMemoryEnabled": false}'
bin/case off "$LAB_ROOT/work/repoA" '보이는 표지 낱말을 적어 줘.' --model haiku
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 LAB_FORWARD=CLAUDE_CODE_DISABLE_AUTO_MEMORY bin/case off-env "$LAB_ROOT/work/repoA" '보이는 표지 낱말을 적어 줘.' --model haiku
```

권한과 색인의 상한은 아래처럼 본다.

```
bin/memperm off-mem "$LAB_ROOT/work/repoA" <기억 폴더>
bin/bigindex <기억 폴더>/MEMORY.md 250 40
bin/case big "$LAB_ROOT/work/repoA" '한 줄로 인사해 줘.' --model haiku
bin/lastline.py "$(cat "$LAB_ROOT/out/big/transcript")"
```

화면은 tmux 안의 대화형 세션으로 본다. 격리 home에서 처음 열면 theme, 보안 안내, trust 물음이 차례로 떠서 `Enter`, `Enter`, `Down`과 `Enter`를 보낸다.

```
bin/launch s1 "$LAB_ROOT/work/repoA" --model sonnet --debug-file "$LAB_ROOT/out/s1/debug.log"
bin/tm key s1 Enter
bin/ask s1 "/context"
bin/tm kill s1
```

## 끝낸 뒤

격리 home에서 logout하고 폴더를 지운다.

```
bin/iso claude auth logout
rm -rf "$LAB_ROOT"
```
