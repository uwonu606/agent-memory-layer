"""경우 묶음. 상태 기계가 받아야 하는 경우(IN), 다른 부품이 맡는 경우(OUT), 기대를 아직 정하지 않은 경우(OPEN).

IN의 각 경우는 기계 하나를 받아 (확인할 것, 맞았나) 목록을 돌려준다. 기대는 상태 이름이 아니라 보이는 행동으로 적어서,
상태 이름을 바꾼 기계에도 같은 경우를 돌릴 수 있다.
"""

from machine import against, support

PERSONAL = {"repo:todo-app", "work:personal", "person"}
JOB = {"repo:corp-portal", "work:job", "person"}


def _is_live(m, memory):
    return memory.id in {x.id for x in m.live(memory.subject)}


def s01_other_context_stays_out(m):
    m.remember("pip 미러", "pip 미러는 사내 주소", "s0#1", {"work:job"})
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.open_session("s4", PERSONAL)
    m.load("s4")
    return [("todo-app 세션에 uv만 실린다", m.loaded_texts("s4") == {"uv를 쓴다"})]


def s02_local_rule_stays_local(m):
    m.remember("주석 방식", "여기서는 주석을 달지 마", "s1#3", {"repo:a"})
    m.open_session("s2", {"repo:b", "work:personal", "person"})
    m.load("s2")
    return [("다른 저장소에는 실리지 않는다", m.loaded_texts("s2") == set())]


def s03_stale_by_cleanup(m):
    m.capture("테스트 결과", "test_login은 깨진다", "s1#2", {"repo:a"})
    memory = m.capture("테스트 결과", "test_login은 깨진다", "s2#5", {"repo:a"})
    m.retire(memory, "stale", "cleanup")
    m.open_session("s3", {"repo:a"})
    m.load("s3")
    return [("낡은 기억은 실리지 않는다", m.loaded_texts("s3") == set())]


def s04_human_retires_while_loaded(m):
    memory = m.remember("배포 대상", "배포는 staging-1로", "s1#4", {"repo:a"})
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    m.forget(memory)
    return [
        ("세션 도중에 끝낼 수 있다", not _is_live(m, memory)),
        ("그 세션의 실린 목록에서 빠진다", "배포는 staging-1로" not in m.loaded_texts("s2")),
    ]


def s05_wrong_mark_while_loaded(m):
    memory = m.remember("디버깅", "원인은 캐시다", "s1#9", {"repo:a"})
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    m.retire(memory, "wrong", "human")
    return [("사람이 wrong으로 표시하면 바로 끝난다", not _is_live(m, memory))]


def s06_old_fact_reaches(m):
    m.remember("auth token 만료", "만료는 900초", "s1#1", {"repo:api"})
    for i in range(5):
        m.open_session(f"x{i}", {"repo:other"})
        m.load(f"x{i}")
    m.open_session("s9", {"repo:api"})
    m.load("s9")
    return [("여러 세션 뒤에도 그 저장소에 실린다", "만료는 900초" in m.loaded_texts("s9"))]


def s07_device_memory(m):
    m.remember("원격 기기 login", "remote-box는 ssh -J bastion", "s1#2", {"device:remote-box"})
    m.open_session("s2", {"repo:a", "device:remote-box"})
    m.load("s2")
    return [("기기에 걸린 기억이 그 기기 일에 실린다", "remote-box는 ssh -J bastion" in m.loaded_texts("s2"))]


def s08_no_memory_no_claim(m):
    m.open_session("s1", {"repo:new"})
    m.load("s1")
    loads = [e for e in m.log if e[0] == "load"]
    return [("새 저장소에는 아무것도 실리지 않는다", m.loaded_texts("s1") == set() and not loads)]


def s09_what_was_loaded_is_logged(m):
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.open_session("s4", PERSONAL)
    m.load("s4")
    loads = [e for e in m.log if e[0] == "load"]
    return [("실린 기억마다 기록 줄이 있다", len(loads) == 1)]


def s11_unsaid_words_refused(m):
    try:
        m.capture("배포", "금요일엔 배포 금지", "s1#7", {"repo:a"}, quote_found=False)
        refused = False
    except Exception:
        refused = True
    return [("인용이 기록에 없으면 생기지 않는다", refused and not m.memories)]


def s12_cleanup_cannot_override_human(m):
    memory = m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    try:
        m.retire(memory, "stale", "cleanup")
    except Exception:
        pass
    blocked = any(e[0] == "retire_blocked" for e in m.log)
    return [
        ("배경 정리는 사람이 정한 기억을 끝내지 못한다", _is_live(m, memory)),
        ("막혔다는 표시가 기록에 남는다", blocked),
    ]


def s13_restore_after_agent_fix(m):
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    old = m.capture("패키지 도구", "uv를 쓴다", "s3#2", {"repo:todo-app"})
    m.supersede(old, "poetry를 쓴다", "s6#11", "agent")
    m.restore(old, "human")
    live = m.live("패키지 도구")
    return [("되돌리면 살아 있는 기억은 옛 판 하나다", [x.text for x in live] == ["uv를 쓴다"])]


def s14_fix_keeps_both_versions(m):
    old = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    new = m.supersede(old, "poetry를 쓴다", "s6#11", "human")
    return [
        ("살아 있는 기억은 새 판 하나다", [x.text for x in m.live("패키지 도구")] == ["poetry를 쓴다"]),
        ("옛 판은 지우지 않는다", old.id in m.memories),
        ("옛 판과 새 판이 서로를 가리킨다", old.replaced_by == new.id and new.replaces == old.id),
    ]


def s15_fix_while_loaded(m):
    old = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.open_session("s6", PERSONAL)
    m.load("s6")
    m.supersede(old, "poetry를 쓴다", "s6#11", "human")
    return [("같은 세션에서 고치면 옛 판이 실린 목록에서 빠진다", "uv를 쓴다" not in m.loaded_texts("s6"))]


