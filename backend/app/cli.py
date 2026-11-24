"""Command line: calls the same services as the API.

uv run python -m app.cli topics --brand mind_facts --find     # search the web for new topics, then list
uv run python -m app.cli topics --brand mind_facts            # list saved topics (best first)
uv run python -m app.cli make --brand mind_facts --topic "decision fatigue" --style stick_doodle
uv run python -m app.cli make --brand mind_facts              # no topic: the best saved topic is used
uv run python -m app.cli make --brand mind_facts --gates      # pause after each gated step
uv run python -m app.cli approve --job 3                      # accept the result, run the next step
uv run python -m app.cli redo --job 3                         # run the current step again
uv run python -m app.cli jobs                                 # list jobs
uv run python -m app.cli source --url "https://youtube.com/watch?v=..."   # ClipForge: add + prepare a long video
uv run python -m app.cli source --file ~/Movies/stream.mp4
uv run python -m app.cli sources                              # list ClipForge sources
uv run python -m app.cli detect --source 1                    # ClipForge: find hot moments
"""
import argparse
import logging

from app.dependencies import brand, job_service, source_service, topic_service
from app.models import Job, JobStatus


def topics(slug: str, find: bool) -> None:
    service, b = topic_service(), brand(slug)
    if find:
        print(f"found {len(service.discover(b))} new topics")
    for t in service.list_new(b):
        print(f"{t.score:4.1f}  {t.title}  {t.scores}\n      {t.angle}")


def make(slug: str, topic: str | None, style: str | None, gates: bool) -> None:
    b = brand(slug)
    if not topic:
        saved = topic_service().list_new(b)
        if not saved:
            raise SystemExit("No saved topics. Run: topics --brand <slug> --find")
        topic = saved[0].title
    jobs = job_service()
    job = jobs.create(b, topic, style)
    print(f"[job {job.id}] {topic} -> {job.folder}")
    report(jobs.run(job.id, auto=not gates))


def report(job: Job) -> None:
    print(f"[job {job.id}] {job.stage}: {job.status}")
    for f in job.flags.get(job.stage, []):
        print(f"   flag: {f}")
    if job.status == JobStatus.WAITING:
        print(f"   check the files in {job.folder}, then: approve --job {job.id}  or  redo --job {job.id}")


def list_jobs() -> None:
    for j in job_service().list_jobs():
        print(f"{j.id:4}  {j.brand}  {j.topic}  [{j.stage}: {j.status}]  {j.error[:80]}")


def add_source(url: str | None, file: str | None) -> None:
    service = source_service()
    s = service.add(url=url, file=file)
    print(f"[source {s.id}] preparing -> {s.folder}")
    s = service.prepare(s.id)
    print(f"[source {s.id}] {s.status}: {s.title} ({s.duration / 3600:.1f} h) {s.error}")


def detect_moments(source_id: int) -> None:
    for c in source_service().detect(source_id):
        print(f"{c.peak / 60:6.1f} min  score {c.score:.2f}  {c.signals}  {c.text[:90]}")


def list_sources() -> None:
    for s in source_service().list_sources():
        print(f"{s.id:4}  [{s.status}]  {s.duration / 3600:4.1f} h  {s.title}  {s.error[:80]}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("make", help="make one video")
    m.add_argument("--brand", required=True)
    m.add_argument("--topic", help="default: the best saved topic")
    m.add_argument("--style", help="image style name from the brand config (default: brand default)")
    m.add_argument("--gates", action="store_true", help="pause for approval after each gated step")
    t = sub.add_parser("topics", help="list saved topics; --find searches the web for new ones")
    t.add_argument("--brand", required=True)
    t.add_argument("--find", action="store_true")
    a = sub.add_parser("approve", help="accept the waiting step and run the next one")
    a.add_argument("--job", type=int, required=True)
    a.add_argument("--auto", action="store_true", help="no more pauses after this approval")
    r = sub.add_parser("redo", help="run the current step again")
    r.add_argument("--job", type=int, required=True)
    sub.add_parser("jobs", help="list jobs")
    s = sub.add_parser("source", help="ClipForge: add a long video (download + audio)")
    src = s.add_mutually_exclusive_group(required=True)
    src.add_argument("--url")
    src.add_argument("--file")
    sub.add_parser("sources", help="list ClipForge sources")
    d = sub.add_parser("detect", help="ClipForge: find hot moments in a source")
    d.add_argument("--source", type=int, required=True)
    args = parser.parse_args()

    if args.command == "make":
        make(args.brand, args.topic, args.style, args.gates)
    elif args.command == "topics":
        topics(args.brand, args.find)
    elif args.command == "approve":
        report(job_service().approve(args.job, args.auto))
    elif args.command == "redo":
        report(job_service().redo(args.job))
    elif args.command == "source":
        add_source(args.url, args.file)
    elif args.command == "sources":
        list_sources()
    elif args.command == "detect":
        detect_moments(args.source)
    else:
        list_jobs()


if __name__ == "__main__":
    main()
