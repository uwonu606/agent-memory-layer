# Claude Code 동작

한 사이클을 돌린 거친 도구(구조를 고르기 전에 만든 시제품)는 Claude Code의 세션이 시작할 때 hook으로 기억을 싣고, 모델이 파일 도구로 쓴 것을 hook으로 적었으며, 원래의 auto memory는 껐다. 구조는 아직 고르지 않아서, 다른 방식의 제품은 다른 자리에 붙을 수 있다.

이 글은 목차다. 내용은 아래 글 셋에 있고, Claude Code가 바뀌면 그 글의 "다시 조사할 때"에 적힌 절만 다시 본다.

```text
Claude Code 세션
│
├── 시작 ───── SessionStart hook ──→ 거친 도구: 기억의 색인을 싣는다   auto memory: MEMORY.md의 앞부분을 싣는다
│
├── 대화 ───── 모델이 Write/Edit ──→ 거친 도구의 기억 폴더에 쓴다      auto memory: 자기 폴더에 쓴다
│              PostToolUse hook ──→ 거친 도구: 쓰고 고친 것을 로그에 적는다 auto memory: 남기지 않는다
│
└── clear · compact · resume · fork → SessionStart hook이 다시 돈다
```

색인은 기억마다 한 줄씩 그 요지를 적은 목록이고, 로그는 언제 어느 기억을 어떻게 바꿨는지 적은 기록이다.

## 글

| 글 | 무엇을 답하나 |
|---|---|
| [Claude Code의 구조와 동작](claude-code/structure.md) | 세션이 어떻게 시작하고, 모델이 무엇을 받고, hook과 권한이 어디서 끼어드나 |
| [거친 도구가 붙은 자리](claude-code/integration.md) | 한 사이클을 돌린 거친 도구가 어느 자리에 어떤 설정으로 붙었고, 거기서 무엇에 걸렸나 |
| [원래 auto memory의 동작](claude-code/auto-memory.md) | 끄기 전의 auto memory는 어디에 두고, 무엇을 싣고, 어떻게 쓰나 |

## 믿는 정도

절마다 끝에 "확인" 줄이 있다. 실제 세션에서 본 것은 Claude Code 버전과 세션 종류를 적고, 모델은 알려진 것만 적었다. 문서로만 읽은 것은 문서라고 적었다.

| 무엇 | 언제 |
|---|---|
| 실제 세션 | 2026-11-15에 Claude Code 2.1.325로, 2026-11-19에 2.1.327과 2.1.328로 돌렸다. 어느 절이 어느 버전인지는 그 절의 확인 줄에 있다 |
| 공식 문서 | 2026-11-14와 2026-11-15에 읽고, 2026-11-22에 다시 읽었다. 그때 changelog의 맨 위는 2.1.330이었다. [Claude Code의 구조와 동작](claude-code/structure.md)의 뒤쪽 네 절(글을 넣을 수 있는 hook 자리, 답과 세션의 끝, prompt caching, auto compaction의 문턱)은 2026-11-25에 읽었고, 그때 맨 위는 2.1.332였다 |

## 다시 확인하는 법

문서로 확인할 것은 공식 문서를 다시 읽는다. 글마다의 "다시 조사할 때" 표에 볼 문서와 changelog에서 찾을 낱말이 있다. 문서의 주소는 표의 이름을 `https://code.claude.com/docs/en/` 뒤에 붙인 것이다(예: `https://code.claude.com/docs/en/hooks.md`).

실제 동작은 쓰던 설정과 기억이 섞이지 않게 빈 HOME으로 띄운 세션에서 본다. 아래 `/tmp/cc-lab`은 예시다.

1. 빈 폴더를 HOME으로 삼아 login한다.

   ```sh
   mkdir -p /tmp/cc-lab/home /tmp/cc-lab/work
   HOME=/tmp/cc-lab/home claude auth login
   ```

2. 그 HOME의 `.claude/settings.json`에 보려는 hook과 권한 줄만 둔다. hook은 받은 입력을 파일에 덧붙이게 한다.

   ```json
   { "hooks": { "SessionStart": [{ "hooks": [{ "type": "command", "command": "cat >> /tmp/cc-lab/hook-input.jsonl" }] }] } }
   ```

3. 작업 폴더에서 세션을 연다.

   ```sh
   cd /tmp/cc-lab/work && HOME=/tmp/cc-lab/home claude -p "안녕"
   ```

4. hook이 받은 입력은 `/tmp/cc-lab/hook-input.jsonl`에서, 모델에게 간 요청은 `/tmp/cc-lab/home/.claude/projects/` 아래의 transcript(`<session id>.jsonl`)에서 읽는다.