def s16_two_sessions_at_once(m):
    memory = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.open_session("A", PERSONAL)
    m.open_session("B", PERSONAL)
    m.load("A")
    m.load("B")
    both_loaded = "uv를 쓴다" in m.loaded_texts("A") and "uv를 쓴다" in m.loaded_texts("B")
    m.forget(memory)
    return [
        ("두 세션 모두에 실린다", both_loaded),
        ("끝낸 기억이 두 세션 모두에서 빠진다", m.loaded_texts("A") == set() and m.loaded_texts("B") == set()),
    ]


def s17_closer_scope_wins(m):
    m.remember("패키지 도구", "pip을 쓴다", "s0#1", {"person"})
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.open_session("s4", PERSONAL)
    m.load("s4")
    return [("같은 주제는 더 가까운 scope의 기억만 실린다", m.loaded_texts("s4") == {"uv를 쓴다"})]


def s18_widen_scope(m):
    memory = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:a"})
    m.supersede(memory, None, "s8#3", "human", applies_to={"person"})
    m.open_session("s9", {"repo:b", "person"})
    m.load("s9")
    return [("사람이 넓힌 scope로 다른 저장소에도 실린다", "uv를 쓴다" in m.loaded_texts("s9"))]


def s19_human_overrides_rejection(m):
    memory = m.remember("커밋 언어", "커밋 메시지는 영어", "s6#20", {"repo:a"})
    m.forget(memory)
    again = m.remember("커밋 언어", "커밋 메시지는 영어", "s9#1", {"repo:a"})
    return [("거절한 주제도 사람이 기억하라면 산다", _is_live(m, again))]


def s20_agent_cannot_revive_rejection(m):
    memory = m.capture("커밋 언어", "커밋 메시지는 영어", "s6#20", {"repo:a"})
    m.forget(memory)
    try:
        m.capture("커밋 언어", "커밋 메시지는 영어", "s9#4", {"repo:a"})
        refused = False
    except Exception:
        refused = True
    return [("거절한 주제는 다시 뽑아도 후보가 되지 않는다", refused)]


def s21_candidate_not_loaded(m):
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.open_session("s2", PERSONAL)
    m.load("s2")
    return [("한 번 한 말은 실리지 않는다", m.loaded_texts("s2") == set())]


def s22_repeat_promotes(m):
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    memory = m.capture("패키지 도구", "uv를 쓴다", "s3#2", {"repo:todo-app"})
    return [("되풀이되면 실릴 수 있는 기억이 된다", _is_live(m, memory))]


def s23_candidate_expires(m):
    memory = m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.retire(memory, "expired", "cleanup")
    return [("되풀이되지 않은 후보는 끝난다", memory.end_reason == "expired")]


def s24_agent_promotion_is_attributed(m):
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    memory = m.capture("패키지 도구", "uv를 쓴다", "s3#2", {"repo:todo-app"})
    promotes = [e for e in m.log if e[0] == "promote" and e[1] == memory.id]
    return [("agent가 올린 것은 누가 올렸는지 기록에 남는다", bool(promotes) and promotes[0][2] == "agent")]


def s25_agent_words_cannot_change_human_decision(m):
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.capture("패키지 도구", "poetry를 쓴다", "s6#2", {"repo:todo-app"})
    said = m.capture("패키지 도구", "poetry를 쓴다", "s7#5", {"repo:todo-app"})
    held = any(e[0] == "held_by_human_decision" for e in m.log)
    return [
        ("agent의 말이 되풀이되어도 사람이 정한 기억은 그대로다", [x.text for x in m.live("패키지 도구")] == ["uv를 쓴다"]),
        ("그 말은 후보로 남고, 막혔다는 줄이 기록에 남는다", said.state == "candidate" and held),
    ]


def s26_origin_never_changes(m):
    old = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.supersede(old, "poetry를 쓴다", "s6#11", "human")
    m.restore(old, "human")
    return [("고치고 되돌려도 처음 출처는 그대로다", old.origin == "s1#14")]


def s27_restore_rejected(m):
    memory = m.remember("커밋 언어", "커밋 메시지는 영어", "s6#20", {"repo:a"})
    m.forget(memory)
    m.restore(memory, "human")
    return [("잘못 거절한 것도 되돌린다", _is_live(m, memory))]


def _loads(m, memory_id=None):
    return [e for e in m.log if e[0] == "load" and (memory_id is None or e[1] == memory_id)]


def _uv_repo(m, repo="repo:a"):
    m.put_file(repo, "uv.lock")


def _uv_memory(m, scope=frozenset({"repo:a"}), by="agent", **details):
    details.setdefault("kind", "repo_fact_pointer")
    details.setdefault("evidence", (support("uv.lock"), against("poetry.lock")))
    if by == "human":
        return m.remember("패키지 도구", "uv를 쓴다", "s1#14", scope, **details)
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", scope, **details)
    return m.capture("패키지 도구", "uv를 쓴다", "s3#2", scope, **details)


def s28_compaction_reloads_start_portion(m):
    kept = m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    dropped = m.remember("배포 대상", "배포는 staging-1로", "s1#4", {"repo:a"})
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    m.forget(dropped)
    added = m.remember("테스트 명령", "테스트는 make test", "s2#9", {"repo:a"})
    before_compaction = set(m.sessions["s2"].loaded)
    m.compact("s2")
    unloads = {e[1] for e in m.log if e[0] == "unload" and e[3].get("reason") == "compaction"}
    return [
        ("compaction 전에 실린 것마다 내린 줄이 있다", unloads == before_compaction),
        ("다시 실린 것은 그 때의 세션 시작 몫이다",
         m.loaded_texts("s2") == {kept.text, added.text}),
    ]


