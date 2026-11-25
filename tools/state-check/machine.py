"""기억의 상태 기계. 모델과 harness 없이 상태, 전이, 칸의 규칙만 담는다."""

from dataclasses import dataclass, field
from itertools import count

PROMOTE_AFTER_SESSIONS = 2
TRANSIENT_DEFAULT_DAYS = 14
BACKGROUND = ("cleanup", "harness")
TARGET_HEIGHT = {"repo": 0, "work": 1, "device": 2, "person": 2}


class Refused(Exception):
    pass


class IllegalTransition(Exception):
    pass


@dataclass
class Memory:
    id: int
    subject: str
    text: str
    origin: str
    applies_to: frozenset
    state: str
    decided_by: str
    repeats: int = 1
    end_reason: str | None = None
    replaces: int | None = None
    replaced_by: int | None = None
    kind: str = "decision"
    transient: bool = False
    evidence: tuple = ()
    expires: dict | None = None
    sightings: frozenset = frozenset()


@dataclass(frozen=True)
class Check:
    polarity: str
    path: str


def support(path):
    return Check("support", path)


def against(path):
    return Check("against", path)


@dataclass
class Session:
    id: str
    targets: frozenset
    loaded: set = field(default_factory=set)


def repo_in(targets):
    return next((t for t in sorted(targets) if t.startswith("repo:")), None)


def session_of(origin):
    return origin.split("#", 1)[0]


def _basename(path):
    return path.rsplit("/", 1)[-1]


