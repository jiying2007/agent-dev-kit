from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone

from agent_dev_kit.runtime_control import RuntimeControlError, evaluate, reduce_events


UTC = timezone.utc
AS_OF = datetime.fromisoformat("2026-08-24T01:12:00+00:00")


def policy() -> dict:
    return {
        "schema_version": "runtime_control.policy/v1",
        "token": {"checkpoint_ratio": 0.7, "compact_ratio": 0.9, "stop_ratio": 1.0},
        "context": {"compact_ratio": 0.5},
        "progress": {"staleness_seconds": 900, "retry_limit": 2, "no_progress_limit": 3},
        "gate_policy": {
            "steady": [],
            "final": ["repo", "build"],
            "commit": ["repo", "build", "review"],
            "apply": ["repo", "build", "plan", "dry-run"],
            "release": ["repo", "build", "live", "review"],
        },
        "retention": {"journal_days": 14, "raw_content_stored": False},
    }


def event(index: int, kind: str, payload: dict, minute: int | None = None) -> dict:
    minute = index if minute is None else minute
    return {
        "schema_version": "runtime_control.event/v1",
        "event_id": "evt-{}".format(index),
        "event_type": kind,
        "thread_id": "thread-1",
        "observed_at": "2026-08-24T01:{:02d}:00Z".format(minute),
        "payload": payload,
    }


def goal_started(index: int = 1) -> dict:
    return event(index, "goal.started", {
        "goal_id": "goal-1",
        "token_budget": 1000,
        "time_budget_seconds": 7200,
        "usage_baseline_tokens": 100,
        "success_criteria": ["tests", "review"],
        "required_evidence": ["tests", "review"],
        "open_items_count": 2,
    })


def usage(index: int, total: int, last_input: int = 100, window: int = 1000) -> dict:
    return event(index, "usage.snapshot", {
        "cwd_hash": "a" * 64,
        "model": "gpt-5.6-sol",
        "input_tokens": max(total - 10, 0),
        "cached_input_tokens": max(total - 20, 0),
        "output_tokens": 10,
        "reasoning_tokens": 2,
        "total_tokens": total,
        "context_window": window,
        "last_input_tokens": last_input,
        "last_delta_tokens": 10,
        "rate_per_minute": 100.0,
    })


def active_events(total: int = 500, last_input: int = 100) -> list[dict]:
    return [goal_started(), event(2, "progress.advanced", {"revision": 1}), event(3, "heartbeat.recorded", {}), usage(4, total, last_input)]


