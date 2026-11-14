# auto memory가 load·save하는 것과 끄면 꺼지는 것

Claude Code 공식 문서가 auto memory에 대해 적은 동작과 한계를 그대로 옮긴 조사다. issue #3 "auto memory는 무엇을 load하고 save하며, 끄면 무엇이 꺼지는가"에 답한다. Claude Code를 돌려서 확인한 것은 없고, 문서에 없는 것은 #확인하지 못한 것에 모았다.

## 출처

Claude Code 공식 문서(`code.claude.com/docs`)만 썼다. 2026-11-14에 읽었고, 그날 changelog의 맨 위 version은 2.1.325다.

각 페이지 주소 끝에 `.md`를 붙인 주소에서 markdown 원문 전체를 받아 읽었다. 요약을 거친 글은 근거로 쓰지 않았다. 큰따옴표 안의 영어는 원문 그대로이고, 원문의 link 표기(`[글](주소)`)에서 주소만 뺐다.

| 이 글에서 부르는 이름 | 주소 |
|---|---|
| memory | https://code.claude.com/docs/en/memory |
| settings | https://code.claude.com/docs/en/settings |
| settings-reference | https://code.claude.com/docs/en/settings-reference |
| env-vars | https://code.claude.com/docs/en/env-vars |
| cli-reference | https://code.claude.com/docs/en/cli-reference |
| errors | https://code.claude.com/docs/en/errors |
| context-window | https://code.claude.com/docs/en/context-window |
| prompt-caching | https://code.claude.com/docs/en/prompt-caching |
| sub-agents | https://code.claude.com/docs/en/sub-agents |
| claude-directory | https://code.claude.com/docs/en/claude-directory |
| sessions | https://code.claude.com/docs/en/sessions |
| permission-modes | https://code.claude.com/docs/en/permission-modes |
| hooks | https://code.claude.com/docs/en/hooks |
| vs-code | https://code.claude.com/docs/en/vs-code |
| self-hosted | https://code.claude.com/docs/en/self-hosted-environments-configuration |
| SDK features | https://code.claude.com/docs/en/agent-sdk/claude-code-features |
| SDK system prompt | https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts |
| changelog | https://code.claude.com/docs/en/changelog |

## load

세션 시작에 Claude Code가 load하는 것은 `MEMORY.md`의 앞부분뿐이다. `MEMORY.md`는 기억 폴더의 index이고, 기억 하나하나는 주제 파일(topic file)에 따로 있다.

