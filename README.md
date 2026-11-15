# agent-memory-layer

코딩 에이전트가 쓰는 기억을 harness 밖의 markdown 파일에 두고, 세션을 연 폴더에 맞는 layer와 그것을 품는 layer의 기억만 load하는 도구다. harness는 모델을 감싸 도구·hook·context를 붙여 주는 프로그램이고, 여기서는 Claude Code와 Codex를 말한다. hook은 harness가 정해진 시점에 부르는 스크립트다. layer는 기억 파일이 놓이는 폴더 하나다. 이 도구는 아직 만들지 않았다.

## 문제

에이전트가 기억을 쓰는 방식에서 두 가지가 걸린다.

- **범위가 맞지 않는다.** 회사 일, 오픈소스 기여처럼 저장소 여럿이 묶이는 일을 이 글에서는 **맥락**이라고 부른다. Claude Code의 auto memory는 저장소마다 기억을 갈라서, 저장소를 넘는 사실이 다른 저장소의 기억에만 있으면 load되지 않는다. 반대로 에이전트가 한 맥락의 세션에서 다른 맥락의 이야기를 꺼내 온 적이 있지만, 그 이야기가 기억에서 왔는지는 확인하지 못했다.
- **세션 시작에 무엇이 load됐는지 보이지 않는다.** 사람이 묻지 않으면 이번 세션에서 에이전트가 어떤 기억을 받았는지 알 수 없다.

## 만들 것

작업 위치로 target layer를 찾아, target layer와 그것을 품는 layer의 기억만 load하는 hook 스크립트 하나(`mem-hook`)다. 상주 프로세스 없이 파일만 읽고 쓴다. Claude Code부터 만든다.

작업 위치는 세션을 연 폴더다. layer는 다른 layer 안에 놓일 수 있다. target layer는 작업 위치에 맞는 layer 가운데 가장 안쪽 layer다. 전역은 가장 바깥 layer여서 모든 세션이 전역을 받는다.

도구가 이 구조여야 하는 까닭을 만든 사람이 직접 세워 보며 이해하는 것이 이 프로젝트의 목적이어서, 기억을 markdown으로 두는 기존 오픈소스를 쓰지 않고 직접 만든다.

## 기능

가장 작은 것부터 만들고 한 단계씩 얹는다. 단계마다 그 단계에서 조용히 일어날 실패를 보이는 줄을 같이 얹는다. 먼저 만드는 것은 1단계뿐이다.

| 단계 | 하는 일 | 같이 보이는 줄 |
|---|---|---|
| 1. load | 작업 위치로 target layer를 찾아, target layer와 그것을 품는 layer의 기억을 세션 시작과 compaction 뒤에 load한다 | 세션 시작 줄: `실림: style.md, work/api-naming.md (1,240자)` |
| 2. save | 에이전트가 배운 것을 묻지 않고 save한다. 쓰기 전에 쓸 layer에서 같은 것을 먼저 찾는다 | log: 쓰기마다 한 줄 |
| 3. decision | decision은 고치지 않고 새 파일로 쌓는다. 옛 decision은 load하지 않는 자리로 옮긴다 | log에 남는 옮긴 줄 |
| 4. split | 넘치면 layer 안에 더 좁은 layer를 두고 거기에만 맞는 항목을 옮겨, layer를 split한다 | 세션 시작 줄의 넘음 표시 |

겨누는 크기는 만든 사람 자신이 auto memory를 끄고 이 도구로 일하는 것이다. 1단계는 다른 맥락의 기억이 load되지 않는지를 기존 auto memory와 견주어 판정한다. 2단계부터의 판정은 그 단계를 얹을 때 정한다.

## 설계와 까닭

### 모양과 규칙을 고르는 기준

전역과 그 안에 놓인 layer 전부를 layer tree라고 부른다. layer tree는 `~/.mem`에 놓이고, `~/.mem`에 다른 이름은 붙이지 않는다. layer 규칙은 작업 위치를 layer에 잇는 규칙이다. layer tree의 모양과 layer 규칙은 아래 기준으로 고른다. 후보는 기준마다 통과하거나 실패한다.

