# Script Generation Flow

How one video is made. **Rule: always make the video, and flag problems for the human review.**

1. **Topic:** search and ranking are **not built yet**. The topic is given by hand (`--topic`).
2. **Research:** 4 searches, 8 web pages (reliable sources first). Sorted into a **core fact**, **established** facts, **debated** findings, surprising details and myths. Stops only if no page can be read.
3. **Writer** (Qwen3.5, **no thinking**): writes 2 scripts around the core fact, with an approved example script as a style guide.
4. **Reviewer** (Qwen3.5, **no thinking**): scores each script on the brand's criteria (Mind Facts: hook, accuracy, clarity, logic, relatability, pacing, originality). The best script is picked.
5. **One repair round at most:** if the best script scores low or has a bad length, only the named sentences are rewritten (or one whole edit for length). Then the best version continues, whatever its score.
6. **Fact-check** (Qwen3.5 **with thinking**, about 4 to 5 minutes): checks every sentence once. **The code removes wrong sentences.** A wrong hook is replaced by another accurate hook.
7. **Video:** storyboard → images (with a vision check) → voice → captions → render → thumbnail → metadata.
8. **Result:**
   - no flags: **ready for review**
   - any flag (low score, removed sentences, failed images): **needs attention**, with the reasons in `review.json`
   - **you approve** in the UI before anything is published

## Output folder

`storage/videos/<brand>/<date>_<topic>_<style>/`

| File | Content |
|---|---|
| `final.mp4` | The video |
| `thumbnail.png` | Thumbnail with text |
| `metadata.txt` / `metadata.json` | Title, description, tags, hashtags, social caption |
| `review.json` | Status, flags, scores, removed sentences, failed images |
| `script.txt`, `storyboard.json`, `research.json` | How the video was made |

## Code

| Step | File |
|---|---|
| Research | `backend/app/pipeline/research.py` |
| Writer | `backend/app/pipeline/writer.py` |
| Reviewer | `backend/app/pipeline/reviewer.py` |
| Fact-check | `backend/app/pipeline/fact_check.py` |
| Script chain | `backend/app/pipeline/script.py` |
| Storyboard, images, video | `backend/app/pipeline/storyboard.py`, `produce.py`, `image_check.py` |
| Thumbnail, metadata | `backend/app/pipeline/thumbnail.py`, `metadata.py` |
| One command | `backend/app/cli.py` |
| Prompts | `backend/prompts/<brand>/` |
