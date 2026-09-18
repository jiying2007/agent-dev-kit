from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from agent_dev_kit.execution_policy import (
    RuntimeControlError,
    evaluate,
    goal_intake_attestation_sha256,
    reduce_events,
)


UTC = timezone.utc
AS_OF = datetime.fromisoformat("2026-08-24T01:12:00+00:00")


def policy() -> dict:
    return {
        "schema_version": "runtime_control.policy/v2",
        "token": {"checkpoint_ratio": 0.7, "compact_ratio": 0.9, "stop_ratio": 1.0},
        "context": {"compact_ratio": 0.5},
        "progress": {"staleness_seconds": 900, "retry_limit": 2, "no_progress_limit": 3},
        "artifact_applicability": {
            "readonly": {
                "steady": [],
                "final": [],
                "commit": None,
                "apply": None,
                "release": None,
            },
            "implementation": {
                "steady": [],
                "final": ["repo", "build"],
                "commit": ["repo", "build", "review"],
                "apply": ["repo", "build", "plan", "dry-run"],
                "release": None,
            },
            "release": {
                "steady": [],
                "final": ["repo", "build"],
                "commit": ["repo", "build", "review"],
                "apply": ["repo", "build", "plan", "dry-run"],
                "release": ["repo", "build", "live", "review"],
            },
        },
        "mode_authority_policy": {
            "managed": True,
            "trusted_mode_authorities": [],
            "verification_backend": "not-configured",
        },
        "retention": {"journal_days": 14, "raw_content_stored": False},
    }


def policy_v2(*, trusted_authority: bool = True) -> dict:
    value = policy()
    value["mode_authority_policy"] = {
        "managed": True,
        "trusted_mode_authorities": ["routing-authority"] if trusted_authority else [],
        "verification_backend": (
            "managed-authority-registry" if trusted_authority else "not-configured"
        ),
    }
    return value


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


def goal_intake(
    task_mode: str,
    artifact_mode: str,
    *,
    kind: str = "routing-decision",
    decision_id: str = "route-1",
    minute: int = 0,
    goal_id: str = "goal-1",
    request_sha256: str = "d" * 64,
    routing_decision_sha256: str = "e" * 64,
    authority_id: str = "routing-authority",
) -> dict:
    provenance = {
        "kind": kind,
        "source_id": "adk-routing-ir",
        "source_version": "v2",
        "decision_id": decision_id,
        "issued_at": "2026-08-24T01:{:02d}:00Z".format(minute),
    }
    return {
        "schema_version": "runtime_control.goal-intake/v1",
        "task_mode": task_mode,
        "artifact_mode": artifact_mode,
        "goal_id": goal_id,
        "request_sha256": request_sha256,
        "routing_decision_sha256": routing_decision_sha256,
        "authority_id": authority_id,
        "attestation_sha256": goal_intake_attestation_sha256(
            task_mode, artifact_mode, provenance,
            goal_id=goal_id,
            request_sha256=request_sha256,
            routing_decision_sha256=routing_decision_sha256,
            authority_id=authority_id,
        ),
        "provenance": provenance,
    }


def managed_mode_verifier(intake: dict, authority_policy: dict) -> bool:
    """Synthetic unit-test verifier; production engine has no verifier by default."""
    return (
        authority_policy["verification_backend"] == "managed-authority-registry"
        and intake["authority_id"] == "routing-authority"
        and intake["request_sha256"] == "d" * 64
        and intake["routing_decision_sha256"] == "e" * 64
    )


def goal_started(index: int = 1) -> dict:
    return event(index, "goal.started", {
        "goal_id": "goal-1",
        "token_budget": 1000,
        "time_budget_seconds": 7200,
        "usage_baseline_tokens": 100,
        "success_criteria": ["tests", "review"],
        "required_evidence": ["tests", "review"],
        "open_items_count": 2,
        "intake": goal_intake("implementation", "implementation"),
    })


def goal_started_v2(task_mode: str, artifact_mode: str, index: int = 1) -> dict:
    value = goal_started(index)
    value["payload"]["intake"] = goal_intake(task_mode, artifact_mode)
    return value


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


def active_events_v2(
    task_mode: str,
    artifact_mode: str,
    total: int = 500,
    last_input: int = 100,
) -> list[dict]:
    return [
        goal_started_v2(task_mode, artifact_mode),
        event(2, "progress.advanced", {"revision": 1}),
        event(3, "heartbeat.recorded", {}),
        usage(4, total, last_input),
    ]


