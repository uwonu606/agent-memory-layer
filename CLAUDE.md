## 이 저장소

코딩 agent의 기억 도구를 설계하고, 같은 테스트셋으로 견줄 제품을 만드는 저장소다. 무엇을 만들고 어디까지 왔는지는 `README.md`에, 낱말은 `GLOSSARY.md`에 있다.

- 설계를 읽거나 고칠 때는 `docs/design.md`에서 시작한다. 만드는 순서와 판단의 근거는 `docs/direction.md`에 있다.
- 문서를 쓰거나 고칠 때는 먼저 `docs/agents/writing.md`를 읽는다.
- 새 방식이나 요구가 오면 받기 전에 `docs/direction.md`의 방식을 거르는 기준과 `docs/constraints/agent-memory-layer.md`의 defining constraint·방향·변경 규칙·tripwire에 대 보고, 사용자가 정한 판정을 그 파일의 gate 기록에 한 줄 남긴다. 받은 것은 `docs/design.md`의 제품 축, 뺀 것, 열어 둔 물음 표 가운데 맞는 곳에 더한다.
- 제품 축의 자리는 하나로 고르지 않고 선택지마다 제품으로 만들어 견준다.
- 테스트셋은 저장소 밖에 있다. 제품을 만드는 동안에는 테스트셋을 읽지 않고, 시험은 사용자나 제품을 만들지 않는 agent가 돌린다. 제품을 만드는 agent에게 설계를 정해 넘기는 세션도 run의 출력과 check가 낸 까닭으로 판정하고, 시험의 정의와 정답은 열지 않는다.
- Claude Code의 hook, 권한, auto memory에 기대는 코드를 쓸 때는 `docs/claude-code.md`를 읽는다.

## Agent skills

### Issue tracker

Issues live in GitHub Issues, via the `gh` CLI. Read `docs/agents/issue-tracker.md` before creating, reading, or closing an issue.

### Triage labels

Read `docs/agents/triage-labels.md` before applying a triage label.

### Domain docs

Single-context: the glossary is `GLOSSARY.md` at the repo root. Read `docs/agents/domain.md` before exploring the codebase.