class RuntimeControlTest(unittest.TestCase):
    def test_active_actions_use_one_priority_chain(self) -> None:
        cases = [
            (500, 100, "continue"),
            (800, 100, "checkpoint"),
            (1000, 100, "compact"),
            (1100, 100, "stop"),
            (500, 600, "compact"),
        ]
        for total, last_input, expected in cases:
            decision = evaluate(reduce_events(active_events(total, last_input)), policy(), as_of=AS_OF)
            self.assertEqual(expected, decision["recommended_action"], decision)

    def test_replay_is_idempotent_and_conflicting_duplicate_fails(self) -> None:
        events = active_events()
        state = reduce_events(events + [copy.deepcopy(events[-1])])
        self.assertEqual(4, state["events_applied"])
        changed = copy.deepcopy(events[-1])
        changed["payload"]["total_tokens"] += 1
        with self.assertRaises(RuntimeControlError):
            reduce_events(events + [changed])

    def test_retry_stale_and_no_progress_replan(self) -> None:
        retries = active_events()[:-1] + [
            event(4, "retry.recorded", {"reason_id": "failure-1"}),
            event(5, "retry.recorded", {"reason_id": "failure-2"}),
            usage(6, 500),
        ]
        self.assertEqual("replan", evaluate(reduce_events(retries), policy(), as_of=AS_OF)["recommended_action"])

        no_progress = [goal_started()]
        no_progress.extend(event(index, "heartbeat.recorded", {}) for index in range(2, 6))
        no_progress.append(usage(6, 500))
        self.assertEqual("replan", evaluate(reduce_events(no_progress), policy(), as_of=AS_OF)["recommended_action"])

        stale = active_events()
        self.assertEqual(
            "replan",
            evaluate(
                reduce_events(stale),
                policy(),
                as_of=datetime.fromisoformat("2026-08-24T02:30:00+00:00"),
            )["recommended_action"],
        )

    def test_completion_requires_evidence_checkpoint_and_gate_artifacts(self) -> None:
        events = active_events()[:-1]
        events.extend([
            event(4, "evidence.added", {"evidence_id": "tests", "sha256": "b" * 64}),
            event(5, "evidence.added", {"evidence_id": "review", "sha256": "c" * 64}),
            event(6, "checkpoint.verified", {"revision": 1, "evidence_ids": ["tests", "review"]}),
            event(7, "goal.updated", {"open_items_count": 0}),
            event(8, "artifact.verified", {"artifact_type": "repo", "evidence_id": "tests"}),
            event(9, "artifact.verified", {"artifact_type": "build", "evidence_id": "tests"}),
            event(10, "goal.completed", {}),
            usage(11, 1200),
        ])
        decision = evaluate(reduce_events(events), policy(), gate_event="final", as_of=AS_OF)
        self.assertTrue(decision["completion_allowed"])
        self.assertEqual("pass", decision["recommended_action"])

        missing = events[:5] + events[6:]
        decision = evaluate(reduce_events(missing), policy(), gate_event="final", as_of=AS_OF)
        self.assertEqual("replan", decision["recommended_action"])

        stale_checkpoint = copy.deepcopy(events)
        stale_checkpoint.insert(-2, event(12, "progress.advanced", {"revision": 2}, minute=9))
        decision = evaluate(reduce_events(stale_checkpoint), policy(), gate_event="final", as_of=AS_OF)
        self.assertEqual("replan", decision["recommended_action"])
        self.assertIn("checkpoint-stale", decision["reasons"])

    def test_apply_gate_allows_active_goal_but_final_does_not(self) -> None:
        events = active_events()[:-1]
        events.extend([
            event(4, "evidence.added", {"evidence_id": "repo-proof", "sha256": "b" * 64}),
            event(5, "artifact.verified", {"artifact_type": "repo", "evidence_id": "repo-proof"}),
            event(6, "artifact.verified", {"artifact_type": "build", "evidence_id": "repo-proof"}),
            event(7, "artifact.verified", {"artifact_type": "plan", "evidence_id": "repo-proof"}),
            event(8, "artifact.verified", {"artifact_type": "dry-run", "evidence_id": "repo-proof"}),
            usage(9, 500),
        ])
        state = reduce_events(events)
        apply_decision = evaluate(state, policy(), gate_event="apply", as_of=AS_OF)
        self.assertTrue(apply_decision["gate_allowed"])
        self.assertFalse(apply_decision["completion_allowed"])
        self.assertEqual("pass", apply_decision["recommended_action"])

        final_decision = evaluate(state, policy(), gate_event="final", as_of=AS_OF)
        self.assertFalse(final_decision["gate_allowed"])
        self.assertEqual("replan", final_decision["recommended_action"])

    def test_goal_budget_revision_is_audited_in_the_same_state(self) -> None:
        events = active_events(total=1100)
        stopped = evaluate(reduce_events(events), policy(), as_of=AS_OF)
        self.assertEqual("stop", stopped["recommended_action"])
        events.insert(-1, event(4, "goal.updated", {"token_budget": 2000}, minute=3))
        events[-1]["event_id"] = "evt-5"
        resumed = evaluate(reduce_events(events), policy(), as_of=AS_OF)
        self.assertEqual(2000, resumed["token_budget"])
        self.assertEqual("continue", resumed["recommended_action"])

    def test_current_verified_checkpoint_clears_warning_without_repeating(self) -> None:
        events = active_events(total=800)
        events.insert(-1, event(4, "evidence.added", {"evidence_id": "tests", "sha256": "b" * 64}, minute=3))
        events.insert(-1, event(5, "checkpoint.verified", {"revision": 1, "evidence_ids": ["tests"]}, minute=3))
        events[-1]["event_id"] = "evt-6"
        decision = evaluate(reduce_events(events), policy(), as_of=AS_OF)
        self.assertEqual("continue", decision["recommended_action"])

    def test_raw_content_unknown_fields_and_delta_usage_are_rejected(self) -> None:
        bad = goal_started()
        bad["payload"]["objective"] = "raw goal text"
        with self.assertRaises(RuntimeControlError):
            reduce_events([bad])
        delta = event(1, "usage.delta", {})
        with self.assertRaises(RuntimeControlError):
            reduce_events([delta])
        invalid_policy = policy()
        invalid_policy["token"]["checkpoint_ratio"] = 0.95
        with self.assertRaises(RuntimeControlError):
            evaluate(reduce_events(active_events()), invalid_policy, as_of=AS_OF)


if __name__ == "__main__":
    unittest.main()