1. layer에 놓인 md 파일은 전부 load되고, md가 아닌 파일은 세션 시작 줄에 이름이 뜬다. 그래서 layer 바로 아래의 파일 목록은 그 layer에서 load된 목록과 세션 시작 줄에 뜬 이름을 합친 것과 같다. layer 규칙 파일과 log처럼 도구가 쓰는 파일은 layer가 아닌 자리에 있다. hook이 파일을 말없이 빼면 놓인 곳과 load되는 곳이 달라지기 때문이다.
2. 세션은 target layer와 그것을 품는 layer를 전부 받는다. 여럿이 걸릴 때 우선순위로 가리거나 빼는 규칙이 없다. target layer만 load하면 저장소를 넘는 사실을 둘 자리가 없기 때문이다. 넓은 layer에 남긴 항목이 target layer가 더 좁은 세션에서 빠지면 세션 시작 줄에 보이지 않지만, 받는 글이 늘어나는 것은 넘음 표시로 보인다.
3. 사람이 작업 위치와 규칙만 읽고, hook을 돌리지 않고 어느 layer가 load될지 맞힌다.
4. 2~4단계를 얹을 때 load 규칙을 고치지 않는다. 뒤 단계는 파일과 폴더를 더하거나 항목을 옮기기만 한다. 1단계의 판정이 load 규칙에 걸려 있어서, load 규칙이 바뀌면 auto memory와 견준 결과를 다시 봐야 하기 때문이다.
5. hook은 뼈대만 안다. layer의 이름, 경로, 깊이는 사람이 정하는 값이고, 사람이 정한 이름이 도구가 정한 이름과 부딪힐 수 없다.
6. layer tree를 통째로 다른 기기에 놓아도 그대로 쓴다. 기기마다 다른 값은 layer tree 밖 한 곳에만 있다.
7. 새 경우를 담으려고 우선순위나 예외 규칙을 더해야 하면, 더하기 전에 구조를 다시 본다. 우선순위와 예외가 늘어나는 것은 구조가 풀 수 없는 문제를 규칙으로 풀려는 신호로 보기 때문이다. 이 문턱은 구조를 몇 번 열어 본 뒤에 고칠 수 있다.

### layer tree 모양

`~/.mem`이 곧 전역이다. `~/.mem` 바로 아래의 md 파일은 전역의 항목이고, `~/.mem` 아래의 폴더는 전부 사람이 이름 붙인 layer다. 좁은 layer는 넓은 layer 안에 놓여서, layer tree는 폴더 tree 하나를 이룬다. 아래 그림에서 `work`·`api`·`web`과 파일 이름은 예시다.

```
~/.mem/
  a.md              전역
  work/b.md         전역 안에 놓인 layer
  work/api/c.md     work 안에 놓인 layer
  work/web/d.md     work 안에 놓인 layer
```

hook은 target layer와 그것을 품는 layer의 md 파일을 전부 load하고, target layer 안에 놓인 layer는 load하지 않는다. target layer가 `work/api`인 세션은 `a.md`·`b.md`·`c.md`를 받고, target layer가 `work`인 세션은 `a.md`·`b.md`만 받는다.

항목 하나는 md 파일 하나이고 제목은 파일 이름이다. 범위는 항목이 놓인 layer가 정한다.

layer의 이름과 깊이는 사람이 정하고, 저장소 하나에만 맞는 layer도 둘 수 있다. layer 여럿에 걸치는 사실은 그 layer를 모두 품는 layer에 둔다.

`~/.mem` 안에는 layer만 놓이고 도구가 정한 이름은 `~/.mem` 안에 없어서, 사람이 정한 이름이 도구가 정한 이름과 부딪힐 자리가 없다.

도구가 쓰는 파일과 대체된 decision을 옮겨 둘 자리는 layer tree 밖에 둔다.

| layer tree 밖에 두는 것 | 경로 |
|---|---|
| layer 규칙 파일 | `~/.mem-hook/layer-rules` |
| log | 2단계를 얹을 때 정한다 |
| 대체된 decision을 옮겨 둘 자리 | 3단계를 얹을 때 정한다 |

기기마다 다른 값은 layer tree 밖에만 둔다. 1단계에서 기기마다 다른 값은 layer 규칙 파일에만 있다.

대체된 decision을 기억과 한 폴더로 옮겨야 하거나 `~/.mem` 바로 아래에 항목이 아닌 파일을 둬야 하면, #모양과 규칙을 고르는 기준의 7번에 따라 모양을 다시 본다.

### layer 규칙

