# idle compaction 실험 도구

쉬고 있는 Claude Code 대화형 세션에서 idle compaction이 일어나는지를 세션을 건드리지 않고 지켜보는 스크립트다.

본 결과는 [idle compaction을 일으켜 그 뒤에 `SessionStart` hook이 도는지 본다](https://github.com/uwonu606/agent-memory-layer/issues/19)의 답에 있다. Claude Code 2.1.325, Linux에서 썼고 `python3`이 필요하다.

세션을 열고 hook을 거는 일은 브랜치 `hook-permission-lab`의 [`lab/hook-permission/`](https://github.com/uwonu606/agent-memory-layer/tree/hook-permission-lab/lab/hook-permission)으로 한다. 아래의 `<iso>`와 `<tm>`은 그 폴더의 `bin/iso`와 `bin/tm`의 경로다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `bin/wait-login.sh <iso> <초>` | 격리 home의 login을 그 시간만큼 기다린다 |
| `bin/watch.sh <tm> <초> <세션...>` | hook 기록의 줄 수, 화면의 `Compacted` 줄, 요청 수를 10초마다 본다. 바뀌면 바로 끝난다 |
| `bin/probe.py <transcript>` | 요청마다 cache TTL을, 답마다 cache에서 읽고 쓴 token을, `compact_boundary` 같은 system record를 보인다 |
| `bin/clock.sh` | 벽시계와 `/proc/uptime`을 한 줄로 찍는다 |
| `bin/binctx.py <실행 파일> <글> <앞> <뒤>` | 설치된 실행 파일에서 그 글의 앞뒤 글자를 읽는다. 조건의 단서를 찾을 때 썼다 |

## 지켜보기

idle compaction은 마지막 요청에서 흐른 시간으로 일어난다. 그래서 `watch.sh`는 세션에 아무것도 보내지 않고 파일과 화면만 읽는다.

`watch.sh`와 `wait-login.sh`는 실험 상태를 두는 폴더를 `LAB_ROOT`로 받는다. `watch.sh`는 세션마다 아래 둘을 읽는다.

| 파일 | 누가 쓰는가 |
|---|---|
| `$LAB_ROOT/out/<세션>/hook-input.jsonl` | `lab/hook-permission/`의 `hooks/session-start.py`가 hook 입력을 한 줄씩 덧붙인다 |
| `$LAB_ROOT/out/<세션>/transcript` | 세션을 연 뒤 손으로 적는다. hook 입력의 `transcript_path` 값 한 줄이다 |

```
export LAB_ROOT=<실험 폴더>
bin/watch.sh <tm> 3600 <세션 이름> <세션 이름>
```

## 기기가 잠들었는지

쉬기 전과 뒤에 `clock.sh`를 한 번씩 돌린다. `wall`과 `uptime`이 같은 만큼 흘렀으면 기기는 그동안 잠들지 않았다.
