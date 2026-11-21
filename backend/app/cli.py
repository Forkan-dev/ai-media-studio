"""Command line: make one video end to end.

uv run python -m app.cli make --brand mind_facts --topic "decision fatigue" --style stick_doodle
"""
import argparse
import time

from app.brand import load_brand
from app.pipeline.metadata import make_metadata, save_metadata
from app.pipeline.produce import produce_video, video_folder
from app.pipeline.research import research_topic
from app.pipeline.script import make_script
from app.pipeline.storyboard import make_storyboard
from app.services.llm import unload


def make(brand_slug: str, topic: str, style: str | None) -> None:
    start = time.time()
    brand = load_brand(brand_slug)
    style = style or brand.images.default_style

    def step(name: str) -> None:
        print(f"[{(time.time() - start) / 60:5.1f} min] {name}", flush=True)

    step("research")
    research = research_topic(brand, topic)
    facts = research.facts_text()

    step("script: write, review, fact-check")
    script = make_script(brand, topic, facts)
    if script.status != "passed":
        step(f"STOPPED: script is {script.status}, nothing is produced")
        return
    narration = script.narration()

    step("storyboard")
    sb = make_storyboard(brand, topic, narration, style=style)

    step("metadata")  # before produce, while the LLM is still loaded
    meta = make_metadata(brand, topic, narration)
    unload()

    out = video_folder(brand, topic, style)
    out.mkdir(parents=True, exist_ok=True)
    (out / "research.json").write_text(research.model_dump_json(indent=1))
    save_metadata(meta, out)

    step("produce: images (with check), voice, captions, render")
    final = produce_video(brand, sb, out)
    step(f"DONE: {final}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("make", help="make one video end to end")
    m.add_argument("--brand", required=True)
    m.add_argument("--topic", required=True)
    m.add_argument("--style", help="image style name from the brand config (default: brand default)")
    args = parser.parse_args()
    if args.command == "make":
        make(args.brand, args.topic, args.style)


if __name__ == "__main__":
    main()
