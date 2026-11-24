from app.brand import Brand
from app.services.stages.base import Stage, StageContext
from app.services.stages.images import ImagesStage
from app.services.stages.render import RenderStage
from app.services.stages.research import ResearchStage
from app.services.stages.script import ScriptStage
from app.services.stages.storyboard import StoryboardStage
from app.services.stages.thumbnail import ThumbnailStage


def video_stages(brand: Brand) -> list[Stage]:
    """The steps of making one video for this brand, in order (brand.pipeline turns steps off)."""
    research = [ResearchStage()] if brand.pipeline.research else []
    return [*research, ScriptStage(), StoryboardStage(), ImagesStage(), RenderStage(), ThumbnailStage()]


__all__ = ["Stage", "StageContext", "video_stages"]
