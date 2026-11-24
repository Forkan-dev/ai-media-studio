from app.modules.studio.brand import Brand
from app.modules.studio.services.stages.base import Stage, StageContext
from app.modules.studio.services.stages.images import ImagesStage
from app.modules.studio.services.stages.render import RenderStage
from app.modules.studio.services.stages.research import ResearchStage
from app.modules.studio.services.stages.script import ScriptStage
from app.modules.studio.services.stages.storyboard import StoryboardStage
from app.modules.studio.services.stages.thumbnail import ThumbnailStage
from app.modules.studio.services.stages.voice import VoiceStage


def video_stages(brand: Brand) -> list[Stage]:
    """The steps of making one video for this brand, in order (brand.pipeline turns steps off)."""
    research = [ResearchStage()] if brand.pipeline.research else []
    return [*research, ScriptStage(), StoryboardStage(), ImagesStage(), VoiceStage(),
            RenderStage(), ThumbnailStage()]


__all__ = ["Stage", "StageContext", "video_stages"]
