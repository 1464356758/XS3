#!/usr/bin/env python3
"""Explicit author-directed manual chapter execution, independent of daily one-chapter scheduling.

Manual receipts are chapter-keyed and never overwrite book/daily/YYYY-MM-DD.json.
The same V4.3 candidate/release gate and immutable adopt apply to both modes.
"""
from __future__ import annotations
from datetime import datetime
import json
from pathlib import Path
import uuid
import daily_update as daily
import novel_state as ns


def _active(root):
    p = root / "manual/active.json"
    return ns.read_json(p) if p.is_file() else None


def _receipt_path(n, sha):
    return "manual/completions/CH%03d_%s.json" % (n, sha)


def _validate_owner(record, controller):
    ns.require(record and record.get("controller") == controller
               and controller.get("kind") == "manual", "手动章节控制者不匹配，禁止占用另一轮执行。")


def begin(project, controller):
    root, state = daily.load(project)
    with ns.writer_lock(root):
        root, state = daily.load(project)
        current = daily.active_record(root)
        if current and current.get("status") in ("running", "blocked"):
            ns.require(str(current["chapter"]) in state["chapters"],
                       "自动日更有未完成章，禁止手动并发抢占。")
        previous = _active(root)
        if previous and previous.get("status") in ("running", "blocked"):
            _validate_owner(previous, controller)
            ns.require(previous["chapter"] == len(state["chapters"]) + 1,
                       "手动任务目标与已采用章数不一致。")
            ns.require(previous["baseline_fingerprint"] ==
                       daily.prefix_fingerprint(state, previous["baseline_count"]),
                       "手动任务的冻结前文已变化。")
            return dict(previous, action="continue_owned")
        if previous and previous.get("status") == "completed":
            ns.require(str(previous["chapter"]) in state["chapters"] and
                       (root / previous["receipt_path"]).is_file(),
                       "上一手动章节缺少合法冻结回执，禁止新建。")
        n = len(state["chapters"]) + 1
        ns.require(state["completion"] is None and n <= state["config"]["target_chapters"],
                   "已完稿或超过目标章节数。")
        ns.require(state.get("serialization", {}).get("enabled"),
                   "手动写作也必须启用冻结审查。")
        stamp = daily.stamp()
        active = {"schema_version": 1, "type": "novel-manual-task-v1",
                  "book_id": state["book_id"], "status": "running", "chapter": n,
                  "run_id": uuid.uuid4().hex, "started_at": stamp,
                  "controller": controller, "baseline_count": n - 1,
                  "baseline_fingerprint": daily.prefix_fingerprint(state, n - 1),
                  "authorization": "explicit-author-request-to-complete-this-chapter",
                  "attempts": []}
        ns.atomic_json(root / "manual/active.json", active)
        return dict(active, action="started")


def assert_owner(project, request):
    root, state = daily.load(project)
    active = _active(root)
    _validate_owner(active, request.get("controller"))
    ns.require(active.get("run_id") == request.get("run_id") and
               active.get("status") in ("running", "blocked") and
               active.get("chapter") == len(state["chapters"]) + 1 and
               active.get("baseline_fingerprint") ==
               daily.prefix_fingerprint(state, active["baseline_count"]),
               "手动目标已变、归属不符或前文有变化。")
    current = daily.active_record(root)
    if current and current.get("status") in ("running", "blocked"):
        ns.require(str(current["chapter"]) in state["chapters"],
                   "自动任务另有未完成章，停止手动写入。")
    return active


def finish(project, request):
    root, state = daily.load(project)
    active = _active(root)
    _validate_owner(active, request.get("controller"))
    ns.require(active.get("run_id") == request.get("run_id") and active.get("status") == "running",
               "只能为本轮实际手动执行完成的章节签收。")
    chapter = active["chapter"]
    ns.require(len(state["chapters"]) == chapter and
               daily.prefix_fingerprint(state, active["baseline_count"]) == active["baseline_fingerprint"],
               "手动采用目标或冻结基线改变。")
    item, gate = daily.formal_evidence(root, state, chapter)
    adopted = item.get("adopted_at")
    ns.require(adopted and datetime.fromisoformat(adopted) >=
               datetime.fromisoformat(active["started_at"]),
               "手动正文必须在本次有权执行开始后实际冻结。")
    receipt_path = _receipt_path(chapter, item["text_sha256"])
    receipt = {"schema_version": 1, "type": "novel-manual-completion-v1",
               "status": "completed", "book_id": state["book_id"],
               "chapter": chapter, "run_id": active["run_id"],
               "controller": active["controller"],
               "started_at": active["started_at"], "completed_at": adopted,
               "date": daily.date_of(adopted), "baseline_count": active["baseline_count"],
               "baseline_fingerprint": active["baseline_fingerprint"],
               "body_path": item["text_path"], "body_sha256": item["text_sha256"],
               "record_path": item["record_path"], "record_sha256": item["record_sha256"],
               "release_path": gate["path"], "release_sha256": gate["sha256"],
               "state_revision": state["revision"]}
    path = root / receipt_path
    ns.require(not path.exists(), "手动冻结回执已存在，拒绝覆盖。")
    ns.immutable_text(path, json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    ns.atomic_json(root / "manual/active.json",
                   dict(active, status="completed", completed_at=adopted,
                        receipt_path=receipt_path))
    return dict(receipt, receipt_path="book/" + receipt_path)
