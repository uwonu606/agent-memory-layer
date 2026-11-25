"""검증 도구가 망가진 기계를 잡는지 잰다. 상태 기계를 한 곳씩 망가뜨려 경우 묶음과 불변식으로 돌린다.

    python3 mutants.py
"""

from check import run_properties, run_scenarios
from machine import TRANSIENT_DEFAULT_DAYS, IllegalTransition, Machine


class RejectionIgnored(Machine):
    def _rejected(self, subject, applies_to):
        return False


class RestoreKeepsCurrent(Machine):
    def restore(self, memory, by):
        memory.end_reason = None
        self._set_state(memory, "active", by, "restore")


class RetireKeepsLoaded(Machine):
    def _unload_everywhere(self, memory):
        pass


class CleanupOverridesHuman(Machine):
    def retire(self, memory, reason, by):
        if memory.state == "retired":
            raise IllegalTransition("retire from retired")
        memory.end_reason = reason
        self._set_state(memory, "retired", by, "retire")
        self._unload_everywhere(memory)


class SilentTransition(Machine):
    def _set_state(self, memory, new_state, by, event):
        memory.state = new_state


class LoadIgnoresScope(Machine):
    def _in_scope(self, memory, session):
        return True


class LoadIgnoresEvidence(Machine):
    def _judge(self, memory, repo):
        result = super()._judge(memory, repo)
        return "ok" if result == "mismatch" else result


class LoadIgnoresExpiry(Machine):
    def _judge(self, memory, repo):
        result = super()._judge(memory, repo)
        return "ok" if result == "expired" else result


class BackgroundEndsHuman(Machine):
    def _hold_or_end(self, memory, repo, result):
        if memory.decided_by == "human":
            memory.decided_by = "agent"
            super()._hold_or_end(memory, repo, result)
            memory.decided_by = "human"
        else:
            super()._hold_or_end(memory, repo, result)


class NewValueSupersedesWhole(Machine):
    def _take_cells(self, memory, cells, origin, by):
        self.retire(memory, "superseded", by)


class CompactionKeepsLoaded(Machine):
    def compact(self, session_id):
        self.load(session_id)


class ResumeReloads(Machine):
    def resume(self, session_id):
        self.compact(session_id)


class LoadsTwice(Machine):
    def load(self, session_id):
        self.sessions[session_id].loaded.clear()
        super().load(session_id)


class RepeatKeepsExpiry(Machine):
    def _add_evidence(self, memory, evidence, origin, by, expires_in, targets, event="evidence"):
        kept = memory.expires
        super()._add_evidence(memory, evidence, origin, by, expires_in, targets, event)
        memory.expires = kept


class SilentPathFix(Machine):
    def _judge(self, memory, repo):
        result, moved = self.verdict(memory, repo)
        if moved:
            memory.evidence = tuple(moved.get(c, c) for c in memory.evidence)
        return result


class ExpiryOnLastingRules(Machine):
    def _expiry(self, transient, expires_in, targets):
        return {t: self.today + TRANSIENT_DEFAULT_DAYS for t in targets}


class SplitLeavesEmptyScope(Machine):
    def _narrow(self, memory, remove, origin, by):
        remaining = memory.applies_to - remove
        narrowed = self._new_version(memory, origin, by, memory.decided_by, applies_to=remaining)
        narrowed.applies_to = remaining
        memory.end_reason = "superseded"
        self._set_state(memory, "retired", by, "retire")
        self._unload_everywhere(memory)
        return narrowed


class CaptureKeepsAllChecks(Machine):
    def _keep_true_now(self, evidence, repo):
        return tuple(evidence)


class NoMovedSearch(Machine):
    def verdict(self, memory, repo):
        result, moved = super().verdict(memory, repo)
        return ("mismatch", {}) if moved else (result, moved)


class CandidatesNotSplit(Machine):
    def _split_candidates(self, subject, applies_to, text, by):
        pass


