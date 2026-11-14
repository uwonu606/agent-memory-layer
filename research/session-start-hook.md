# `SessionStart` hook의 입력과 출력

`README.md` #1단계가 load하는 방식이 기대는 `SessionStart` hook의 동작 다섯 가지는 Claude Code 공식 문서와 맞다. 문서와 어긋나는 곳은 셋이다. README가 시작 방식 `fork`를 다루지 않고, 10,000자를 넘은 글에서 모델이 받는 것을 좁게 적었고, hook 입력의 `cwd`를 세션을 연 폴더로 본다.

| 항목 | 내용 |
|---|---|
| 질문 | issue #2 "`SessionStart` hook의 입력과 출력은 README가 적은 대로인가" |
| 조사한 날 | 2026-11-14 |
| 방법 | 공식 문서만 읽었다. Claude Code를 돌려 보지 않았다 |
| 인용 | 큰따옴표 안은 문서 원문이다. 각 페이지의 markdown 주소(주소 끝에 `.md`)를 받아 원문에서 옮겼고, 링크 표시만 뺐다 |
| 판 | 이 기기의 Claude Code는 2.1.325다(issue #2 본문). hooks 문서가 판 조건으로 적은 가장 높은 판은 v2.1.319다 |

문서로 갈리지 않은 것은 issue #5 "임시 세션에 hook을 걸어 README가 기대는 동작을 실제로 본다"로 넘긴다. 넘길 것은 #확인하지 못한 것에 모았다.

## 입력

`SessionStart` hook은 `cwd`와 시작 방식을 받는다. 시작 방식은 `source` 필드에 `startup`·`resume`·`clear`·`compact`·`fork` 가운데 하나로 온다. `fork`로 시작한 세션에서도 hook이 돈다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| `cwd`는 모든 hook 입력에 든다 | `cwd` 행: "Current working directory when the hook is invoked" | [hooks#common-input-fields](https://code.claude.com/docs/en/hooks#common-input-fields) |
| 시작 방식은 `source`로 온다 | "How the session started: `"startup"` for new sessions, `"resume"` for resumed sessions, `"clear"` after `/clear`, `"compact"` after compaction, or `"fork"` for a new session forked from an existing one" | [hooks#sessionstart-input](https://code.claude.com/docs/en/hooks#sessionstart-input) |
| matcher는 같은 값을 거른다 | "The matcher value corresponds to how the session was initiated" | [hooks#sessionstart](https://code.claude.com/docs/en/hooks#sessionstart) |
| `fork`가 가리키는 시작 | `fork` 행: "A new session forked from an existing one: `--fork-session` with `--resume` or `--continue`, the `/fork` background copy, `/branch`, or a conversation you move to the background" | [hooks#sessionstart](https://code.claude.com/docs/en/hooks#sessionstart) |
| `resume`과 `fork`에서도 hook이 돈다 | "`SessionStart` hooks run again on resume with `source` set to `"resume"`, or `"fork"` if you added `--fork-session`, so they can refresh their context." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| matcher가 없으면 모든 시작 방식에 돈다 | "`"*"`, `""`, or omitted" 행: "Match all" | [hooks#matcher-patterns](https://code.claude.com/docs/en/hooks#matcher-patterns) |
| `\|`로 이은 matcher는 적은 값에만 돈다 | "Exact string, or list of exact strings separated by `\|` or `,` with optional surrounding whitespace" | [hooks#matcher-patterns](https://code.claude.com/docs/en/hooks#matcher-patterns) |

그래서 matcher를 `startup|clear|compact`로 걸면 `resume`과 `fork`로 시작한 세션에서는 hook이 돌지 않는다.

### `cwd`의 뜻

`cwd`는 세션을 연 폴더가 아니라 hook이 불린 때의 working directory다. 세션을 연 곳은 환경 변수 `CLAUDE_PROJECT_DIR`에 온다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| `cwd`는 Claude를 따라 움직인다 | "**`cwd` follows Claude**: the `cwd` field in the hook's input JSON is the worktree root after Claude enters a worktree, and the new directory after Claude runs `cd`." | [hooks#reference-scripts-by-path](https://code.claude.com/docs/en/hooks#reference-scripts-by-path) |
| 세션을 연 곳은 `CLAUDE_PROJECT_DIR`이다 | "`${CLAUDE_PROJECT_DIR}`: the project root where the session started." | [hooks#reference-scripts-by-path](https://code.claude.com/docs/en/hooks#reference-scripts-by-path) |
| `cd`가 남는 범위 | "When Claude runs `cd` in the main session, the new working directory carries over to later Bash commands as long as it stays inside the project directory or an additional working directory you added with `--add-dir`, `/add-dir`, or `additionalDirectories` in settings." | [tools-reference#what-persists-between-commands](https://code.claude.com/docs/en/tools-reference#what-persists-between-commands) |

hook이 `compact`로 불릴 때, Claude가 그 사이 `cd`했거나 worktree에 들어갔으면 `cwd`는 세션을 연 폴더와 다르다.

README의 맥락 규칙은 경로의 앞부분을 맞춰 보기 때문에, Claude가 세션을 연 폴더의 하위 폴더로 `cd`한 것은 맥락을 바꾸지 않는다. 맥락이 바뀌는 때는 `cwd`가 규칙의 경로 밖으로 나간 때, 곧 다른 맥락에 있는 additional working directory나 worktree로 옮긴 때다.

## `additionalContext`

Claude Code는 `additionalContext`의 글을 system reminder로 감싸 대화의 맨 앞, 첫 prompt 앞에 넣는다. system prompt에는 넣지 않는다. system reminder는 Claude Code가 모델에게 context를 주려고 대화에 끼워 넣는 메시지다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| 넣는 방식 | "Claude Code wraps the string in a system reminder and inserts it into the conversation at the point where the hook fired. Claude reads the reminder on the next model request, but it doesn't appear as a chat message in the interface." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| `SessionStart`의 글이 놓이는 자리 | "SessionStart and SubagentStart: at the start of the conversation, before the first prompt" | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| API 요청에서의 모양 | "In a logged API request, a system reminder appears wrapped in `<system-reminder>` tags inside a user message, or on some models as a separate message with the `system` role." | [glossary#system-reminder](https://code.claude.com/docs/en/glossary#system-reminder) |
| 모델의 첫 응답은 hook을 기다린다 | "Claude's first response still waits for the hooks to finish, so their context reaches Claude." | [hooks#sessionstart](https://code.claude.com/docs/en/hooks#sessionstart) |
| 출력에서의 자리 | "Return `additionalContext` inside `hookSpecificOutput` alongside the event name" | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| 최상위에 두면 말없이 버려진다 | "When your hook returns `permissionDecision` or `additionalContext` at the top level instead of inside `hookSpecificOutput`, the JSON still parses, and Claude Code ignores the misplaced fields without reporting an error." | [hooks-guide#fields-at-the-wrong-level](https://code.claude.com/docs/en/hooks-guide#fields-at-the-wrong-level) |
| stdout에는 JSON만 찍는다 | "Print nothing but the JSON object to stdout." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| 넣은 글은 transcript에 남는다 | "Claude Code saves the injected text in the session transcript." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| 글투는 사실 서술을 권한다 | "Write the text as factual statements rather than imperative system instructions." "Text framed as out-of-band system commands can trigger Claude's prompt-injection defenses, which causes Claude to surface the text to you instead of treating it as context." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| 글 안의 태그는 바뀐다 | "If your string contains a `<system-reminder>` or `</system-reminder>` tag, Claude receives the string with that tag's `<` replaced by `&lt;`." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |

## `systemMessage`

Claude Code는 `systemMessage`의 글을 사람에게 보여 주고 모델에게는 주지 않는다. hook을 `async`로 걸면 사람에게 보이지 않는다. 터미널 화면에 어떤 모양으로 언제 뜨는지는 문서에 없다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| 사람에게 보인다 | `systemMessage` 행: "Warning message shown to the user." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| 모델은 받지 않는다 | "The `systemMessage` field shows a message to the user, not the model." | [agent-sdk/hooks#systemmessage-not-appearing-in-output](https://code.claude.com/docs/en/agent-sdk/hooks#systemmessage-not-appearing-in-output) |
| 버리거나 다른 곳으로 보내는 event는 그 절이 적는다 | "Every event accepts them, but some events discard them or deliver `systemMessage` somewhere other than the transcript. Each event's section says so." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| `SessionStart` 절은 예외를 적지 않고 쓰는 예를 든다 | "Your hook can use them to report what resuming a stale conversation costs before the first request, for example in a `systemMessage`." | [hooks#sessionstart-input](https://code.claude.com/docs/en/hooks#sessionstart-input) |
| `async` hook의 글은 사람에게 보이지 않는다 | "Unlike a synchronous hook's `systemMessage`, neither field is shown to you." | [hooks#how-async-hooks-execute](https://code.claude.com/docs/en/hooks#how-async-hooks-execute) |
| hook이 터미널에 직접 쓰는 길은 없다 | "On macOS and Linux, command hooks run in their own session without a controlling terminal." "To surface a message to the user on any platform, return `systemMessage` in JSON output." | [hooks#hook-input-and-output](https://code.claude.com/docs/en/hooks#hook-input-and-output) |
| hook은 사람이 입력하는 동안 뒤에서 돈다 | "When you start an interactive session, resume a conversation at launch with `--continue` or `--resume`, or run `/clear`, SessionStart hooks run in the background. You can type right away" | [hooks#sessionstart](https://code.claude.com/docs/en/hooks#sessionstart) |

문서가 화면의 모양을 적은 곳은 둘인데, 둘 다 터미널의 기본 화면을 말하지 않는다.

| 어디의 모양인가 | 문서 원문 | 출처 |
|---|---|---|
| `Ctrl+O`로 여는 transcript viewer | "**Success**: you see nothing, unless the hook's JSON surfaces something, such as `systemMessage` or Stop hook feedback." | [hooks-guide#check-what-a-hook-did](https://code.claude.com/docs/en/hooks-guide#check-what-a-hook-did) |
| Agent SDK의 message stream | "a hook's `systemMessage` can arrive as this message, with each line prefixed by the hook's name, such as `PostToolUse:Bash says:`" | [agent-sdk/typescript#sdkinformationalmessage](https://code.claude.com/docs/en/agent-sdk/typescript#sdkinformationalmessage) |

## 10,000자

README가 적은 대로 Claude Code는 10,000자를 넘는 글을 파일로 돌린다. 모델이 받는 것은 README가 적은 "앞 2,000자"보다 넓어서, 그 파일의 경로와 앞 2,000자까지의 미리보기다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| 상한이 걸리는 글 | "A hook's `additionalContext`, `systemMessage`, and `initialUserMessage` strings, and its plain stdout, are capped at 10,000 characters" | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| 넘으면 파일로 돌린다 | "Claude Code saves the output to a file in the session directory. It replaces the output with the file path and a preview of up to the first 2,000 characters." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| 모델은 경로와 미리보기를 받는다 | "If a value exceeds 10,000 characters, Claude Code writes the text to a file in the session directory and passes Claude the file path with a preview of up to the first 2,000 characters instead. Claude can read the file, but Claude Code doesn't ask it to." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| Claude Code는 파일을 읽으라고 시키지 않는다 | "Claude Code doesn't ask Claude to read the file, so keep anything Claude must always see within the cap." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| 상한을 올리는 설정은 없다 | "this cap has no setting or environment variable to raise it." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| 문자열마다 따로 잰다 | "Claude Code measures each string on its own, even when several hooks run for the same event. For JSON output, each field is measured separately; plain stdout is measured whole." | [hooks#json-output](https://code.claude.com/docs/en/hooks#json-output) |
| hook 여럿이 돌려준 글은 모두 간다 | "When several hooks return `additionalContext` for the same event, Claude receives all of the values." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |

그래서 상한은 hook 하나가 돌려준 `additionalContext` 문자열 하나에 걸린다. 세션 시작 줄을 담는 `systemMessage`도 따로 10,000자 상한을 받는다.

## compaction

compaction 뒤에 Claude Code는 matcher가 `compact`에 맞는 `SessionStart` hook을 다시 돌리고, 돌려준 글을 compaction을 거친 context에 넣는다. 앞서 넣은 글은 대화와 함께 요약된다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| `compact`로 도는 때 | `compact` 행: "Auto or manual compaction" | [hooks#sessionstart](https://code.claude.com/docs/en/hooks#sessionstart) |
| 다시 돌고 글이 다시 들어간다 | "SessionStart hooks that match the `compact` source" 행: "Claude Code runs them and adds their output to the compacted context" | [context-window#what-survives-compaction](https://code.claude.com/docs/en/context-window#what-survives-compaction) |
| 앞서 넣은 글은 요약된다 | "Context that hooks added earlier" 행: "Summarized with the rest of the conversation" | [context-window#what-survives-compaction](https://code.claude.com/docs/en/context-window#what-survives-compaction) |
| 문서가 권하는 쓰임 | "Use a `SessionStart` hook with a `compact` matcher to re-inject critical context after every compaction." | [hooks-guide#re-inject-context-after-compaction](https://code.claude.com/docs/en/hooks-guide#re-inject-context-after-compaction) |

## `resume`과 `fork`

README는 `resume`에 글을 넣지 않는 까닭으로 앞 대화에 `additionalContext`가 이미 있다는 것을 든다. 문서는 `SessionStart`가 넣은 글이 resume한 대화에 남는다고 짚어 말하지 않는다.

| 확인한 것 | 문서 원문 | 출처 |
|---|---|---|
| resume은 transcript에서 대화를 되살린다 | "Conversation history: the messages, tool calls, and results." | [sessions#what-a-resumed-session-restores](https://code.claude.com/docs/en/sessions#what-a-resumed-session-restores) |
| 저장한 글을 다시 쓴다고 적은 것은 세션 도중의 event다 | "For mid-session events like `PostToolUse` or `UserPromptSubmit`, when you resume with `--continue` or `--resume`, Claude Code replays the saved text rather than re-running the hook for past turns, so values like timestamps or commit SHAs become stale." | [hooks#add-context-for-claude](https://code.claude.com/docs/en/hooks#add-context-for-claude) |
| compaction을 거친 세션을 resume하면 | "Claude continues with the last compaction's summary, the messages that compaction left unsummarized, and every message since." | [sessions#what-a-resumed-session-restores](https://code.claude.com/docs/en/sessions#what-a-resumed-session-restores) |
| `/branch`는 대화를 복사한다 | "Conversation history" 행: "Copied into the branch up to the point you ran `/branch`" | [sessions#branch-a-session](https://code.claude.com/docs/en/sessions#branch-a-session) |
| `/fork`도 대화를 복사한다 | "The copy starts with everything in the conversation up to that point" | [agent-view#copy-the-session-with-/fork](https://code.claude.com/docs/en/agent-view#copy-the-session-with-%2Ffork) |
| agent view를 끄면 `/fork`는 세션을 만들지 않는다 | "When agent view is turned off, `/fork` starts a forked subagent instead of copying the session." | [agent-view#copy-the-session-with-/fork](https://code.claude.com/docs/en/agent-view#copy-the-session-with-%2Ffork) |
| `async`로 건 `SessionStart` hook의 옛 동작 | "Before v2.1.295, Claude Code added the same text to the conversation again on every resume." | [hooks#limitations](https://code.claude.com/docs/en/hooks#limitations) |

`[추정]` resume하거나 fork한 세션의 대화에는 앞 세션에서 `SessionStart` hook이 넣은 글이 남아 있다(근거: 넣은 글을 transcript에 저장한다는 문장과, resume·fork가 대화를 되살리거나 복사한다는 문장, 2개).

문서가 드는 쓰임은 README와 반대쪽이다. 문서는 resume에서 hook을 다시 돌려 context를 새로 고치는 것("so they can refresh their context")을 든다. README처럼 `resume`과 `fork`를 빼면, 그 세션은 앞 세션이 시작한 때의 기억을 그대로 들고 간다.

## README에서 고칠 곳

고칠 곳은 넷이고 README는 고치지 않았다. `제안:`은 반영할지를 사용자가 정하는 것이고, `참고:`는 행동을 요구하지 않는 것이다.

| 곳 | 지금 글 | 고칠 내용 |
|---|---|---|
| #1단계가 load하는 방식 표의 `시점` 줄 | 값 "startup·clear·compact. resume은 넣지 않는다" | `제안:` 값을 "startup·clear·compact. resume과 fork는 넣지 않는다"로 고친다. 까닭에 fork는 앞 대화를 복사해서 시작한다는 것을 더한다. 문서의 시작 방식은 다섯인데 README는 `fork`를 다루지 않는다 |
| 같은 표의 `10,000자 넘음` 줄 | 까닭 "모델에게는 앞 2,000자만 보인다" | `제안:` "모델에게는 그 파일의 경로와 앞 2,000자까지의 미리보기만 간다. Claude Code는 모델에게 그 파일을 읽으라고 시키지 않는다"로 고친다. 값은 그대로 둔다 |
| 같은 표의 `preamble` 줄 | 값 "…이르고, …쓰라고 이른다" | `참고:` 문서는 `additionalContext`의 글을 지시가 아니라 사실 서술로 쓰라고 권한다. preamble을 지시형으로 쓰면 모델이 그 글을 context로 받지 않고 사람에게 드러낼 수 있다고 문서가 적는다 |
| #맥락 규칙의 "작업 위치(hook 입력의 `cwd`)"와 #만들 것의 "작업 위치는 세션을 연 폴더다" | 두 문장이 `cwd`를 세션을 연 폴더로 본다 | `제안:` 둘 가운데 하나로 맞춘다. 작업 위치를 세션을 연 폴더로 두려면 hook이 `CLAUDE_PROJECT_DIR`을 읽는다. hook 입력의 `cwd`를 쓰려면 작업 위치의 뜻을 hook이 불린 때 Claude가 있는 폴더로 고친다 |

`시점` 줄의 까닭 "resume은 앞 대화에 `additionalContext`가 이미 있다"는 #`resume`과 `fork`의 추정에 기댄다. issue #5에서 본 뒤에 굳힌다.

표 위의 문장 "세션 시작 줄을 `systemMessage`로 띄운다"는 문서와 맞다. hook을 `async`로 걸지 않는다는 조건이 붙는다.

## 확인하지 못한 것

문서가 적지 않아서 issue #5에서 돌려 봐야 아는 것이다.

| 문서가 적지 않은 것 | issue #5에서 해 볼 것 |
|---|---|
| `systemMessage`가 터미널의 기본 화면에 뜨는지, 어떤 모양인지, 사람이 첫 prompt를 치기 전에 뜨는지 | `startup`·`clear`·`compact`(`/compact`와 auto) 각각에서 `systemMessage`를 돌려주고, `Ctrl+O`를 누르지 않은 화면에 줄이 뜨는지와 뜨는 때를 본다 |
| 10,000자를 세는 단위와 경계 | 한글로 9,999자·10,000자·10,001자인 글을 넣어, 어느 길이부터 파일로 돌아가는지 본다 |
| 10,000자를 넘은 때 모델이 받는 글의 모양과 파일이 놓이는 곳 | 넘는 글을 넣고 transcript 파일이나 `claude --debug-file <path>`의 로그에서 모델에게 간 글을 찾는다 |
| resume·fork한 세션의 대화에 앞 세션의 `additionalContext`가 남는지 | matcher를 `startup\|clear\|compact`로 걸고 `--continue`·`/resume`·`/branch`·`--fork-session`·`/fork`로 세션을 연 뒤, hook이 돌지 않는지와 앞서 넣은 글이 모델에게 남아 있는지를 본다. compaction을 거친 세션으로도 본다 |
| idle compaction 뒤와 `/rewind`의 Summarize 뒤에 `SessionStart`가 `compact`로 도는지 | 두 경우에 hook이 불리는지와 `source` 값을 본다 |
| `CLAUDE_PROJECT_DIR`이 세션을 연 폴더와 같은 값인지 | 저장소의 하위 폴더에서 세션을 열어 `cwd`와 `CLAUDE_PROJECT_DIR`을 찍는다. `/add-dir`로 더한 폴더로 `cd`한 뒤 `/compact`를 해서 `cwd`를 다시 찍는다 |
| 지시형으로 쓴 preamble을 모델이 사람에게 드러내는지 | README의 preamble을 지시형과 사실 서술 두 가지로 넣고 모델의 첫 응답을 견준다 |

idle compaction을 표에 넣은 까닭은 `SessionStart` 절이 `compact`를 "Auto or manual compaction"이라고만 적기 때문이다. `PreCompact` 절은 `auto`에 idle compaction이 든다고 적는다([hooks#precompact](https://code.claude.com/docs/en/hooks#precompact)).

`/rewind`의 Summarize는 문서가 "like a targeted `/compact`"라고 적지만 hook을 말하지 않는다([checkpointing#rewind-and-summarize](https://code.claude.com/docs/en/checkpointing#rewind-and-summarize)).

## 출처

모두 Claude Code 공식 문서이고 2026-11-14에 받았다.

| 페이지 | URL |
|---|---|
| Hooks reference | https://code.claude.com/docs/en/hooks |
| Automate actions with hooks | https://code.claude.com/docs/en/hooks-guide |
| Explore the context window | https://code.claude.com/docs/en/context-window |
| Manage sessions | https://code.claude.com/docs/en/sessions |
| Glossary | https://code.claude.com/docs/en/glossary |
| Tools reference | https://code.claude.com/docs/en/tools-reference |
| Manage multiple agents with agent view | https://code.claude.com/docs/en/agent-view |
| Checkpointing | https://code.claude.com/docs/en/checkpointing |
| Intercept and control agent behavior with hooks | https://code.claude.com/docs/en/agent-sdk/hooks |
| Agent SDK reference - TypeScript | https://code.claude.com/docs/en/agent-sdk/typescript |