def s29_resume_keeps_loaded(m):
    m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    lines_before = len(m.log)
    m.resume("s2")
    new_lines = [e[0] for e in m.log[lines_before:] if e[0] in ("load", "unload")]
    return [
        ("resume하면 실린 것이 그대로다", m.loaded_texts("s2") == {"커밋 메시지는 한국어"}),
        ("resume은 싣거나 내리지 않는다", new_lines == []),
    ]


def s30_loaded_not_loaded_again(m):
    memory = m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    m.load("s2")
    return [("이미 실린 기억은 다시 싣지 않는다", len(_loads(m, memory.id)) == 1)]


def s31_against_evidence_ends_agent_memory(m):
    _uv_repo(m)
    memory = _uv_memory(m)
    m.put_file("repo:a", "poetry.lock")
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    return [
        ("반대 근거가 참이면 싣지 않는다", m.loaded_texts("s2") == set()),
        ("scope가 비어 agent의 기억은 낡음으로 끝난다", memory.state == "retired" and memory.end_reason == "stale"),
    ]


def s32_moved_support_fixes_path(m):
    _uv_repo(m)
    memory = _uv_memory(m)
    m.drop_file("repo:a", "uv.lock")
    m.put_file("repo:a", "backend/uv.lock")
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    fixed = any(e[0] == "evidence_path_fixed" and e[1] == memory.id for e in m.log)
    return [
        ("지지 근거가 옮겨 가면 찾아서 싣는다", "uv를 쓴다" in m.loaded_texts("s2")),
        ("고친 경로가 근거 칸과 기록에 남는다", support("backend/uv.lock") in memory.evidence and fixed),
    ]


def s33_unrunnable_check_is_unknown(m):
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"person"},
               kind="repo_fact_pointer", evidence=(support("uv.lock"),))
    m.open_session("s2", {"repo:fresh", "person"})
    m.load("s2")
    unknown = [e for e in _loads(m) if e[3].get("evidence") == "unknown"]
    return [("검사가 돌지 못하면 낡음으로 치지 않고 싣되 모름을 남긴다", "uv를 쓴다" in m.loaded_texts("s2") and bool(unknown))]


def s34_capture_keeps_only_true_checks(m):
    _uv_repo(m)
    m.put_file("repo:a", "poetry.lock")
    memory = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:a"},
                        evidence=(support("uv.lock"), support("requirements.txt"), against("poetry.lock"), against("Pipfile")))
    return [("capture 때 지금 참인 지지 근거와 지금 거짓인 반대 근거만 남는다",
             set(memory.evidence) == {support("uv.lock"), against("Pipfile")})]


def s35_expired_agent_memory(m):
    memory = _uv_memory(m, kind="external_fact", transient=True, evidence=(), expires_in=7)
    m.advance(8)
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    return [
        ("기한이 지난 기억은 싣지 않는다", m.loaded_texts("s2") == set()),
        ("agent의 기억은 낡음으로 끝난다", memory.state == "retired" and memory.end_reason == "stale"),
    ]


def s36_repeat_restarts_expiry(m):
    say = dict(kind="external_fact", transient=True, expires_in=7)
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s1#2", {"repo:a"}, **say)
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s2#4", {"repo:a"}, **say)
    m.advance(5)
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s3#1", {"repo:a"}, **say)
    m.advance(5)
    m.open_session("s4", {"repo:a"})
    m.load("s4")
    return [("같은 문장이 다시 나오면 기한이 다시 시작한다", m.loaded_texts("s4") == {"스테이징은 10.0.0.5"})]


def s37_lasting_rule_has_no_expiry(m):
    memory = m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"}, expires_in=7)
    m.advance(1000)
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    return [
        ("지금 상태가 아닌 기억에는 기한이 없다", memory.expires is None),
        ("오래 지나도 실린다", m.loaded_texts("s2") == {"커밋 메시지는 한국어"}),
    ]


def s38_human_memory_held_then_back(m):
    _uv_repo(m)
    memory = _uv_memory(m, by="human")
    m.put_file("repo:a", "poetry.lock")
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    held = any(e[0] == "held" and e[1] == memory.id for e in m.log)
    not_loaded = m.loaded_texts("s2") == set()
    m.drop_file("repo:a", "poetry.lock")
    m.open_session("s3", {"repo:a"})
    m.load("s3")
    return [
        ("근거가 어긋난 사람의 기억은 싣지 않는다", not_loaded),
        ("끝내지 않고 막혔다는 줄만 남긴다", memory.state == "active" and held),
        ("근거가 다시 맞으면 저절로 다시 실린다", m.loaded_texts("s3") == {"uv를 쓴다"}),
    ]


def s39_human_memory_expired_then_said_again(m):
    say = dict(kind="external_fact", transient=True, expires_in=7)
    memory = m.remember("스테이징 주소", "스테이징은 10.0.0.5", "s1#2", {"repo:a"}, **say)
    m.advance(8)
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    not_loaded = m.loaded_texts("s2") == set()
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s9#3", {"repo:a"}, **say)
    m.open_session("s3", {"repo:a"})
    m.load("s3")
    return [
        ("기한이 지난 사람의 기억은 싣지 않는다", not_loaded),
        ("끝내지 않는다", memory.state == "active"),
        ("같은 문장이 다시 나오면 다시 실린다", m.loaded_texts("s3") == {"스테이징은 10.0.0.5"}),
    ]


def s40_split_on_evidence(m):
    _uv_repo(m, "repo:a")
    _uv_repo(m, "repo:b")
    _uv_memory(m, scope={"repo:a", "repo:b"})
    m.put_file("repo:a", "poetry.lock")
    m.open_session("A", {"repo:a"})
    m.load("A")
    m.open_session("B", {"repo:b"})
    m.load("B")
    live = m.live("패키지 도구")
    return [
        ("어긋난 저장소만 scope에서 빠진다", [set(x.applies_to) for x in live] == [{"repo:b"}]),
        ("어긋난 저장소에는 싣지 않고 맞는 저장소에는 싣는다",
         m.loaded_texts("A") == set() and m.loaded_texts("B") == {"uv를 쓴다"}),
    ]


