# 새 기억이 옛 기억과 같은 사실을 말할 때 옛 것을 다루는 방식과 겪은 문제

Mem0, Graphiti(Zep), Letta(MemGPT), data warehouse의 slowly changing dimension이 같은 사실을 말하는 새 것과 옛 것을 다루는 방식을 source code, 공식 문서, 만든 사람이 쓴 논문에서 옮긴 조사다. issue #34 "기억을 쌓는 도구는 새 기억이 옛 기억과 같은 사실을 말할 때 옛 것을 어떻게 하고, 쓰는 사람은 어떤 문제를 겪었는가"에 답한다.

네 시스템을 돌려서 확인한 것은 없다. 읽어서 갈리지 않은 것은 #확인하지 못한 것에 모았다.

같은 사실을 말하는 경우를 이 글에서는 셋으로 부른다. 뒤집힘은 새 것과 옛 것이 함께 참일 수 없는 경우다. 보탬은 새 것이 옛 것에 내용을 더하는 경우다. 겹침은 같은 말이 다시 들어오는 경우다.

Slowly changing dimension은 data warehouse에서 고객이나 상품처럼 가끔 바뀌는 대상의 설명을 담은 table을 부르는 이름이다. 이 글에서는 SCD로 줄여 쓴다.

## 출처

2026-11-15에 읽었다. source code는 아래 commit에 고정해 읽었다.

| 저장소 | 읽은 자리 | version |
|---|---|---|
| `mem0ai/mem0` | commit `f1791da` | Python package `mem0ai` 2.2.1 |
| `mem0ai/mem0` | tag `v1.0.11`(commit `144627c`) | 1.0.11. 1.x의 마지막 tag다 |
| `getzep/graphiti` | commit `3a8a78c` | `graphiti-core` 0.31.2 |
| `letta-ai/letta` | main의 commit `8816d3a` | 안내문만 있다 |
| `letta-ai/letta` | `archive` branch의 commit `56ba9c2` | 0.16.8. 물러난 V1 server다 |
| `letta-ai/letta-code` | commit `57d61bd` | 0.34.62 |

Mem0의 문서와 code 주석은 새 algorithm을 v3이라고 부르고, 그것을 실은 Python package의 version은 2.0.0이다. 이 글은 package의 version으로 적는다.

docs.mem0.ai, help.getzep.com, docs.letta.com의 문서는 쪽 주소에 `.md`를 붙여 markdown 원문을 받았다. Microsoft Learn의 문서는 요청 header `Accept: text/markdown`으로 받았다. Kimball Group의 글과 dbt 문서, arXiv의 논문은 HTML을 받아 글자만 뽑아 읽었다. GitHub issue는 GitHub API에서 본문과 댓글을 받았다.

큰따옴표 안의 영어는 원문 그대로이고, 원문의 굵은 글씨와 link 표기는 뺐다. 인용 119개가 받은 원문에 있는지 스크립트로 맞춰 보았다. 낱말이 둘뿐인 인용 둘은 눈으로 맞춰 보았다. 요약을 거친 글은 근거로 쓰지 않았다.

쓰는 사람이 겪은 문제는 그 사람이 직접 쓴 GitHub issue에서만 옮겼다. issue마다 답한 사람의 `author_association`(GitHub이 그 계정과 저장소의 관계를 적는 값)을 함께 적었다.

| 이 글에서 부르는 이름 | 주소 |
|---|---|
| Mem0 main.py | https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py |
| Mem0 prompts.py | https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/configs/prompts.py |
| Mem0 storage.py | https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/storage.py |
| Mem0 1.0.11 main.py | https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py |
| Mem0 1.0.11 prompts.py | https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py |
| Mem0 release 2.0.0 | https://github.com/mem0ai/mem0/releases/tag/v2.0.0 |
| Mem0 migration | https://docs.mem0.ai/migration/oss-v2-to-v3 |
| Mem0 how it works | https://docs.mem0.ai/core-concepts/how-it-works |
| Mem0 add | https://docs.mem0.ai/core-concepts/memory-operations/add |
| Mem0 overview | https://docs.mem0.ai/open-source/overview |
| Mem0 Dream | https://docs.mem0.ai/platform/features/dream |
| Mem0 platform vs OSS | https://docs.mem0.ai/platform/platform-vs-oss |
| Mem0 논문 | https://arxiv.org/abs/2504.19413 (v1) |
| mem0 #4536 | https://github.com/mem0ai/mem0/issues/4536 |
| mem0 #5867 | https://github.com/mem0ai/mem0/issues/5867 |
| mem0 #4956 | https://github.com/mem0ai/mem0/issues/4956 |
| mem0 #4573 | https://github.com/mem0ai/mem0/issues/4573 |
| mem0 #4467 | https://github.com/mem0ai/mem0/issues/4467 |
| Graphiti README | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/README.md |
| Graphiti edges.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/edges.py |
| Graphiti edge_operations.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py |
| Graphiti dedupe_edges.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/prompts/dedupe_edges.py |
| Graphiti graphiti.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/graphiti.py |
| Graphiti search_filters.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/search/search_filters.py |
| Graphiti search_helpers.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/search/search_helpers.py |
| Graphiti node_operations.py | https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/node_operations.py |
| Zep facts | https://help.getzep.com/facts |
| Zep concepts | https://help.getzep.com/concepts |
| Zep searching | https://help.getzep.com/searching-the-graph |
| Zep deleting | https://help.getzep.com/deleting-data-from-the-graph |
| Zep 논문 | https://arxiv.org/abs/2501.13956 (v1) |
| graphiti #1728 | https://github.com/getzep/graphiti/issues/1728 |
| graphiti #1956 | https://github.com/getzep/graphiti/issues/1956 |
| graphiti #1166 | https://github.com/getzep/graphiti/issues/1166 |
| graphiti #2034 | https://github.com/getzep/graphiti/issues/2034 |
| Letta AGENTS.md | https://github.com/letta-ai/letta/blob/8816d3a8516893bfdc0fa14bfb1235226012e295/AGENTS.md |
| Letta V1 base.py | https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/functions/function_sets/base.py |
| Letta V1 core_tool_executor.py | https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/tool_executor/core_tool_executor.py |
| Letta V1 memory.py | https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/schemas/memory.py |
| Letta V1 block_history.py | https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/orm/block_history.py |
| Letta V1 block_manager.py | https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager.py |
| Letta V1 block_manager_git.py | https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager_git.py |
| Letta V1 memory blocks | https://docs.letta.com/v1-sdk/memory/memory-blocks |
| Letta MemFS | https://docs.letta.com/concepts/memfs |
| Letta memory | https://docs.letta.com/configuration/memory |
| letta-code system prompt | https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/agent/prompts/letta_root_memfs.md |
| letta-code core memory skill | https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/skills/builtin/maintaining-core-memory/SKILL.md |
| letta-code reflection prompt | https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/agent/subagents/builtin/reflection.md |
| letta-code commit reminder | https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/reminders/memory-git-sync.ts |
| letta-code removed tools | https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/tools/removed-tools.ts |
| MemGPT 논문 | https://arxiv.org/abs/2310.08560 (v2) |
| letta #3431 | https://github.com/letta-ai/letta/issues/3431 |
| letta-code #4029 | https://github.com/letta-ai/letta-code/issues/4029 |
| Kimball Type 1 | https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-1/ |
| Kimball Type 2 | https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/ |
| Kimball Type 3 | https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-3/ |
| Kimball Type 4 | https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-4-mini-dimension/ |
| Kimball Design Tip 152 | https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/ |
| Kimball 2008 1부 | https://www.kimballgroup.com/2008/08/slowly-changing-dimensions/ |
| Kimball 2008 2부 | https://www.kimballgroup.com/2008/09/slowly-changing-dimensions-part-2/ |
| temporal tables | https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables |
| temporal usage | https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios |
| Fabric dimension tables | https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables |
| dbt snapshots | https://docs.getdbt.com/docs/build/snapshots |
| dbt #4661 | https://github.com/dbt-labs/dbt/issues/4661 |
| dbt #11235 | https://github.com/dbt-labs/dbt/issues/11235 |

