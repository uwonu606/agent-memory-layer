# 테스트 구조 prototype

[auto memory와 이 도구를 같은 조건으로 견주는 테스트 구조는 어떤 모양인가](https://github.com/uwonu606/agent-memory-layer/issues/14)를 정하려고 만든 버리는 하니스다. auto memory 쪽에서 테스트 둘을 끝까지 돌린다. Claude Code 2.1.325, Linux에서 썼고 `python3`이 필요하다. 격리 도구(`bin/iso`, `bin/cfg`, `hooks/pre-tool-guard.py`)는 브랜치 `auto-memory-lab`의 `lab/auto-memory/`에서 가져왔다.

## 준비

```
export LAB_ROOT=<빈 폴더> LAB_SEALED=<LAB_ROOT 밖의 빈 폴더>
mkdir -p "$LAB_ROOT/home" "$LAB_ROOT/runs" "$LAB_SEALED"
HOME="$LAB_ROOT/home" claude auth login
bin/cfg
```

`LAB_SEALED`는 정답을 두는 곳이다. guard hook이 `LAB_ROOT` 밖의 실제 home 경로를 막아서 실험 세션은 이 폴더를 읽지 못한다. 정답 파일은 저장소에 두지 않는다. 형식은 `answer.example.json`에 있다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `tests/<이름>/test.json` | 테스트 하나의 정의. 사람이 시킬 말, 세션에 줄 tool, 판정 방식(`script` 또는 `human`), 돌릴 횟수(`times`) |
| `tests/<이름>/fixture/` | 세션 시작 전에 기억 폴더에 심을 기억 파일. 지어낸 내용만 둔다. 실제 기억을 옮긴 것은 `LAB_TESTS_PRIVATE/<이름>/`에 같은 모양으로 두면 그쪽을 먼저 쓴다 |
| `bin/run-once <테스트>` | 새 저장소와 기억 폴더를 만들고 심은 뒤 `claude -p`를 한 번 돌려 `runs/<run>/`에 결과를 남기고 `judge.py`를 부른다 |
| `bin/run-test <테스트>` | `run-once`를 `times`번 돌리고 `script` 판정은 모두 통과해야 통과로 센다 |
| `bin/judge.py <run 폴더>` | `script` 테스트는 봉한 정답과 견주어 통과나 실패를 낸다. `human` 테스트는 정답을 봉해 두고 사람 답을 기다린다 |
| `bin/sheet html` | 사람이 읽는 테스트의 답안지를 html 한 장(`$LAB_ROOT/sheet.html`)으로 만든다. 도구마다 테스트마다 가장 나중 run만 담는다 |
| `bin/sheet grade <answers.json>` | 답안지가 내는 JSON을 봉한 정답과 견주고 읽기 어려움과 걸린 시간을 곁에 적는다 |

테스트는 `ending`(끝까지, 쉬움), `ending-hard`(끝까지, 기억 24개·낡은 주소 두 곳·사람의 말과 기억의 낱말이 다름), `when`(언제)이다.

## 돌리는 법

```
bin/run-test ending-hard
bin/run-test when
bin/sheet html      # 사람이 답안지를 열어 채우고 JSON을 복사한다
bin/sheet grade answers.json
```

## 끝낸 뒤

```
bin/iso claude auth logout
rm -rf "$LAB_ROOT" "$LAB_SEALED"
```