def s41_split_on_new_value(m):
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:a", "repo:b"})
    m.capture("패키지 도구", "uv를 쓴다", "s3#2", {"repo:a", "repo:b"})
    m.capture("패키지 도구", "poetry를 쓴다", "s6#2", {"repo:a"})
    m.open_session("A", {"repo:a"})
    m.load("A")
    m.open_session("B", {"repo:b"})
    m.load("B")
    return [
        ("다른 값이 온 저장소에는 새 값이 실린다", m.loaded_texts("A") == {"poetry를 쓴다"}),
        ("나머지 저장소는 옛 값 그대로다", m.loaded_texts("B") == {"uv를 쓴다"}),
    ]


def s42_broad_change_supersedes_all(m):
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:a", "repo:b"})
    m.remember("패키지 도구", "poetry를 쓴다", "s6#2", {"repo:a", "repo:b"})
    return [("모든 곳을 바꾸라면 기억 하나로 바뀐다",
             [(x.text, set(x.applies_to)) for x in m.live("패키지 도구")] == [("poetry를 쓴다", {"repo:a", "repo:b"})])]


def s43_compaction_rechecks_evidence(m):
    _uv_repo(m)
    _uv_memory(m)
    m.open_session("s2", {"repo:a"})
    m.load("s2")
    loaded_first = m.loaded_texts("s2") == {"uv를 쓴다"}
    m.put_file("repo:a", "poetry.lock")
    m.compact("s2")
    return [("세션 도중 근거가 어긋나면 compaction 뒤에 다시 싣지 않는다", loaded_first and m.loaded_texts("s2") == set())]


def s44_broad_scope_evidence_mismatch(m):
    _uv_repo(m, "repo:a")
    _uv_repo(m, "repo:b")
    _uv_memory(m, scope={"person"})
    m.put_file("repo:a", "poetry.lock")
    m.open_session("A", {"repo:a", "person"})
    m.load("A")
    m.open_session("B", {"repo:b", "person"})
    m.load("B")
    return [("넓은 scope의 기억은 어긋난 저장소에만 실리지 않는다",
             m.loaded_texts("A") == set() and m.loaded_texts("B") == {"uv를 쓴다"})]


def s45_queue_check_without_session(m):
    _uv_repo(m)
    memory = _uv_memory(m)
    m.put_file("repo:a", "poetry.lock")
    m.check_evidence("repo:a")
    return [("큐 처리의 판정도 세션 없이 낡음을 끝낸다", memory.state == "retired" and memory.end_reason == "stale")]


def s46_promote_meets_restored_version(m):
    old = m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:a"})
    m.retire(old, "wrong", "human")
    m.capture("패키지 도구", "poetry를 쓴다", "s2#3", {"repo:a", "repo:b"})
    m.restore(old, "human")
    m.capture("패키지 도구", "poetry를 쓴다", "s5#1", {"repo:b"})
    live = m.live("패키지 도구")
    overlapping = [(a.id, b.id) for i, a in enumerate(live) for b in live[i + 1:] if a.applies_to & b.applies_to]
    return [("후보가 올라가도 같은 주제·겹치는 scope의 살아 있는 기억은 하나다", not overlapping)]


def s47_different_text_is_not_a_repeat(m):
    m.capture("패키지 도구", "poetry를 쓴다", "s1#2", {"repo:a"})
    m.remember("패키지 도구", "uv를 쓴다", "s2#1", {"repo:a"})
    return [("후보와 다른 문장은 되풀이로 세지 않고, 사람이 기억하라 한 문장이 산다",
             [x.text for x in m.live("패키지 도구")] == ["uv를 쓴다"])]


def s48_candidate_keeps_unoverlapped_part(m):
    m.capture("패키지 도구", "poetry를 쓴다", "s1#2", {"repo:a", "repo:b"})
    m.remember("패키지 도구", "uv를 쓴다", "s2#1", {"repo:a"})
    m.capture("패키지 도구", "poetry를 쓴다", "s5#1", {"repo:b"})
    live = sorted((x.text, tuple(sorted(x.applies_to))) for x in m.live("패키지 도구"))
    return [("새 말과 겹친 저장소만 후보에서 빠지고, 남은 저장소의 되풀이는 이어서 센다",
             live == [("poetry를 쓴다", ("repo:b",)), ("uv를 쓴다", ("repo:a",))])]


def s49_later_person_statement_keeps_closer(m):
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.capture("패키지 도구", "pip을 쓴다", "s5#2", {"person"})
    m.capture("패키지 도구", "pip을 쓴다", "s6#2", {"person"})
    m.open_session("t", PERSONAL)
    m.load("t")
    m.open_session("o", {"repo:other", "person"})
    m.load("o")
    return [
        ("뒤에 온 사람에 관한 문장은 가까운 저장소의 기억을 덮지 않는다", m.loaded_texts("t") == {"uv를 쓴다"}),
        ("가까운 기억이 없는 곳에는 넓은 기억이 실린다", m.loaded_texts("o") == {"pip을 쓴다"}),
    ]


def s50_everywhere_overrides_closer(m):
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.remember("패키지 도구", "pip을 쓴다", "s5#2", {"person"}, everywhere=True)
    m.open_session("t", PERSONAL)
    m.load("t")
    return [("사람이 어디서나라고 하면 좁은 기억까지 덮는다", m.loaded_texts("t") == {"pip을 쓴다"})]


def s51_closer_appears_mid_session(m):
    m.remember("패키지 도구", "pip을 쓴다", "s0#1", {"person"})
    m.open_session("t", PERSONAL)
    m.load("t")
    m.remember("패키지 도구", "uv를 쓴다", "s1#14", {"repo:todo-app"})
    m.load("t")
    return [("세션 도중 가까운 기억이 생기면 먼 기억을 내리고 가까운 기억을 싣는다", m.loaded_texts("t") == {"uv를 쓴다"})]


