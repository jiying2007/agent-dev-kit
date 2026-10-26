"""Behavioral regressions for long-goal convergence and milestone boundaries."""
from __future__ import annotations

import unittest

from agent_dev_kit.execution_policy import ExecutionPolicyError, evaluate, evaluate_milestone, reduce_events
from test_execution_policy import (
    AS_OF, active_events, completed_events_without_artifacts, event,
    goal_started, managed_mode_verifier, policy, policy_v2, usage,
)


def proof(revision: int, evidence_id: str = "tests", **extra: object) -> dict:
    return {"revision": revision, "criterion_id": "tests", "change_kind": "evidence-changed",
            "evidence_ids": [evidence_id], **extra}


def bound_events() -> list[dict]:
    return [goal_started(),
            event(2, "evidence.added", {"evidence_id": "tests", "sha256": "b" * 64}),
            event(3, "progress.advanced", proof(1)),
            event(4, "heartbeat.recorded", {}),
            event(5, "checkpoint.verified", {"revision": 1, "evidence_ids": ["tests"]}),
            usage(6, 500)]


class GoalConvergenceTest(unittest.TestCase):
    def test_revision_only_cannot_keep_clearing_no_progress(self) -> None:
        events = [goal_started()]
        for revision in range(1, 5):
            events.append(event(len(events) + 1, "progress.advanced", {"revision": revision}))
            events.append(event(len(events) + 1, "heartbeat.recorded", {}))
        state = reduce_events(events)
        self.assertEqual(4, state["progress"]["revision"])
        self.assertEqual(0, state["progress"]["verified_revision"])
        self.assertIn("no-progress-limit-reached", evaluate(state, policy(), as_of=AS_OF)["reasons"])

    def test_evidence_bound_progress_and_hypothesis_are_valid(self) -> None:
        for kind in ("evidence-changed", "hypothesis-resolved", "blocker-changed", "criterion-closed"):
            events = bound_events()
            events[2]["payload"]["change_kind"] = kind
            self.assertTrue(evaluate_milestone(reduce_events(events), policy(), criterion_id="tests", as_of=AS_OF)["milestone_allowed"])

    def test_progress_rejects_missing_out_of_scope_and_renamed_evidence(self) -> None:
        for updates in ({"criterion_id": "unrelated"}, {"evidence_ids": ["missing"]}, {"change_kind": "status-only"}):
            events = bound_events()
            events[2]["payload"].update(updates)
            with self.assertRaises(ExecutionPolicyError):
                reduce_events(events)
        events = bound_events()[:-1]
        events.extend([event(6, "evidence.added", {"evidence_id": "renamed", "sha256": "b" * 64}),
                       event(7, "progress.advanced", proof(2, "renamed"))])
        with self.assertRaisesRegex(ExecutionPolicyError, "renamed digest"):
            reduce_events(events)

    def test_non_closing_progress_requires_replan_despite_new_evidence(self) -> None:
        events = bound_events()[:-1]
        events.extend([event(6, "evidence.added", {"evidence_id": "next", "sha256": "c" * 64}),
                       event(7, "progress.advanced", proof(2, "next"))])
        config = policy()
        config["progress"]["non_closing_limit"] = 2
        self.assertIn("non-closing-progress-limit-reached", evaluate(reduce_events(events), config, as_of=AS_OF)["reasons"])
        events.append(event(8, "goal.updated", {"token_budget": 10000}))
        self.assertIn("non-closing-progress-limit-reached", evaluate(reduce_events(events), config, as_of=AS_OF)["reasons"])
        events.append(event(9, "goal.updated", {"open_items_count": 1}))
        self.assertIn("non-closing-progress-limit-reached", evaluate(reduce_events(events), config, as_of=AS_OF)["reasons"])
        events.extend([event(10, "evidence.added", {"evidence_id": "closed", "sha256": "d" * 64}),
                       event(11, "progress.advanced", proof(3, "closed", change_kind="criterion-closed"))])
        self.assertNotIn("non-closing-progress-limit-reached", evaluate(reduce_events(events), config, as_of=AS_OF)["reasons"])

    def test_counter_oscillation_and_malformed_kind_cannot_reset_progress(self) -> None:
        events = bound_events()[:-1]
        events.extend([event(6, "goal.updated", {"open_items_count": 1}),
                       event(7, "goal.updated", {"open_items_count": 2})])
        self.assertEqual(1, reduce_events(events)["progress"]["non_closing_advances"])
        for value in ([], {}):
            malformed = bound_events()
            malformed[2]["payload"]["change_kind"] = value
            with self.assertRaises(ExecutionPolicyError):
                reduce_events(malformed)

    def test_replan_requires_changed_registered_plan_and_execution_adjustment(self) -> None:
        events = bound_events()[:-1]
        events.append(event(6, "evidence.added", {"evidence_id": "new-plan", "sha256": "c" * 64}))
        payload = proof(2, "new-plan", change_kind="replan", plan_before_sha256="b" * 64,
                        plan_after_sha256="c" * 64, adjustment="dependency")
        state = reduce_events(events + [event(7, "progress.advanced", payload)])
        self.assertEqual(0, state["progress"]["non_closing_advances"])
        for updates in ({"plan_after_sha256": "b" * 64}, {"adjustment": "budget"}, {"adjustment": []}, {"plan_before_sha256": "d" * 64}):
            with self.assertRaises(ExecutionPolicyError):
                reduce_events(events + [event(7, "progress.advanced", {**payload, **updates})])

    def test_milestone_never_completes_parent_or_grants_final(self) -> None:
        state = reduce_events(bound_events())
        decision = evaluate_milestone(state, policy(), criterion_id="tests", as_of=AS_OF)
        self.assertTrue(decision["milestone_allowed"])
        self.assertFalse(decision["completion_allowed"])
        self.assertFalse(decision["domain_acceptance_verified"])
        self.assertEqual("active", state["goal"]["status"])
        self.assertEqual(2, state["goal"]["open_items_count"])
        self.assertFalse(evaluate(state, policy(), gate_event="final", as_of=AS_OF)["gate_allowed"])

    def test_milestone_rejects_stale_legacy_unrelated_and_over_budget(self) -> None:
        cases = [active_events(), bound_events()]
        cases[1][-2]["payload"]["revision"] = 0
        for events in cases:
            self.assertFalse(evaluate_milestone(reduce_events(events), policy(), criterion_id="tests", as_of=AS_OF)["milestone_allowed"])
        events = bound_events()
        events[-1] = usage(6, 1200)
        result = evaluate_milestone(reduce_events(events), policy(), criterion_id="tests", as_of=AS_OF)
        self.assertFalse(result["milestone_allowed"])
        self.assertEqual("exceeded", result["budget_status"]["status"])
        self.assertFalse(evaluate_milestone(reduce_events(bound_events()), policy(), criterion_id="other", as_of=AS_OF)["milestone_allowed"])

    def test_final_evidence_pass_and_budget_exhaustion_are_separate(self) -> None:
        decision = evaluate(reduce_events(completed_events_without_artifacts("readonly", "readonly")),
                            policy_v2(), gate_event="final", mode_authority_verifier=managed_mode_verifier, as_of=AS_OF)
        self.assertTrue(decision["gate_allowed"])
        self.assertEqual("exceeded", decision["budget_status"]["status"])
        self.assertFalse(decision["budget_status"]["historical_compliance_verified"])


if __name__ == "__main__":
    unittest.main()