layer 규칙은 `~/.mem-hook/layer-rules` 파일 하나에 `<layer>: <경로>` 줄로 적는다. hook은 작업 위치를 품는 경로의 줄을 전부 찾고, 그 줄들이 가리키는 layer 가운데 가장 안쪽 layer를 target layer로 삼는다. 줄이 잇는 곳이 언제나 layer여서 이 규칙을 layer 규칙이라고 부른다.

아래에서 `work`·`work/api`와 경로는 예시다.

```
work: ~/workspace/work
work: /mnt/c/workspace/work
work/api: ~/workspace/work/api-server
```

| 세션을 연 폴더 | 맞는 layer | target layer | 세션이 받는 layer |
|---|---|---|---|
| `~/workspace/work/api-server/src` | `work`, `work/api` | `work/api` | 전역, `work`, `work/api` |
| `~/workspace/work/web` | `work` | `work` | 전역, `work` |
| `/mnt/c/workspace/work/web` | `work` | `work` | 전역, `work` |
| `~/workspace/work-old` | 전역뿐이다 | 전역 | 전역 |
| `~/notes` | 전역뿐이다 | 전역 | 전역 |

작업 위치는 세션을 연 폴더다. 그래서 target layer가 세션 내내 같고, 사람이 세션을 연 폴더만 알면 load될 layer를 맞힌다. 이 도구는 Claude Code 밖에서도 쓸 것이어서, 작업 위치의 뜻에는 harness가 붙인 이름을 넣지 않는다.

Claude Code에서 hook은 작업 위치를 환경 변수 `CLAUDE_PROJECT_DIR`에서 읽고, hook 입력의 `cwd`는 쓰지 않는다. `cwd`는 Claude가 `cd`하면 옮긴 폴더를 따라가서, `cwd`로 읽으면 compaction 뒤에 target layer가 바뀌기 때문이다.

Claude Code의 hooks 문서는 `CLAUDE_PROJECT_DIR`을 "the project root where the session started"라고 적고, `cwd`를 "Current working directory when the hook is invoked"라고 적는다. `SessionStart` hook의 입력 JSON에 세션을 연 폴더를 주는 필드는 그 문서의 필드 목록에 없다.

layer는 `~/.mem` 안의 폴더 경로여서 `work/api`는 `~/.mem/work/api/`다. 한 줄에 경로 하나를 적고, layer 하나에 경로가 여럿이면 같은 layer로 줄을 여럿 쓴다. 전역은 줄에 적지 않는다.

경로는 `/`나 `~`로 시작한다. 줄에는 symlink를 지나지 않는 실제 경로만 적는다. hook은 줄 머리의 `~`를 home의 실제 경로로 푼다. 끝의 `/`는 있어도 없어도 같다. hook은 대소문자를 가른다. 이 기기에 없는 경로를 적은 줄은 어떤 세션에도 맞지 않는다.

작업 위치가 줄의 경로와 같거나 그 아래에 있으면 그 줄의 layer가 작업 위치에 맞는다. hook은 폴더 이름 단위로 맞춰서 `~/workspace/work`는 `~/workspace/work-old`에 맞지 않는다. 전역은 모든 작업 위치에 맞아서, 맞는 줄이 없으면 target layer는 전역이다.

hook은 가장 안쪽 layer를 찾을 때 경로의 길이를 견주지 않는다. 그래서 경로가 더 좁은 줄이 더 넓은 layer를 가리키면, 그 줄은 load되는 것을 바꾸지 않는다.

줄의 순서에는 뜻이 없다. hook은 빈 줄을 건너뛴다. 주석은 없고, 줄에 까닭을 적어야 할 일이 생기면 hook이 `#`로 시작하는 줄을 건너뛰게 한다.

