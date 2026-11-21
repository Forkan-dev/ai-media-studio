# Script Generation Flow

How one script is made, step by step.

1. **Topic:** search and ranking are **not built yet**. For the tests, the topic ("the spotlight effect") is given by hand.
2. **Research:** searches 8 web pages and extracts facts, details and myths.
3. **Writer** (Qwen3.5, **no thinking**, fast): writes 2 scripts from the facts.
4. **Reviewer** (Qwen3.5, **no thinking**): rates each script on 7 criteria.
5. **The code decides pass or fail, not the AI.** The rule: average ≥ 7, no score below 5, accuracy ≥ 7, length within ±15% of the brand's target (60 s means about 150 words).
6. **Fact-check** (Qwen3.5 **with thinking**, about 4 to 5 minutes): checks every sentence of the best passing script. **Thinking is used only here**, because it is slow and logic matters most here.
7. **Result:**
   - no wrong sentences: **accepted**
   - wrong sentences or a low rating: the Writer **rewrites** with the notes, up to 2 times
   - still failing: **rejected** (`below_quality`, never uploaded)

## Code

| Step | File |
|---|---|
| Research | `backend/app/pipeline/research.py` |
| Writer | `backend/app/pipeline/writer.py` |
| Reviewer | `backend/app/pipeline/reviewer.py` |
| Fact-check | `backend/app/pipeline/fact_check.py` |
| Whole chain | `backend/app/pipeline/script.py` |
| Prompts | `backend/prompts/<brand>/` |