def completed_events_without_artifacts(
    task_mode: str | None = None,
    artifact_mode: str | None = None,
) -> list[dict]:
    events = (
        active_events()[:-1]
        if task_mode is None
        else active_events_v2(task_mode, str(artifact_mode))[:-1]
    )
    events.extend([
        event(4, "evidence.added", {"evidence_id": "tests", "sha256": "b" * 64}),
        event(5, "evidence.added", {"evidence_id": "review", "sha256": "c" * 64}),
        event(6, "checkpoint.verified", {"revision": 1, "evidence_ids": ["tests", "review"]}),
        event(7, "goal.updated", {"open_items_count": 0}),
        event(8, "goal.completed", {}),
        usage(9, 1200),
    ])
    return events


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

    def test_secret_like_values_never_enter_event_policy_or_goal_state(self) -> None:
        for secret_value in (
            "ghp_abcdefghijklmnop",
            "github_pat_abcdefghijklmnop",
            "sk-abcdefghijklmnop",
            "Bearer abcdefghijklmnop",
            "AKIAABCDEFGHIJKLMNOP",
            "-----BEGIN PRIVATE KEY-----",
        ):
            secret_event = goal_started_v2("readonly", "readonly")
            secret_event["payload"]["intake"] = goal_intake(
                "readonly", "readonly", authority_id=secret_value
            )
            with self.subTest(surface="event", secret=secret_value), self.assertRaisesRegex(
                RuntimeControlError, "secret-like content"
            ):
                reduce_events([secret_event])

            secret_policy = policy_v2()
            secret_policy["mode_authority_policy"]["trusted_mode_authorities"] = [secret_value]
            with self.subTest(surface="policy", secret=secret_value), self.assertRaisesRegex(
                RuntimeControlError, "secret-like content"
            ):
                evaluate(reduce_events(active_events_v2("readonly", "readonly")), secret_policy, as_of=AS_OF)

    def test_readonly_final_passes_without_implementation_artifacts(self) -> None:
        decision = evaluate(
            reduce_events(completed_events_without_artifacts("readonly", "readonly")),
            policy_v2(),
            gate_event="final",
            mode_authority_verifier=managed_mode_verifier,
            as_of=AS_OF,
        )
        self.assertEqual("runtime_control.decision/v2", decision["schema_version"])
        self.assertEqual("readonly", decision["task_mode"])
        self.assertEqual("readonly", decision["artifact_mode"])
        self.assertEqual("readonly", decision["effective_artifact_mode"])
        self.assertTrue(decision["mode_authority_managed"])
        self.assertEqual("routing-authority", decision["mode_authority_id"])
        self.assertEqual("routing-decision", decision["intake_provenance"]["kind"])
        self.assertTrue(decision["gate_applicable"])
        self.assertEqual([], decision["required_artifacts"])
        self.assertEqual([], decision["missing_artifacts"])
        self.assertTrue(decision["completion_allowed"])
        self.assertTrue(decision["gate_allowed"])
        self.assertEqual("pass", decision["recommended_action"])

    def test_unmanaged_readonly_mode_gets_implementation_artifact_floor(self) -> None:
        events = completed_events_without_artifacts("readonly", "readonly")
        unconfigured = evaluate(
            reduce_events(events),
            policy_v2(trusted_authority=False),
            gate_event="final",
            as_of=AS_OF,
        )
        self.assertFalse(unconfigured["mode_authority_managed"])
        self.assertEqual("readonly", unconfigured["artifact_mode"])
        self.assertEqual("implementation", unconfigured["effective_artifact_mode"])
        self.assertEqual(["build", "repo"], unconfigured["missing_artifacts"])
        self.assertFalse(unconfigured["gate_allowed"])

        synthetic_authority_events = completed_events_without_artifacts("readonly", "readonly")
        synthetic_authority_events[0]["payload"]["intake"] = goal_intake(
            "readonly",
            "readonly",
            authority_id="routing-authority",
            request_sha256="1" * 64,
            routing_decision_sha256="2" * 64,
        )
        synthetic = evaluate(
            reduce_events(synthetic_authority_events),
            policy_v2(),
            gate_event="final",
            as_of=AS_OF,
        )
        self.assertFalse(synthetic["mode_authority_managed"])
        self.assertEqual("implementation", synthetic["effective_artifact_mode"])
        self.assertEqual(["build", "repo"], synthetic["missing_artifacts"])

        forged_with_test_verifier = evaluate(
            reduce_events(synthetic_authority_events),
            policy_v2(),
            gate_event="final",
            mode_authority_verifier=managed_mode_verifier,
            as_of=AS_OF,
        )
        self.assertFalse(forged_with_test_verifier["mode_authority_managed"])
        self.assertEqual("implementation", forged_with_test_verifier["effective_artifact_mode"])

        missing_policy = policy_v2()
        missing_policy.pop("mode_authority_policy")
        with self.assertRaisesRegex(RuntimeControlError, "policy fields are invalid"):
            evaluate(reduce_events(events), missing_policy, gate_event="final", as_of=AS_OF)

    def test_readonly_final_still_requires_a_completed_goal(self) -> None:
        active = evaluate(
            reduce_events(active_events_v2("readonly", "readonly")),
            policy_v2(),
            gate_event="final",
            as_of=AS_OF,
        )
        self.assertFalse(active["gate_allowed"])
        self.assertIn("goal-not-completed", active["reasons"])

        with self.assertRaisesRegex(RuntimeControlError, "attested goal intake"):
            evaluate(
                reduce_events([usage(1, 100)]),
                policy_v2(),
                gate_event="final",
                as_of=AS_OF,
            )

        missing_evidence_events = completed_events_without_artifacts("readonly", "readonly")
        missing_evidence_events.pop(3)
        missing_evidence = evaluate(
            reduce_events(missing_evidence_events),
            policy_v2(),
            gate_event="final",
            as_of=AS_OF,
        )
        self.assertFalse(missing_evidence["gate_allowed"])
        self.assertIn("required-evidence-missing", missing_evidence["reasons"])

    def test_readonly_final_preserves_every_completion_guard(self) -> None:
        cases = []

        open_items = completed_events_without_artifacts("readonly", "readonly")
        next(item for item in open_items if item["event_type"] == "goal.updated")["payload"]["open_items_count"] = 1
        cases.append((open_items, "open-items-remain"))

        checkpoint_missing = [
            item for item in completed_events_without_artifacts("readonly", "readonly")
            if item["event_type"] != "checkpoint.verified"
        ]
        cases.append((checkpoint_missing, "checkpoint-not-verified"))

        checkpoint_stale = completed_events_without_artifacts("readonly", "readonly")
        insert_at = next(
            index for index, item in enumerate(checkpoint_stale)
            if item["event_type"] == "goal.updated"
        )
        checkpoint_stale.insert(
            insert_at,
            event(60, "progress.advanced", {"revision": 2}, minute=6),
        )
        cases.append((checkpoint_stale, "checkpoint-stale"))

        retry_exhausted = completed_events_without_artifacts("readonly", "readonly")
        insert_at = next(
            index for index, item in enumerate(retry_exhausted)
            if item["event_type"] == "goal.completed"
        )
        retry_exhausted[insert_at:insert_at] = [
            event(60, "retry.recorded", {"reason_id": "failure-1"}, minute=7),
            event(61, "retry.recorded", {"reason_id": "failure-2"}, minute=7),
        ]
        cases.append((retry_exhausted, "retry-budget-exhausted"))

        no_progress = completed_events_without_artifacts("readonly", "readonly")
        insert_at = next(
            index for index, item in enumerate(no_progress)
            if item["event_type"] == "goal.updated"
        )
        no_progress[insert_at:insert_at] = [
            event(index, "heartbeat.recorded", {}, minute=6)
            for index in range(60, 64)
        ]
        cases.append((no_progress, "no-progress-limit-reached"))

        for events, expected_reason in cases:
            with self.subTest(expected_reason=expected_reason):
                decision = evaluate(
                    reduce_events(events),
                    policy_v2(),
                    gate_event="final",
                    as_of=AS_OF,
                )
                self.assertFalse(decision["gate_allowed"], decision)
                self.assertFalse(decision["completion_allowed"], decision)
                self.assertIn(expected_reason, decision["reasons"], decision)

    def test_implementation_and_release_artifacts_remain_fail_closed(self) -> None:
        implementation = evaluate(
            reduce_events(completed_events_without_artifacts("implementation", "implementation")),
            policy_v2(),
            gate_event="final",
            as_of=AS_OF,
        )
        self.assertFalse(implementation["gate_allowed"])
        self.assertEqual(["build", "repo"], implementation["missing_artifacts"])
        self.assertIn("required-artifact-missing", implementation["reasons"])

        release = evaluate(
            reduce_events(completed_events_without_artifacts("release", "release")),
            policy_v2(),
            gate_event="release",
            as_of=AS_OF,
        )
        self.assertFalse(release["gate_allowed"])
        self.assertEqual(["build", "live", "repo", "review"], release["missing_artifacts"])
        self.assertIn("required-artifact-missing", release["reasons"])

    def test_task_mode_and_gate_applicability_are_fail_closed(self) -> None:
        implementation_state = reduce_events(completed_events_without_artifacts())
        with self.assertRaisesRegex(RuntimeControlError, "state-bound"):
            evaluate(
                implementation_state,
                policy(),
                gate_event="final",
                task_mode="readonly",
                as_of=AS_OF,
            )

        state = reduce_events(completed_events_without_artifacts("readonly", "readonly"))
        with self.assertRaisesRegex(RuntimeControlError, "state-bound"):
            evaluate(
                state,
                policy_v2(),
                gate_event="final",
                task_mode="implementation",
                as_of=AS_OF,
            )

        decision = evaluate(
            state,
            policy_v2(),
            gate_event="release",
            as_of=AS_OF,
        )
        self.assertFalse(decision["gate_applicable"])
        self.assertFalse(decision["gate_allowed"])
        self.assertFalse(decision["completion_allowed"])
        self.assertIn("gate-not-applicable", decision["reasons"])

    def test_v2_policy_rejects_weakened_or_sensitive_applicability(self) -> None:
        weakened = policy_v2()
        weakened["artifact_applicability"]["implementation"]["final"] = ["repo"]
        with self.assertRaisesRegex(RuntimeControlError, "fail-closed artifact requirements"):
            evaluate(
                reduce_events(active_events()),
                weakened,
                as_of=AS_OF,
            )

        readonly_implementation_artifact = policy_v2()
        readonly_implementation_artifact["artifact_applicability"]["readonly"]["final"] = ["repo"]
        with self.assertRaisesRegex(RuntimeControlError, "cannot require implementation artifacts"):
            evaluate(
                reduce_events(active_events_v2("readonly", "readonly")),
                readonly_implementation_artifact,
                as_of=AS_OF,
            )

        sensitive = policy_v2()
        sensitive["artifact_applicability"]["readonly"]["content"] = "raw task text"
        with self.assertRaisesRegex(RuntimeControlError, "forbidden sensitive field"):
            evaluate(
                reduce_events(active_events_v2("readonly", "readonly")),
                sensitive,
                as_of=AS_OF,
            )

        trusted_without_backend = policy_v2()
        trusted_without_backend["mode_authority_policy"]["verification_backend"] = "not-configured"
        with self.assertRaisesRegex(RuntimeControlError, "require a configured"):
            evaluate(
                reduce_events(active_events_v2("readonly", "readonly")),
                trusted_without_backend,
                as_of=AS_OF,
            )

        backend_without_registry = policy_v2(trusted_authority=False)
        backend_without_registry["mode_authority_policy"]["verification_backend"] = (
            "managed-authority-registry"
        )
        with self.assertRaisesRegex(RuntimeControlError, "without trusted authorities"):
            evaluate(
                reduce_events(active_events_v2("readonly", "readonly")),
                backend_without_registry,
                as_of=AS_OF,
            )

    def test_goal_intake_attestation_and_mapping_are_fail_closed(self) -> None:
        tampered = goal_started_v2("readonly", "readonly")
        tampered["payload"]["intake"]["task_mode"] = "implementation"
        with self.assertRaisesRegex(RuntimeControlError, "inconsistent|digest mismatch"):
            reduce_events([tampered])

        request_tampered = goal_started_v2("readonly", "readonly")
        request_tampered["payload"]["intake"]["request_sha256"] = "f" * 64
        with self.assertRaisesRegex(RuntimeControlError, "digest mismatch"):
            reduce_events([request_tampered])

        routing_tampered = goal_started_v2("readonly", "readonly")
        routing_tampered["payload"]["intake"]["routing_decision_sha256"] = "f" * 64
        with self.assertRaisesRegex(RuntimeControlError, "digest mismatch"):
            reduce_events([routing_tampered])

        wrong_goal = goal_started()
        wrong_goal["payload"]["intake"] = goal_intake(
            "readonly", "readonly", goal_id="goal-other"
        )
        with self.assertRaisesRegex(RuntimeControlError, "goal_id does not match"):
            reduce_events([wrong_goal])

        inconsistent = goal_started()
        inconsistent["payload"]["intake"] = goal_intake("review", "implementation")
        with self.assertRaisesRegex(RuntimeControlError, "inconsistent"):
            reduce_events([inconsistent])

        state = reduce_events(active_events_v2("review", "readonly"))
        state["goal"]["task_mode"] = "implementation"
        with self.assertRaisesRegex(RuntimeControlError, "inconsistent|digest mismatch"):
            evaluate(state, policy_v2(), as_of=AS_OF)

        ungoverned = goal_started_v2("readonly", "readonly")
        ungoverned["payload"]["task_mode"] = "implementation"
        with self.assertRaisesRegex(RuntimeControlError, "payload fields are invalid"):
            reduce_events([ungoverned])

    def test_goal_mode_changes_only_through_attested_replan(self) -> None:
        replanned_intake = goal_intake(
            "implementation",
            "implementation",
            kind="goal-replan",
            decision_id="replan-2",
            minute=3,
        )
        events = active_events_v2("review", "readonly")[:-1]
        events.extend([
            event(4, "goal.updated", {
                "intake": replanned_intake,
                "mode_change_reason": "replan",
            }, minute=3),
            usage(5, 500),
        ])
        state = reduce_events(events)
        self.assertEqual("implementation", state["goal"]["task_mode"])
        self.assertEqual("implementation", state["goal"]["artifact_mode"])
        self.assertEqual(2, state["goal"]["intake_revision"])
        decision = evaluate(state, policy_v2(), as_of=AS_OF)
        self.assertEqual("implementation", decision["task_mode"])
        self.assertEqual("implementation", decision["artifact_mode"])
        self.assertEqual("goal-replan", decision["intake_provenance"]["kind"])

        missing_reason = active_events_v2("review", "readonly")[:-1]
        missing_reason.append(event(4, "goal.updated", {"intake": replanned_intake}, minute=3))
        with self.assertRaisesRegex(RuntimeControlError, "require intake and mode_change_reason"):
            reduce_events(missing_reason)

        wrong_kind = goal_intake(
            "implementation", "implementation", decision_id="route-2", minute=3
        )
        invalid_replan = active_events_v2("review", "readonly")[:-1]
        invalid_replan.append(event(4, "goal.updated", {
            "intake": wrong_kind,
            "mode_change_reason": "replan",
        }, minute=3))
        with self.assertRaisesRegex(RuntimeControlError, "provenance kind must be goal-replan"):
            reduce_events(invalid_replan)

    def test_v1_policy_is_rejected_and_v2_json_schemas_validate(self) -> None:
        old_policy = {
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
        with self.assertRaisesRegex(RuntimeControlError, "unsupported runtime control policy schema"):
            evaluate(
                reduce_events(completed_events_without_artifacts()),
                old_policy,
                gate_event="final",
                as_of=AS_OF,
            )

        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        policy_schema = json.loads((schema_dir / "runtime-control-policy-v2.schema.json").read_text())
        decision_schema = json.loads((schema_dir / "runtime-control-decision-v2.schema.json").read_text())
        Draft202012Validator.check_schema(policy_schema)
        Draft202012Validator.check_schema(decision_schema)
        Draft202012Validator(policy_schema).validate(policy_v2())
        Draft202012Validator(policy_schema).validate(policy_v2(trusted_authority=False))
        intake_schema = json.loads(
            (schema_dir / "runtime-control-goal-intake-v1.schema.json").read_text()
        )
        Draft202012Validator.check_schema(intake_schema)
        Draft202012Validator(intake_schema).validate(goal_intake("readonly", "readonly"))
        readonly = evaluate(
            reduce_events(completed_events_without_artifacts("readonly", "readonly")),
            policy_v2(),
            gate_event="final",
            mode_authority_verifier=managed_mode_verifier,
            as_of=AS_OF,
        )
        self.assertEqual("runtime_control.decision/v2", readonly["schema_version"])
        Draft202012Validator(decision_schema).validate(readonly)


if __name__ == "__main__":
    unittest.main()
