"""상태 기계를 경우 묶음과 불변식으로 잰다.

    python3 check.py
"""

import random

from machine import BACKGROUND, IllegalTransition, Machine, Refused, against, support
from scenarios import GAP_KIND, IN, OPEN, OUT

RANDOM_RUNS = 2000
STEPS_PER_RUN = 40
SUBJECTS = ("패키지 도구", "커밋 언어")
SCOPES = ({"repo:a"}, {"repo:b"}, {"person"}, {"repo:a", "repo:b"}, {"work:x"})
SESSION_TARGETS = {"A": {"repo:a", "work:x", "person"}, "B": {"repo:b", "work:x", "person"}}
EVIDENCE_CHOICES = ((), (support("uv.lock"),), (against("poetry.lock"),), (support("uv.lock"), against("poetry.lock")))
FILES = ("uv.lock", "poetry.lock", "sub/uv.lock")
OPS = ("capture", "capture", "remember", "forget", "fix", "stale", "restore", "open", "load", "load",
       "compact", "resume", "advance", "file", "file", "check", "everywhere")


def run_scenarios(machine_cls):
    results = []
    for scenario_id, source, scenario in IN:
        try:
            checks = scenario(machine_cls())
            failed = [label for label, ok in checks if not ok]
            note = "; ".join(failed)
        except Exception as error:
            failed, note = ["예외"], f"{type(error).__name__}: {error}"
        results.append((scenario_id, source, not failed, note))
    return results


def _snapshot(m):
    return {i: (x.state, x.origin, x.applies_to, x.evidence, x.expires) for i, x in m.memories.items()}


def check_invariants(m, before, log_before, origins):
    violations = []
    new_log = m.log[log_before:]
    loaded_ids = set().union(*(s.loaded for s in m.sessions.values())) if m.sessions else set()
    for memory_id in loaded_ids:
        if m.memories[memory_id].state not in m.LIVE_STATES:
            violations.append("I1 끝난 기억이 세션에 실려 있다")
    for memory_id, origin in origins.items():
        if m.memories[memory_id].origin != origin:
            violations.append("I2 출처가 바뀌었다")
    for subject in SUBJECTS:
        live = m.live(subject)
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                if a.applies_to & b.applies_to:
                    violations.append("I3 같은 주제·겹치는 scope에 살아 있는 기억이 둘")
    for event, memory_id, by, detail in new_log:
        if event == "retire" and by in BACKGROUND and m.memories[memory_id].decided_by == "human":
            violations.append("I4 배경 정리가 사람이 정한 기억을 끝냈다")
        if event == "supersede" and by in BACKGROUND and m.memories[detail["replaces"]].decided_by == "human":
            violations.append("I4 배경 정리가 사람이 정한 기억의 scope를 줄였다")
        if event == "retire" and by == "agent" and m.memories[memory_id].decided_by == "human":
            violations.append("I12 agent의 말이나 고침이 사람이 정한 기억을 끝냈다")
        if event == "supersede" and by == "agent" and m.memories[detail["replaces"]].decided_by == "human":
            violations.append("I12 agent의 말이나 고침이 사람이 정한 기억을 바꿨다")
        if event == "load":
            result, _ = m.verdict(m.memories[memory_id], m.sessions[detail["session"]].targets)
            if result in ("mismatch", "expired"):
                violations.append("I7 근거가 어긋나거나 기한이 지난 기억이 실렸다")
    for memory in m.memories.values():
        if memory.expires is not None and not memory.transient:
            violations.append("I8 지금 상태가 아닌 기억에 기한이 있다")
        if memory.state == "active" and not memory.applies_to:
            violations.append("I9 scope가 빈 기억이 살아 있다")
    for session in m.sessions.values():
        subjects = [m.memories[i].subject for i in session.loaded]
        if len(subjects) != len(set(subjects)):
            violations.append("I11 한 세션에 같은 주제의 기억이 둘 실려 있다")
        loads = [e[1] for e in new_log if e[0] == "load" and e[3]["session"] == session.id]
        if len(loads) != len(set(loads)):
            violations.append("I10 한 걸음에 같은 기억을 한 세션에 두 번 실었다")
    for event, memory_id, _, detail in new_log:
        if event == "capture" and not detail["explicit"]:
            new = m.memories[memory_id]
            had_live_version = any(
                x.subject == new.subject and x.applies_to & new.applies_to
                and before.get(x.id, (None,))[0] in m.LIVE_STATES
                for x in m.memories.values()
            )
            if not had_live_version and any(
                x.id < new.id and x.state == m.ENDED_STATE and x.end_reason == "rejected"
                and x.subject == new.subject and x.applies_to & new.applies_to
                for x in m.memories.values()
            ):
                violations.append("I6 거절된 주제가 사람이 시키지 않았는데 다시 뽑혔다")
    after = _snapshot(m)
    logged_ids = {e[1] for e in new_log}
    for memory_id, now in after.items():
        if before.get(memory_id, (None,))[0] != now[0] and memory_id not in logged_ids:
            violations.append("I5 상태가 바뀌었는데 기록 줄이 없다")
        elif memory_id in before and before[memory_id][2:] != now[2:] and memory_id not in logged_ids:
            violations.append("I5 scope·근거·기한이 바뀌었는데 기록 줄이 없다")
    return violations


