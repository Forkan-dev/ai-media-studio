"""Image check: the vision model confirms each image is a drawing in the brand style and matches its prompt."""
from pathlib import Path

from pydantic import BaseModel

from app.modules.studio.brand import Brand
from app.core.prompts import render
from app.core.clients.llm import chat_json


class ImageCheck(BaseModel):
    reason: str  # what the model sees, written first
    is_drawing: bool
    matches: bool

    @property
    def ok(self) -> bool:
        return self.is_drawing and self.matches


def check_image(brand: Brand, style: str, description: str, image: Path) -> ImageCheck:
    st = brand.images.style(style)
    system = render(brand.prompt_folders, "image_check", style_name=style.replace("_", " "),
                    look=f"{st.character}. {st.style}", description=description)
    return chat_json(system, "Check the image now.", ImageCheck, temperature=0, images=[image])
