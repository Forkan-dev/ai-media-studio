"""Scene rules on the storyboard, and input limits on the API schemas."""
import pytest
from pydantic import ValidationError

from app.modules.studio.pipeline.storyboard import Scene, Storyboard
from app.modules.studio.schemas import ImageRedo, JobCreate, RedoRequest, ScriptEdit, VoiceRedo


def storyboard() -> Storyboard:
    scene = Scene(narration="line", image_prompt="a cat", motion="zoom_in", transition="fade")
    return Storyboard(style="round_cartoon", scenes=[scene])


def test_scene_is_outdated_only_after_a_change_since_drawing():
    sb = storyboard()
    scene = sb.scenes[0]
    assert not sb.is_outdated(scene)  # never drawn
    scene.drawn = sb.key(scene)
    assert not sb.is_outdated(scene)
    sb.edit_scene(0, prompt="a dog")
    assert sb.is_outdated(scene)


def test_edit_scene_stores_the_default_style_as_none():
    sb = storyboard()
    sb.edit_scene(0, style="cinematic_real")
    assert sb.style_of(sb.scenes[0]) == "cinematic_real"
    sb.edit_scene(0, style="round_cartoon")  # back to the video's style
    assert sb.scenes[0].style is None
    sb.edit_scene(0, prompt="   ")  # blank prompt is ignored
    assert sb.scenes[0].image_prompt == "a cat"


@pytest.mark.parametrize("make", [
    lambda: ImageRedo(prompt="x" * 2001),
    lambda: VoiceRedo(text="x" * 1001),
    lambda: RedoRequest(notes="x" * 2001),
    lambda: ScriptEdit(text="x" * 8001),
    lambda: ScriptEdit(text="too short"),
    lambda: JobCreate(brand="b", topic="x"),
])
def test_api_inputs_are_limited(make):
    with pytest.raises(ValidationError):
        make()