def _details(rng):
    transient = rng.random() < 0.3
    return dict(kind="external_fact" if transient else "repo_fact_pointer", transient=transient,
                evidence=rng.choice(EVIDENCE_CHOICES), expires_in=rng.choice((None, 3, 10)))


def _random_step(m, rng):
    subject = rng.choice(SUBJECTS)
    scope = rng.choice(SCOPES)
    text = rng.choice(("uv를 쓴다", "poetry를 쓴다"))
    origin = f"s{rng.randrange(100)}#{rng.randrange(50)}"
    memories = list(m.memories.values())
    op = rng.choice(OPS)
    if op == "capture":
        clear = rng.random() < 0.3
        m.capture(subject, text, origin, scope, by=rng.choice(("agent", "human")), **_details(rng), clear=clear)
    elif op == "remember":
        m.remember(subject, text, origin, scope, **_details(rng))
    elif op == "forget" and memories:
        m.forget(rng.choice(memories))
    elif op == "fix" and memories:
        target = rng.choice(memories)
        if target.state in m.LIVE_STATES:
            m.supersede(target, text, origin, rng.choice(("agent", "human")))
    elif op == "stale" and memories:
        m.retire(rng.choice(memories), "stale", "cleanup")
    elif op == "restore" and memories:
        m.restore(rng.choice(memories), "human")
    elif op == "open":
        session_id = rng.choice(tuple(SESSION_TARGETS))
        if session_id not in m.sessions:
            m.open_session(session_id, SESSION_TARGETS[session_id])
    elif op == "load" and m.sessions:
        m.load(rng.choice(tuple(m.sessions)))
    elif op == "compact" and m.sessions:
        m.compact(rng.choice(tuple(m.sessions)))
    elif op == "resume" and m.sessions:
        m.resume(rng.choice(tuple(m.sessions)))
    elif op == "advance":
        m.advance(rng.choice((1, 5)))
    elif op == "file":
        repo, path = rng.choice(("repo:a", "repo:b")), rng.choice(FILES)
        (m.put_file if rng.random() < 0.5 else m.drop_file)(repo, path)
    elif op == "check":
        m.check_evidence(rng.choice(("repo:a", "repo:b")))
    elif op == "everywhere":
        m.remember(subject, text, origin, {"person"}, everywhere=True, **_details(rng))


def run_properties(machine_cls, seed=0):
    rng = random.Random(seed)
    counts, refused = {}, 0
    for _ in range(RANDOM_RUNS):
        m = machine_cls()
        origins = {}
        for _ in range(STEPS_PER_RUN):
            before, log_before = _snapshot(m), len(m.log)
            try:
                _random_step(m, rng)
            except (Refused, IllegalTransition):
                refused += 1
            for memory_id, memory in m.memories.items():
                origins.setdefault(memory_id, memory.origin)
            for violation in set(check_invariants(m, before, log_before, origins)):
                counts[violation] = counts.get(violation, 0) + 1
    return counts, refused


def reachable_states(machine_cls):
    seen = set()
    rng = random.Random(1)
    for _ in range(200):
        m = machine_cls()
        for _ in range(STEPS_PER_RUN):
            try:
                _random_step(m, rng)
            except (Refused, IllegalTransition):
                pass
            seen |= {x.state for x in m.memories.values()}
            if m.sessions and any(s.loaded for s in m.sessions.values()):
                seen.add("(세션에 실림)")
    return seen


def report(machine_cls):
    results = run_scenarios(machine_cls)
    passed = sum(ok for *_, ok, _ in results)
    print(f"\n경우 표현률 {passed}/{len(results)} ({passed / len(results):.0%})")
    for scenario_id, source, ok, note in results:
        if not ok:
            print(f"- {scenario_id} {source} — {GAP_KIND.get(scenario_id, '분류 없음')} — {note}")
    counts, refused = run_properties(machine_cls)
    total = RANDOM_RUNS * STEPS_PER_RUN
    print(f"\n불변식 위반 (무작위 {RANDOM_RUNS}회 × {STEPS_PER_RUN}걸음, 막힌 걸음 {refused}/{total})")
    for name in sorted(counts) or ["없음"]:
        print(f"- {name}: {counts.get(name, 0)}")
    states = reachable_states(machine_cls)
    missing = [s for s in machine_cls.STATES if s not in states]
    print(f"\n도달한 상태: {', '.join(sorted(states))}" + (f" · 닿지 않은 상태: {missing}" if missing else ""))


def main():
    print(f"경우 {len(IN)}개(기계가 받음) · 다른 부품이 맡는 경우 {len(OUT)}개 · 기대를 정하지 않은 경우 {len(OPEN)}개")
    report(Machine)
    print("\n## 다른 부품이 맡는 경우")
    for branch, story, owner in OUT:
        print(f"- {branch}: {story} → {owner}")
    print("\n## 기대를 정하지 않은 경우")
    for scenario_id, story in OPEN:
        print(f"- {scenario_id} {story}")


if __name__ == "__main__":
    main()