class CandidateEndedWhole(Machine):
    def _split_candidates(self, subject, applies_to, text, by):
        for candidate in list(self.memories.values()):
            if (candidate.subject == subject and candidate.state == "candidate"
                    and candidate.text != text and candidate.applies_to & applies_to):
                candidate.end_reason = "superseded"
                self._set_state(candidate, "retired", by, "retire")


class SilentCandidateNarrow(Machine):
    def _split_candidates(self, subject, applies_to, text, by):
        for candidate in list(self.memories.values()):
            if (candidate.subject == subject and candidate.state == "candidate"
                    and candidate.text != text and candidate.applies_to & applies_to):
                remaining = candidate.applies_to - applies_to
                if remaining:
                    candidate.applies_to = remaining
                else:
                    candidate.end_reason = "superseded"
                    self._set_state(candidate, "retired", by, "retire")


class FartherWins(Machine):
    def _distance(self, memory, session):
        return -super()._distance(memory, session)


class OlderWinsTie(Machine):
    def _closest_per_subject(self, memories, session):
        best = {}
        for memory in memories:
            rank = (self._distance(memory, session), memory.id)
            if memory.subject not in best or rank < best[memory.subject][0]:
                best[memory.subject] = (rank, memory)
        return {memory.subject: memory for _, memory in best.values()}


class EverywhereIgnored(Machine):
    def _override_everywhere(self, subject, text):
        pass


class KeepsFartherLoaded(Machine):
    def load(self, session_id):
        kept = set(self.sessions[session_id].loaded)
        super().load(session_id)
        self.sessions[session_id].loaded |= {i for i in kept if self.memories[i].state == "active"}


class CountsEveryCapture(Machine):
    def sessions_seen(self, memory):
        return memory.repeats


class NoWidening(Machine):
    def _widen(self, subject, text, origin, applies_to, by, decider, details, states=("candidate", "active")):
        return None


class WidenIgnoresDecidedBy(Machine):
    def _widen(self, subject, text, origin, applies_to, by, decider, details, states=("candidate", "active")):
        for memory in self._versions(subject):
            if memory.state in states and memory.text == text and not memory.applies_to & applies_to:
                return super()._widen(subject, text, origin, applies_to, by, memory.decided_by, details, states)
        return None


class SharedExpiry(Machine):
    def _add_evidence(self, memory, evidence, origin, by, expires_in, targets, event="evidence"):
        super()._add_evidence(memory, evidence, origin, by, expires_in, targets, event)
        if memory.expires:
            latest = max(memory.expires.values())
            memory.expires = {t: latest for t in memory.expires}

    def _widen(self, subject, text, origin, applies_to, by, decider, details, states=("candidate", "active")):
        wider = super()._widen(subject, text, origin, applies_to, by, decider, details, states)
        if wider is not None and wider.expires:
            latest = max(wider.expires.values())
            wider.expires = {t: latest for t in wider.expires}
        return wider


class FirstOverlapOnly(Machine):
    def live(self, subject):
        return super().live(subject)[:1]


class ClearIgnored(Machine):
    def capture(self, *args, clear=False, **kwargs):
        return super().capture(*args, **kwargs)


class ClearProtected(Machine):
    def promote(self, memory, by):
        if any(e[0] == "clear_human_word" and e[1] == memory.id for e in self.log):
            by = "human"
        super().promote(memory, by)


class ClearForAgentWords(Machine):
    def capture(self, subject, text, origin, applies_to, by="agent", clear=False, **kwargs):
        return super().capture(subject, text, origin, applies_to, by="human" if clear else by, clear=clear, **kwargs)


class HumanDecisionUnprotected(Machine):
    def _may_change_human_decision(self, subject, text, cells, clear_human_word, explicit):
        return True


class OverruledIgnored(Machine):
    def _overruled(self, subject, text, cells):
        return False


class HeldCandidatePromotes(Machine):
    def _held_by_human_decision(self, candidate):
        return False