def s52_same_height_later_wins(m):
    m.remember("발표 형식", "슬라이드는 16:9", "s1#3", {"work:job"})
    m.remember("발표 형식", "슬라이드는 4:3", "s2#3", {"work:study"})
    m.open_session("t", {"repo:notes", "work:job", "work:study", "person"})
    m.load("t")
    return [("같은 높이에서 겹치면 뒤에 나온 기억이 실린다", m.loaded_texts("t") == {"슬라이드는 4:3"})]


def s53_same_session_repeat_not_counted(m):
    m.capture("테스트 결과", "test_login은 깨진다", "s1#2", {"repo:a"})
    memory = m.capture("테스트 결과", "test_login은 깨진다", "s1#5", {"repo:a"})
    m.capture("테스트 결과", "test_login은 깨진다", "s1#9", {"repo:a"})
    return [("한 세션 안에서 몇 번을 말해도 되풀이는 한 번이다", memory.state == "candidate")]


def s54_repeat_across_repos_merges(m):
    m.capture("커밋 언어", "커밋 메시지는 한국어", "s1#2", {"repo:a"})
    m.capture("커밋 언어", "커밋 메시지는 한국어", "s2#4", {"repo:b"})
    live = m.live("커밋 언어")
    return [("다른 저장소의 다른 세션에서 나온 같은 말은 합쳐져 기억이 되고, scope는 나온 저장소들이다",
             [set(x.applies_to) for x in live] == [{"repo:a", "repo:b"}])]


def s55_active_widens_on_one_sighting(m):
    m.capture("커밋 언어", "커밋 메시지는 한국어", "s1#2", {"repo:a"})
    m.capture("커밋 언어", "커밋 메시지는 한국어", "s2#4", {"repo:a"})
    m.capture("커밋 언어", "커밋 메시지는 한국어", "s7#1", {"repo:c"})
    m.open_session("c", {"repo:c"})
    m.load("c")
    return [
        ("기억이 된 문장은 새 저장소에서 한 번 나와도 그 저장소까지 넓힌다",
         [set(x.applies_to) for x in m.live("커밋 언어")] == [{"repo:a", "repo:c"}]),
        ("넓힌 저장소에 실린다", m.loaded_texts("c") == {"커밋 메시지는 한국어"}),
    ]


def s56_human_memory_not_merged_with_agent_sighting(m):
    m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#2", {"repo:a"})
    seen = m.capture("커밋 언어", "커밋 메시지는 한국어", "s2#4", {"repo:b"})
    return [
        ("사람이 정한 기억과 agent가 본 칸은 합치지 않는다",
         [set(x.applies_to) for x in m.live("커밋 언어")] == [{"repo:a"}]),
        ("agent가 본 칸은 따로 후보로 센다", seen.state == "candidate" and set(seen.applies_to) == {"repo:b"}),
    ]


def s57_expiry_per_target(m):
    say = dict(kind="external_fact", transient=True, expires_in=14)
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s1#2", {"repo:a"}, **say)
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s2#2", {"repo:a"}, **say)
    m.advance(6)
    m.capture("스테이징 주소", "스테이징은 10.0.0.5", "s3#1", {"repo:b"}, **say)
    m.advance(9)
    m.open_session("A", {"repo:a"})
    m.load("A")
    m.open_session("B", {"repo:b"})
    m.load("B")
    return [
        ("기한은 대상마다 따로 지난다", m.loaded_texts("A") == set() and m.loaded_texts("B") == {"스테이징은 10.0.0.5"}),
        ("기한이 지난 대상만 scope에서 빠진다", [set(x.applies_to) for x in m.live("스테이징 주소")] == [{"repo:b"}]),
    ]


def s58_one_word_over_two_versions(m):
    m.remember("패키지 도구", "poetry를 쓴다", "s1#1", {"repo:a", "person"})
    m.capture("패키지 도구", "uv를 쓴다", "s2#1", {"repo:b"})
    m.capture("패키지 도구", "uv를 쓴다", "s3#1", {"repo:b"})
    m.remember("패키지 도구", "uv를 쓴다", "s4#1", {"repo:a", "repo:b"})
    live = [x for x in m.live("패키지 도구") if x.applies_to & {"repo:a", "repo:b"}]
    return [("말 하나가 살아 있는 기억 여럿과 겹쳐도 겹치는 칸마다 기억은 하나다",
             all(not (x.applies_to & y.applies_to) for i, x in enumerate(live) for y in live[i + 1:]))]


def s59_rejection_stays_in_its_cells(m):
    rejected = m.remember("커밋 언어", "커밋 메시지는 영어", "s1#1", {"repo:a"})
    m.forget(rejected)
    m.capture("커밋 언어", "커밋 메시지는 영어", "s2#1", {"repo:b"})
    elsewhere = m.capture("커밋 언어", "커밋 메시지는 영어", "s3#1", {"repo:b"})
    return [("거절은 그 말을 한 scope의 칸에만 닿는다", elsewhere.state == "active" and set(elsewhere.applies_to) == {"repo:b"})]


def s60_clear_human_decision_once(m):
    memory = m.capture("커밋 언어", "커밋 메시지는 한국어", "s1#3", {"repo:a"}, by="human", clear=True)
    m.open_session("n", {"repo:a"})
    m.load("n")
    loaded = m.loaded_texts("n") == {"커밋 메시지는 한국어"}
    m.retire(memory, "stale", "cleanup")
    return [
        ("분명히 둘 사람의 결정은 한 번 말해도 다음 세션에 실린다", loaded),
        ("판정은 모델이 해서 agent가 올린 것이고, 배경 정리가 끝낼 수 있다", memory.state == "retired"),
    ]