class Machine:
    """기억의 생애(candidate → active → retired)와 세션의 실림(loaded)을 떼어 낸다. 세션의 끝은 계기가 아니다."""

    STATES = ("candidate", "active", "retired")
    LIVE_STATES = ("active",)
    ENDED_STATE = "retired"

    def __init__(self):
        self.memories: dict[int, Memory] = {}
        self.sessions: dict[str, Session] = {}
        self.log: list[tuple] = []
        self._ids = count(1)
        self.files: dict[str, set] = {}
        self.today = 0

    def _write_log(self, event, memory_id=None, by=None, **detail):
        self.log.append((event, memory_id, by, detail))

    def _set_state(self, memory, new_state, by, event):
        memory.state = new_state
        self._write_log(event, memory.id, by, state=new_state)

    def _versions(self, subject):
        return [m for m in self.memories.values() if m.subject == subject]

    def _rejected(self, subject, applies_to):
        covered = frozenset().union(*(m.applies_to for m in self.live(subject)))
        uncovered = frozenset(applies_to) - covered
        return any(
            m.state == self.ENDED_STATE and m.end_reason == "rejected" and m.applies_to & uncovered
            for m in self._versions(subject)
        )

    def _overruled(self, subject, text, cells):
        return any(
            m.state == self.ENDED_STATE and m.end_reason == "rejected" and m.text == text and m.applies_to & cells
            for m in self._versions(subject)
        )

    def _held_by_human_decision(self, candidate):
        return any(
            m.decided_by == "human" and m.text != candidate.text and m.applies_to & candidate.applies_to
            for m in self.live(candidate.subject)
        )

    def _open_candidate(self, subject, applies_to):
        for m in self._versions(subject):
            if m.state == "candidate" and m.applies_to & applies_to:
                return m
        return None

    def live(self, subject):
        return [m for m in self._versions(subject) if m.state in self.LIVE_STATES]

    def find(self, subject, text):
        return next(m for m in self._versions(subject) if m.text == text)

    def open_session(self, session_id, targets):
        self.sessions[session_id] = Session(session_id, frozenset(targets))

    def loaded_texts(self, session_id):
        return {self.memories[i].text for i in self.sessions[session_id].loaded}

    def _new_memory(self, subject, text, origin, applies_to, state, by, decider):
        memory = Memory(next(self._ids), subject, text, origin, frozenset(applies_to), state, decider)
        self.memories[memory.id] = memory
        self._write_log("capture", memory.id, by, state=state, origin=origin, explicit=decider == "human")
        return memory

    def put_file(self, repo, path):
        self.files.setdefault(repo, set()).add(path)

    def drop_file(self, repo, path):
        self.files.get(repo, set()).discard(path)

    def advance(self, days):
        self.today += days

    def _expiry(self, transient, expires_in, targets):
        if not transient:
            return None
        day = self.today + (expires_in if expires_in is not None else TRANSIENT_DEFAULT_DAYS)
        return {target: day for target in targets}

    def _expired_targets(self, memory):
        if memory.expires is None:
            return frozenset()
        return frozenset(t for t, day in memory.expires.items() if t in memory.applies_to and self.today >= day)

    def sessions_seen(self, memory):
        return len({session for target, session in memory.sightings if target in memory.applies_to})

    def _sight(self, memory, targets, origin):
        memory.sightings = memory.sightings | {(t, session_of(origin)) for t in targets}

    def _true_now(self, check, present):
        return (check.path in present) == (check.polarity == "support")

    def _keep_true_now(self, evidence, repo):
        if repo not in self.files:
            return tuple(evidence)
        return tuple(c for c in evidence if self._true_now(c, self.files[repo]))

    def verdict(self, memory, targets):
        """실을 수 있는지의 판정과, 지지 근거가 옮겨 갔을 때 고칠 경로. 상태를 바꾸지 않는다."""
        repo = repo_in(targets)
        judged = memory.applies_to & frozenset(targets)
        if judged and judged <= self._expired_targets(memory):
            return "expired", {}
        if not memory.evidence:
            return "ok", {}
        if repo not in self.files:
            return "unknown", {}
        present = self.files[repo]
        if any(c.polarity == "against" and c.path in present for c in memory.evidence):
            return "mismatch", {}
        supports = [c for c in memory.evidence if c.polarity == "support"]
        if not supports or any(c.path in present for c in supports):
            return "ok", {}
        moved = {}
        for check in supports:
            found = sorted(p for p in present if _basename(p) == _basename(check.path))
            if found:
                moved[check] = Check("support", found[0])
        return ("ok", moved) if moved else ("mismatch", {})

    def _judge(self, memory, targets):
        result, moved = self.verdict(memory, targets)
        if moved:
            memory.evidence = tuple(moved.get(c, c) for c in memory.evidence)
            self._write_log("evidence_path_fixed", memory.id, "harness", repo=repo_in(targets))
        return result

    def capture(self, subject, text, origin, applies_to, by="agent", quote_found=True,
                kind="decision", transient=False, evidence=(), expires_in=None, clear=False, explicit=False):
        clear_human_word = clear and by == "human"
        placed = self._capture_cells(subject, text, origin, applies_to, by, quote_found,
                                     kind, transient, evidence, expires_in, clear_human_word, explicit)
        if (clear_human_word and placed is not None and placed.state == "candidate"
                and not self._held_by_human_decision(placed)):
            self._write_log("clear_human_word", placed.id, "agent", origin=origin)
            self.promote(placed, "agent")
        return placed

    def _capture_cells(self, subject, text, origin, applies_to, by, quote_found,
                       kind, transient, evidence, expires_in, clear_human_word, explicit):
        applies_to = frozenset(applies_to)
        decider = "human" if explicit else "agent"
        if not quote_found:
            raise Refused("quote not found in record")
        if not explicit and self._rejected(subject, applies_to):
            raise Refused("subject was rejected")
        details = dict(kind=kind, transient=transient,
                       evidence=self._keep_true_now(evidence, repo_in(applies_to)),
                       expires=self._expiry(transient, expires_in, applies_to))
        self._split_candidates(subject, applies_to, text, by)
        same_cells, replaced_cells, held_cells = frozenset(), frozenset(), frozenset()
        same_memory, replaced_first = None, None
        for memory in list(self.live(subject)):
            overlap = memory.applies_to & applies_to
            if not overlap:
                continue
            if memory.text == text:
                if explicit and memory.decided_by != "human":
                    memory = self._claim_for_human(memory, overlap, origin)
                self._add_evidence(memory, details["evidence"], origin, by, expires_in, applies_to)
                same_cells, same_memory = same_cells | overlap, same_memory or memory
            elif memory.decided_by == "human" and not self._may_change_human_decision(
                    subject, text, overlap, clear_human_word, explicit):
                self._write_log("held_by_human_decision", memory.id, by, origin=origin, text=text)
                held_cells |= overlap
            else:
                replaced_first = replaced_first or memory
                self._take_cells(memory, applies_to, origin, by)
                replaced_cells |= overlap
        placed = None
        if replaced_cells:
            placed = self._place_value(subject, text, origin, replaced_cells, by, decider, details, replaced_first)
        empty_cells = applies_to - same_cells - replaced_cells - held_cells
        if empty_cells:
            placed = self._place_in_empty(subject, text, origin, empty_cells, by, decider, details, expires_in) or placed
        if held_cells:
            held = self._place_in_empty(subject, text, origin, held_cells, by, decider, details, expires_in, held=True)
            placed = placed or held
        return placed or same_memory

    def _may_change_human_decision(self, subject, text, cells, clear_human_word, explicit):
        return explicit or (clear_human_word and not self._overruled(subject, text, cells))

    def _claim_for_human(self, memory, cells, origin):
        if memory.applies_to <= cells:
            memory.decided_by = "human"
            self._write_log("claimed_by_human", memory.id, "human", origin=origin)
            return memory
        self._narrow(memory, cells, origin, "human")
        return self._new_version(memory, origin, "human", "human", applies_to=cells)

    def _take_cells(self, memory, cells, origin, by):
        if memory.applies_to <= cells:
            self.retire(memory, "superseded", by)
        else:
            self._narrow(memory, cells, origin, by)

    def _place_value(self, subject, text, origin, cells, by, decider, details, replaced):
        wider = self._widen(subject, text, origin, cells, by, decider, details, states=("active",))
        if wider:
            return wider
        cell_details = dict(details, expires=self._only(details["expires"], cells))
        new = self._new_version(replaced, origin, by, decider, text=text, applies_to=cells, sightings=frozenset(), **cell_details)
        replaced.replaced_by = replaced.replaced_by or new.id
        self._sight(new, cells, origin)
        return new

    def _absorb_candidates(self, subject, text, cells, by):
        for candidate in list(self._versions(subject)):
            if candidate.state != "candidate" or candidate.text != text or not candidate.applies_to & cells:
                continue
            remaining = candidate.applies_to - cells
            if remaining:
                candidate.applies_to = remaining
                if candidate.expires is not None:
                    candidate.expires = {t: d for t, d in candidate.expires.items() if t in remaining}
                self._write_log("narrow_candidate", candidate.id, by, applies_to=sorted(remaining))
            else:
                candidate.end_reason = "superseded"
                self._set_state(candidate, "retired", by, "retire")

    def _place_in_empty(self, subject, text, origin, cells, by, decider, details, expires_in, held=False):
        candidate = self._open_candidate(subject, cells)
        if candidate and candidate.text == text:
            self._add_evidence(candidate, details["evidence"], origin, by, expires_in, cells, event="repeat")
            self._promote_if_repeated(candidate, by)
            return candidate
        widened = None if held else self._widen(subject, text, origin, cells, by, decider, details)
        if widened:
            return widened
        memory = self._new_memory(subject, text, origin, cells, "candidate", by, decider)
        for name, value in dict(details, expires=self._only(details["expires"], cells)).items():
            setattr(memory, name, value)
        self._sight(memory, cells, origin)
        return memory

    @staticmethod
    def _only(expires, cells):
        return None if expires is None else {t: d for t, d in expires.items() if t in cells}

    def _promote_if_repeated(self, candidate, by):
        if (candidate.state == "candidate" and self.sessions_seen(candidate) >= PROMOTE_AFTER_SESSIONS
                and not self._held_by_human_decision(candidate)):
            self.promote(candidate, "agent")

    def _widen(self, subject, text, origin, applies_to, by, decider, details, states=("candidate", "active")):
        same = next((m for m in self._versions(subject)
                     if m.state in states and m.text == text and m.decided_by == decider
                     and m.kind == details["kind"] and m.transient == details["transient"]
                     and not m.applies_to & applies_to
                     and not (m.state == "candidate" and self._held_by_human_decision(m))), None)
        if same is None:
            return None
        expires = None if same.expires is None and details["expires"] is None else {
            **(same.expires or {}), **(details["expires"] or {})}
        evidence = tuple(dict.fromkeys(same.evidence + details["evidence"]))
        if same.state == "candidate":
            same.applies_to = same.applies_to | applies_to
            same.expires, same.evidence = expires, evidence
            self._sight(same, applies_to, origin)
            self._write_log("widen", same.id, by, applies_to=sorted(same.applies_to), origin=origin)
            self._promote_if_repeated(same, by)
            return same
        wider = self._new_version(same, origin, by, same.decided_by, applies_to=same.applies_to | applies_to,
                                  expires=expires, evidence=evidence)
        self._sight(wider, applies_to, origin)
        same.replaced_by = wider.id
        same.end_reason = "superseded"
        self._set_state(same, "retired", by, "retire")
        self._unload_everywhere(same)
        return wider

    def _add_evidence(self, memory, evidence, origin, by, expires_in, targets, event="evidence"):
        memory.repeats += 1
        memory.evidence = tuple(dict.fromkeys(memory.evidence + tuple(evidence)))
        restarted = self._expiry(memory.transient, expires_in, memory.applies_to & targets)
        if restarted is not None:
            memory.expires = {**(memory.expires or {}), **restarted}
        self._sight(memory, memory.applies_to & targets, origin)
        self._write_log(event, memory.id, by, origin=origin, sessions=self.sessions_seen(memory), expires=memory.expires)

    def _new_version(self, old, origin, by, decided_by, **changes):
        fields = dict(subject=old.subject, text=old.text, applies_to=old.applies_to, kind=old.kind,
                      transient=old.transient, evidence=old.evidence, expires=old.expires, sightings=old.sightings)
        fields.update({k: v for k, v in changes.items() if v is not None or k == "expires"})
        fields["applies_to"] = frozenset(fields["applies_to"])
        if fields["expires"] is not None:
            fields["expires"] = {t: d for t, d in fields["expires"].items() if t in fields["applies_to"]}
        new = Memory(next(self._ids), origin=origin, state="active", decided_by=decided_by,
                     replaces=old.id, **fields)
        self.memories[new.id] = new
        self._write_log("supersede", new.id, by, state="active", replaces=old.id,
                        applies_to=sorted(new.applies_to), decided_by=decided_by)
        self._absorb_candidates(new.subject, new.text, new.applies_to, by)
        return new

    def promote(self, memory, by):
        if memory.state != "candidate":
            raise IllegalTransition(f"promote from {memory.state}")
        memory.decided_by = by
        self._set_state(memory, "active", by, "promote")

    def remember(self, subject, text, origin, applies_to, everywhere=False, **details):
        if everywhere:
            self._override_everywhere(subject, text)
        memory = self.capture(subject, text, origin, applies_to, by="human", explicit=True, **details)
        if memory.state == "candidate":
            self.promote(memory, "human")
        return memory

    def _override_everywhere(self, subject, text):
        for version in list(self.live(subject)) + [m for m in self._versions(subject) if m.state == "candidate"]:
            if version.text != text:
                version.end_reason = "superseded"
                self._set_state(version, "retired", "human", "retire")
                self._unload_everywhere(version)

    def retire(self, memory, reason, by):
        if memory.state == "retired":
            raise IllegalTransition("retire from retired")
        if by == "cleanup" and memory.decided_by == "human":
            self._write_log("retire_blocked", memory.id, by, reason=reason)
            raise Refused("cleanup cannot retire a human decision")
        memory.end_reason = reason
        self._set_state(memory, "retired", by, "retire")
        self._unload_everywhere(memory)

    def forget(self, memory):
        self.retire(memory, "rejected", "human")

    def supersede(self, memory, new_text, origin, by, applies_to=None, **details):
        if by != "human" and memory.decided_by == "human":
            self._write_log("held_by_human_decision", memory.id, by, origin=origin, text=new_text)
            raise Refused("only the human changes a human decision")
        details.setdefault("expires", memory.expires)
        new = self._new_version(memory, origin, by, by, text=new_text, applies_to=applies_to, **details)
        memory.replaced_by = new.id
        self.retire(memory, "superseded", by)
        return new

    def _narrow(self, memory, remove, origin, by):
        remaining = memory.applies_to - remove
        if not remaining:
            self.retire(memory, "stale", by)
            return None
        narrowed = self._new_version(memory, origin, by, memory.decided_by, applies_to=remaining)
        memory.replaced_by = narrowed.id
        memory.end_reason = "superseded"
        self._set_state(memory, "retired", by, "retire")
        self._unload_everywhere(memory)
        return narrowed

    def _split_candidates(self, subject, applies_to, text, by):
        for candidate in list(self.memories.values()):
            if (candidate.subject != subject or candidate.state != "candidate"
                    or (text is not None and candidate.text == text) or not candidate.applies_to & applies_to):
                continue
            remaining = candidate.applies_to - applies_to
            if remaining:
                candidate.applies_to = remaining
                if candidate.expires is not None:
                    candidate.expires = {t: d for t, d in candidate.expires.items() if t in remaining}
                self._write_log("narrow_candidate", candidate.id, by, applies_to=sorted(remaining))
            else:
                candidate.end_reason = "superseded"
                self._set_state(candidate, "retired", by, "retire")

    def restore(self, memory, by):
        if memory.state != "retired":
            raise IllegalTransition(f"restore from {memory.state}")
        self._split_candidates(memory.subject, memory.applies_to, None, by)
        for current in self.live(memory.subject):
            if current.applies_to & memory.applies_to:
                overruled_by_human = by == "human" and current.applies_to <= memory.applies_to
                current.end_reason = "rejected" if overruled_by_human else "superseded"
                self._set_state(current, "retired", by, "retire")
                self._unload_everywhere(current)
        memory.end_reason = None
        if by == "human":
            memory.decided_by = "human"
        self._set_state(memory, "active", by, "restore")

    def _unload_everywhere(self, memory):
        for session in self.sessions.values():
            if memory.id in session.loaded:
                session.loaded.discard(memory.id)
                self._write_log("unload", memory.id, "harness", session=session.id)

    def _hold_or_end(self, memory, targets, result):
        repo = repo_in(targets)
        if memory.decided_by == "human":
            self._write_log("held", memory.id, "harness", repo=repo, reason=result)
            return
        if result == "expired":
            self._narrow(memory, self._expired_targets(memory), "check:expiry", "cleanup")
        elif repo in memory.applies_to:
            self._narrow(memory, {repo}, f"check:{repo}", "cleanup")
        else:
            self._write_log("held", memory.id, "harness", repo=repo, reason=result)

    def _in_scope(self, memory, session):
        return bool(memory.applies_to & session.targets)

    def _distance(self, memory, session):
        return min((TARGET_HEIGHT[target.split(":")[0]] for target in memory.applies_to & session.targets),
                   default=max(TARGET_HEIGHT.values()) + 1)

    def _closest_per_subject(self, memories, session):
        best = {}
        for memory in memories:
            rank = (self._distance(memory, session), -memory.id)
            if memory.subject not in best or rank < best[memory.subject][0]:
                best[memory.subject] = (rank, memory)
        return {memory.subject: memory for _, memory in best.values()}

    def load(self, session_id):
        session = self.sessions[session_id]
        loadable, results = [], {}
        for memory in list(self.memories.values()):
            if memory.state != "active" or not self._in_scope(memory, session):
                continue
            if memory.id not in session.loaded:
                results[memory.id] = self._judge(memory, session.targets)
                if results[memory.id] not in ("ok", "unknown"):
                    self._hold_or_end(memory, session.targets, results[memory.id])
                    continue
            loadable.append(memory)
        chosen = self._closest_per_subject([m for m in loadable if m.state == "active"], session)
        chosen_ids = {m.id for m in chosen.values()}
        for memory_id in sorted(session.loaded - chosen_ids):
            if self.memories[memory_id].subject in chosen:
                session.loaded.discard(memory_id)
                self._write_log("unload", memory_id, "harness", session=session_id, reason="closer")
        for memory_id in sorted(chosen_ids - session.loaded):
            session.loaded.add(memory_id)
            self._write_log("load", memory_id, "harness", session=session_id, evidence=results.get(memory_id, "ok"))

    def check_evidence(self, repo):
        """큐 처리 때의 판정. 세션 없이 그 저장소에 걸린 기억을 본다."""
        for memory in list(self.memories.values()):
            if memory.state == "active" and repo in memory.applies_to:
                result = self._judge(memory, {repo})
                if result not in ("ok", "unknown"):
                    self._hold_or_end(memory, {repo}, result)

    def compact(self, session_id):
        session = self.sessions[session_id]
        for memory_id in sorted(session.loaded):
            self._write_log("unload", memory_id, "harness", session=session_id, reason="compaction")
        session.loaded.clear()
        self.load(session_id)

    def resume(self, session_id):
        self._write_log("resume", None, "harness", session=session_id)
