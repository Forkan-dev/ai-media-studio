"""Job lifecycle: queue, claim, gates, redo with notes, reopen, actions, crash recovery."""
from pathlib import Path

import pytest

from app.core.errors import InvalidStateError
from app.modules.studio.models import JobStatus


def started(jobs, brand):
    job = jobs.create(brand, "test topic")
    claimed = jobs.next_job()
    assert claimed and claimed.id == job.id
    return jobs.run(job.id)


def test_create_queues_and_claim_is_exclusive(jobs, brand):
    job = jobs.create(brand, "test topic")
    assert job.status == JobStatus.QUEUED and job.stage == "a"
    assert jobs.next_job().id == job.id
    assert jobs.next_job() is None  # already claimed


def test_run_stops_at_the_first_gate(jobs, brand):
    job = started(jobs, brand)
    assert (job.stage, job.status) == ("a", JobStatus.WAITING)
    assert job.flags == {"a": ["flag from a"]}
    assert job.progress == ["working on a"]


def test_advance_runs_through_steps_without_gate_and_auto_finishes(jobs, brand):
    job = started(jobs, brand)
    jobs.advance(job.id)
    job = jobs.run(jobs.next_job().id)
    assert (job.stage, job.status) == ("b", JobStatus.WAITING)
    jobs.advance(job.id, auto=True)  # c (no gate) and d (gate, skipped by auto)
    job = jobs.run(jobs.next_job().id)
    assert job.status == JobStatus.DONE


def test_redo_cleans_outputs_and_uses_notes_once(jobs, brand, stages):
    job = started(jobs, brand)
    jobs.prepare_redo(job.id, "make it shorter")
    assert not (Path(job.folder) / "a.out").exists()
    jobs.run(jobs.next_job().id)
    assert stages[0].seen_notes == ["", "make it shorter"]
    assert not (Path(job.folder) / "notes.txt").exists()  # notes are for one run only


def test_failure_is_saved_and_can_be_retried(jobs, brand, stages):
    stages[0].fail = True
    jobs.create(brand, "test topic")
    with pytest.raises(RuntimeError):
        jobs.run(jobs.next_job().id)
    job = jobs.list_jobs()[0]
    assert job.status == JobStatus.FAILED and "boom" in job.error
    stages[0].fail = False
    jobs.prepare_redo(job.id)
    assert jobs.run(jobs.next_job().id).status == JobStatus.WAITING


def test_reopen_deletes_later_outputs_but_keeps_files_the_step_owns(jobs, brand):
    job = started(jobs, brand)
    for _ in range(2):  # through b and c to the gate of d
        jobs.advance(job.id)
        job = jobs.run(jobs.next_job().id)
    folder = Path(job.folder)
    (folder / "shared.png").write_text("image")
    assert job.stage == "d"

    job = jobs.reopen(job.id, "b")
    assert (job.stage, job.status) == ("b", JobStatus.WAITING)  # b has its result: back at its gate
    assert (folder / "b.out").exists() and (folder / "shared.png").exists()  # owned by b: kept
    assert not (folder / "c.out").exists() and not (folder / "d.out").exists()
    assert set(job.flags) == {"a", "b"}


def test_reopen_guards(jobs, brand):
    job = started(jobs, brand)
    with pytest.raises(InvalidStateError):
        jobs.reopen(job.id, "d")  # not reached yet
    with pytest.raises(InvalidStateError):
        jobs.reopen(job.id, "nope")
    jobs.advance(job.id)  # now queued: nothing may be reopened while work is pending
    with pytest.raises(InvalidStateError):
        jobs.reopen(job.id, "a")


def test_action_runs_and_returns_to_the_gate_even_when_it_fails(jobs, brand, stages):
    job = started(jobs, brand)
    jobs.queue_action(job.id, "a", {"type": "redraw", "scene": 1})
    job = jobs.run(jobs.next_job().id)
    assert job.status == JobStatus.WAITING and job.action is None
    assert stages[0].actions == [{"type": "redraw", "scene": 1}]

    jobs.queue_action(job.id, "a", {"type": "redraw", "fail": True})
    with pytest.raises(RuntimeError):
        jobs.run(jobs.next_job().id)
    job = jobs.get(job.id)
    assert job.status == JobStatus.WAITING and job.action is None


def test_action_only_at_its_gate(jobs, brand):
    job = started(jobs, brand)
    with pytest.raises(InvalidStateError):
        jobs.queue_action(job.id, "b", {"type": "redraw"})


def test_recover_marks_cut_off_jobs_failed(jobs, brand):
    job = jobs.create(brand, "test topic")
    jobs.next_job()  # claimed = running, then the worker "dies"
    assert jobs.recover_interrupted() == [job.id]
    job = jobs.get(job.id)
    assert job.status == JobStatus.FAILED and "Interrupted" in job.error