class HeldWordsWiden(Machine):
    def _widen(self, subject, text, origin, applies_to, by, decider, details, states=("candidate", "active")):
        self._held_by_human_decision = lambda candidate: False
        try:
            return super()._widen(subject, text, origin, applies_to, by, decider, details, states)
        finally:
            del self._held_by_human_decision


class RestoreKeepsDecider(Machine):
    def restore(self, memory, by):
        decided_by = memory.decided_by
        super().restore(memory, by)
        memory.decided_by = decided_by


class RestoreForgetsOverruled(Machine):
    def restore(self, memory, by):
        displaced = [x for x in self.live(memory.subject) if x.applies_to & memory.applies_to]
        super().restore(memory, by)
        for x in displaced:
            x.end_reason = "superseded"


class RepeatedHumanWordsProtected(Machine):
    def _promote_if_repeated(self, candidate, by):
        if candidate.state == "candidate" and self.sessions_seen(candidate) >= 2 and not self._held_by_human_decision(candidate):
            self.promote(candidate, by)


class RememberLeavesAgentDecided(Machine):
    def _claim_for_human(self, memory, cells, origin):
        return memory


class HeldWordsLeftBehind(Machine):
    def _absorb_candidates(self, subject, text, cells, by):
        pass


class AgentFixOverridesHuman(Machine):
    def supersede(self, memory, new_text, origin, by, applies_to=None, **details):
        details.setdefault("expires", memory.expires)
        new = self._new_version(memory, origin, by, by, text=new_text, applies_to=applies_to, **details)
        memory.replaced_by = new.id
        self.retire(memory, "superseded", by)
        return new


MUTANTS = [
    RejectionIgnored, RestoreKeepsCurrent, RetireKeepsLoaded, CleanupOverridesHuman, SilentTransition,
    LoadIgnoresScope, LoadIgnoresEvidence, LoadIgnoresExpiry, BackgroundEndsHuman,
    NewValueSupersedesWhole, CompactionKeepsLoaded, ResumeReloads, LoadsTwice, RepeatKeepsExpiry,
    SilentPathFix, ExpiryOnLastingRules, SplitLeavesEmptyScope, CaptureKeepsAllChecks, NoMovedSearch,
    CandidatesNotSplit, CandidateEndedWhole, SilentCandidateNarrow,
    FartherWins, OlderWinsTie, EverywhereIgnored, KeepsFartherLoaded,
    CountsEveryCapture, NoWidening, WidenIgnoresDecidedBy, SharedExpiry, FirstOverlapOnly,
    ClearIgnored, ClearProtected, ClearForAgentWords,
    HumanDecisionUnprotected, OverruledIgnored, HeldCandidatePromotes, HeldWordsWiden,
    RestoreKeepsDecider, RestoreForgetsOverruled, RepeatedHumanWordsProtected,
    RememberLeavesAgentDecided, AgentFixOverridesHuman, HeldWordsLeftBehind,
]


def main():
    baseline_failures = {sid for sid, _, ok, _ in run_scenarios(Machine) if not ok}
    baseline_violations, _ = run_properties(Machine)
    caught = 0
    for mutant in MUTANTS:
        new_failures = [sid for sid, _, ok, _ in run_scenarios(mutant) if not ok and sid not in baseline_failures]
        violations, _ = run_properties(mutant)
        new_violations = sorted(k for k, v in violations.items() if v > baseline_violations.get(k, 0) * 2 + 5)
        was_caught = bool(new_failures or new_violations)
        caught += was_caught
        print(f"- {mutant.__name__}: {'잡음' if was_caught else '놓침'} · 새로 깨진 경우 {new_failures or '없음'} · 새 불변식 위반 {new_violations or '없음'}")
    print(f"\n변이 {len(MUTANTS)}개 가운데 {caught}개를 잡았다")


if __name__ == "__main__":
    main()