| 대상 | 문서가 적은 동작 | 원문 | 출처 |
|---|---|---|---|
| `MEMORY.md`의 앞부분 | 앞 200줄과 앞 25KB 가운데 먼저 닿는 데까지 세션 시작에 load한다 | "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| `MEMORY.md`의 그 뒤 | 세션 시작에 load하지 않는다 | "Content beyond that threshold is not loaded at session start." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| 주제 파일 | 세션 시작에 load하지 않는다. Claude가 필요할 때 file tool로 읽는다 | "Claude Code doesn't load topic files such as `user_role.md` or `feedback_testing.md` at startup. Claude reads them on demand using its standard file tools when it needs the information." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| subagent | 본 대화(main conversation)의 auto memory를 받지 않는다. fork만 받는다 | "The main conversation's auto memory isn't loaded into subagents; the exception is a fork, which inherits the parent conversation and system prompt." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| compaction 뒤 | Claude Code가 disk에서 다시 넣는다 | 표의 "Auto memory" 행에 "Re-injected from disk" | [context-window](https://code.claude.com/docs/en/context-window#what-survives-compaction) |
| `/clear` 뒤 | 문서는 auto memory가 든 층이 바뀌는 때로 `/clear`를 든다 | "CLAUDE.md, auto memory, unscoped rules" 층이 바뀌는 때는 "Session starts, or after `/clear` or `/compact`" | [prompt-caching](https://code.claude.com/docs/en/prompt-caching) |

### 상한을 재는 법

상한은 load되는 내용에만 걸린다. errors 문서는 "Only the content that loads counts toward the limits. YAML frontmatter and block-level HTML comments are stripped before the index is loaded, so they're excluded from the measurement."라고 적는다([errors](https://code.claude.com/docs/en/errors#memory-index-is-over-its-read-limit)).

이 상한은 CLAUDE.md에는 걸리지 않는다. memory 문서는 "This limit applies only to `MEMORY.md`."라고 적는다([memory](https://code.claude.com/docs/en/memory#how-it-works)).

문서는 25KB가 몇 byte인지 적지 않는다.

### load된 글이 놓이는 자리

auto memory 폴더의 경로가 system prompt에 든다는 데는 세 문서(prompt-caching, cli-reference, SDK system prompt)가 맞는다. `MEMORY.md`의 내용이 system prompt에 드는지 대화 쪽에 드는지는 문서마다 다르게 적혀 있어서 #확인하지 못한 것에 넣었다.

| 문서 | 원문 |
|---|---|
| [SDK features](https://code.claude.com/docs/en/agent-sdk/claude-code-features) | auto memory는 "Loaded into the system prompt at session start." |
| [prompt-caching](https://code.claude.com/docs/en/prompt-caching) | 요청을 세 층으로 나눈 표에서 `System prompt` 층은 "Core instructions, tool definitions"이고, `Project context` 층이 "CLAUDE.md, auto memory, unscoped rules"다 |
| [prompt-caching](https://code.claude.com/docs/en/prompt-caching) | "The system prompt embeds your auto memory paths" |
| [cli-reference](https://code.claude.com/docs/en/cli-reference) | `--exclude-dynamic-system-prompt-sections`는 "Move per-user context, such as the auto memory location, out of the system prompt and into the first user message." |
| [SDK system prompt](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts#improve-prompt-caching-across-users-and-machines) | system prompt 밖으로 옮길 수 있는 글은 "at least the auto memory directory's location, and often the whole auto memory section" |
| [memory](https://code.claude.com/docs/en/memory) | CLAUDE.md는 system prompt에 들지 않는다. "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself." |

## 단위와 자리

auto memory는 git 저장소 하나를 단위로 기억을 가르고, 기억 폴더를 `~/.claude/projects/<project>/memory/`에 둔다.

| 물음 | 답 | 원문 | 출처 |
|---|---|---|---|
| 폴더의 자리 | `~/.claude/projects/<project>/memory/` | "Each project gets its own memory directory at `~/.claude/projects/<project>/memory/`." | [memory](https://code.claude.com/docs/en/memory#storage-location) |
| 가르는 단위 | git 저장소. 그 저장소의 worktree와 하위 폴더는 폴더 하나를 같이 쓴다 | "The `<project>` path is derived from the git repository, so all worktrees and subdirectories within the same repo share one auto memory directory." | [memory](https://code.claude.com/docs/en/memory#storage-location) |
| git 저장소 밖 | project root를 쓴다 | "Outside a git repo, the project root is used instead." | [memory](https://code.claude.com/docs/en/memory#storage-location) |
| 같은 저장소를 다른 경로에 받은 것 | 경로가 다르면 폴더가 다르다 | "The location defaults to an absolute path under `~/.claude/projects/` named for the repository's path on disk, so it differs across users, machines, and checkouts." | [SDK system prompt](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts#improve-prompt-caching-across-users-and-machines) |
| 기기 | 그 기기 안에만 있다 | "Auto memory is machine-local." "Files are not shared across machines or cloud environments." | [memory](https://code.claude.com/docs/en/memory#storage-location) |
| 폴더 안의 모양 | index 하나와 기억마다 주제 파일 하나 | "The directory contains a `MEMORY.md` index and one topic file per memory" | [memory](https://code.claude.com/docs/en/memory#storage-location) |
| subagent의 기억 | 본 대화와 다른 폴더다 | "A subagent's own auto memory, enabled with the subagent `memory` field, is a separate directory." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |

내가 읽은 문서에는 본 대화의 auto memory가 저장소를 넘어 같이 쓰는 층을 적은 문장이 없다.

subagent의 기억은 `memory: user`로 두면 모든 project에 걸친다. sub-agents 문서는 그 범위를 "the subagent should remember learnings across all projects"일 때 쓰라고 적는다([sub-agents](https://code.claude.com/docs/en/sub-agents#enable-persistent-memory)).

본 대화의 단위를 바꾸는 설정은 둘이 적혀 있다.

- `autoMemoryDirectory`: "Store auto memory in a directory of your choice instead of the per-project default." 값은 "an absolute path or start with `~/`"여야 한다([settings-reference](https://code.claude.com/docs/en/settings-reference#automemorydirectory), [memory](https://code.claude.com/docs/en/memory#storage-location)).
- `CLAUDE_CODE_PROJECT_DIR_NAME`: `CLAUDE_CONFIG_DIR`과 함께 두면 "projects launched with that config directory share one auto memory directory"가 된다. v2.1.234부터다([memory](https://code.claude.com/docs/en/memory#storage-location), [sessions](https://code.claude.com/docs/en/sessions#name-the-project-directory-yourself)).

## save

Claude가 세션 도중에 무엇을 남길지 스스로 고르고, `Write`·`Edit` 도구로 기억 폴더에 쓴다.

| 물음 | 답 | 원문 | 출처 |
|---|---|---|---|
| 무엇을 남기나 | 네 종류다. `user`, `feedback`, `project`, `reference` | "As it works, Claude saves four kinds of notes for itself. Claude records the kind as a `type` field in the memory file's frontmatter" | [memory](https://code.claude.com/docs/en/memory#auto-memory) |
| 무엇을 남기지 않나 | 코드에서 알아낼 수 있는 것과 CLAUDE.md에 이미 있는 것 | "Claude skips anything it can derive from the codebase, such as architecture, file paths, or debugging fixes. It also skips anything your CLAUDE.md files already say." | [memory](https://code.claude.com/docs/en/memory#auto-memory) |
| 언제 남기나 | 세션마다 남기지는 않는다. Claude가 고른다 | "Claude doesn't save something every session. It decides what's worth remembering based on whether the information would be useful in a future conversation." | [memory](https://code.claude.com/docs/en/memory#auto-memory) |
| 세션 도중인가 | 세션 내내 읽고 쓴다 | "Claude reads and writes files in this directory throughout your session, using `MEMORY.md` to keep track of what's stored where." | [memory](https://code.claude.com/docs/en/memory#storage-location) |
| 사람이 기억하라고 말하면 | auto memory에 쓴다 | "Claude saves it to auto memory." | [memory](https://code.claude.com/docs/en/memory) |
| 무슨 도구로 쓰나 | 전용 도구 없이 `Write`와 `Edit` | "The agent writes new memories there with the standard `Write` and `Edit` tools rather than a dedicated memory tool, so those tools must be enabled for the agent to save memories" | [SDK features](https://code.claude.com/docs/en/agent-sdk/claude-code-features) |
| 쓴 시각 | Claude Code가 frontmatter의 `modified`에 적는다 | "When Claude writes a memory file that begins with YAML frontmatter, Claude Code records the write time in a `modified` frontmatter field as an ISO 8601 timestamp." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| index가 상한에 가까우면 | Claude Code가 Claude에게 줄이라고 알린다 | "If the file is near a limit, Claude Code reminds Claude to shorten it: keep one line per entry, move detail into topic files, and merge or drop stale entries." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| index가 상한을 넘으면 | 쓰기는 되고, Claude Code가 Claude에게 error를 돌려준다 | "If the file is over a limit, the write still succeeds, but Claude Code returns an error telling Claude to rewrite the index, because everything past the limit is dropped on the next load." | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| 얼마나 남나 | 사람이나 Claude가 고치거나 지울 때까지 | "`MEMORY.md` and topic files stay until you or Claude edits or deletes them." | [memory](https://code.claude.com/docs/en/memory#storage-location) |

permission-modes 문서는 기억 폴더의 markdown 파일을 protected path의 예외로 적는다. 원문은 "Markdown files in the project's auto memory directory, such as `~/.claude/projects/<project>/memory/`, in a session started without `--restricted`"다([permission-modes](https://code.claude.com/docs/en/permission-modes)).

protected path는 permission mode마다 쓰기 규칙이 따로 정해진 경로이고, `.claude` 폴더가 여기에 든다.

### changelog에만 나오는 동작

changelog에는 memory 문서가 설명하지 않는 동작의 이름이 나온다. 이름은 recall과 extraction 둘이다. 이 둘이 무엇을 언제 하는지는 문서에 없어서 #확인하지 못한 것에 넣었다.

| version | 원문 |
|---|---|
| 2.1.323 | "Changed `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` in Anthropic-hosted cloud sessions to stop applying to auto-memory extraction" |
| 2.1.288 | "Fixed session titles, memory recall and prompt hooks failing on Mantle or behind gateways that reject structured outputs" |
| 2.1.284 | "invisible characters and tags that imitate Claude Code's own markup are neutralized in `MEMORY.md` and recalled memory notes before they reach Claude" |
| 2.1.273 | "a memory directory chosen by a repository's settings is no longer loaded into the prompt, recalled, indexed, or used by memory extraction" |
| 2.1.77 | "a race between memory-extraction writes and the main transcript" |

출처는 모두 [changelog](https://code.claude.com/docs/en/changelog)다.

## 사람이 보는 길

문서가 적은 길은 여섯이다.

| 길 | 원문 | 출처 |
|---|---|---|
| 세션 도중의 알림. `Saved 2 memories`, `Recalled 2 memories` 같은 줄이 뜬다 | 이런 줄이 뜨면 "Claude is actively updating or reading from `~/.claude/projects/<project>/memory/`" | [memory](https://code.claude.com/docs/en/memory#how-it-works) |
| `/memory` | "Run `/memory` and select the auto memory folder to browse what Claude has saved. Everything is plain markdown you can read, edit, or delete." | [memory](https://code.claude.com/docs/en/memory) |
| `/context` | "run `/context` for a live breakdown by category with optimization suggestions, including which CLAUDE.md and auto memory files loaded" | [context-window](https://code.claude.com/docs/en/context-window) |
| 파일을 직접 연다 | "Auto memory files are plain markdown you can edit or delete at any time." | [memory](https://code.claude.com/docs/en/memory#audit-and-edit-your-memory) |
| VS Code의 Customize 메뉴 | "While it's on, you can also browse the memories Claude has saved and reveal the folders that store them in your file manager." | [vs-code](https://code.claude.com/docs/en/vs-code) |
| transcript 파일. 모델에 보낸 요청이 남는다 | "Conversation transcript: messages, tool calls, and tool results, plus the system prompt, tool definitions, and parameters of the requests Claude Code sent the model" | [claude-directory](https://code.claude.com/docs/en/claude-directory) |

index가 상한을 넘었다는 error는 사람의 터미널에 뜨지 않는다. errors 문서는 "Claude Code delivers the error to Claude after the write rather than printing it as a banner in your terminal, so you may notice it only in the transcript."라고 적는다([errors](https://code.claude.com/docs/en/errors#memory-index-is-over-its-read-limit)).

hooks 문서는 `InstructionsLoaded` hook이 "Fires when a `CLAUDE.md` or `.claude/rules/*.md` file is loaded into context."라고 적고, `MEMORY.md`는 적지 않는다([hooks](https://code.claude.com/docs/en/hooks#instructionsloaded)).

## 끄기

끄는 설정의 이름은 `autoMemoryEnabled`이고, 값은 `false`다. settings 파일 넷(user, project, local, managed) 어디에나 둘 수 있다.

### 끄는 길

| 길 | 자리 | 원문 | 출처 |
|---|---|---|---|
| `autoMemoryEnabled: false` | settings 파일. 문서의 Scope는 `Any file`이고 Default는 `true`다 | "When `false`, Claude doesn't read from or write to the auto memory directory." | [settings-reference](https://code.claude.com/docs/en/settings-reference#automemoryenabled) |
| `/memory`의 toggle | Claude Code가 user settings에 key를 쓴다 | "open `/memory` in a session and use the auto memory toggle, which saves `autoMemoryEnabled` to your user settings at `~/.claude/settings.json`" | [memory](https://code.claude.com/docs/en/memory#enable-or-disable-auto-memory) |
| project 하나에서만 | 그 project의 settings | "To turn it off for a single project, set `autoMemoryEnabled` in that project's settings" | [memory](https://code.claude.com/docs/en/memory#enable-or-disable-auto-memory) |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | 환경 변수 | "Set to `1` to disable auto memory." "When disabled, Claude does not create or load auto memory files" | [env-vars](https://code.claude.com/docs/en/env-vars) |
| `--bare`(`CLAUDE_CODE_SIMPLE`) | 실행 옵션. hook도 함께 건너뛴다 | "skip auto-discovery of hooks, skills, custom commands, subagents, installed plugins, MCP servers, auto memory, and CLAUDE.md" | [cli-reference](https://code.claude.com/docs/en/cli-reference) |
| `--safe-mode`(`CLAUDE_CODE_SAFE_MODE`) | 실행 옵션. hook도 함께 load하지 않는다 | "LSP servers, and auto memory do not load" | [cli-reference](https://code.claude.com/docs/en/cli-reference) |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` | 환경 변수. CLAUDE.md도 함께 load하지 않는다 | "Set to `1` to prevent loading any CLAUDE.md memory files into context, including user, project, and auto memory files" | [env-vars](https://code.claude.com/docs/en/env-vars) |

local 세션에서는 기본으로 켜져 있다. memory 문서는 "Auto memory is on by default in local sessions."라고 적는다([memory](https://code.claude.com/docs/en/memory#enable-or-disable-auto-memory)).

### 설정이 겹칠 때

| 겹치는 것 | 이기는 쪽 | 원문 | 출처 |
|---|---|---|---|
| 환경 변수와 `autoMemoryEnabled` | 환경 변수. 켜는 쪽으로도 이긴다 | "`CLAUDE_CODE_DISABLE_AUTO_MEMORY` takes precedence over this key for one session, in either direction" | [settings-reference](https://code.claude.com/docs/en/settings-reference#automemoryenabled) |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=0`과 `--bare` 또는 `false` | 환경 변수 | "Set to `0` to force auto memory on even when `--bare` mode or `autoMemoryEnabled: false` would otherwise disable it." | [env-vars](https://code.claude.com/docs/en/env-vars) |
| settings 파일끼리 | 위 층. user settings가 맨 아래다 | "Settings precedence, highest first: managed settings, command line, project local, shared project, user." | [settings](https://code.claude.com/docs/en/settings#settings-precedence) |
| `true`로 적은 값 | 적지 않은 것과 같다 | "`true`: the same as unset; auto memory stays on unless something that outranks this key turns it off for the session, such as `--bare`, safe mode, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY`" | [settings-reference](https://code.claude.com/docs/en/settings-reference#automemoryenabled) |

`/memory`의 toggle은 두 가지 세션에서 끄기만 하고 다시 켜지 못한다. 하나는 background session이고, 다른 하나는 다른 Claude Code 세션이 띄운 세션이다. 원문은 "The toggle turns auto memory off but doesn't turn it back on in these sessions"다([memory](https://code.claude.com/docs/en/memory#enable-or-disable-auto-memory)).

### 꺼지는 것과 남는 것

| 물음 | 문서의 답 | 원문 | 출처 |
|---|---|---|---|
| 읽기 | 꺼진다 | "When `false`, Claude doesn't read from or write to the auto memory directory." | [settings-reference](https://code.claude.com/docs/en/settings-reference#automemoryenabled) |
| 쓰기 | 꺼진다 | 위와 같은 문장. env-vars는 "When disabled, Claude does not create or load auto memory files" | [env-vars](https://code.claude.com/docs/en/env-vars) |
| subagent의 `memory` field | 꺼진다. 지시와 도구 접근이 함께 빠진다 | "the `memory` field has no effect and the subagent launches without the memory instructions or the memory tool access described below" | [sub-agents](https://code.claude.com/docs/en/sub-agents#enable-persistent-memory) |
| 본 대화의 system prompt에 든 auto memory 지시 | 문서에 없다 | settings 문서는 "Claude Code's system prompt isn't published."라고 적는다 | [settings](https://code.claude.com/docs/en/settings) |
| 이미 있는 기억 파일 | 끌 때 지운다는 문장이 없다 | "`MEMORY.md` and topic files stay until you or Claude edits or deletes them." | [memory](https://code.claude.com/docs/en/memory#storage-location) |

기억 파일이 지워지는 길로 문서가 적은 것은 둘이다. 하나는 사람이나 Claude가 지우는 것이고, 다른 하나는 `claude purge`다. `claude purge`는 "Transcripts and auto memory under `projects/`"를 지운다([claude-directory](https://code.claude.com/docs/en/claude-directory#clear-local-data)).

폴더는 빈 채로 보존 기간이 지나야 지워진다. 원문은 "Claude Code removes that directory only if it has been empty for the whole retention period."다([claude-directory](https://code.claude.com/docs/en/claude-directory)).

## 문서가 적은 한계

앞 절에 옮긴 것은 다시 적지 않는다. 앞 절에 있는 것은 일곱이다.

- #load: index의 상한, 주제 파일을 세션 시작에 load하지 않는 것, subagent가 받지 않는 것
- #단위와 자리: 기기 밖으로 나가지 않는 것
- #save: 세션마다 save하지 않는 것
- #사람이 보는 길: 상한을 넘은 error가 터미널에 뜨지 않는 것
- #끄기: toggle이 다시 켜지 못하는 세션

아래는 그 밖의 것이다.

| 한계 | 원문 | 출처 |
|---|---|---|
| Claude가 기억을 지키게 강제하지 않는다 | "Claude treats them as context, not enforced configuration." | [memory](https://code.claude.com/docs/en/memory#claude-md-vs-auto-memory) |
| self-hosted environment의 세션은 기본으로 꺼져 있다 | "a session in a self-hosted environment runs with auto memory off by default" | [self-hosted](https://code.claude.com/docs/en/self-hosted-environments-configuration) |
| SDK는 `settingSources`와 관계없이 auto memory를 읽는다 | "an SDK process can pick up host-level configuration and per-directory memory" | [SDK features](https://code.claude.com/docs/en/agent-sdk/claude-code-features) |
| auto memory 글을 system prompt 밖으로 옮기면 Claude가 덜 따를 수 있다 | "Instructions in a user message carry marginally less weight than the same text in the system prompt, so Claude may follow its auto memory guidance less consistently." | [SDK system prompt](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts#improve-prompt-caching-across-users-and-machines) |
| 저장소의 settings가 고른 폴더는 읽기 차단이 켜져 있으면 쓰이지 않는다 | "Claude Code loads no auto memory from a directory that a repository-supplied settings file chooses and saves none to it, wherever that directory sits." | [memory](https://code.claude.com/docs/en/memory#storage-location) |

### version에 따라 다른 것

| version | 그 앞에서의 동작 | 원문 | 출처 |
|---|---|---|---|
| 2.1.210 | 상한을 넘은 index가 알림 없이 잘렸다 | "Before v2.1.210, an over-limit index was silently truncated on the next load with no write-time signal." | [errors](https://code.claude.com/docs/en/errors#memory-index-is-over-its-read-limit) |
| 2.1.211 | frontmatter와 주석까지 상한에 셌다 | "Before v2.1.211, Claude Code measured the raw file, and frontmatter or comments could trigger this error even when the loaded content fit." | [errors](https://code.claude.com/docs/en/errors#memory-index-is-over-its-read-limit) |
| 2.1.228 | 오래된 세션 자료를 지우는 정리가 기억 폴더 안의 파일을 지울 수 있었다 | "Before v2.1.228, the sweep treated folders inside the memory directory as session data and could delete old files beneath it." | [claude-directory](https://code.claude.com/docs/en/claude-directory) |

## README #문제와 견줌

`README.md` #문제가 auto memory에 대해 적은 문장 가운데 문서와 어긋나는 문장은 없다. 아래 둘은 문서가 더 적은 것이 있어서 나란히 둔다.

| README의 문장 | 문서의 문장 | 견준 결과 |
|---|---|---|
| "Claude Code의 auto memory는 저장소마다 기억을 갈라서, 저장소를 넘는 사실이 다른 저장소의 기억에만 있으면 load되지 않는다." | "Per repository, shared across worktrees" | 기본 동작과 맞는다. 문서는 #단위와 자리의 세 가지를 더 적는다. git 저장소 밖의 단위, 경로가 다른 checkout, 단위를 바꾸는 설정 둘이다 |
| "세션 시작에 무엇이 load됐는지 보이지 않는다. 사람이 묻지 않으면 이번 세션에서 에이전트가 어떤 기억을 받았는지 알 수 없다." | "run `/context` for a live breakdown by category with optimization suggestions, including which CLAUDE.md and auto memory files loaded" | 둘째 문장까지 읽으면 맞는다. 첫 문장만 읽으면 다르다. 문서는 사람이 `/context`를 실행하면 load된 파일이 보인다고 적는다 |

문서는 세션 도중의 읽기와 쓰기에 뜨는 줄(`Saved 2 memories`, `Recalled 2 memories`)을 적는다. 세션 시작의 load를 사람에게 알리는 줄은 내가 읽은 문서에 없다.

#문제의 셋째 문장은 에이전트가 다른 맥락의 이야기를 꺼내 왔고 "그 이야기가 기억에서 왔는지는 확인하지 못했다"고 적는다. 문서가 모든 project에서 load된다고 적은 것은 user 범위의 CLAUDE.md와 rules다. `~/.claude/CLAUDE.md`는 "Personal preferences for all projects"이고, rules는 "Personal rules in `~/.claude/rules/` apply to every project on your machine."이다([memory](https://code.claude.com/docs/en/memory)).

## 확인하지 못한 것

| 모르는 것 | 문서가 적은 데까지 | 알아볼 방법 |
|---|---|---|
| `MEMORY.md`의 내용이 system prompt에 드는지 대화 쪽에 드는지 | #load의 표대로 문서마다 다르다 | 세션을 열고 transcript 파일에 적힌 system prompt와 첫 메시지를 본다 |
| 끈 세션의 system prompt에 auto memory 지시가 남는지 | subagent는 지시가 빠진다고 적혀 있다. 본 대화는 적혀 있지 않다 | 켠 세션과 끈 세션의 transcript에서 system prompt를 견준다 |
| 끈 세션에서 Claude가 기억 폴더의 파일을 file tool로 열거나 고칠 수 있는지 | "Claude doesn't read from or write to the auto memory directory"가 막는다는 뜻인지 시키지 않는다는 뜻인지 적혀 있지 않다 | 끈 세션에서 그 경로를 읽으라고 시켜 본다 |
| 끈 세션에서 사람이 기억하라고 말하면 Claude가 어디에 쓰는지 | 켠 세션에서는 auto memory에 쓴다고만 적혀 있다 | 끈 세션에서 말해 보고 바뀐 파일을 찾는다 |
| 세션 도중에 끄면 그 세션에 바로 걸리는지, 이미 load된 `MEMORY.md`가 context window에서 빠지는지 | settings 문서는 대부분의 key가 재시작 없이 걸린다고 적고, 세션 시작에만 읽는 key의 목록에 `autoMemoryEnabled`를 넣지 않았다. 그 목록은 다 적은 목록이 아니다 | 세션 도중에 끄고 `/context`를 다시 본다 |
| recall과 extraction이 무엇을 언제 하는지. Claude Code가 주제 파일을 골라 넣는지, 대화와 따로 기억을 쓰는지 | changelog에 이름만 나온다 | transcript와 `claude --debug`의 log를 본다 |
| `--resume` 때 `MEMORY.md`를 다시 읽는지 | 세션 시작, `/clear`, `/compact`만 적혀 있다 | `MEMORY.md`를 고친 뒤 resume하고 `/context`를 본다 |
| git 저장소 밖에서 "the project root"가 무엇인지 | 낱말만 적혀 있다 | git 저장소가 아닌 폴더 둘에서 세션을 열고 `/memory`가 여는 폴더를 본다 |
| user settings에 `autoMemoryDirectory`를 두면 모든 저장소가 폴더 하나를 같이 쓰는지 | "instead of the per-project default"까지만 적혀 있다 | 저장소 둘에서 `/memory`가 여는 폴더를 본다 |
| 세션 시작의 load를 알리는 줄이 터미널에 뜨는지 | 세션 도중의 읽기와 쓰기에 뜨는 줄만 적혀 있다 | 기억이 있는 저장소에서 세션을 열어 본다 |
| `InstructionsLoaded` hook이 `MEMORY.md`의 load에도 도는지 | CLAUDE.md와 `.claude/rules/*.md`만 적혀 있다 | hook을 걸고 세션을 열어 log를 본다 |
| 기억 파일 쓰기가 permission prompt를 띄우는지 | protected path의 예외라는 것까지만 적혀 있다 | `default` permission mode에서 기억하라고 말해 본다 |
| 25KB가 몇 byte인지 | 적혀 있지 않다 | 상한 언저리의 `MEMORY.md`로 세션을 열고 `/context`를 본다 |

## 새 질문 후보

- 끈 세션에서 system prompt의 auto memory 지시, 기억 폴더의 file tool 접근, "기억해"라는 말의 처리가 어떻게 되는가. 실행해서 확인해야 하고, auto memory를 언제 끄는가와 preamble의 글에 쓰인다.
- recall과 extraction이 무엇을 언제 하는가. auto memory와 견주는 테스트의 칸에 쓰인다.
- `MEMORY.md`의 내용이 system prompt에 드는가 대화 쪽에 드는가. `additionalContext`로 넣는 글과 놓이는 자리가 같은지에 쓰인다.
