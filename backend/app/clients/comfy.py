"""Image generation through the ComfyUI HTTP API."""
import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import settings


@dataclass
class ImageSpec:
    prompt: str
    negative: str = ""
    checkpoint: str = "animagine-xl-4.0-opt.safetensors"
    lora: str = "dmd2_sdxl_4step_lora_fp16.safetensors"
    lora_weight: float = 1.0
    width: int = 832  # 832x1216 ≈ 9:16; use 1216x832 for 16:9
    height: int = 1216
    steps: int = 8
    cfg: float = 1.0
    sampler: str = "lcm"
    scheduler: str = "sgm_uniform"
    seed: int | None = None  # None = random, so every image differs


def _build_workflow(spec: ImageSpec, name: str = "sdxl_lora.json") -> dict:
    wf = json.loads((settings.workflows_dir / name).read_text())
    wf["checkpoint"]["inputs"]["ckpt_name"] = spec.checkpoint
    wf["lora"]["inputs"].update(
        lora_name=spec.lora, strength_model=spec.lora_weight, strength_clip=spec.lora_weight
    )
    wf["positive"]["inputs"]["text"] = spec.prompt
    wf["negative"]["inputs"]["text"] = spec.negative
    wf["latent"]["inputs"].update(width=spec.width, height=spec.height)
    wf["sampler"]["inputs"].update(
        seed=spec.seed if spec.seed is not None else random.randint(0, 2**32 - 1),
        steps=spec.steps,
        cfg=spec.cfg,
        sampler_name=spec.sampler,
        scheduler=spec.scheduler,
    )
    return wf


def generate_image(spec: ImageSpec, out_path: Path, timeout: float = 600) -> Path:
    """Run the workflow in ComfyUI and save the first output image to out_path."""
    base = settings.comfy_url
    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{base}/prompt", json={"prompt": _build_workflow(spec)})
        if resp.status_code != 200:
            raise RuntimeError(f"ComfyUI rejected workflow: {resp.text}")
        prompt_id = resp.json()["prompt_id"]

        deadline = time.time() + timeout
        while time.time() < deadline:
            history = client.get(f"{base}/history/{prompt_id}").json()
            if prompt_id in history:
                break
            time.sleep(1)
        else:
            raise TimeoutError(f"ComfyUI job {prompt_id} did not finish in {timeout}s")

        job = history[prompt_id]
        if job["status"]["status_str"] != "success":
            raise RuntimeError(f"ComfyUI job failed: {job['status']['messages']}")
        image = job["outputs"]["save"]["images"][0]
        data = client.get(f"{base}/view", params=image).content

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return out_path


def free_memory() -> None:
    """Unload SDXL from memory so another model (e.g. the LLM) can use it."""
    httpx.post(f"{settings.comfy_url}/free", json={"unload_models": True, "free_memory": True}, timeout=60)
