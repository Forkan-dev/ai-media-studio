"""ClipForge sources: add a long video, prepare it (download + audio) in the background."""
from pathlib import Path

from app.models import Source, SourceStatus
from app.pipeline.clipforge.detect import Candidate, detect
from app.pipeline.clipforge.source import prepare_file, prepare_url
from app.repositories import SourceRepository
from app.services.errors import InvalidStateError, NotFoundError


class SourceService:
    def __init__(self, sources: SourceRepository, root: Path):
        self._sources = sources
        self._root = root  # storage/clipforge

    def get(self, source_id: int) -> Source:
        source = self._sources.get(source_id)
        if not source:
            raise NotFoundError(f"No source {source_id}")
        return source

    def list_sources(self) -> list[Source]:
        return self._sources.find()

    def add(self, url: str | None = None, file: str | None = None) -> Source:
        """Save the source (status preparing). Call prepare() next; it takes minutes."""
        source = self._sources.save(Source(url=url or "", file=file or "", title=Path(file).stem if file else ""))
        folder = self._root / str(source.id)
        folder.mkdir(parents=True, exist_ok=True)
        source.folder = str(folder)
        return self._sources.save(source)

    def prepare(self, source_id: int) -> Source:
        source = self.get(source_id)
        folder = Path(source.folder)
        try:
            info = prepare_url(source.url, folder) if source.url else prepare_file(Path(source.file), folder)
        except Exception as e:  # saved on the source so the UI can show it
            source.status, source.error = SourceStatus.FAILED, str(e)[:2000]
            return self._sources.save(source)
        source.title, source.channel, source.duration = info.title, info.channel, info.duration
        source.status, source.error = SourceStatus.READY, ""
        return self._sources.save(source)

    def check_can_detect(self, source_id: int) -> Source:
        source = self.get(source_id)
        if source.status != SourceStatus.READY:
            raise InvalidStateError(f"Source {source_id} is {source.status}, not ready")
        return source

    def detect(self, source_id: int) -> list[Candidate]:
        """Hot moments -> candidates.json in the source folder (minutes, even for long videos)."""
        source = self.check_can_detect(source_id)
        return detect(Path(source.folder))