def s61_clear_judgement_needs_human_words(m):
    memory = m.capture("빌드 시간", "빌드는 3분 걸린다", "s1#8", {"repo:a"}, by="agent", clear=True)
    return [("agent의 말은 분명해 보여도 한 번에 올리지 않는다", memory.state == "candidate")]


def s62_unclear_human_words_wait(m):
    m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    said = m.capture("커밋 언어", "커밋 메시지는 영어", "s2#3", {"repo:a"}, by="human")
    return [
        ("분명하지 않은 사람의 말은 사람이 정한 기억을 바꾸지 못한다", [x.text for x in m.live("커밋 언어")] == ["커밋 메시지는 한국어"]),
        ("그 말은 후보로 남는다", said.state == "candidate"),
    ]


def s63_clear_human_words_change_human_decision(m):
    m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    new = m.capture("커밋 언어", "커밋 메시지는 영어", "s2#3", {"repo:a"}, by="human", clear=True)
    return [
        ("사람의 분명한 말은 고쳐 달라고 하지 않아도 사람이 정한 기억을 바꾼다", [x.text for x in m.live("커밋 언어")] == ["커밋 메시지는 영어"]),
        ("모델이 뽑은 것이라 agent가 정한 것으로 적힌다", new.decided_by == "agent"),
    ]


def s64_human_restore_is_not_undone(m):
    old = m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    wrong = m.capture("커밋 언어", "커밋 메시지는 영어", "s2#3", {"repo:a"}, by="human", clear=True)
    m.restore(old, "human")
    m.capture("커밋 언어", "커밋 메시지는 영어", "s3#1", {"repo:a"}, by="human", clear=True)
    m.capture("커밋 언어", "커밋 메시지는 영어", "s4#1", {"repo:a"}, by="agent")
    kept = [x.text for x in m.live("커밋 언어")] == ["커밋 메시지는 한국어"]
    m.remember("커밋 언어", "커밋 메시지는 영어", "s5#1", {"repo:a"})
    return [
        ("되돌리며 물러난 문장은 거절로 남는다", wrong.end_reason == "rejected"),
        ("되돌린 기억은 사람이 정한 것이 된다", old.decided_by == "human"),
        ("같은 문장이 다시 뽑혀도 되돌린 기억이 그대로다", kept),
        ("사람이 기억하라고 하면 바뀐다", [x.text for x in m.live("커밋 언어")] == ["커밋 메시지는 영어"]),
    ]


def s65_restored_memory_survives_evidence_check(m):
    _uv_repo(m)
    memory = _uv_memory(m)
    m.put_file("repo:a", "poetry.lock")
    m.check_evidence("repo:a")
    ended = memory.state == "retired"
    m.restore(memory, "human")
    m.check_evidence("repo:a")
    m.open_session("s9", {"repo:a"})
    m.load("s9")
    return [
        ("낡음 검사가 agent의 기억을 끝낸다", ended),
        ("사람이 되돌린 뒤에는 검사가 다시 끝내지 못한다", memory.state == "active"),
        ("근거가 어긋나는 동안에는 싣지 않는다", m.loaded_texts("s9") == set()),
    ]


def s66_repeated_human_words_are_agent_decided(m):
    m.capture("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"}, by="human")
    memory = m.capture("커밋 언어", "커밋 메시지는 한국어", "s2#1", {"repo:a"}, by="human")
    decided_by = memory.decided_by
    m.retire(memory, "stale", "cleanup")
    return [
        ("되풀이된 사람의 말은 기억이 되어도 agent가 정한 것이다", decided_by == "agent"),
        ("배경 정리가 끝낼 수 있다", memory.state == "retired"),
    ]


def s67_remember_claims_existing_memory(m):
    m.capture("패키지 도구", "uv를 쓴다", "s1#14", {"repo:a", "repo:b"})
    m.capture("패키지 도구", "uv를 쓴다", "s2#2", {"repo:a", "repo:b"})
    m.remember("패키지 도구", "uv를 쓴다", "s3#1", {"repo:a"})
    by_scope = {tuple(sorted(x.applies_to)): x.decided_by for x in m.live("패키지 도구")}
    return [("이미 있는 기억에 사람이 기억하라고 하면, 말한 저장소의 몫만 사람이 정한 것이 된다",
             by_scope == {("repo:a",): "human", ("repo:b",): "agent"})]


def s68_agent_fix_blocked_by_human_decision(m):
    memory = m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    try:
        m.supersede(memory, "커밋 메시지는 영어", "s2#3", "agent")
        refused = False
    except Exception:
        refused = True
    return [("agent의 고침은 사람이 정한 기억에 막힌다", refused and _is_live(m, memory))]


def s69_held_words_counted_apart_elsewhere(m):
    m.remember("커밋 언어", "커밋 메시지는 한국어", "s1#1", {"repo:a"})
    m.capture("커밋 언어", "커밋 메시지는 영어", "s2#3", {"repo:a"})
    m.capture("커밋 언어", "커밋 메시지는 영어", "s3#1", {"repo:b"})
    m.capture("커밋 언어", "커밋 메시지는 영어", "s4#1", {"repo:b"})
    live = sorted((x.text, tuple(sorted(x.applies_to)), x.decided_by) for x in m.live("커밋 언어"))
    return [("막힌 말은 다른 저장소의 되풀이와 섞이지 않는다",
             live == [("커밋 메시지는 영어", ("repo:b",), "agent"), ("커밋 메시지는 한국어", ("repo:a",), "human")])]


def s70_human_fix_absorbs_held_words(m):
    old = m.remember("패키지 도구", "poetry를 쓴다", "s1#1", {"repo:a"})
    m.capture("패키지 도구", "uv를 쓴다", "s2#1", {"repo:a"})
    m.supersede(old, "uv를 쓴다", "s3#1", "human")
    m.capture("패키지 도구", "uv를 쓴다", "s4#1", {"repo:b"})
    live = sorted((tuple(sorted(x.applies_to)), x.decided_by) for x in m.live("패키지 도구"))
    return [("막혀 있던 말과 같은 문장으로 사람이 고치면 후보는 그 기억에 들어가서, 다른 저장소의 되풀이로 올라오지 않는다",
             live == [(("repo:a",), "human")])]


