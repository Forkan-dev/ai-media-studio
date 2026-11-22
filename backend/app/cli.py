"""Command line.

uv run python -m app.cli topics --brand mind_facts --find     # search the web for new topics, then list
uv run python -m app.cli topics --brand mind_facts            # list saved topics (best first)
uv run python -m app.cli make --brand mind_facts --topic "decision fatigue" --style stick_doodle
uv run python -m app.cli make --brand mind_facts              # no topic: the best saved topic is used
"""
import argparse
import json
import time

from app.brand import load_brand
from app.pipeline.metadata import make_metadata, save_metadata
from app.pipeline.produce import produce_video, video_folder
from app.pipeline.research import research_topic
from app.pipeline.script import ScriptResult, make_script
from app.pipeline.storyboard import make_storyboard
from app.pipeline.thumbnail import make_thumbnail, plan_thumbnail
from app.pipeline.topics import discover_topics, list_topics, mark_used
from app.services.llm import unload


def topics(brand_slug: str, find: bool) -> None:
    brand = load_brand(brand_slug)
    if find:
        print(f"found {len(discover_topics(brand))} new topics", flush=True)
    for t in list_topics(brand):
        print(f"{t.score:4.1f}  {t.title}  {t.scores}\n      {t.angle}")


def _report_attempts(script: ScriptResult, min_score: float) -> None:
    """Print why each script attempt passed or failed."""
    for i, c in enumerate(script.attempts, 1):
        r = c.review
        status = "PASS" if c.passed(min_score) else "FAIL"
        print(f"   attempt {i} ({c.structure}): {status} | review avg {r.average():.1f} {r.scores()}"
              f" | length: {c.length_note or 'OK'} | facts: {c.fact_ok}", flush=True)
        for w in r.real_weaknesses()[:3]:
            print(f"      [{w.criterion}] {w.problem[:140]}", flush=True)
        for s in c.wrong_sentences:
            print(f"      wrong fact: {s[:140]}", flush=True)


def make(brand_slug: str, topic: str | None, style: str | None) -> None:
    start = time.time()
    brand = load_brand(brand_slug)
    style = style or brand.images.default_style
    if not topic:
        saved = list_topics(brand)
        if not saved:
            raise SystemExit("No saved topics. Run: topics --brand <slug> --find")
        topic = saved[0].title
        print(f"topic: {topic}", flush=True)

    def step(name: str) -> None:
        print(f"[{(time.time() - start) / 60:5.1f} min] {name}", flush=True)

    out = video_folder(brand, topic, style)
    out.mkdir(parents=True, exist_ok=True)

    flags: list[str] = []  # everything the human should check on the review screen

    step("research")
    research = research_topic(brand, topic)  # stops only if no source is readable at all
    (out / "research.json").write_text(research.model_dump_json(indent=1))
    if not research.is_solid():
        flags.append(f"Research found only {len(research.research.established)} established facts")
    facts = research.facts_text()

    step("script: write, review (max 1 repair), fact-check")
    script = make_script(brand, topic, facts)
    _report_attempts(script, brand.min_quality_score)
    flags += script.flags
    narration = script.narration()

    step("storyboard")
    sb = make_storyboard(brand, topic, narration, style=style)

    step("metadata + thumbnail plan")  # before produce, while the LLM is still loaded
    meta = make_metadata(brand, topic, narration)
    thumb = plan_thumbnail(brand, style, meta.youtube_title, narration, research.research.core_fact.text)
    unload()
    save_metadata(meta, out)

    step("produce: images (with check), voice, captions, render")
    final, failed_images = produce_video(brand, sb, out)
    if failed_images:
        flags.append(f"Images may not match the style or prompt: scenes {failed_images}")

    step(f"thumbnail: {thumb.text}")
    _, thumb_ok = make_thumbnail(brand, style, thumb, out)
    if not thumb_ok:
        flags.append("Thumbnail image may not match the style or prompt")

    mark_used(brand, topic)  # never suggested again
    status = "needs_attention" if flags else "ready_for_review"
    (out / "review.json").write_text(json.dumps({
        "status": status,
        "flags": flags,
        "review_scores": script.best.review.scores(),
        "review_average": round(script.best.review.average(), 1),
        "removed_sentences": script.removed,
        "failed_image_scenes": failed_images,
        "thumbnail_ok": thumb_ok,
    }, indent=1))
    step(f"DONE ({status}): {final}")
    for f in flags:
        print(f"   flag: {f}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("make", help="make one video end to end")
    m.add_argument("--brand", required=True)
    m.add_argument("--topic", help="default: the best saved topic")
    m.add_argument("--style", help="image style name from the brand config (default: brand default)")
    t = sub.add_parser("topics", help="list saved topics; --find searches the web for new ones")
    t.add_argument("--brand", required=True)
    t.add_argument("--find", action="store_true")
    args = parser.parse_args()
    if args.command == "make":
        make(args.brand, args.topic, args.style)
    else:
        topics(args.brand, args.find)


if __name__ == "__main__":
    main()