## 네 시스템을 나란히

행마다의 근거는 아래 절에 있다.

| 물음 | Mem0 | Graphiti | Letta | SCD |
|---|---|---|---|---|
| 같은 사실인지 알아보는 쪽 | 1.0.11까지는 LLM이 네 조작에서 고른다. 2.0.0부터는 LLM이 겹침만 건너뛰고, 글자가 같은 것은 hash 규칙이 건너뛴다 | LLM. 글자와 양 끝 node가 같은 것은 규칙 | 에이전트인 모델. 같은 사실을 가리는 단계가 code에 따로 없다 | 사람이 attribute마다 정한 규칙. key가 같은 행을 적재 code가 견준다 |
| 알아보는 때 | 기억을 넣을 때 | episode를 넣을 때 | 대화 중, 그리고 대화 뒤에 도는 subagent | data를 적재할 때 |
| 뒤집힘일 때 옛 것 | 1.0.11까지는 지운다. 2.0.0부터는 그대로 둔다. Platform은 superseded 표시를 단다 | 지우지 않고 `invalid_at`과 `expired_at`을 적는다 | 같은 자리에 고쳐 쓴다 | Type 1은 덮어쓰고, Type 2는 새 행을 쌓고, Microsoft가 Type 4라고 부르는 방식은 history table로 옮긴다 |
| 겹침일 때 | 1.0.11까지는 LLM이 NONE을 고른다. 2.0.0부터는 건너뛴다 | 새 edge를 만들지 않고 기존 edge에 episode id를 덧붙인다 | 정한 규칙이 없다. 지시문은 겹치는 글을 지우라고 적는다 | 읽은 문서는 값이 바뀐 때만 다룬다 |
| 옛 내용을 되찾는 길 | history table의 `old_memory` | 같은 graph에 남은 edge와 원문 episode | 지금 Letta는 git history. V1 server의 기본 경로는 block 쪽에 남기지 않는다 | Type 1은 없다. Type 2는 같은 table. history table은 `FOR SYSTEM_TIME` query |
| 문서의 경고 | 더하기만 하면 옛 사실과 새 사실이 함께 쌓인다 | 시각 표시가 사실의 참을 보증하지 않는다 | block의 값을 통째로 바꾸면 마지막에 쓴 쪽이 이긴다 | Type 1은 내력을 없앤다. Type 2는 version이 많아지면 읽기 어렵다 |
| 쓰는 사람이 겪은 문제 | 1.x에서는 옛 것만 지워지고 새 것이 들어가지 않았다. 2.x에서는 옛 값이 검색에 나온다 | 관계없는 사실이 무효가 된다. 무효가 되어야 할 사실이 남는다 | 최신 것을 따르라는 지시 한 줄이 두어야 할 기억까지 고친다 | Type 2를 만드는 도구에서 지금 값인 행이 둘 생긴다 |

## Mem0

Mem0는 version에 따라 방식이 다르다. open source SDK는 1.0.11까지 LLM이 더하기, 고치기, 지우기, 그대로 두기에서 골랐고, 2.0.0(2026-04-16)부터는 더하기만 한다. Mem0가 운영하는 Platform은 Dream이라는 기능이 옛 기억에 표시를 단다.