| 규칙 | 값 | 까닭 |
|---|---|---|
| 파일의 자리 | `~/.mem-hook/layer-rules` | `~/.mem` 옆에 놓여서 `ls -a ~`에서 함께 보인다. `~/.config` 아래에 두면 `XDG_CONFIG_HOME`을 따를지를 더 정해야 하고, 따르면 환경에 따라 자리가 달라진다 |
| 줄의 형식 | `<layer>: <경로>`. hook은 줄에서 처음 나오는 `: `(colon과 빈칸)에서 줄을 가르고, 그 뒤는 전부 경로로 읽는다 | 줄이 늘어나면 짧은 layer가 앞에 있는 쪽이 읽기 좋다. 경로를 뒤에 두면 경로에 빈칸이나 colon이 있어도 따옴표 없이 적는다 |
| symlink | hook은 줄 머리의 `~`를 푸는 것 말고는 줄의 경로를 바꾸지 않고 작업 위치와 글자로 견준다 | Claude Code가 hook에 주는 작업 위치는 symlink를 푼 실제 경로다. 줄에도 실제 경로만 있으면 사람이 줄과 작업 위치를 글자로만 견주어 맞힌다. 경로가 symlink를 지나는 줄을 hook이 가려내지 않고 글자로만 견주면, 그 줄은 말없이 맞지 않는다. hook이 `~`를 home의 실제 경로로 풀지 않으면, home이 symlink 뒤에 있는 기기에서 `~`로 시작하는 줄 가운데 이 기기에 있는 경로를 적은 줄이 전부 읽지 못하는 줄이 된다 |
| 맞는 layer가 서로 품지 않을 때 | hook은 고르지 않는다. 전역만 load하고 실패를 알린다 | 경로가 긴 줄이 이기게 하면 우선순위 규칙이 하나 생기고, 넓은 줄의 layer가 빠진다. 맞는 layer를 전부 load하면 target layer가 둘이 되어 save할 곳을 가를 수 없다 |
| 읽지 못하는 줄이 있을 때 | 하나라도 있으면 hook은 `layer-rules` 전체를 쓰지 않는다. 전역만 load하고 실패를 알린다 | 그 줄만 건너뛰면, 읽지 못한 줄이 이 세션에 맞는 줄이었는지 hook이 알 수 없어서 줄 하나가 빠진 채로 다른 target layer를 고를 수 있다 |
| `layer-rules`가 없을 때 | 줄이 하나도 없는 것과 같아서 hook은 전역만 load하고, 실패로 보지 않는다 | `layer-rules`가 없는 것은 처음 설치한 기기의 상태다 |
| 줄이 가리키는 layer의 폴더가 `~/.mem`에 없을 때 | hook은 빈 layer로 본다. 그때 target layer는 그 layer이고 load할 파일이 없을 뿐이다. hook은 폴더를 만들지 않는다 | layer 폴더가 없는 것은 첫 기억을 쓰기 전인 layer의 상태다 |

읽지 못하는 줄은 `: `가 없는 줄, layer가 비었거나 `~/.mem` 밖을 가리키는 줄(`/`로 시작하거나 `..`가 든 것), 경로가 `/`나 `~`로 시작하지 않는 줄, 경로가 symlink를 지나는 줄이다. hook은 `~`를 풀고 끝의 `/`를 뗀 경로를 symlink까지 풀어 보고, 풀어 본 경로가 풀어 보기 전의 경로와 다르면 그 경로가 symlink를 지난다고 본다. hook은 이 기기에 없는 경로를 풀어 보지 않아서, 없는 경로를 적은 줄은 symlink 때문에 읽지 못하는 줄이 되는 일이 없고 어떤 세션에도 맞지 않는 줄로 남는다. 작업 위치는 이 기기에 있는 폴더여서, 없는 경로를 적은 줄은 symlink를 지나든 아니든 맞을 세션이 없기 때문이다.

맞는 layer가 서로 품지 않는 예시는 아래 두 줄이다. `~/workspace/work/shared-lib`에서 연 세션에는 `work`와 `oss/lib`이 맞고, 어느 쪽도 다른 쪽을 품지 않는다.

```
work: ~/workspace/work
oss/lib: ~/workspace/work/shared-lib
```

넓은 경로를 이은 줄 아래의 폴더 하나를 다른 가지의 layer로 떼어 내는 길은 두지 않는다. 그런 폴더가 실제로 나오고 옮길 수 없으면, #모양과 규칙을 고르는 기준의 7번에 따라 구조를 다시 본다.

실패를 알리는 줄의 모양은 아직 정하지 않았다. `layer-rules`의 파일 이름이나 줄의 layer 이름을 잘못 적으면, 세션은 실패 없이 전역만 받거나 빈 layer를 target layer로 삼는다. 세션 시작 줄이 target layer를 보이는지도 아직 정하지 않았다. symlink를 지나는 경로로 세션을 열면 사람이 본 경로와 hook이 읽은 작업 위치가 다르다. 세션 시작 줄이 hook이 읽은 작업 위치를 보이는지도 아직 정하지 않았다.