IN = [
    ("S01", "끼어듦: 다른 맥락이 끼어듦", s01_other_context_stays_out),
    ("S02", "끼어듦: 한 자리에 준 말이 모든 곳의 규칙이 됨", s02_local_rule_stays_local),
    ("S03", "고침: 낡은 기억이 앞섬", s03_stale_by_cleanup),
    ("S04", "고침: \"그거 이제 아니야\"를 세션 도중에 말함", s04_human_retires_while_loaded),
    ("S05", "고침: 지난 실패 기억을 사람이 지움", s05_wrong_mark_while_loaded),
    ("S06", "닿음: 오래된 설정값이 닿지 않음", s06_old_fact_reaches),
    ("S07", "닿음: 기기에 대한 기억", s07_device_memory),
    ("S08", "보임: 없는 기억을 근거로 듦", s08_no_memory_no_claim),
    ("S09", "보임: 무엇이 쓰였는지 안 보임", s09_what_was_loaded_is_logged),
    ("S11", "기억이 맞다: 하지 않은 말이 기억이 됨", s11_unsaid_words_refused),
    ("S12", "기억이 맞다: 배경 정리가 사람이 정한 것을 덮음", s12_cleanup_cannot_override_human),
    ("S13", "기억이 맞다: agent가 고친 것을 되돌림", s13_restore_after_agent_fix),
    ("S14", "고침: 새 판이 기억이 되고 옛 판은 남음", s14_fix_keeps_both_versions),
    ("S15", "고침: 실린 채로 같은 세션에서 고침", s15_fix_while_loaded),
    ("S16", "끼어듦: 같은 저장소에 세션 둘", s16_two_sessions_at_once),
    ("S17", "끼어듦: 같은 주제, scope가 다른 기억 둘", s17_closer_scope_wins),
    ("S18", "끼어듦: scope를 넓힘", s18_widen_scope),
    ("S19", "기억이 맞다: 거절한 주제를 사람이 다시 기억하라 함", s19_human_overrides_rejection),
    ("S20", "기억이 맞다: 거절한 주제를 agent가 다시 뽑음", s20_agent_cannot_revive_rejection),
    ("S21", "문턱: 후보는 실리지 않음", s21_candidate_not_loaded),
    ("S22", "문턱: 되풀이로 승격", s22_repeat_promotes),
    ("S23", "문턱: 후보 만료", s23_candidate_expires),
    ("S24", "기억이 맞다: agent가 올린 것의 표시", s24_agent_promotion_is_attributed),
    ("S25", "기억이 맞다: agent의 말이 사람이 정한 기억과 다름", s25_agent_words_cannot_change_human_decision),
    ("S26", "내력: 처음 출처는 바뀌지 않음", s26_origin_never_changes),
    ("S27", "기억이 맞다: 잘못 거절한 것 되돌리기", s27_restore_rejected),
    ("S28", "숨은 비용: compaction이 오면 내리고 시작 몫을 다시 싣기", s28_compaction_reloads_start_portion),
    ("S29", "숨은 비용: resume은 실린 것을 이어 쓰기", s29_resume_keeps_loaded),
    ("S30", "숨은 비용: 이미 실린 것은 다시 싣지 않기", s30_loaded_not_loaded_again),
    ("S31", "고침: 반대 근거가 참이면 agent 기억이 끝남", s31_against_evidence_ends_agent_memory),
    ("S32", "고침: 지지 근거가 옮겨 가면 경로를 고침", s32_moved_support_fixes_path),
    ("S33", "고침: 검사가 돌지 못하면 모름", s33_unrunnable_check_is_unknown),
    ("S34", "고침: capture 때 참인 검사만 남김", s34_capture_keeps_only_true_checks),
    ("S35", "고침: 기한이 지난 agent 기억", s35_expired_agent_memory),
    ("S36", "고침: 같은 문장이 다시 나오면 기한을 다시 시작", s36_repeat_restarts_expiry),
    ("S37", "고침: 오래 맞는 규칙에는 기한이 없음", s37_lasting_rule_has_no_expiry),
    ("S38", "고침·기억이 맞다: 근거가 어긋난 사람의 기억은 끝내지 않고 싣지 않음", s38_human_memory_held_then_back),
    ("S39", "고침·기억이 맞다: 기한이 지난 사람의 기억은 끝내지 않고 싣지 않음", s39_human_memory_expired_then_said_again),
    ("S40", "끼어듦·고침: 근거가 한 저장소에서 어긋나면 나누기", s40_split_on_evidence),
    ("S41", "끼어듦·고침: 한 저장소에 다른 값이 오면 나누기", s41_split_on_new_value),
    ("S42", "끼어듦·고침: 모든 곳을 바꾸라면 전체를 고침", s42_broad_change_supersedes_all),
    ("S43", "고침·숨은 비용: 세션 도중 어긋난 근거를 compaction이 거름", s43_compaction_rechecks_evidence),
    ("S44", "끼어듦·고침: 넓은 scope의 기억이 한 저장소에서 어긋남", s44_broad_scope_evidence_mismatch),
    ("S45", "고침: 큐 처리 때의 판정", s45_queue_check_without_session),
    ("S46", "끼어듦·고침: scope가 둘인 후보가 되돌려진 기억과 겹친 채 올라감", s46_promote_meets_restored_version),
    ("S47", "문턱·기억이 맞다: 후보와 다른 문장이 되풀이로 세어짐", s47_different_text_is_not_a_repeat),
    ("S48", "끼어듦·문턱: 새 말과 일부만 겹친 후보는 나머지를 지킴", s48_candidate_keeps_unoverlapped_part),
    ("S49", "끼어듦: 뒤에 온 넓은 말(사람에 관한 문장)", s49_later_person_statement_keeps_closer),
    ("S50", "끼어듦: 뒤에 온 \"어디서나\"", s50_everywhere_overrides_closer),
    ("S51", "끼어듦: 세션 도중 가까운 기억이 생김", s51_closer_appears_mid_session),
    ("S52", "끼어듦: 같은 높이의 scope 둘", s52_same_height_later_wins),
    ("S53", "문턱: 한 세션 안의 되풀이", s53_same_session_repeat_not_counted),
    ("S54", "끼어듦: 다른 저장소에서 되풀이되면 합침", s54_repeat_across_repos_merges),
    ("S55", "끼어듦: 기억이 된 문장이 새 저장소에서 나옴", s55_active_widens_on_one_sighting),
    ("S56", "끼어듦·기억이 맞다: 사람이 정한 기억과 agent가 본 칸", s56_human_memory_not_merged_with_agent_sighting),
    ("S57", "고침: 기한은 대상마다", s57_expiry_per_target),
    ("S58", "끼어듦·고침: 말 하나가 기억 여럿과 겹침", s58_one_word_over_two_versions),
    ("S59", "끼어듦·기억이 맞다: 거절이 닿는 곳", s59_rejection_stays_in_its_cells),
    ("S60", "기억이 맞다: 한 번 말한 분명한 사람의 결정", s60_clear_human_decision_once),
    ("S61", "기억이 맞다: 분명해 보이는 agent의 말", s61_clear_judgement_needs_human_words),
    ("S62", "기억이 맞다: 분명하지 않은 사람의 말이 사람이 정한 기억과 다름", s62_unclear_human_words_wait),
    ("S63", "기억이 맞다: 사람의 분명한 말이 사람이 정한 기억을 바꿈", s63_clear_human_words_change_human_decision),
    ("S64", "기억이 맞다: 사람이 되돌린 것을 도구가 다시 뒤집으려 함", s64_human_restore_is_not_undone),
    ("S65", "고침·기억이 맞다: 낡음 검사가 끝낸 기억을 사람이 되돌림", s65_restored_memory_survives_evidence_check),
    ("S66", "기억이 맞다: 되풀이된 사람의 말은 누가 정한 것인가", s66_repeated_human_words_are_agent_decided),
    ("S67", "기억이 맞다: 이미 있는 기억에 사람이 기억하라고 함", s67_remember_claims_existing_memory),
    ("S68", "기억이 맞다: agent가 사람이 정한 기억을 고치려 함", s68_agent_fix_blocked_by_human_decision),
    ("S69", "끼어듦·기억이 맞다: 막힌 말이 다른 저장소에서 되풀이됨", s69_held_words_counted_apart_elsewhere),
    ("S70", "고침·기억이 맞다: 막혀 있던 말과 같은 문장으로 사람이 고침", s70_human_fix_absorbs_held_words),
]

