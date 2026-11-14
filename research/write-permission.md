# 작업 폴더 밖 `~/.mem`에 쓸 때 Claude Code는 권한을 묻는가

설정이 없으면 Claude Code는 permission mode에 따라 사람에게 묻거나, classifier에게 넘기거나, 거부하고, `bypassPermissions`에서만 묻지 않고 실행한다. `~/.claude/settings.json`에서 `~/.mem`을 작업 폴더로 더하고 `Edit(~/.mem/**)` allow rule을 두면 `Write`와 `Edit`은 사람에게 묻지 않는다. `Bash`로 지우는 명령은 `Edit` allow rule이 덮지 않아서 따로 정해야 한다.

이 글은 issue #4 "작업 폴더 밖 `~/.mem`에 쓸 때 Claude Code는 권한을 묻는가"의 답이다. 2026-11-14에 Claude Code 공식 문서의 markdown 원문(문서 주소 끝에 `.md`를 붙인 주소)을 받아 읽고 썼다. Claude Code를 실행해서 확인한 것은 없고, 실행해야 갈리는 것은 #확인하지 못한 것에 모았다.

## 낱말

| 낱말 | 뜻 | 문서의 문장 |
|---|---|---|
| 작업 폴더 | Claude Code를 띄운 폴더와 거기에 더한 폴더. 문서는 working directories라고 부른다 | "By default, Claude has access to files in the directory where you launched it." ([permissions#working-directories](https://code.claude.com/docs/en/permissions#working-directories)) |
| permission mode | Claude가 세션에서 묻지 않고 할 수 있는 행동을 정하는 값 | "A permission mode sets which actions Claude can take in a session without asking you first." ([permission-modes](https://code.claude.com/docs/en/permission-modes)) |
| Manual | 설정값이 `default`인 permission mode | "Its config value is `default`" ([permission-modes#available-modes](https://code.claude.com/docs/en/permission-modes#available-modes)) |
| classifier | auto mode에서 사람 대신 행동을 검토하는 둘째 모델 | "In auto mode, a second model, the classifier, reviews actions instead of you" ([permission-modes](https://code.claude.com/docs/en/permission-modes)) |
| allow rule | 사람 승인 없이 tool을 쓰게 하는 permission rule | "Allow rules let Claude Code use the specified tool without manual approval." ([permissions#manage-permissions](https://code.claude.com/docs/en/permissions#manage-permissions)) |

## mode와 설정에 따른 결과

`Write`나 `Edit`으로 `~/.mem` 아래 파일을 쓰거나 고칠 때의 결과다. 칸마다 근거는 아래 절에 있다.

| 설정 | `default`(Manual) | `acceptEdits` | `auto` | `dontAsk` | `bypassPermissions` |
|---|---|---|---|---|---|
| 없음 | 사람에게 묻는다 | 사람에게 묻는다 | classifier가 정한다 | 거부한다 | 실행한다 |
| `~/.mem`을 작업 폴더로 더함 | 사람에게 묻는다 | 묻지 않고 실행한다 | 묻지 않고 실행한다(문서 두 문장을 이어 읽은 것) | 거부한다 | 실행한다 |
| `Edit(~/.mem/**)` allow rule | 묻지 않고 실행한다 | 묻지 않고 실행한다 | 묻지 않고 실행한다 | 실행한다 | 실행한다 |

`plan`에서는 어느 줄이든 고치지 못한다. `permissions.blockWritesOutsideWorkingDirectories`가 `true`면 첫 줄과 셋째 줄은 모든 mode에서 거부로 바뀐다(#길을 막는 설정).

`Bash`의 `rm`으로 `~/.mem` 아래 파일 하나를 지울 때의 결과다. `Edit` allow rule은 `Bash` 명령을 덮지 않아서 설정이 없는 줄과 같다.

| 설정 | `default`(Manual) | `acceptEdits` | `auto` | `dontAsk` | `bypassPermissions` |
|---|---|---|---|---|---|
| 없음 | 사람에게 묻는다 | 사람에게 묻는다 | classifier가 정한다 | 거부한다 | 실행한다 |
| `~/.mem`을 작업 폴더로 더함 | 사람에게 묻는다 | 묻지 않고 실행한다 | classifier가 정한다 | 거부한다 | 실행한다 |

## 세션이 시작하는 mode

기본 동작은 세션이 어느 mode로 시작하느냐에 달려 있다. Claude Code는 `--permission-mode` flag, settings 파일의 `permissions.defaultMode`, built-in default 순으로 처음 맞는 것을 쓴다([permission-modes#which-mode-a-session-starts-in](https://code.claude.com/docs/en/permission-modes#which-mode-a-session-starts-in)).

| 세션 | built-in default | 문서의 문장 |
|---|---|---|
| 터미널이나 VS Code에서 여는 대화형 세션 | `auto` | "With Claude Code v2.1.283 or later, auto mode is the built-in starting permission mode for interactive terminal and VS Code sessions." ([permission-modes](https://code.claude.com/docs/en/permission-modes)) |
| `claude -p`, Agent SDK | `default` | "In Claude Code v2.1.302 or later, `claude -p` and Agent SDK runs with no permission mode set start in Manual mode." ([permission-modes](https://code.claude.com/docs/en/permission-modes), Tool calls denied in `claude -p` and Agent SDK runs 절) |
| auto mode를 쓸 수 없는 세션 | `default` | "When the flag, a settings file, or the built-in default selects `auto` but auto mode isn't available to the session, Claude Code starts the session in Manual instead." ([permission-modes#which-mode-a-session-starts-in](https://code.claude.com/docs/en/permission-modes#which-mode-a-session-starts-in)) |

`claude -p`와 Agent SDK에는 물어볼 사람이 없어서, Claude Code는 승인이 필요한 호출을 묻는 대신 거부한다. 같은 절이 "Calls needing approval are denied unless you approve them with an allow rule, hook, `canUseTool` callback, or `--permission-prompt-tool`."이라고 적는다.

## 기본 동작

### `Write`와 `Edit`

| mode | 결과 | 문서의 문장 |
|---|---|---|
| `default` | 사람에게 묻는다 | Available modes 표에서 `default`가 묻지 않고 하는 일은 "Reads only"다([permission-modes#available-modes](https://code.claude.com/docs/en/permission-modes#available-modes)). Permission system 표의 File modification 줄은 Approval required 칸이 "Yes"다([permissions#permission-system](https://code.claude.com/docs/en/permissions#permission-system)) |
| `acceptEdits` | 사람에게 묻는다 | "Like file edits, auto-approval applies only to paths inside your working directory or `additionalDirectories`." 같은 절이 "These still prompt:" 아래에 "Paths outside that scope"를 든다([permission-modes#auto-approve-file-edits-with-acceptedits-mode](https://code.claude.com/docs/en/permission-modes#auto-approve-file-edits-with-acceptedits-mode)) |
| `plan` | 고치지 못한다 | "Except in interactive terminal sessions with bypass permissions available, edits stay blocked until you approve the plan." ([permission-modes#analyze-before-you-edit-with-plan-mode](https://code.claude.com/docs/en/permission-modes#analyze-before-you-edit-with-plan-mode)) |
| `auto` | 사람에게 묻지 않고 classifier가 정한다 | 결정 순서의 2번이 "Read-only actions and file edits in your working directory are auto-approved"이고 3번이 "Everything else goes to the classifier"다([permission-modes#how-the-classifier-evaluates-actions](https://code.claude.com/docs/en/permission-modes#how-the-classifier-evaluates-actions)) |
| `dontAsk` | 거부한다 | "If you set `dontAsk` mode, Claude Code auto-denies every tool call that would otherwise prompt you" ([permission-modes#allow-only-pre-approved-tools-with-dontask-mode](https://code.claude.com/docs/en/permission-modes#allow-only-pre-approved-tools-with-dontask-mode)) |
| `bypassPermissions` | 묻지 않고 실행한다 | "`bypassPermissions` mode disables permission prompts and safety checks so tool calls execute immediately" ([permission-modes#skip-all-checks-with-bypasspermissions-mode](https://code.claude.com/docs/en/permission-modes#skip-all-checks-with-bypasspermissions-mode)) |

Manual에서 사람이 prompt에 "Yes, and don't ask again"으로 답해도 file 승인은 그 세션에서 끝난다. "A file-modification approval isn't saved to the file: as the table shows, it lasts until the session ends." ([permissions#permission-system](https://code.claude.com/docs/en/permissions#permission-system))

`auto`에서 classifier가 `~/.mem` 쓰기를 통과시키는지는 문서로 갈리지 않는다. 작업 폴더 밖 로컬 파일에 쓰는 일이 classifier의 기본 허용 목록에도 기본 차단 목록에도 없기 때문이다.

- classifier가 믿는 범위. "By default, the classifier trusts only the working directory and the current repo's configured remotes." ([auto-mode-config](https://code.claude.com/docs/en/auto-mode-config))
- 기본 허용 목록의 파일 항목. "Local file operations in your working directory" ([permission-modes#what-the-classifier-blocks-by-default](https://code.claude.com/docs/en/permission-modes#what-the-classifier-blocks-by-default))

classifier가 막으면 그 호출은 실행되지 않는다. "If the classifier blocks, Claude receives the reason." ([permission-modes#how-the-classifier-evaluates-actions](https://code.claude.com/docs/en/permission-modes#how-the-classifier-evaluates-actions))

막힘이 쌓이면 Claude Code가 사람에게 묻는 방식으로 돌아간다. "if the classifier blocks an action 3 times in a row or 20 times total, auto mode pauses and Claude Code resumes prompting" ([permission-modes#when-auto-mode-falls-back](https://code.claude.com/docs/en/permission-modes#when-auto-mode-falls-back))

### `Bash`

Manual에서 `Bash` 명령 가운데 묻지 않는 것은 built-in read-only 명령뿐이다. Permission system 표의 Bash commands 줄은 Approval required 칸이 "Yes, except a built-in set of read-only commands"다([permissions#permission-system](https://code.claude.com/docs/en/permissions#permission-system)).

`rm`, `mv`, 쓰기 redirect는 그 집합에 들지 않는다. "The set includes `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, and read-only forms of `git`." ([permissions#read-only-commands](https://code.claude.com/docs/en/permissions#read-only-commands))

| 하는 일 | 문서가 적은 것 | 문서의 문장 |
|---|---|---|
| `rm`·`rmdir`·`mv`·`cp`·`mkdir`·`touch`·`sed` | `acceptEdits`가 묻지 않고 실행하지만 작업 폴더 안의 경로에만 그렇다. `~/.mem`은 밖이라서 묻는다 | "In addition to file edits, `acceptEdits` mode auto-approves common filesystem Bash commands: `mkdir`, `touch`, `rm`, `rmdir`, `mv`, `cp`, and `sed`." ([permission-modes#auto-approve-file-edits-with-acceptedits-mode](https://code.claude.com/docs/en/permission-modes#auto-approve-file-edits-with-acceptedits-mode)) |
| `> file`·`>> file` redirect | Claude Code가 redirect 대상을 `Edit` rule과 작업 폴더에 비추어 검사한다. `~`로 시작하는 대상은 승인이 필요하다 | "A target that starts with `~` or contains a glob character needs your approval." ([permissions#redirections](https://code.claude.com/docs/en/permissions#redirections)) |
| `tee` | `Bash(tee *)` allow rule은 작업 폴더 밖 대상을 덮지 않는다 | "An allow rule such as `Bash(tee *)` doesn't cover a destination outside the working directories." ([permissions#redirections](https://code.claude.com/docs/en/permissions#redirections)) |
| `auto`에서 이미 있던 파일을 지우기 | classifier의 기본 차단 목록에 든다 | "Irreversibly destroying files that existed before the session" ([permission-modes#what-the-classifier-blocks-by-default](https://code.claude.com/docs/en/permission-modes#what-the-classifier-blocks-by-default)) |

classifier의 차단 가운데 `soft_deny`에 든 것은 사람이 그 행동을 짚어서 시켰을 때 풀린다. "if the user's message directly and specifically describes the exact action Claude is about to take, the classifier allows it even when a `soft_deny` rule matches" ([auto-mode-config#override-the-block-and-allow-rules](https://code.claude.com/docs/en/auto-mode-config#override-the-block-and-allow-rules)) 같은 절이 "General requests don't count as explicit intent."라고 적는다. 위 표의 지우기 항목이 `soft_deny`에 드는지는 그 문서에 없다.

### 읽기

`Edit` tool의 조건에 read-before-edit가 있어서, 고치는 일에는 읽기 권한도 걸린다. "Claude reads the file in the current conversation before editing it" ([tools-reference#edit-tool-behavior](https://code.claude.com/docs/en/tools-reference#edit-tool-behavior)) 새 모델은 읽지 않은 파일도 고칠 수 있지만 그 조건이 읽기 권한이다. "Newer models can edit an unread file when reading it wouldn't need a permission prompt and the Read tool is available." (같은 절)

| mode | 작업 폴더 밖 읽기 | 문서의 문장 |
|---|---|---|
| `default` | 묻지 않는 범위가 작업 폴더 안으로 적혀 있다 | Permission system 표의 Read-only 줄은 Approval required 칸이 "No, within the working directory and additional directories"다([permissions#permission-system](https://code.claude.com/docs/en/permissions#permission-system)) |
| `auto` | 대화형 세션에서 처음 한 번 사람에게 묻는다 | "The first time Claude uses the Read, Grep, or Glob tool on a path outside them, Claude Code asks whether to allow that read." ([permission-modes#first-read-outside-the-working-directories](https://code.claude.com/docs/en/permission-modes#first-read-outside-the-working-directories)) |

`auto`의 그 prompt에서 사람이 "No, and block reads outside the working directories from now on"을 고르면 이후 모든 세션에서 작업 폴더 밖 읽기가 막힌다. "the read is refused, and Claude Code sets `permissions.blockReadsOutsideWorkingDirectories` to `true` in your user settings" (같은 절)

## 묻지 않게 하는 길

### 작업 폴더로 더하기

`~/.mem`을 작업 폴더로 더하는 방법은 셋이다. 세션을 띄울 때 주는 `--add-dir <path>`, 세션 안에서 치는 `/add-dir`, settings 파일의 `permissions.additionalDirectories`다([permissions#working-directories](https://code.claude.com/docs/en/permissions#working-directories)). 어느 저장소에서 연 세션에도 통하게 하려면 user settings인 `~/.claude/settings.json`에 둔다. 문서는 그 파일이 닿는 범위를 "You, in every project on this machine"이라고 적는다([settings#settings-files-and-who-they-affect](https://code.claude.com/docs/en/settings#settings-files-and-who-they-affect)).

이 길은 `~/.mem` 폴더 하나를 열고, 편집을 묻느냐는 mode에 맡긴다. "Files in additional directories follow the same permission rules as the original working directory: they become readable without prompts apart from the network path check, and file editing permissions follow the current permission mode." ([permissions#working-directories](https://code.claude.com/docs/en/permissions#working-directories)) 그래서 Manual에서는 `Write`와 `Edit`을 여전히 묻고, `acceptEdits`에서는 묻지 않는다.

`auto`에서 묻지 않는다는 것은 위 문장과 결정 순서 2번 "Read-only actions and file edits in your working directory are auto-approved"를 이어 읽은 것이다. 2번 문장은 더한 폴더를 따로 적지 않는다.

이 길에 따라오는 것은 다음과 같다.

| 따라오는 것 | 문서의 문장 |
|---|---|
| `acceptEdits`에서 `~/.mem` 안의 `rm`·`mv` 같은 명령도 묻지 않는다 | "Like file edits, auto-approval applies only to paths inside your working directory or `additionalDirectories`." ([permission-modes#auto-approve-file-edits-with-acceptedits-mode](https://code.claude.com/docs/en/permission-modes#auto-approve-file-edits-with-acceptedits-mode)) |
| sandbox를 켠 세션에서 sandboxed command가 `~/.mem`에 쓸 수 있다 | "By default, sandboxed commands can write to the current working directory, the per-user temp directory, and any directories you've added with `--add-dir`, `/add-dir`, or `permissions.additionalDirectories`." ([sandboxing](https://code.claude.com/docs/en/sandboxing), Configure sandboxing 절) |
| `rm -rf ~/.mem/*` 같은 glob 지우기가 critical path 지우기가 되어 allow rule로 승인되지 않는다 | critical path 목록의 한 줄이 "Your additional working directories and their parents, but only when the removal is a glob under one of them, such as `rm -rf <dir>/*`."다([permission-modes#which-paths-are-critical](https://code.claude.com/docs/en/permission-modes#which-paths-are-critical)). "no allow rule approves one whose target it recognizes as a critical path" ([permission-modes#critical-paths](https://code.claude.com/docs/en/permission-modes#critical-paths)) |
| settings 파일로 더한 폴더에서는 `.claude/` 설정이 load되지 않는다 | "Directories listed in `permissions.additionalDirectories` in a settings file grant file access only and don't load any of the configuration below." ([permissions#additional-directories-grant-file-access-not-configuration](https://code.claude.com/docs/en/permissions#additional-directories-grant-file-access-not-configuration)) |

두는 곳에 따라 걸리는 조건이 있다. 저장소의 `.claude/settings.json`에 둔 항목은 trust를 받은 뒤에만 통한다. "Like `allow` rules, entries in a project's `.claude/settings.json` take effect only after you accept the workspace trust dialog for that folder." ([settings-reference#permissions-additionaldirectories](https://code.claude.com/docs/en/settings-reference#permissions-additionaldirectories)) `--add-dir`는 폴더가 있어야 한다. "Validates that each path exists as a directory." ([cli-reference#cli-flags](https://code.claude.com/docs/en/cli-reference#cli-flags))

### `Edit` allow rule

`permissions.allow`에 `Edit(~/.mem/**)`를 두면 `~/.mem` 아래 경로에 대한 `Edit`·`Write`·`NotebookEdit` 호출만 승인 없이 실행된다. rule은 `Write(...)`가 아니라 `Edit(...)`로 적어야 맞는다.

| 문법 | 문서의 문장 |
|---|---|
| `Edit` rule이 파일을 고치는 built-in tool 전부에 걸린다 | "`Edit` rules apply to all built-in tools that edit files." ([permissions#read-and-edit](https://code.claude.com/docs/en/permissions#read-and-edit)) |
| `Write(path)` rule은 맞지 않는다 | "use `Edit(docs/**)` in place of `Write(docs/**)`" ([permissions#read-and-edit](https://code.claude.com/docs/en/permissions#read-and-edit)) |
| `~/path`는 home에서 시작하는 경로다 | 경로 pattern 표의 `~/path` 줄이 "Path from home directory"다([permissions#read-and-edit](https://code.claude.com/docs/en/permissions#read-and-edit)) |
| user settings에서는 `~/`나 `//`로 적는다 | "To write a rule in user settings that applies inside every project, use a `//` absolute path or a `~/` home-relative path instead." ([permissions#read-and-edit](https://code.claude.com/docs/en/permissions#read-and-edit)) |
| `**`가 하위 폴더까지 맞는다 | "In gitignore patterns, `*` matches within a single path segment and can appear at any position in the pattern, while `**` matches across directories." ([permissions#read-and-edit](https://code.claude.com/docs/en/permissions#read-and-edit)) |
| 같은 경로의 읽기도 함께 열린다 | "An `Edit(...)` allow rule also grants read access to the same path, so you don't need a matching `Read(...)` rule." ([tools-reference#configure-tools-with-permission-rules-and-hooks](https://code.claude.com/docs/en/tools-reference#configure-tools-with-permission-rules-and-hooks)) |

이 rule은 mode를 가리지 않는다. `auto`에서는 classifier 앞에서 끝난다. 결정 순서의 1번이 "Actions matching your allow, ask, or deny rules resolve immediately, with these exceptions:"이고, 그 예외에 `~/.mem` 같은 보통 경로의 쓰기는 없다([permission-modes#how-the-classifier-evaluates-actions](https://code.claude.com/docs/en/permission-modes#how-the-classifier-evaluates-actions)). `dontAsk`에서도 실행된다. "Actions matching your `permissions.allow` rules and calls approved by a PreToolUse hook run too." ([permission-modes#allow-only-pre-approved-tools-with-dontask-mode](https://code.claude.com/docs/en/permission-modes#allow-only-pre-approved-tools-with-dontask-mode))

모든 저장소에 통하게 하려면 user settings에 둔다. "To apply permission rules across all your projects, add them to your user settings instead: `~/.claude/settings.json`, or `$CLAUDE_CONFIG_DIR/settings.json` when `CLAUDE_CONFIG_DIR` is set." ([permissions#when-your-local-settings-file-needs-trust](https://code.claude.com/docs/en/permissions#when-your-local-settings-file-needs-trust)) 한 세션에만 주려면 `--allowedTools`에 같은 rule을 준다. "`--allowedTools` adds allow rules for one session" ([settings-reference#permissions-allow](https://code.claude.com/docs/en/settings-reference#permissions-allow))

이 rule이 덮지 못하는 것은 둘이다.

- `Bash` 명령. `rm`이나 `mv`는 `Bash` rule이나 mode가 정한다. 문서는 `Bash` rule의 `*`가 공백까지 맞고, 인자를 좁히려는 pattern이 깨지기 쉽다고 적는다. "A `*` in a Bash rule matches any text, including spaces, so one rule covers a family of commands." ([permissions#wildcard-patterns](https://code.claude.com/docs/en/permissions#wildcard-patterns)) "Bash permission patterns that try to constrain command arguments are fragile." ([permissions#read-only-commands](https://code.claude.com/docs/en/permissions#read-only-commands))
- symlink를 거치는 경로. allow rule은 "apply only when both the requested path and the file it resolves to match"다([permissions#symlinks](https://code.claude.com/docs/en/permissions#symlinks)). `~/.mem`이 다른 곳을 가리키는 symlink면 rule이 맞지 않는다.

### permission mode 바꾸기

mode는 세션 전체에 걸려서, `~/.mem`만 열지 않고 그 세션의 다른 일도 함께 연다.

| mode | `~/.mem`에서 묻지 않게 되는 것 | 함께 열리는 것 |
|---|---|---|
| `acceptEdits` | `~/.mem`을 작업 폴더로 더했을 때의 `Write`·`Edit`과 `rm`·`mv` 같은 7개 명령 | 세션을 연 저장소의 file edit과 같은 7개 명령 |
| `auto` | 사람에게 묻는 일. classifier가 대신 정한다 | classifier가 통과시키는 모든 행동 |
| `bypassPermissions` | 모든 호출 | 모든 호출. 문서는 "Only use this mode in isolated environments like containers or VMs where Claude Code can't cause damage."라고 경고한다([permissions#permission-modes](https://code.claude.com/docs/en/permissions#permission-modes)) |

시작 mode는 `permissions.defaultMode`로 정한다. "`auto` and `bypassPermissions` don't take effect from project or local settings, so set them in `~/.claude/settings.json` instead." ([settings-reference#permissions-defaultmode](https://code.claude.com/docs/en/settings-reference#permissions-defaultmode))

`auto`에서는 `autoMode` 설정으로 classifier에게 규칙을 더할 수 있다. `autoMode.allow`는 "exceptions to soft block rules"이고, 항목은 "an array of prose descriptions, read as natural-language rules"다([auto-mode-config#override-the-block-and-allow-rules](https://code.claude.com/docs/en/auto-mode-config#override-the-block-and-allow-rules)). 이 key는 user settings에 둔다. "The classifier doesn't read `autoMode` from project settings in `.claude/settings.json` or `.claude/settings.local.json`." ([auto-mode-config](https://code.claude.com/docs/en/auto-mode-config), Where the classifier reads configuration 절)

### hook으로 승인하기

hook 스크립트가 고른 호출만 승인하므로, 범위는 스크립트가 정한다.

| hook | 하는 일 | 문서의 문장 |
|---|---|---|
| `PreToolUse` | `permissionDecision`으로 `"allow"`를 돌려주면 prompt를 건너뛴다 | `"allow"`는 "skips the permission prompt, except for actions no mode auto-approves and reads from network paths"다([hooks#pretooluse-decision-control](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)) |
| `PermissionRequest` | prompt가 뜨려는 순간에 사람 대신 답한다 | "Runs when Claude Code is about to ask you for permission to use a tool." ([hooks#permissionrequest](https://code.claude.com/docs/en/hooks#permissionrequest)) |

hook이 경로를 가릴 때 쓸 값은 절대 경로로 온다. "For the file tools `Write`, `Edit`, and `Read`, `tool_input.file_path` is always absolute:" ([hooks#pretooluse-input](https://code.claude.com/docs/en/hooks#pretooluse-input))

hook의 승인은 deny rule과 ask rule을 이기지 못한다. "Deny and ask rules are still evaluated regardless of what the hook returns" ([hooks#pretooluse-decision-control](https://code.claude.com/docs/en/hooks#pretooluse-decision-control)) `plan`에서는 통하지 않는다. "In plan mode, apart from `ExitPlanMode`, your `PreToolUse` hook's `"allow"` has no effect on a file edit or another call that isn't read-only." ([permissions#hook-approvals-in-plan-mode](https://code.claude.com/docs/en/permissions#hook-approvals-in-plan-mode))

### sandbox auto-allow mode

이 길은 shell 명령에만 통하고, `~/.mem`만 열지 않고 sandbox 안에서 도는 `Bash` 명령 전부를 묻지 않게 한다. sandbox는 shell 명령이 닿는 파일과 network를 운영체제가 막는 경계이고, 기본값은 꺼짐이다. "The sandbox is off by default." ([sandboxing](https://code.claude.com/docs/en/sandboxing), What the sandbox restricts 절)

| 설정 | 하는 일 | 문서의 문장 |
|---|---|---|
| `sandbox.enabled`와 `sandbox.autoAllowBashIfSandboxed` | sandboxed `Bash` 명령을 묻지 않고 실행한다 | "When you enable sandboxing and set `sandbox.autoAllowBashIfSandboxed` to `true`, sandboxed Bash commands run without prompting." ([permissions](https://code.claude.com/docs/en/permissions), How permissions interact with sandboxing 절) |
| `sandbox.filesystem.allowWrite` | sandboxed command가 쓸 수 있는 경로를 더한다 | "If subprocess commands like `kubectl`, `terraform`, or `npm` need to write outside those directories, use `sandbox.filesystem.allowWrite` to grant access to specific paths:" ([sandboxing](https://code.claude.com/docs/en/sandboxing), Configure sandboxing 절) |

`Write`와 `Edit`은 이 길로 열리지 않는다. "The sandbox covers shell commands only. Claude's file tools, MCP servers, and hooks run outside it." ([sandboxing](https://code.claude.com/docs/en/sandboxing)) Linux와 WSL2에서는 준비물과 조건이 있다. "the sandbox relies on `bubblewrap` and `socat`" (같은 문서, Get started 절) "On Linux and WSL2, an entry for a path that doesn't exist yet has no effect, so create the path first." (같은 문서, Configure sandboxing 절)

## 길을 막는 설정

| 설정 | 막는 것 | 통과하는 길 | 문서의 문장 |
|---|---|---|---|
| `permissions.blockWritesOutsideWorkingDirectories` | 모든 mode에서 `Write`·`Edit`·`NotebookEdit`의 작업 폴더 밖 쓰기. allow rule로는 통과하지 못한다 | user settings의 `additionalDirectories`, `--add-dir`, `/add-dir` | "No allow rule lets Claude's file tools through either block." ([settings-reference#let-one-directory-through-the-read-or-write-block](https://code.claude.com/docs/en/settings-reference#let-one-directory-through-the-read-or-write-block)) |
| deny rule과 ask rule | 맞는 호출. allow rule보다 먼저 판정된다 | 없음. 그 rule을 지워야 한다 | "Rules are evaluated in order: deny, then ask, then allow." ([permissions#manage-permissions](https://code.claude.com/docs/en/permissions#manage-permissions)) |
| 경로를 덮는 `Read` deny rule | 그 경로의 `Edit`과 `Write` | 없음 | "A `Read` deny rule also blocks the Edit and Write tools on the same path, including creating a new file there." ([permissions#read-and-edit](https://code.claude.com/docs/en/permissions#read-and-edit)) |
| `allowManagedPermissionRulesOnly` | user settings의 allow rule | 조직의 managed settings만 정한다 | "Claude Code then ignores `allow`, `ask`, and `deny` rules in user, project, local, and `--settings` files" ([settings-reference#allowmanagedpermissionrulesonly](https://code.claude.com/docs/en/settings-reference#allowmanagedpermissionrulesonly)) |
| `permissions.denyInsteadOfPrompting` | prompt가 뜰 호출. 묻는 대신 거부한다 | allow rule, mode, classifier의 승인 | "A call goes ahead if an allow rule, your permission mode, or auto mode's classifier approves it." ([settings-reference#permissions-denyinsteadofprompting](https://code.claude.com/docs/en/settings-reference#permissions-denyinsteadofprompting)) |

`blockWritesOutsideWorkingDirectories`는 저장소가 제 설정으로 켤 수 있다. "A `true` in any file the session loads applies, so a repository can turn the block on for itself but can't lift yours." ([settings-reference#permissions-blockwritesoutsideworkingdirectories](https://code.claude.com/docs/en/settings-reference#permissions-blockwritesoutsideworkingdirectories)) 그런 저장소에서 연 세션에서도 `~/.mem`에 쓰게 하는 길은 user settings의 `additionalDirectories`다. 저장소 설정으로만 더한 폴더는 통과하지 못한다. 같은 문서가 block이 거부하는 것으로 "A directory that only repository settings add"를 든다([settings-reference#what-the-write-block-refuses-and-what-stays-writable](https://code.claude.com/docs/en/settings-reference#what-the-write-block-refuses-and-what-stays-writable)).

deny rule은 어느 settings 파일에 있어도 user settings의 allow rule을 이긴다. "if user settings allow a permission and project settings deny it, the deny rule blocks it" ([permissions#settings-precedence](https://code.claude.com/docs/en/permissions#settings-precedence))

`~/.mem`은 protected path 목록에 없다. 그 목록은 `.git`, `.claude` 같은 이름을 들고, allow rule로 열리지 않는다. "`permissions.allow` rules in settings files do not pre-approve protected-path writes." ([permission-modes#protected-paths](https://code.claude.com/docs/en/permission-modes#protected-paths)) `~/.mem`을 git 저장소로 만들면 그 안의 `.git`은 이 목록에 든다.

Claude Code의 auto memory 폴더는 이 검사들에서 예외로 적혀 있고, `~/.mem`은 그런 예외가 없다. protected path의 예외 목록에 "Markdown files in the project's auto memory directory, such as `~/.claude/projects/<project>/memory/`, in a session started without `--restricted`"가 있다([permission-modes#protected-paths](https://code.claude.com/docs/en/permission-modes#protected-paths)).

## hook이 직접 읽고 쓰는 것

permission 검사는 Claude가 부르는 tool call에 걸리고, hook이 돌리는 프로그램에는 걸리지 않는 것으로 문서에 적혀 있다. sandbox 문서는 hook 프로그램이 사용자 권한 그대로 돈다고 적는다. "command hooks, local MCP servers, plugin monitors, LSP servers, and helper commands such as your status line command and `apiKeyHelper` run with your full access" ([sandboxing#what-runs-outside-the-sandbox](https://code.claude.com/docs/en/sandboxing#what-runs-outside-the-sandbox))

write block도 hook 프로그램을 막지 않는다. "The key doesn't limit shell commands, MCP tools, or the programs hooks run." ([settings-reference#permissions-blockwritesoutsideworkingdirectories](https://code.claude.com/docs/en/settings-reference#permissions-blockwritesoutsideworkingdirectories)) 그래서 `mem-hook`이 `~/.mem`을 읽어 load하거나 log에 덧붙이는 일은 이 글이 다룬 prompt의 대상이 아니다.

## 확인하지 못한 것

아래는 문서로 갈리지 않았다. issue #5 "임시 세션에 hook을 걸어 README가 기대는 동작을 실제로 본다"에서 해 볼 것을 함께 적는다.

| 확인하지 못한 것 | 문서가 적은 데까지 | 해 볼 것 |
|---|---|---|
| `auto`에서 classifier가 `~/.mem`의 `Write`·`Edit`·`rm`을 통과시키는가 | classifier는 작업 폴더만 믿고, 작업 폴더 밖 로컬 파일 쓰기는 기본 허용 목록에도 기본 차단 목록에도 없다 | `claude auto-mode defaults`로 built-in rule 전문을 읽는다. 설정 없는 `auto` 세션에서 사람이 시킨 쓰기·고치기·지우기와 에이전트가 스스로 하는 save를 각각 해 본다 |
| 작업 폴더로 더한 `~/.mem`의 file edit이 `auto`에서 classifier 없이 실행되는가 | 더한 폴더가 "the same permission rules as the original working directory"를 따른다는 문장과 결정 순서 2번을 이어 읽었다 | `additionalDirectories`만 둔 `auto` 세션에서 `Write`를 시키고 classifier 검토가 있었는지 본다 |
| `additionalDirectories`에 `~/.mem` 철자가 통하는가 | 문서의 예시는 `"../docs/"`뿐이고 Type은 "array of directory paths"다. `autoMemoryDirectory`는 "an absolute or `~/`-prefixed directory path"라고 따로 적는다 | `~/.mem`과 절대 경로를 각각 넣어 본다. 폴더가 아직 없을 때 항목이 어떻게 되는지도 본다 |
| `Edit(~/.mem/**)` allow rule 하나로 Manual의 prompt와 `auto`의 첫 읽기 prompt가 모두 사라지는가 | allow rule이 승인 없이 tool을 쓰게 하고, `Edit` allow rule이 읽기도 연다고 적혀 있다 | rule만 둔 Manual 세션과 `auto` 세션에서 읽기·쓰기·고치기를 시킨다 |
| `rm`을 `~/.mem` 아래로 좁힌 `Bash` allow rule이 작업 폴더 밖 대상에도 통하는가 | 문서는 `tee`와 redirect에 대해서만 allow rule이 작업 폴더 밖 대상을 덮지 않는다고 적는다 | rule을 두고 Manual 세션에서 `~/.mem`의 파일 하나를 지우게 한다 |
| `PreToolUse` hook의 `"allow"`가 `auto`에서 classifier 검토도 건너뛰는가 | 문서는 "skips the permission prompt"라고만 적는다 | `~/.mem` 경로에 `"allow"`를 돌려주는 hook을 걸고 `auto` 세션에서 본다 |
| `~`로 시작하는 redirect 대상이 mode마다 어떻게 처리되는가 | "needs your approval"이라고만 적혀 있다 | `echo x > ~/.mem/t.md`를 mode마다 시킨다 |
| Manual에서 file prompt의 세션 승인이 작업 폴더 밖 경로에도 걸리는가 | 승인이 "lasts until the session ends"라고만 적혀 있다 | 한 번 승인한 뒤 `~/.mem`의 다른 파일을 쓰게 한다 |

문서가 version을 걸어 둔 동작이 있어서, 해 볼 때는 Claude Code version을 함께 적는다. built-in default가 `auto`인 것은 v2.1.283부터이고, `permissions.blockWritesOutsideWorkingDirectories`는 "Requires Claude Code v2.1.314 or later."다([settings-reference#permissions-blockwritesoutsideworkingdirectories](https://code.claude.com/docs/en/settings-reference#permissions-blockwritesoutsideworkingdirectories)).

## 출처

모두 Claude Code 공식 문서이고 2026-11-14에 받았다.

| 문서 | 주소 |
|---|---|
| Configure permissions | https://code.claude.com/docs/en/permissions |
| Choose a permission mode | https://code.claude.com/docs/en/permission-modes |
| Settings files and precedence | https://code.claude.com/docs/en/settings |
| All settings | https://code.claude.com/docs/en/settings-reference |
| Configure auto mode | https://code.claude.com/docs/en/auto-mode-config |
| Configure the sandboxed Bash tool | https://code.claude.com/docs/en/sandboxing |
| Hooks reference | https://code.claude.com/docs/en/hooks |
| Tools reference | https://code.claude.com/docs/en/tools-reference |
| CLI reference | https://code.claude.com/docs/en/cli-reference |
