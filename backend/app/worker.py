"""Worker: runs queued video jobs one at a time, separate from the API (restarting the API never stops a video).

uv run python -m app.worker
"""
import logging
import time

from app.modules.studio.dependencies import job_service

POLL_SECONDS = 2
log = logging.getLogger("worker")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    jobs = job_service()
    if interrupted := jobs.recover_interrupted():
        log.warning("jobs cut off by the last stop, marked failed (retry them): %s", interrupted)
    log.info("worker ready")
    while True:
        job = jobs.next_job()
        if job is None:
            time.sleep(POLL_SECONDS)
            continue
        log.info("job %s: %s (%s)", job.id, job.topic, job.stage)
        try:
            jobs.run(job.id)
        except Exception:  # saved on the job by run(); keep the worker alive for the next job
            log.exception("job %s failed", job.id)


if __name__ == "__main__":
    main()