layer 규칙에 한 번 적은 경로는 그 아래 저장소 전부에 걸리므로, 새 저장소는 그 경로 아래에 만들기만 하면 규칙을 고치지 않아도 제 layer에 든다.

### 누가 무엇을 하나

| 누가 | 하는 일 | 하지 않는 일 |
|---|---|---|
| 사람 | layer 규칙을 정한다. `~/.mem`과 세션 시작 줄을 기존 markdown 뷰어와 터미널로 본다. save하거나 고치거나 지울 일을 에이전트에게 말로 시킨다 | 기억 파일을 손으로 쓰거나 옮기지 않는다 |
| 에이전트 | 1단계에서는 사람이 시킬 때 `~/.mem` 아래 md를 쓰고 고치고 지운다. 2단계부터는 배운 것을 묻지 않고 save한다 | 지시 파일(CLAUDE.md·AGENTS.md)을 건드리지 않는다 |
| hook | load하고, 세션 시작 줄을 띄운다. 2단계부터 log에 덧붙인다 | 항목을 바꾸지 않는다. 무엇을 save할지 판단하지 않는다. 사람을 부르지 않는다 |

Claude Code의 auto memory는 끈다. 켜 두면 같은 것이 두 곳에 쌓여서, 답에 쓰인 것이 어느 쪽에서 왔는지 가를 수 없기 때문이다.

### 1단계가 load하는 방식

`mem-hook`이 SessionStart hook으로 돈다. `mem-hook`은 layer 규칙으로 target layer를 찾는다. 그다음 preamble과 전역부터 target layer까지 각 layer의 항목을 그 순서로 이어 `additionalContext`로 넣고, 세션 시작 줄을 `systemMessage`로 띄운다.

| 규칙 | 값 | 까닭 |
|---|---|---|
| preamble | load된 기억은 지시 파일과 사용자가 말하지 않을 때만 따르는 기본값이라고 이르고, 기억을 save하라는 말을 들으면 target layer(어디서나 필요한 것은 전역)에 md 파일 하나로 쓰라고 이른다 | 첫 문장은 기억이 지시 파일이나 사용자 말과 부딪힐 때의 기준이다. 둘째 문장은 쓸 곳을 이른다. 쓸 곳이 틀리면 범위가 틀린다 |
| 시점 | startup·clear·compact. resume은 넣지 않는다 | compaction 뒤 비는 context window를 다시 채운다. resume은 앞 대화에 `additionalContext`가 이미 있다 |
| 10,000자 넘음 | 상한 없이 다 넣고 세션 시작 줄에 `10,000자 넘음`을 붙인다 | Claude Code는 넣는 글이 10,000자를 넘으면 그 글을 파일로 돌리고, 모델에게는 그 파일의 경로와 앞 2,000자까지의 미리보기만 준다. Claude Code는 모델에게 그 파일을 읽으라고 시키지 않는다. 그때는 세션 시작 줄의 `실림`이 모델이 받은 것과 다르다 |
| md가 아닌 파일 | load하지 않고 세션 시작 줄에 그 이름을 띄운다. 이름을 띄운 줄의 모양은 아직 정하지 않았다 | hook이 말없이 빼면 놓인 곳과 load되는 곳이 달라진다 |

### 2단계 log

log에는 덧붙이기만 하고 고치거나 지우지 않는다. log는 layer tree 밖에 두고, 경로는 2단계를 얹을 때 정한다.

hook은 세션 시작과 compaction 뒤에는 load된 경로를, 에이전트가 `~/.mem`을 쓰거나 고치거나 지울 때마다 시각·맥락·경로(shell 명령이면 명령 원문)와 그 줄을 부른 사람의 말을 transcript에서 찾아갈 `p=`를 적는다. 항목 본문과 바꾼 내용은 담지 않는다. 사람이 뒤에 log를 보고 고치거나 지우라고 시키는 이 방식을 사후 검토라고 부른다.

log에는 명령 원문과 `p=`처럼 기기마다 다른 값이 들어간다. 이것이 #모양과 규칙을 고르는 기준의 6번과 부딪히는지는 2단계를 얹을 때 정한다.

### 3단계 decision

한번 쓴 decision은 고치지 않고, 바꿀 때 새 decision을 쓴다. 대체된 decision은 layer tree 밖으로 옮긴다. 옮긴 decision은 layer에 놓여 있지 않아서 계산 없이 load에서 빠진다. 옮겨 둘 경로는 3단계를 얹을 때 정한다.

