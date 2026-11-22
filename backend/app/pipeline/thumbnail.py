"""Thumbnail: the LLM plans an image that tells a story + text options; SDXL draws it; the code adds the text.

Files in the video folder:
  thumbnail_raw.png  clean image without text (kept, so the text can change without a new image)
  thumbnail.png      final image with text
  thumbnail.json     plan: symbol, image prompt, chosen text, text options (for the UI)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat
from pydantic import BaseModel, Field

from app.brand import Brand
from app.config import settings
from app.pipeline.image_check import check_image
from app.pipeline.produce import MAX_IMAGE_RETRIES, generate_scene_image
from app.pipeline.storyboard import insert_character, no_text
from app.prompts import render
from app.services.comfy import free_memory
from app.services.llm import chat_json, unload

FINAL_SIZE = {"short": (1080, 1920), "long": (1280, 720)}


class ThumbnailPlan(BaseModel):
    symbol: str  # first: one object/metaphor from the topic, so the picture tells a story
    image_prompt: str
    text_options: list[str] = Field(min_length=1, max_length=8)
    text: str = Field(max_length=40)


def plan_thumbnail(brand: Brand, style: str, title: str, narration: str, core_fact: str = "",
                   user_text: str | None = None) -> ThumbnailPlan:
    """`user_text`: a text the user picked or typed; the image is designed to match it."""
    system = render(brand.prompts, "thumbnail", brand_name=brand.name, niche=brand.niche,
                    title=title, narration=narration, core_fact=core_fact or "(see narration)",
                    user_text=user_text or "(none)")
    plan = chat_json(system, "Design the thumbnail now.", ThumbnailPlan, temperature=0.8)
    if user_text:  # the user's words are used exactly, whatever the model wrote
        plan.text = user_text
        plan.text_options = [user_text, *[t for t in plan.text_options if t.upper() != user_text.upper()]]
    prompt = no_text(plan.image_prompt)
    if "MAIN_CHARACTER" not in prompt:  # the brand character must be the dominant subject
        prompt = f"MAIN_CHARACTER, {prompt}"
    prompt = insert_character(prompt, brand.images.style(style).character)
    return plan.model_copy(update={
        "image_prompt": prompt, "text": plan.text.upper(),
        "text_options": [t.upper() for t in plan.text_options],
    })


def render_text(folder: Path, text: str, size: tuple[int, int]) -> Path:
    """Draw `text` on the clean image. Fast: used by the UI when the user picks or types a text."""
    img = Image.open(folder / "thumbnail_raw.png").convert("RGB")
    scale = max(size[0] / img.width, size[1] / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - size[0]) // 2, (img.height - size[1]) // 2
    img = img.crop((left, top, left + size[0], top + size[1]))

    draw = ImageDraw.Draw(img)
    font_size = size[0] // 7
    font = ImageFont.truetype(str(settings.thumbnail_font), font_size)
    lines: list[str] = []
    for word in text.upper().split():  # wrap to fit 90% of the width
        if lines and draw.textlength(f"{lines[-1]} {word}", font=font) <= size[0] * 0.9:
            lines[-1] += f" {word}"
        else:
            lines.append(word)
    line_h = int(font_size * 1.1)
    block_h = line_h * len(lines)
    y0 = _calmest_band(img, block_h)

    # soft dark shadow behind the text block so it reads on any background
    shade = Image.new("L", img.size, 0)
    ImageDraw.Draw(shade).rectangle((0, y0 - font_size // 3, size[0], y0 + block_h + font_size // 3), fill=150)
    shade = shade.filter(ImageFilter.GaussianBlur(font_size // 2))
    img = Image.composite(Image.new("RGB", img.size, "black"), img, shade)
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        w = draw.textlength(line, font=font)
        draw.text(((size[0] - w) / 2, y0 + i * line_h), line, font=font, fill="white",
                  stroke_width=font_size // 12, stroke_fill="black")
    out = folder / "thumbnail.png"
    img.save(out)
    return out


def _calmest_band(img: Image.Image, block_h: int) -> int:
    """Top y of the calmest area for the text: bottom or middle first (keeps the face clear), top last.
    'Calm' = fewest edges, measured in code (no model)."""
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    h = img.height
    margin = h // 14
    candidates = {"bottom": h - block_h - margin * 2, "middle": (h - block_h) // 2, "top": margin}
    busy = {name: ImageStat.Stat(edges.crop((0, y, img.width, y + block_h))).mean[0]
            for name, y in candidates.items()}
    busy["top"] *= 1.5  # prefer bottom/middle: the face is usually in the upper part
    return candidates[min(busy, key=busy.get)]


def make_thumbnail(brand: Brand, style: str, plan: ThumbnailPlan, folder: Path) -> tuple[Path, bool]:
    """Draw the image (with the vision check), then add the text. Returns the thumbnail and check result."""
    raw = folder / "thumbnail_raw.png"
    ok = False
    for _ in range(MAX_IMAGE_RETRIES + 1):
        generate_scene_image(brand, style, plan.image_prompt, raw)
        free_memory()
        ok = check_image(brand, style, plan.image_prompt, raw).ok
        unload()
        if ok:
            break
    (folder / "thumbnail.json").write_text(plan.model_dump_json(indent=1))
    return render_text(folder, plan.text, FINAL_SIZE[brand.format]), ok