GAP_KIND = {}

OUT = [
    ("끼어듦", "대화 하나만 기억 끄기", "넣지 않음(들어올 조건: scope와 가까운 쪽 규칙을 갖춘 제품을 돌린 뒤에도 사람이 \"메모리 쓰지 마\"를 붙일 때)"),
    ("기억이 맞다", "가정으로 한 질문이 사실이 됨", "뽑기의 걸러내기(어느 말을 후보로 뽑나)"),
    ("닿음", "주제를 말해도 불려 오지 않음", "싣는 자리(세션 시작, prompt, 도구 호출 직전: 닿음의 제품 축)"),
    ("따름", "닿아도 따르지 않음", "실린 동안의 검사(따름의 제품 축)"),
    ("measurement", "점수와 느낀 도움이 갈림", "테스트셋"),
    ("닿음", "다른 말로 불러도 닿아야 함", "주제 붙이기(같은 말 알아보기)"),
    ("고침", "사람이 부르는 말로 고칠 기억을 찾음", "주제 붙이기(같은 말 알아보기), 값으로 찾기"),
    ("보임", "실린 기억을 사람 화면에 보임", "화면(기록의 load 줄을 읽어 한 줄로)"),
    ("measurement", "사람의 helpful 표시", "기록 줄(상태는 바뀌지 않음)"),
    ("조용한 실패", "저장 실패·잘림을 알림", "기록과 화면(실패 줄, 덜어냄 줄)"),
    ("숨은 비용", "사용량과 시간이 보임", "기록 읽기(실은 글자 수, 호출 수)"),
    ("한 곳", "모든 기억을 한 자리에서", "저장 배치(폴더 하나)"),
    ("기억이 맞다", "사람이 기억 파일을 직접 고침", "저장 배치(세션이 시작할 때 파일을 기록의 마지막 판과 대 본다)"),
    ("기억이 맞다", "사람이 정한 기억에 막힌 말을 알림", "화면(기록의 막힌 줄을 읽어 한 줄로)"),
    ("기억이 맞다", "새로 올라간 기억을 알림", "화면(기록의 올리기 줄을 읽어 한 줄로)"),
]

OPEN = [
    ("O2", "기억 하나가 주제 둘에 걸릴 때, 주제를 얼마나 잘게 자르나: 다시 묶기가 일이 닿을 때 문장 조각으로 나누기로 했고, 문장 조각은 도구에 넣지 않았다"),
    ("O5", "capture 자리에서 검사가 돌지 못할 때 제안된 근거를 남기나(지금 도구는 남긴다)"),
    ("O6", "넓은 scope(사람, 일의 갈래)의 기억이 한 저장소에서만 어긋날 때, 나누기가 그 저장소를 뺄 칸이 없다(지금은 실을 때마다 근거로 거른다)"),
    ("O7", "낡음 검사가 끝낸 기억을 사람이 되돌렸을 때, 그 기억을 끝냈던 근거를 어떻게 하나(지금은 끝내지 않고, 근거가 어긋나는 동안 싣지 않는다)"),
]