### 4단계 split

세션 시작 줄에 넘음 표시가 뜨면 layer 안에 더 좁은 layer를 두고, 더 좁은 layer에만 맞는 항목을 그리로 옮긴다. target layer가 더 좁은 layer인 세션도 넓은 layer를 받기 때문에, 넓은 layer에는 그 아래 전부에 맞는 항목만 남긴다. 모델이 index를 읽고 고르게 하는 것은 그다음이다.

## 본질

이 도구의 구조에서 지켜지는 제약 가운데, 빼면 어떤 성질이 사라지는지로 본질을 가른다. 새 요구는 이 제약을 깨서 아래 성질을 잃게 하는지로 거른다.

### 정체성을 정하는 제약

**범위는 자리다.** 기억은 언제나 놓인 layer가 정한 곳에서만 load된다.

모델이 범위를 고르면 빠뜨려도 알기 어렵기 때문에, load될 곳을 모델이 고르지 않고 layer와 layer 규칙이 정한다. 그래서 다른 일의 기억이 딸려 오지 않고, 무엇이 load되는지가 `ls`로 보인다.

사람이 이 제약을 보고 만지는 곳은 layer 폴더, layer 규칙, 세션 시작 줄의 경로다.

### 이 제약과 함께 지키는 것

| 제약 | 낳는 성질 | 빼면 사라지는 것 |
|---|---|---|
| 기억의 원본은 `~/.mem/` 아래 사람이 읽는 md 파일이고, 서버나 DB는 두지 않는다 | 사람과 에이전트가 같은 원본을 `ls`·`grep`·에디터로 본다 | 원본을 보는 길이 서버나 DB를 여는 도구로 좁아진다 |
| load는 hook이 세션 시작에 한다. 에이전트의 자발적 호출에 맡기지 않는다 | 무엇이 load되는지가 모델 판단에 달리지 않는다 | load가 매번 일어난다는 보장 |
| target layer와 그것을 품는 layer의 항목은 고르지 않고 전부 load한다. 검색 성능은 기준에 두지 않는다 | load된 것이 그 layer의 md 파일 목록과 같다 | load된 것을 `ls`로 아는 길. 고르는 쪽이 범위를 정하게 된다 |
| 상주 프로세스 없이 파일만 읽고 쓰는 hook 스크립트 하나로 둔다 | 죽을 프로세스가 없고 한 사람이 전체를 읽는다 | 프로세스가 죽으면 load가 빠진다 |
| load된 항목의 경로를 세션 시작 줄로 터미널에 띄운다 | 사람이 묻지 않아도 이번 세션의 재료를 안다 | 사람이 묻지 않으면 무엇이 load됐는지 알 수 없다 |
| `~/.mem`의 변경을 log 한 줄로 남긴다 | 묻지 않고 쓰게 해도 뒤에 따라갈 수 있다 | 묻지 않고 쓴 것을 뒤에 따라갈 길 |

1단계에는 log가 없어서 마지막 행을 지키지 않는다. 2단계에서는 에이전트가 쓸 때마다 한 줄을 남기는 데까지 지킨다. 에디터로 고친 것과 바꾼 내용은 2단계에서도 log에 남지 않는다.

### 제약에서 벗어나는 것

이 제약은 무엇을 만드는지를 분명히 제한하려고 정했다. 아래는 이 제약에서 벗어나서 지금은 만들지 않는 것이다. 기준이 분명해지고 부족한 부분이 생기면 이 본질부터 다시 열어 추가한다.

| 제약에서 벗어나는 것 | 까닭 |
|---|---|
| frontmatter나 metadata로 load될 곳 정하기, 항목에 "이럴 때만 쓴다" 적기 | 자리가 아닌 것이 범위를 정하게 된다 |
| 모델이 index·낱말 trigger·vector 검색으로 골라 load하기 | 모델이 범위를 고르면 빠뜨려도 모른다 |
| hook 말고 기억을 load하는 다른 길(MCP 검색 같은 것) | 범위를 지나지 않는 길이 생긴다 |
| layer에 놓인 항목을 계산으로 빼기 | 놓인 곳과 load되는 곳이 달라진다 |
| layer 여럿이 걸릴 때 우선순위나 예외 규칙으로 가리기 | 무엇이 load될지 미리 맞히기 어려워진다 |

새 요구는 이 본질에 대 본 뒤에 받는다.