### 알아보는 쪽

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| 논문의 방식 | 뽑은 사실마다 비슷한 기억을 꺼내고, LLM이 네 조작에서 하나를 고른다 | "The LLM itself determines which of four distinct operations to execute: ADD for creation of new memories when no semantically equivalent memory exists; UPDATE for augmentation of existing memories with complementary information; DELETE for removal of memories contradicted by new information; and NOOP when the candidate fact requires no modification to the knowledge base." | [Mem0 논문](https://arxiv.org/abs/2504.19413) 2.1절 |
| 1.0.11의 흐름 | LLM을 두 번 부른다. 첫 호출이 사실을 뽑고, code가 사실마다 기존 기억 5개를 vector 검색으로 꺼내고, 둘째 호출이 ADD, UPDATE, DELETE, NONE에서 고른다 | "Compare newly retrieved facts with the existing memory. For each new fact, decide whether to:" | [Mem0 1.0.11 main.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L513-L690), [Mem0 1.0.11 prompts.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L176-L186) |
| 1.0.11의 뒤집힘 규칙 | 모순이면 옛 기억을 지우라고 prompt가 시킨다 | "If the retrieved facts contain information that contradicts the information present in the memory, then you have to delete it." | [Mem0 1.0.11 prompts.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L263) |
| 1.0.11의 보탬 규칙 | 같은 뜻이면 정보가 많은 쪽을 남긴다 | "If the retrieved fact contains information that conveys the same thing as the elements present in the memory, then you have to keep the fact which has the most information." | [Mem0 1.0.11 prompts.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/configs/prompts.py#L215-L216) |
| 2.0.0에서 바뀐 것 | LLM을 한 번 부르고 조작은 더하기뿐이다 | "Extraction: Single-pass ADD-only (one LLM call, no UPDATE/DELETE)" | [Mem0 migration](https://docs.mem0.ai/migration/oss-v2-to-v3) |
| 2.x의 흐름 | code가 기존 기억 10개를 꺼내 prompt에 넣는다. prompt는 조작을 더하기 하나로 못 박는다 | "Your sole operation is ADD: identify every piece of memorable information and produce self-contained, contextually rich factual statements." | [Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L918-L964), [Mem0 prompts.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/configs/prompts.py#L472) |
| 2.x에서 기존 기억의 쓰임 | 겹침을 건너뛰고 잇는 데만 쓴다 | "Use these ONLY for deduplication and linking — do NOT extract new memories from Existing Memories." | [Mem0 prompts.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/configs/prompts.py#L511) |
| 2.x의 규칙 쪽 판정 | 글의 MD5 hash가 기존 기억과 같으면 건너뛴다 | "Hash-based deduplication prevents exact duplicates; ranking at retrieval time handles the rest." | [Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1022-L1025), [Mem0 release 2.0.0](https://github.com/mem0ai/mem0/releases/tag/v2.0.0) |
| 2.x에서 망설여질 때 | prompt는 뽑으라고 시킨다 | "A slightly redundant memory is far less costly than a missing one." | [Mem0 prompts.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/configs/prompts.py#L578) |
| Platform의 Dream | 뒤집힘과 겹침을 기억을 넣을 때 가린다 | "Supersede and Merge are part of the memory-addition pipeline." | [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |

2.x의 prompt는 뒤집힘을 만나면 새 기억에 옛 기억의 id를 `linked_memory_ids`로 달라고 시킨다. 원문은 "Contradiction: New information that conflicts with an existing memory"다([Mem0 prompts.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/configs/prompts.py#L692-L701)).

저장할 payload를 짓는 code는 LLM의 답에서 `text`와 `attributed_to`만 읽는다([Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1017-L1041)). LLM이 돌려준 `linked_memory_ids`를 저장하는 자리는 이 commit에서 찾지 못했다.

Dream이 뒤집힘과 겹침을 가리는 것이 모델인지 규칙인지는 문서에 없다. Platform의 code는 공개되어 있지 않다.

### 옛 것의 행방

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| 1.0.11의 UPDATE | 같은 id의 글을 덮어쓰고, history table에 옛 글과 새 글을 한 행으로 적는다 | 없음(code) | [Mem0 1.0.11 main.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L1281-L1338) |
| 1.0.11의 DELETE | vector store에서 지우고, history table에 옛 글과 `is_deleted=1`을 적는다 | 없음(code) | [Mem0 1.0.11 main.py](https://github.com/mem0ai/mem0/blob/144627c4ce5bc4db6acac17cbd158065f2b27a8d/mem0/memory/main.py#L1340-L1364) |
| history table의 자리 | SQLite 파일 하나 | "History store" 행의 "SQLite at `~/.mem0/history.db`" | [Mem0 overview](https://docs.mem0.ai/open-source/overview) |
| history table의 열 | `id`, `memory_id`, `old_memory`, `new_memory`, `event`, `created_at`, `updated_at`, `is_deleted`, `actor_id`, `role` | 없음(code) | [Mem0 storage.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/storage.py#L102-L125) |
| 되찾는 길 | `history(memory_id)`가 그 기억의 행을 시간순으로 돌려준다 | "Get the history of changes for a memory by ID." | [Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1960-L1973) |
| 2.x의 뒤집힘 | 옛 기억을 그대로 두고 새 기억을 더한다 | "When information changes, the new fact is stored alongside the old one. Retrieval handles ranking: the most relevant, current information surfaces first." | [Mem0 migration](https://docs.mem0.ai/migration/oss-v2-to-v3) |
| 2.x의 저장 | 덮어쓰지도 지우지도 않는다 | "New memories are added without overwriting or deleting existing memories." | [Mem0 add](https://docs.mem0.ai/core-concepts/memory-operations/add) |
| 2.x에서 고치려면 | 쓰는 쪽이 `update`나 `delete`를 직접 부른다 | "Use explicit `update` or `delete` operations when your application needs to correct or remove a memory." | [Mem0 how it works](https://docs.mem0.ai/core-concepts/how-it-works) |
| Platform의 Supersede | 옛 기억에 superseded 표시를 달고 새 기억과 잇는다. 지우지 않고 기본 읽기에도 나온다 | "Superseded memories are not deleted and not hidden by default." | [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |
| Platform의 Merge | 덜 자세한 쪽에 merged 표시를 단다. 기본 읽기에서 빠진다 | "The merged record is hidden from reads by default (you get the one canonical memory), retained rather than deleted, and surfaced with `include_merged=true`." | [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |
| Platform의 겹침 | 같은 말이 다시 오면 사본을 만들지 않는다 | "No second copy is created, so you simply keep the one memory." | [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |
| Platform에서 지금 값만 읽기 | 읽는 쪽이 `latest_only=true`를 준다 | "When you want only the current truth, ask for it explicitly with `latest_only=true`" | [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |
| Dream이 지우는 것 | 없다고 문서가 적는다 | "Nothing Dream does is destructive." | [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |
| Dream과 open source | open source에는 없다 | "Dream (background consolidation)" 행의 open source 칸은 "Not available" | [Mem0 platform vs OSS](https://docs.mem0.ai/platform/platform-vs-oss) |

2.x에서도 쓰는 쪽이 `update()`와 `delete()`를 부르면 history table에 UPDATE 행과 DELETE 행이 생긴다([Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L2052-L2143)).

`add()`가 적는 행은 `old_memory`가 비어 있는 ADD 행뿐이다([Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L1079-L1089)).

history의 행에서 옛 글로 되돌리는 API는 이 commit의 `Memory` class에서 찾지 못했다.

### 문제

문서가 적은 경고는 둘이다.

| 경고 | 원문 | 출처 |
|---|---|---|
| 더하기만 하면 기억이 쌓인다 | "The ADD-only model means memories accumulate over time." | [Mem0 migration](https://docs.mem0.ai/migration/oss-v2-to-v3) |
| LLM을 거치지 않고 넣으면 겹친다 | "When you switch to `infer=False`, Mem0 stores your payload exactly as provided, so duplicates can land." | [Mem0 add](https://docs.mem0.ai/core-concepts/memory-operations/add) |

쓰는 사람이 낸 보고는 다섯을 옮긴다. 답한 계정 blazingretinol은 `mem0ai/mem0`에 release commit을 올리는 계정이고 `author_association`은 CONTRIBUTOR다.

| issue | version | 겪은 것 | 원문 | 답 |
|---|---|---|---|---|
| [mem0 #4536](https://github.com/mem0ai/mem0/issues/4536) | 1.0.5 | 모순되는 사실을 넣자 옛 기억만 지워지고 새 사실은 들어가지 않았다 | "It deleted the first memory without adding the second memory." | blazingretinol이 2.0.0에서 바뀌었다고 답하고 닫았다. "The v3 algorithm is ADD-only — it no longer uses DELETE for contradictions." |
| [mem0 #5867](https://github.com/mem0ai/mem0/issues/5867) | 2.x | 옛 선호와 새 선호가 둘 다 남아 검색 결과가 갈린다 | "The current ADD-only extraction flow can store both the old and new facts as separate ADD memories." | blazingretinol이 설계라고 답했다. "this is a design/feature gap rather than a bug" 열려 있다 |
| [mem0 #4956](https://github.com/mem0ai/mem0/issues/4956) | 2.x | 직장처럼 바뀌는 값에서 옛 값이 위에 나온다 | "can return Company A as a top-ranked candidate because the scoring signals don't incorporate recency" | 읽은 댓글에 maintainer의 답이 없다. 열려 있다 |
| [mem0 #4573](https://github.com/mem0ai/mem0/issues/4573) | 적혀 있지 않다. 2026-02-23부터 32일 동안 썼다 | 32일 동안 쌓인 기억 10,134개 가운데 224개만 남겼다. 버린 것의 52.7%가 같은 사실을 다시 뽑은 것이다 | "The same facts re-extracted every session." | blazingretinol이 2.0.0의 변화를 들고 닫았다. "Changes are additive — no more destructive overwrites that lose temporal context." |
| [mem0 #4467](https://github.com/mem0ai/mem0/issues/4467) | 1.0.7 | history의 DELETE 행에 시각이 없어서 순서가 뒤바뀐다 | "DELETE events appear without timestamps" | blazingretinol이 고치겠다고 답했고 닫혔다. "We'll look into adding `deleted_at` to the history record so the full lifecycle is trackable." |

mem0 #5867의 첫 답은 더하기만 하는 설계가 얻는 것과 잃는 것을 함께 적는다. 원문은 "The additive approach preserves historical progression, which is useful for understanding how preferences evolved — but it does create ambiguous retrieval when the user expects only the latest preference to survive."다.

`add()`의 docstring은 2.2.1에서도 LLM이 "decide whether to add, update, or delete related memories"라고 적고 있어서 code와 어긋난다([Mem0 main.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/main.py#L790-L791)).

## Graphiti

Graphiti는 사실을 두 entity node를 잇는 edge에 적고, 뒤집힌 edge를 지우지 않고 시각을 적어 둔다. Zep은 Graphiti를 써서 만든 hosted service다.

### 알아보는 쪽

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| 겹침 후보를 꺼내는 범위 | 새 edge와 같은 두 node 사이의 edge만 꺼낸다 | "The hybrid search for relevant edges is constrained to edges existing between the same entity pairs as the proposed new edge." | [Zep 논문](https://arxiv.org/abs/2501.13956) 2.2.2절, [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L526-L543) |
| 뒤집힘 후보를 꺼내는 범위 | filter 없이 같은 group의 edge 전체에서 비슷한 것을 꺼낸다 | 없음(code). `search_filter=SearchFilters()` | [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L558-L571) |
| 판정하는 쪽 | 새 edge마다 작은 모델을 한 번 불러 겹친 것의 번호와 뒤집힌 것의 번호를 받는다 | "The system employs an LLM to compare new edges against semantically related existing edges to identify potential contradictions." | [Zep 논문](https://arxiv.org/abs/2501.13956) 2.2.3절, [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L986-L995) |
| 뒤집힘의 기준 | 둘이 함께 참일 수 없을 때만 | "Only mark a fact as contradicted when the NEW FACT and the existing fact cannot both be true." | [Graphiti dedupe_edges.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/prompts/dedupe_edges.py#L56) |
| 겹침의 기준 | 숫자, 날짜, 한정어가 다르면 겹침이 아니다 | "NEVER mark facts as duplicates if they have key differences, particularly around numeric values, dates, or key qualifiers." | [Graphiti dedupe_edges.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/prompts/dedupe_edges.py#L54) |
| 규칙 쪽 판정 | 글자와 양 끝 node가 같으면 LLM을 부르지 않고 기존 edge를 쓴다 | 없음(code) | [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L945-L955) |
| LLM의 답 뒤에 붙는 규칙 | LLM이 뒤집혔다고 고른 후보 가운데 `valid_at`이 새 edge보다 이른 것을 무효로 한다. `valid_at`이 더 늦은 후보가 있으면 새 edge를 무효로 한다 | 없음(code) | [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L715-L783) |
| 논문이 적은 이기는 쪽 | 새로 들어온 쪽 | "Graphiti consistently prioritizes new information when determining edge invalidation." | [Zep 논문](https://arxiv.org/abs/2501.13956) 2.2.3절 |

### 옛 것의 행방

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| 뒤집힌 edge | 지우지 않는다 | "When information changes, old facts are invalidated — not deleted." | [Graphiti README](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/README.md?plain=1#L125-L126) |
| 적는 값 | `invalid_at`에 새 edge의 `valid_at`을, `expired_at`에 처리한 시각을 적고 graph에 다시 저장한다 | 없음(code) | [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L774-L781), [Graphiti graphiti.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/graphiti.py#L1507) |
| `invalid_at`의 뜻 | 사실이 참이기를 그친 시각 | "datetime of when the fact stopped being true; soft deadlines are not invalid_at" | [Graphiti edges.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/edges.py#L246-L249) |
| 문서의 정의 | 무효가 된 시각을 그 사실의 edge에 적는다 | "When new data invalidates a prior fact, the time the fact became invalid is stored on that fact's edge in the Context Graph." | [Zep concepts](https://help.getzep.com/concepts) |
| 시각 넷 | `valid_at`과 `invalid_at`은 사실이 세상에서 참인 기간을 적는다. `created_at`과 `expired_at`은 system이 edge를 만든 때와 무효로 한 때를 적는다 | "Each fact has two timelines: when the fact applies in the world, and when Zep records or invalidates it." | [Zep facts](https://help.getzep.com/facts) |
| 겹친 edge | 새 edge를 만들지 않고 기존 edge의 `episodes`에 episode id를 덧붙인다 | 없음(code) | [Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L905-L908) |
| 원문 | episode node가 들어온 글을 그대로 담는다 | "Episodes serve as a non-lossy data store from which semantic entities and relations are extracted." | [Zep 논문](https://arxiv.org/abs/2501.13956) 2절 |
| 기본 검색 | 무효가 된 edge도 나온다. 읽는 쪽이 filter를 주어야 빠진다 | "Find current/valid facts: Filter for edges where `invalid_at` is null to find facts that are still valid" | [Zep searching](https://help.getzep.com/searching-the-graph), [Graphiti search_filters.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/search/search_filters.py#L187) |
| LLM에 넘기는 글 | 검색 결과를 글로 바꾸는 helper가 사실마다 유효한 기간을 붙인다 | "Facts are considered valid between their valid_at and invalid_at dates." | [Graphiti search_helpers.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/search/search_helpers.py#L56-L57) |
| entity node의 summary | edge와 달리 덮어쓴다 | "Node summaries are intended to be mutable. We haven't yet implemented the concept of versioned node properties." | [graphiti #1166](https://github.com/getzep/graphiti/issues/1166)의 danielchalef(MEMBER), [Graphiti node_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/node_operations.py#L1262) |

### 문제

문서와 prompt가 적은 경고는 셋이다.

| 경고 | 원문 | 출처 |
|---|---|---|
| 시각 표시는 사실의 참을 보증하지 않는다 | "The fields do not establish that the source content or the derived fact is true." | [Zep facts](https://help.getzep.com/facts) |
| 무효로 만든 episode를 지워도 무효 표시는 남는다 | "If an episode invalidates a fact, and the episode is deleted, the fact will remain marked as invalidated." | [Zep deleting](https://help.getzep.com/deleting-data-from-the-graph) |
| prompt가 모델에게 거는 제동 | "NEVER mark facts as contradicted unless the new fact explicitly makes the old fact false." | [Graphiti dedupe_edges.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/prompts/dedupe_edges.py#L49) |

쓰는 사람이 낸 보고는 넷을 옮긴다.

| issue | version | 겪은 것 | 원문 | 답 |
|---|---|---|---|---|
| [graphiti #1728](https://github.com/getzep/graphiti/issues/1728) | 0.29.3 기반 | entity를 언급만 한 새 사실이 관계없는 옛 사실을 무효로 만든다. 사실 3,950개 가운데 1,616개에 `invalid_at`이 붙었고, 손으로 본 넷 가운데 셋이 잘못이다 | "Saving a memory that merely mentions an entity can retire an unrelated, still-true fact about that entity." | 댓글 아홉에 maintainer의 답이 없다. 열려 있다 |
| [graphiti #1956](https://github.com/getzep/graphiti/issues/1956) | commit `5d47d4d` | 한 대상의 옛 값이 10개쯤 쌓이면 지금 값이 후보 10개에 들지 못해서 무효가 되지 않는다 | "Once a subject has about 10 past values of a fact, the current one is often not among the candidates, the model never sees it, and it is never retired." | maintainer의 답이 없다. 열려 있다 |
| [graphiti #1166](https://github.com/getzep/graphiti/issues/1166) | 적혀 있지 않다 | node의 attribute가 덮어써져서 옛 값을 볼 수 없다 | "making it impossible to retrieve the historical state of a node at a specific point in time" | danielchalef(MEMBER)가 bug가 아니라고 답했다. 열려 있다 |
| [graphiti #2034](https://github.com/getzep/graphiti/issues/2034) | 0.30.2, 0.31.1 | episode를 지워도 그 episode가 만든 무효 표시와 summary의 글이 남는다 | "Leaves invalidations in place." | danielchalef(MEMBER)가 답하고 닫았다. "This wasn't a bug, but was a limitation of Graphiti open source. The related PR has been merged." |

graphiti #1728의 보고자는 원인을 둘로 든다. 하나는 뒤집힘 후보를 꺼내는 검색에 범위가 없다는 것이고, 다른 하나는 LLM의 판정을 다시 보는 단계가 없다는 것이다. 원문은 "Nothing checks the LLM's contradiction call."이다.

0.31.2의 code에서도 뒤집힘 후보의 검색은 filter 없이 돈다([Graphiti edge_operations.py](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/graphiti_core/utils/maintenance/edge_operations.py#L558-L571)).

## Letta

Letta는 저장소가 둘로 갈려 있어서 둘을 따로 적는다. `letta-ai/letta`의 main은 안내문만 담고, memory block을 쓰던 server는 `archive` branch에 있다. 지금의 Letta는 `letta-ai/letta-code`이고 기억을 git이 관리하는 Markdown 파일로 둔다.

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| main branch | 안내문만 있다 | "`main` is intentionally a small landing page." | [Letta AGENTS.md](https://github.com/letta-ai/letta/blob/8816d3a8516893bfdc0fa14bfb1235226012e295/AGENTS.md?plain=1#L5) |
| `archive` branch | 물러난 V1 server이고 지금의 Letta를 대표하지 않는다고 적는다 | "The code on `archive` is unsupported, receives no fixes or security updates, and does not represent current Letta." | [Letta AGENTS.md](https://github.com/letta-ai/letta/blob/8816d3a8516893bfdc0fa14bfb1235226012e295/AGENTS.md?plain=1#L7) |
| memory block 문서 | 남아 있고 `status: legacy`가 붙어 있다 | "Memory blocks are structured sections of the agent’s context window that persist across all interactions." | [Letta V1 memory blocks](https://docs.letta.com/v1-sdk/memory/memory-blocks) |
| 지금의 기억 | 모든 agent가 MemFS를 쓴다 | "All Letta agents use MemFS." | [Letta MemFS](https://docs.letta.com/concepts/memfs) |

### 알아보는 쪽

V1 server와 지금의 Letta 모두 같은 사실인지 가리는 단계를 code에 두지 않는다. 에이전트인 모델이 제 기억의 글을 보고 고칠지를 정한다.

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| 논문의 방식 | 기억을 고치고 찾는 일을 에이전트가 스스로 한다 | "Memory edits and retrieval are entirely self-directed: MemGPT autonomously updates and searches through its own memory based on the current context." | [MemGPT 논문](https://arxiv.org/abs/2310.08560) 2.3절 |
| 논문의 working context | 도구 호출로만 쓸 수 있는 글 덩어리다 | "Working context is a fixed-size read/write block of unstructured text, writeable only via MemGPT function calls." | [MemGPT 논문](https://arxiv.org/abs/2310.08560) 2.1절 |
| V1의 도구 | `core_memory_append`, `core_memory_replace`, `memory_replace`, `memory_insert`, `memory_apply_patch`, `memory_rethink` | "Replace the contents of core memory. To delete memories, use an empty string for new_content." | [Letta V1 base.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/functions/function_sets/base.py#L263-L281) |
| V1의 `memory_rethink` | block 전체를 새 글로 바꾼다 | "The memory_rethink command allows you to completely rewrite the contents of a memory block." | [Letta V1 base.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/functions/function_sets/base.py#L488-L518) |
| 지금의 도구 | 에이전트가 파일 도구로 MemFS의 Markdown 파일을 고친다. `memory`와 `memory_apply_patch`는 없어진 도구의 목록에 있다 | "MemFS projects that repository onto whatever computer the agent is running on, as a real checkout the agent reads and edits with ordinary file tools." | [Letta MemFS](https://docs.letta.com/concepts/memfs), [letta-code removed tools](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/tools/removed-tools.ts#L1-L27) |
| 지금의 뒤집힘 지시 | 부딪히는 줄을 둘 다 두지 말고 풀라고 skill이 시킨다 | "Check that a change does not contradict an existing line; resolve the conflict instead of adding both." | [letta-code core memory skill](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/skills/builtin/maintaining-core-memory/SKILL.md?plain=1#L66) |
| 지금의 겹침 지시 | 낡거나 겹치는 글을 지우라고 skill이 시킨다 | "Delete stale, duplicated, or rederivable content." | [letta-code core memory skill](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/skills/builtin/maintaining-core-memory/SKILL.md?plain=1#L99) |
| 대화 뒤에 도는 쪽 | reflection subagent가 대화 기록을 읽고 기억과 부딪히는 것을 찾는다. 최신 근거를 따른다 | "resolve contradictions in favor of the latest evidence" | [letta-code reflection prompt](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/agent/subagents/builtin/reflection.md?plain=1#L58) |
| 대화 뒤에 도는 때 | 정한 step 수가 지나거나 context가 압축될 때 | "Dreaming uses background subagents to review recent conversations, consolidate useful lessons, and update memory without interrupting your active work." | [Letta memory](https://docs.letta.com/configuration/memory) |

### 옛 것의 행방

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| V1의 기본 경로 | 도구가 block의 `value`를 새 문자열로 바꾸고 DB의 행을 고친다 | 없음(code). `block.value = value` | [Letta V1 memory.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/schemas/memory.py#L771-L780), [Letta V1 core_tool_executor.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/tool_executor/core_tool_executor.py#L328-L344) |
| V1의 `block_history` table | block의 옛 상태를 담는 table과 checkpoint, undo, redo 함수가 있다 | "Stores a single historical state of a Block for undo/redo functionality." | [Letta V1 block_history.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/orm/block_history.py#L12-L13), [Letta V1 block_manager.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager.py#L842-L912) |
| V1의 git 경로 | `git-memory-enabled` tag를 단 agent는 block을 쓸 때 git에 먼저 commit한다 | "This provides full version history while maintaining fast reads from PostgreSQL." | [Letta V1 block_manager_git.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager_git.py#L1-L8) |
| 논문의 대화 기록 | 들어온 message와 LLM의 출력을 recall storage에 적는다 | "The queue manager writes both the incoming message and the generated LLM output to recall storage (the MemGPT message database)." | [MemGPT 논문](https://arxiv.org/abs/2310.08560) 2.2절 |
| 지금의 고치기 | 파일을 고쳐 쓰고 git commit으로 남긴다 | "Every memory edit is committed to the MemFS git repository. This provides version history, conflict resolution, and a clear boundary between saved memory and uncommitted changes." | [Letta MemFS](https://docs.letta.com/concepts/memfs) |
| 지금의 옛 글 | git이 가지고 있다고 skill이 적는다 | "nothing is lost, because git keeps the old text" | [letta-code core memory skill](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/skills/builtin/maintaining-core-memory/SKILL.md?plain=1#L64) |
| 지금의 까닭 적기 | 누가 언제 무슨 말을 했는지는 기억 파일이 아니라 commit message에 적는다 | "Every memory commit must let someone reading `git log` or `git blame` on a memory or skill line trace back to the events that justified it." | [letta-code core memory skill](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/skills/builtin/maintaining-core-memory/SKILL.md?plain=1#L105) |
| commit하는 쪽 | 에이전트다. harness는 commit되지 않은 변경을 알리고, commit된 것을 push한다 | "MEMORY COMMIT NEEDED: The memory repository has uncommitted changes." | [letta-code commit reminder](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/reminders/memory-git-sync.ts#L83-L95) |
| 지금의 대화 기록 | harness가 남기고 에이전트가 고칠 수 없다 | "All of your experience (message history) is stored in recall memory automatically by the Letta Code harness (cannot be mutated)" | [letta-code system prompt](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/agent/prompts/letta_root_memfs.md?plain=1#L12) |

`archive` branch의 commit `56ba9c2`에서 `checkpoint_block_async`를 부르는 곳은 test뿐이다. `grep -rl "checkpoint_block_async" .`가 낸 파일은 함수를 정의한 `letta/services/block_manager.py`와 `tests/managers/test_block_manager.py` 둘이다.

V1의 `core_memory_replace`는 바꿀 옛 글을 인자 `old_content`로 받고, `memory_rethink`의 인자는 `label`과 `new_memory` 둘이다([Letta V1 base.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/functions/function_sets/base.py#L263-L281)).

### 문제

문서와 prompt가 적은 경고는 셋이다.

| 경고 | 원문 | 출처 |
|---|---|---|
| V1에서 block의 값을 통째로 바꾸면 앞선 변경이 사라진다 | "If multiple processes (agents or external scripts) modify the same block concurrently, the last write wins and overwrites all earlier changes." | [Letta V1 memory blocks](https://docs.letta.com/v1-sdk/memory/memory-blocks) |
| 지금의 고친 글은 commit하고 push해야 기억이 된다 | "Edits are local until committed and pushed, at which point they become the agent’s memory everywhere." | [Letta MemFS](https://docs.letta.com/concepts/memfs) |
| 지금의 고친 글은 그 대화에는 듣지 않는다 | "Editing memory does NOT change your behavior in the current turn." | [letta-code system prompt](https://github.com/letta-ai/letta-code/blob/57d61bd34f963e686847279f2cccee47a4d9c69e/src/agent/prompts/letta_root_memfs.md?plain=1#L58) |

쓰는 사람이 낸 보고는 둘을 옮긴다.

| issue | 대상 | 겪은 것 | 원문 | 답 |
|---|---|---|---|---|
| [letta-code #4029](https://github.com/letta-ai/letta-code/issues/4029) | reflection prompt | 최신 근거를 따르라는 한 줄을 모델 10개에 case 넷을 세 번씩 주어 쟀다. 고쳐야 하는 case는 다 맞았고, 그대로 두어야 하는 case는 절반이 틀렸다 | "Action-type conflicts: 60/60 pass. Restraint-type: 30/60 fail — exactly half." | maintainer의 답이 없다. 열려 있다 |
| [letta #3431](https://github.com/letta-ai/letta/issues/3431) | V1 0.16.8 | 밖의 연구자가 V1을 읽고, 옛 값은 기본으로 덮어써지고 checkpoint를 부르는 곳이 test뿐이라고 적어 확인을 청했다 | "Fate of the old value: overwritten in place by default." | cpacker(COLLABORATOR)가 답하고 닫았다. "Most of this is wrong / outdated" |

letta-code #4029의 보고자는 틀린 예 둘을 든다. 하나는 확인된 알레르기를 적은 줄이 대화 속 일화 하나 때문에 약해지거나 지워진 것이다. 다른 하나는 모델이 옛 주소의 거리 이름과 새 도시를 이어 붙여 없는 주소를 만든 것이다. 보고자는 한계도 적는다. 이 측정은 prompt만 모델에 준 것이고 Letta Code를 돌린 것이 아니다.

letta #3431의 답은 어느 대목이 틀렸는지를 적지 않고 `letta-ai/letta-code`를 보라고 한다.

## slowly changing dimension

SCD는 값이 바뀐 행을 다루는 방식을 Type 번호로 부른다. 번호는 Kimball Group이 붙였고, Type 4의 뜻은 Kimball Group과 Microsoft가 다르게 적는다.

Kimball Group은 이 개념이 나온 때를 "Ralph introduced the concept of slowly changing dimension (SCD) attributes in 1996."이라고 적는다([Kimball Design Tip 152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/)).

### 분류

Kimball Group은 기본 방식을 셋으로 든다. 원문은 "Most Kimball readers are familiar with the core SCD approaches: type 1 (overwrite), type 2 (add a row), and type 3 (add a column)."이다([Kimball Design Tip 152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/)).

| Type | Kimball Group의 이름 | 하는 일 | 원문 | 출처 |
|---|---|---|---|---|
| 0 | Retain Original | 값을 바꾸지 않는다 | "the dimension attribute value never changes" | [Kimball Design Tip 152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/) |
| 1 | Overwrite | 같은 행의 옛 값을 새 값으로 덮어쓴다 | "the old attribute value in the dimension row is overwritten with the new value" | [Kimball Type 1](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-1/) |
| 2 | Add New Row | 새 값을 담은 행을 더하고 옛 행을 남긴다 | "Slowly changing dimension type 2 changes add a new row in the dimension with the updated attribute values." | [Kimball Type 2](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/) |
| 3 | Add New Attribute | 옛 값을 같은 행의 다른 column으로 옮기고 주 column을 덮어쓴다 | "add a new attribute in the dimension to preserve the old attribute value; the new value overwrites the main attribute as in a type 1 change" | [Kimball Type 3](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-3/) |
| 4 | Add Mini-Dimension | 자주 바뀌는 attribute 묶음을 작은 dimension으로 떼어 낸다 | "Slowly changing dimension type 4 is used when a group of attributes in a dimension rapidly changes and is split off to a mini–dimension." | [Kimball Type 4](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-4-mini-dimension/) |
| 5, 6, 7 | 앞의 것을 섞은 방식 | 옛 값을 지키면서 지금 값으로도 묶어 보게 한다 | "The hybrid approaches provide more analytic flexibility, albeit with greater complexity." | [Kimball Design Tip 152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/) |

Microsoft의 SQL Server 문서는 Type 4를 history table로 적는다.

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| Microsoft의 Type 4 | 지금 값은 원래 table에 두고 내력은 다른 table에 둔다 | "Keeping history in the separate table while original dimension table keeps latest (current) dimension member versions" | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions) |
| SQL Server의 temporal table | table 둘로 되어 있어서 Type 4에 가깝다고 적는다 | "Given its implementation using two tables, temporal tables are closest to Type 4 SCD." | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions) |
| 옛 행이 옮겨지는 때 | 행을 고치거나 지울 때마다 system이 옛 version을 history table에 넣는다 | "The system uses the history table to automatically store the previous version of the row each time a row in the temporal table gets updated or deleted." | [temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) |
| 두 table이 담는 것 | current table은 지금 값을, history table은 옛 값과 그 값이 유효했던 기간을 담는다 | "The current table contains the current value for each row." | [temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) |
| 값이 바뀌지 않은 수정 | history table에 행이 생긴다 | "When you run any data modification queries on a temporal table, the Database Engine adds a row to the history table, even if no column values change." | [temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) |
| 옛 값을 읽는 길 | `SELECT`에 `FOR SYSTEM_TIME` 절을 붙인다 | "Only queries that deal with history data return data for which a row is closed." | [temporal tables](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables) |

### 알아보는 쪽

SCD에서는 값이 바뀌었을 때의 대응을 사람이 attribute마다 미리 정하고, 적재하는 code가 그 규칙을 따른다. 읽은 문서에 모델이 판정하는 방식은 없다.

| 물음 | 읽은 것 | 원문 | 출처 |
|---|---|---|---|
| 대응을 정하는 쪽 | 설계자와 업무 쪽 대표 | "Dimensional modelers, in conjunction with the business’s data governance representatives, must specify the data warehouse’s response to operational attribute value changes." | [Kimball Design Tip 152](https://www.kimballgroup.com/2013/02/design-tip-152-slowly-changing-dimension-types-0-4-5-6-7/) |
| 규칙을 지키는 쪽 | 적재하는 ETL code | "it's the responsibility of the ETL layer (Extract-Transform-Load) to keep dimension tables accurate" | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions) |
| 같은 대상인지 아는 길 | 원천 시스템의 natural key가 같은 행을 한 대상으로 본다 | "A surrogate key is required because there will be duplicate natural keys when multiple versions are stored." | [Fabric dimension tables](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables) |
| 고침과 변화의 구분 | 틀린 값을 바로잡는 것은 Type 1로, 실제로 바뀐 것은 Type 2로 다룬다 | "Type 1 changes are appropriate for correcting errors and for situations where a conscious choice is made not to track history." | [Kimball 2008 1부](https://www.kimballgroup.com/2008/08/slowly-changing-dimensions/) |
| 한 table 안에서 | attribute마다 Type을 달리 줄 수 있다 | "It's possible that a dimension could support both SCD type 1 and SCD type 2 changes." | [Fabric dimension tables](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables) |

### 방식마다 문서가 적은 득실

| 방식 | 얻는 것 | 잃는 것 | 원문 | 출처 |
|---|---|---|---|---|
| Type 1 | 만들기 쉽고 행이 늘지 않는다 | 내력이 없어진다 | "this technique destroys history" | [Kimball Type 1](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-1/) |
| Type 1 | 위와 같다 | 옛 값으로 묶은 집계가 달라져서 다시 계산해야 한다 | "This SCD type doesn't preserve historical perspective because the existing row is updated." | [Fabric dimension tables](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables) |
| Type 1 | 위와 같다 | 규제를 받는 환경에서는 쓰지 못할 수 있다 | "Type 1 changes may be outlawed" | [Kimball 2008 1부](https://www.kimballgroup.com/2008/08/slowly-changing-dimensions/) |
| Type 2 | 내력을 그대로 지킨다 | 행마다 새 surrogate key를 주고, 시작 시각·끝 시각·지금 값 표시를 더 둔다 | "Type 2, in particular, allows us to make good on the data warehouse pledge to preserve history faithfully." | [Kimball 2008 2부](https://www.kimballgroup.com/2008/09/slowly-changing-dimensions-part-2/) |
| Type 2 | 위와 같다 | version이 너무 많으면 읽는 사람이 알아보기 어렵다 | "Try to avoid having too many SCD type 2 changes on a dimension table because it can result in an overwhelming number of versions that might make it difficult for analysts to comprehend." | [Fabric dimension tables](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-dimension-tables) |
| Type 3 | 옛 값과 지금 값을 한 행에서 고른다 | 옛 값을 몇 개밖에 두지 못한다 | "this approach does not scale gracefully beyond a few choices" | [Kimball 2008 2부](https://www.kimballgroup.com/2008/09/slowly-changing-dimensions-part-2/) |
| history table | 내력이 저절로 남고, 적재 code를 더 쓰지 않는다 | 유효 기간이 DB에 쓴 시각으로 정해져서, 늦게 적재한 data에는 맞지 않을 수 있다 | "If you load data with a significant delay, transaction time might not be acceptable." | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions) |
| history table | 위와 같다 | 적재한 뒤에는 옛 data를 고칠 수 없다 | "By default, system-versioned temporal tables don't allow changing historical data after loading" | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions) |
| history table | 위와 같다 | column 하나만 바뀌어도 version이 생긴다 | "Temporal system-versioned tables generate a row version on any column change." | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions) |

Type 2의 행에 더 두는 column은 Kimball Group이 셋으로 든다. 원문은 "1) row effective date or date/time stamp; 2) row expiration date or date/time stamp; and 3) current row indicator"다([Kimball Type 2](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/)).

Kimball은 Type 1을 쓰려면 방침을 드러내 두라고 적는다. 원문은 "The data warehouse needs an explicit, visible policy for Type 1 fields"다([Kimball 2008 1부](https://www.kimballgroup.com/2008/08/slowly-changing-dimensions/)).

### 문제

쓰는 사람이 낸 보고는 dbt의 snapshot에서 둘을 옮긴다.

dbt는 SQL로 data를 변환하는 도구이고, snapshot은 Type 2를 만드는 기능이다. 문서는 "Snapshots implement type-2 Slowly Changing Dimensions over mutable source tables."라고 적는다([dbt snapshots](https://docs.getdbt.com/docs/build/snapshots)).

| issue | 겪은 것 | 원문 | 답 |
|---|---|---|---|
| [dbt #4661](https://github.com/dbt-labs/dbt/issues/4661) | key 하나에 지금 값으로 표시된 행이 여럿 쌓인다 | "One of my running snapshots is amassing multiple valid records per unique_key." | graciegoheen(CONTRIBUTOR)이 명령을 동시에 둘 돌리지 말라는 문서를 들고 닫았다. 다른 사용자는 명령 하나만 돌려도 생긴다고 답했다 |
| [dbt #11235](https://github.com/dbt-labs/dbt/issues/11235) | 값이 `null`에서 바뀔 때 같은 행이 둘 들어간다 | "two rows identical rows are inserted instead of just one" | dbeatty10(CONTRIBUTOR)이 재현하지 못했다고 답했다. "many were never able to be reproduced" 열려 있다 |

SQL Server의 temporal table을 쓰는 사람이 낸 보고는 찾지 않았다.

## 세 방식으로 가름

issue #33은 옛 것을 두는 방식을 셋으로 든다. 이 글에서는 고쳐 쓰기, 옮기기, 지우기로 부른다.

| 이름 | 뜻 |
|---|---|
| 고쳐 쓰기 | 옛 것이 놓인 자리에 새 글을 쓰고, 옛 글은 따로 남긴 기록에서 되찾는다 |
| 옮기기 | 옛 것을 평소에 읽지 않는 다른 곳으로 옮긴다 |
| 지우기 | 옛 것을 없앤다 |

네 시스템의 방식을 세 물음으로 가른다. 가까운 방식 칸은 앞의 세 칸에서 나온다.

| 시스템과 방식 | 새 글이 놓이는 자리 | 옛 글이 남는 곳 | 기본 읽기에 옛 글이 나오는가 | 가까운 방식 |
|---|---|---|---|---|
| Mem0 1.0.11의 UPDATE | 옛 기억의 자리 | history table | 나오지 않는다 | 고쳐 쓰기 |
| Mem0 1.0.11의 DELETE | 새 글을 꼭 넣지는 않는다 | history table | 나오지 않는다 | 지우기. 내력은 남는다 |
| Mem0 2.x | 새 기억 | 제자리에 그대로 | 나온다 | 셋에 들지 않는다. 둘 다 둔다 |
| Mem0 Platform의 Supersede | 새 기억 | 제자리에 표시를 달고 | 나온다. `latest_only=true`를 주면 빠진다 | 셋에 들지 않는다. 남기고 표시한다 |
| Mem0 Platform의 Merge | 자세한 쪽의 기억 | 제자리에 표시를 달고 | 나오지 않는다 | 옮기기에 가깝다. 자리는 그대로이고 표시로 뺀다 |
| Graphiti의 edge | 새 edge | 제자리에 시각을 달고 | 나온다. filter를 주면 빠진다 | 셋에 들지 않는다. 남기고 표시한다 |
| Graphiti의 node summary | 옛 summary의 자리 | 옛 summary는 남지 않는다. 원문 episode는 남는다 | 나오지 않는다 | 고쳐 쓰기 |
| Letta V1의 기본 경로 | 옛 글의 자리 | block 쪽에는 없다 | 나오지 않는다 | 고쳐 쓰기에서 옛 글을 남기는 기록이 빠진 것 |
| Letta V1의 git 경로 | 옛 글의 자리 | git history | 나오지 않는다 | 고쳐 쓰기 |
| 지금의 Letta | 옛 글의 자리 | git history. 근거가 된 대화는 대화 기록에 남는다 | 나오지 않는다 | 고쳐 쓰기 |
| SCD Type 1 | 옛 값의 자리 | 없다 | 나오지 않는다 | 고쳐 쓰기에서 옛 글을 남기는 기록이 빠진 것 |
| SCD Type 2 | 새 행 | 같은 table에 끝 시각과 표시를 달고 | 나온다. 지금 값 표시로 거른다 | 셋에 들지 않는다. 남기고 표시한다 |
| SCD Type 3 | 옛 값의 자리 | 같은 행의 다른 column | 나온다 | 셋에 들지 않는다 |
| history table | 옛 행의 자리 | history table | 나오지 않는다 | 옮기기 |

옛 것을 제자리에 남기고 표시를 다는 방식은 넷이다. Mem0 Platform의 Supersede, Graphiti의 edge, SCD Type 2에서는 읽는 쪽이 filter를 주어야 옛 것이 빠진다. Mem0 Platform의 Merge에서는 표시가 붙은 것이 기본 읽기에서 빠진다.

SCD Type 1은 옛 값을 어디에도 남기지 않는다. Letta V1의 기본 경로는 block 쪽에 옛 글을 남기지 않고, 대화 기록에서 되찾을 수 있는지는 확인하지 못했다. Mem0 1.0.11의 DELETE는 store에서 지우지만 history table에 옛 글을 남긴다.

## issue #34의 주장과 견줌

issue #34가 확인하지 않은 주장으로 적은 넷을 문장 일곱으로 나누어 견준다.

| 주장 | 판정 | 근거 | 출처 |
|---|---|---|---|
| Mem0는 새 기억을 넣을 때 모델이 기존 기억과 견주어 더하기, 고치기, 지우기, 그대로 두기 가운데 하나를 고른다 | 일부만 맞다 | 논문과 1.0.11까지의 code에서는 맞다. 2.0.0부터 open source는 더하기만 한다. Platform은 넣을 때 superseded와 merged 표시를 단다 | [Mem0 논문](https://arxiv.org/abs/2504.19413) 2.1절, [Mem0 migration](https://docs.mem0.ai/migration/oss-v2-to-v3), [Mem0 Dream](https://docs.mem0.ai/platform/features/dream) |
| Mem0는 바뀐 내력을 따로 남긴다 | 맞다 | SQLite의 history table에 옛 글, 새 글, 사건 종류를 적는다. 2.x의 `add()`는 ADD 행만 적는다 | [Mem0 storage.py](https://github.com/mem0ai/mem0/blob/f1791daa86d469249c9b002f62644d58a1eb96a0/mem0/memory/storage.py#L102-L125) |
| Graphiti는 옛 사실을 지우지 않고, 그 사실이 맞지 않게 된 시각을 적어 둔다 | 맞다 | edge에 `invalid_at`과 `expired_at`을 적는다. entity node의 summary는 덮어쓴다 | [Graphiti README](https://github.com/getzep/graphiti/blob/3a8a78c997a07cceeb3411ede533b0f342d71c64/README.md?plain=1#L125-L126), [graphiti #1166](https://github.com/getzep/graphiti/issues/1166) |
| Letta의 에이전트는 memory block의 글을 도구로 고쳐 쓴다 | 일부만 맞다 | V1 server에서는 맞다. 지금의 Letta는 기억 전용 고치기 도구 없이 파일 도구로 Markdown 파일을 고친다 | [Letta V1 base.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/functions/function_sets/base.py#L263-L281), [Letta MemFS](https://docs.letta.com/concepts/memfs) |
| Letta에서 고친 뒤 옛 글은 따로 남지 않는다 | 일부만 맞다 | V1의 기본 경로에서는 block 쪽에 남지 않는다. V1의 git 경로와 지금의 Letta는 git history에 남긴다 | [Letta V1 block_manager_git.py](https://github.com/letta-ai/letta/blob/56ba9c25552605eec89de8ed3dc6394b625c1993/letta/services/block_manager_git.py#L1-L8), [Letta MemFS](https://docs.letta.com/concepts/memfs) |
| SCD에는 덮어쓰기(Type 1)와 새 행으로 쌓기(Type 2)가 있다 | 맞다 | Kimball Group의 이름이 Overwrite와 Add New Row다 | [Kimball Type 1](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-1/), [Kimball Type 2](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/) |
| 옛 값을 history table로 옮기는 방식이 Type 4다 | 일부만 맞다 | Microsoft의 문서는 그렇게 적는다. 번호를 붙인 Kimball Group의 Type 4는 mini-dimension이다 | [temporal usage](https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-table-usage-scenarios#slowly-changing-dimensions), [Kimball Type 4](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-4-mini-dimension/) |

## 확인하지 못한 것

| 모르는 것 | 읽은 데까지 | 알아볼 방법 |
|---|---|---|
| Mem0 Platform이 뒤집힘과 겹침을 가리는 것이 모델인지 규칙인지 | Dream 문서는 가리는 때만 적는다. Platform의 code는 공개되어 있지 않다 | Platform에 뒤집히는 두 문장을 넣고 응답과 dashboard를 본다 |
| Mem0 2.x가 LLM이 돌려준 `linked_memory_ids`를 저장하는지 | payload를 짓는 code는 `text`와 `attributed_to`만 읽는다. 저장하는 자리를 찾지 못했다 | `add()`를 돌린 뒤 vector store의 payload를 본다 |
| Mem0에 history의 옛 글로 되돌리는 API가 있는지 | `Memory` class에는 `history()`만 있다. Platform의 API는 읽지 않았다 | Platform의 API reference를 읽는다 |
| Graphiti의 기본 검색이 무효가 된 edge를 순위에서 낮추는지 | filter를 주지 않으면 거르는 code가 없다는 것까지 읽었다. graphiti #1728의 보고자는 검색이 그런 edge를 낮추거나 뺀다고 적는다 | 무효가 된 edge가 있는 graph에 `search()`를 돌려 본다 |
| Zep service가 Graphiti와 같은 방식으로 무효를 가리는지 | Zep 문서는 Zep이 따로 가진 추출 모델을 쓴다고 적는다. service의 code는 공개되어 있지 않다 | Zep에 뒤집히는 두 episode를 넣고 edge를 본다 |
| Letta V1의 기본 경로에서 `memory_rethink`로 바꾼 옛 글을 대화 기록에서 되찾을 수 있는지 | 도구의 인자에 옛 글이 없다는 것까지 읽었다. V1이 system message를 대화 기록에 남기는지는 읽지 않았다 | `archive` branch의 message 저장 code를 읽는다 |
| letta #3431의 답이 틀렸다고 한 대목이 어디인지 | 답은 대목을 적지 않는다. checkpoint를 부르는 곳이 test뿐이라는 것은 `grep`으로 같은 결과를 얻었다 | `letta-ai/letta-code`의 issue로 묻는다 |
| 지금의 Letta에서 에이전트가 commit을 빠뜨린 고침이 어떻게 되는지 | harness가 다음 turn에 알린다는 것까지 읽었다 | Letta Code를 돌려 commit하지 않고 대화를 끝내 본다 |
| letta-code #4029의 실패율이 Letta Code를 돌렸을 때도 같은지 | 보고자는 prompt만 모델에 주어 쟀다고 적는다 | 같은 case를 Letta Code의 reflection으로 돌린다 |
| Kimball의 책이 Type 4를 어떻게 적는지 | Kimball Group의 web 글만 읽었다. The Data Warehouse Toolkit 3판은 읽지 않았다 | 책에서 slowly changing dimension을 다루는 장을 읽는다 |
| SCD에서 겹침을 다루는 규칙 | 읽은 문서는 값이 바뀐 때만 적는다. SQL Server는 값이 바뀌지 않은 수정에도 history 행을 더한다고 적는다 | Kimball의 ETL 글과 dbt snapshot의 strategy 문서를 읽는다 |
| temporal table을 쓰는 사람이 겪은 문제 | 문서의 고려 사항까지 옮겼다. 사용자 보고는 찾지 않았다 | Microsoft Q&A를 찾는다 |

## 새 질문 후보

- 모델이 뒤집힘이라고 가린 판정이 틀리는 비율을 무엇으로 재는가. graphiti #1728은 손으로 본 넷 가운데 셋이, letta-code #4029는 그대로 두어야 하는 case의 절반이 틀렸다고 적는다. 에이전트가 틀리게 바꿨을 때 사람이 알아채는 길을 정할 때 쓰인다.
- 분류된 항목이 늘면 새 원문과 견줄 항목을 어떻게 고르는가. Mem0는 10개를, Graphiti는 검색이 돌려준 것만 모델에 보이고, graphiti #1956은 그 한도 때문에 지금 값이 후보에서 빠진다고 적는다. 알아보는 범위를 정할 때 쓰인다.
- 기억 폴더를 git으로 관리하면 읽기 전용 원문 보관과 덧붙이기만 하는 로그가 하는 일 가운데 무엇이 겹치는가. 지금의 Letta는 옛 글을 git history에, 까닭을 commit message에 둔다. 로그와 원문 보관의 자리와 모양을 정할 때 쓰인다.
