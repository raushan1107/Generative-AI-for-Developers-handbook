# Generative AI for Developers handbook: build guide

Notes for myself (not published on the site): how this handbook is built and how to add Parts II–V in the same style. Part I (setup, Modules 01–03, the project, labs and capstone pages) is live. Parts II (Modules 04–05) and III (Modules 06–07, Milestones 6–7) are built as **drafts**: complete and tested, but not linked from live pages yet (see "Draft modules" below). The **open-source lab guide** (section 8) is also a draft.

---

## 1. What this handbook is

- A **hands-on** handbook for the *Generative AI for Developers* course (TrainCrest TOC: 12 modules). Every concept is followed immediately by practice.
- **Three practice tracks:**
  1. **Drills**: one or more per topic, 10–20 min, in a scratch folder `genai-labs/`.
  2. **The build**: one progressive project, **Traincrest Assist**, one milestone per module, in `traincrest-assist/`.
  3. **Capstone**: a different problem in Part V, from a brief (page exists; brief to be written).
- Labs mix six **step types**: Run (copy code), Ask AI (given prompt for GitHub Copilot / Claude Code / Codex), Your prompt (learner writes it from a template, then compares), Verify, No-code, Think (and Portal for Azure portal steps).
- Explanations always include the **developer mindset** (traditional vs GenAI developer lens) and an **"In the real world"** callout about how real products use the idea.

### Branding (strict)

- "Written by Raushan Ranjan (MCT)" and "by Raushan Ranjan · RR Skillverse" (sidebar brand, sidebar footer, page footer, home hero, author card). Author link: `https://raushan-ranjan.azurewebsites.net/`.
- Footer disclaimer: not affiliated with Microsoft, OpenAI, Anthropic or GitHub; TrainCrest scenario data and policies are fictional; model names and prices change.
- Days are never mentioned: the course is presented as **Parts I–V**.

### Visual design (keep it minimal)

- Content first: one font family (Inter) plus JetBrains Mono for code, 17px body, ~740px reading width, generous line height.
- Neutral greys with a single accent colour; semantic colours appear only as thin left borders and small labels (definition, analogy, real world, trap, interview cue). Only the takeaway has a faint background.
- Light code blocks in the light theme, dark in the dark theme; no window dots, gradients, glows, shadows or pills.
- The sidebar follows the theme. Light and dark themes via the toggle; don't add decorative colour.

### Audience and tone

- Global audience. Use USD for costs, neutral analogies (restaurant kitchen, tailor, toll plaza, exam desk, call centre). Multilingual examples (Spanish, Hindi, Japanese, Arabic) appear where they teach something (tokens, triage).
- Classroom voice, first person is fine, short sentences, no hype, no emojis in body text.

---

## 2. How the site is built

```
tools/nav.json        the single source of truth for page order, sidebar and prev/next
tools/build.py        wraps src/ fragments in the shared shell and writes the final pages
src/**.html           page CONTENT ONLY, each starting with a <!--meta {...} --> JSON header
code/genai-labs/      every drill script, helper, dataset and test (real, tested files)
code/traincrest-assist/m01..m07/   complete project snapshot per milestone
code/oss-labs/        the open-source lab guide's project (Ollama only), see section 8
src/oss/              the open-source lab guide's pages
assets/css/handbook.css, assets/js/handbook.js
index.html, start/, setup/, modules/NN/, project/, labs/, capstone/   GENERATED: don't edit by hand
```

Build after any change: `python tools/build.py` (from the repo root). It fails loudly on a missing code file, a page not in `nav.json`, or a source file in the wrong place.

### Page meta header

```html
<!--meta
{"id": "m01-tokens", "short": "Tokens and Context Windows", "h1": "Tokens and Context Windows",
 "description": "…", "lead": "…", "chips": ["…"], "time": "Learn 12 min · Do 25 min"}
-->
```
`id` must match `nav.json`; `short` is the `<title>`; the hero (eyebrow, h1, lead, chips, Learn/Do/Check strip) is generated.

### Build-time features

- `<pre class="code" data-file="name.py" data-src="code/genai-labs/x.py"></pre>` inlines the real file, HTML-escaped, with `#` comments highlighted. Optional `data-lines="a-b"`.
- `<!--MODULE_PAGES:NN-->` renders the module's page cards with their drills (overview pages).
- `<!--DRILL_INDEX-->` renders the catalogue of all drills (labs page), filterable by step type.
- Sidebar, breadcrumbs, prev/next pager and "Mark this page as done" are generated for every page.

### Draft modules (build now, publish later)

- In `tools/nav.json`, a module with `"draft": true` and a `pages` list is built like any other module, but:
  - live pages still show it as "soon" in the sidebar, and it is left out of the live prev/next pager, the drill catalogue (`<!--DRILL_INDEX-->`) and the drill count;
  - draft pages link to each other (sidebar and pager), carry `<meta name="robots" content="noindex">` and show "Draft" in the top bar;
  - the build **fails** if a live page links to a draft page, so nothing leaks by accident.
- Files inlined on live pages must not change while their module is a draft. In `genai-labs/` that means `llm.py`, `.env.example` and `requirements.txt` stay at their Part I versions; Part II adds `llm_tools.py` (tool settings) and `embed.py` (embedding model setting), and its pages list the extra `.env` lines and packages.

**Going live (Part II, or any draft module):**
1. Remove `"draft": true` from the module in `tools/nav.json`.
2. Update the home page (`src/index.html`) cards and map, and the project roadmap status in `src/project/index.html`.
3. Optionally fold the Part II settings into `llm.py`, `.env.example` and `requirements.txt` (and update the pages that mention `llm_tools.py`/`embed.py`).
4. `python tools/build.py`, then the QA checks below. The build prints the live drill count.

### Adding a module (Parts II–V)

1. Add its pages to `tools/nav.json` (replace `"soon": true` with `"draft": true` and a `pages` list): overview, one page per TOC topic, `build`, `recap`.
2. Write drill code in `code/genai-labs/` (`labNN_XX_name.py`), and the milestone snapshot in `code/traincrest-assist/mNN/` (copy the previous snapshot, then change it).
3. Test the code: unit tests with pytest, and the app with a fake OpenAI client (see section 6).
4. Write `src/modules/NN/*.html` using the anatomy below, then build and run the QA checks.
5. When it's approved, go live (above): remove `draft`, update the home page module cards and the project roadmap status.

---

## 3. Page anatomy

**Topic page** (`kind: topic`):
1. `<div class="phase" id="learn">` → definition → plain words → analogy → diagram (inline SVG) or WWW strip → facts / tables → **In the real world** (`.callout.realworld`) → lens (`.lens`) → common trap → interview cue (`.callout.exam`).
2. `<div class="phase do" id="do">` → one or two drills.
3. `<div class="phase check" id="check">` → 1–3 quiz questions (`.quiz details`) → takeaway.

**Overview page**: mental-map SVG, takeaway, the "why" story with the lens, `<!--MODULE_PAGES:NN-->`, lab kit list.
**Build page**: phases `plan` / `build` / `verify`; a case brief; an architecture SVG; a file tree; one `drill exercise` with id `bNN-1`; a "still to do → module" table; a catch-up note linking to `code/traincrest-assist/mNN/`.
**Recap page**: checklist (with drill references), Traincrest decisions table, six quiz questions, carry-forward takeaway.

### Drill markup

```html
<div class="drill" id="d01-5" data-title="…" data-time="~10 min" data-steps="run,ask,verify">
  <div class="drill-head"><span class="drill-id">Drill 01.5</span><h3>…</h3>
    <div class="drill-meta"><span class="time">~10 min</span><span class="badge b-azure">Azure OpenAI</span><span class="badge b-tool">Python</span></div></div>
  <div class="drill-body">
    <p class="drill-goal"><b>Goal:</b> …</p>
    <ol class="dsteps">
      <li class="dstep run"><span class="st">Run</span><h4>…</h4> <pre class="code" data-file="…" data-src="…"></pre>
        <pre class="term"><code><span class="ps">$ </span>python …</code></pre>
        <span class="out-label">Expected output</span><pre class="out"><code>…</code></pre></li>
      <li class="dstep ask"><span class="st">Ask AI</span> <div class="prompt-box"><pre><code>…</code></pre></div>
        <div class="why"><b>Why this prompt works:</b> …</div>
        <details class="solution"><summary>Reference solution</summary><div>…</div></details></li>
      <li class="dstep write"><span class="st">Your prompt</span> <div class="template-box"><pre><code>Goal: …
Context: …
Constraints: …
Done when: …</code></pre></div> <p class="hint"><b>Hint:</b> …</p>
        <details class="solution"><summary>Compare with my prompt</summary><div><div class="prompt-box">…</div></div></details></li>
      <li class="dstep verify"><span class="st">Verify</span><ul class="verify-list"><li>…</li></ul></li>
    </ol>
  </div>
  <div class="drill-foot"><label class="done-row"><input type="checkbox" data-done="d01-5"> I've completed Drill 01.5</label></div>
</div>
```
The attribute order of the opening `div` must stay exactly as shown (the build indexes drills with a regex). Use `class="drill exercise"` for the TOC's hands-on exercise. Escape `<` and `>` inside every `<pre>`, including prompt text (`&lt;message&gt;`).

### Rules for Ask AI / Your prompt steps

- Prompts follow **Goal / Context / Constraints / Done when**, name exact files (`#file` for Copilot, `@file` for Claude Code), forbid touching other files where relevant, and never include secrets.
- Always say *why the prompt works* and *what you should get*, and give a reference solution (inlined from `code/`).
- Prefer prompts whose output is **verifiable** (tests, commands, checkers).

---

## 4. Lab conventions

- `genai-labs/`: `llm.py` (Azure OpenAI v1 / OpenAI / Ollama via `LLM_PROVIDER`, `MODEL` = deployment name on Azure), `claude_llm.py` (native Anthropic SDK, `CLAUDE_MODEL = "claude-opus-5-5"`, `FALLBACK` server-side fallback beta, `text_of()`), `tickets.py`, `data/train_tickets.json`, `data/eval_tickets.json`, `prompts.py`.
- Chat Completions everywhere (common format); `max_completion_tokens`, never `max_tokens`; guard empty `chunk.choices`; catch `openai.BadRequestError` where a parameter may be unsupported (reasoning models reject `temperature`/`logprobs`).
- Azure names: `rg-genai-labs`, `proj-genai-labs`, deployment `chat` (optional `chat-big`), embedding deployment `embed` (text-embedding-3-small), search service `srch-genai-labs-<initials>` (Free tier).
- Structured outputs and tools (Part II): Pydantic models via `parse()` / `openai.pydantic_function_tool()` (strict). Keep `pattern`, `maxLength`, `minimum`/`maximum`, `format` out of schemas (Azure strict mode rejects them) and enforce them with validators. Optional tool arguments get `= None` defaults (still required in the strict schema, tolerant with lenient providers). Strict tools on Azure need `parallel_tool_calls=False`. Reasoning deployments may need `TOOLS_REASONING_EFFORT=none` (`llm_tools.TOOL_EXTRAS`).
- Real outputs for Part II embedding and search drills come from a local run with Ollama `nomic-embed-text` (and `qwen2.5:1.5b` for tool smoke tests); Azure-only outputs are labelled illustrative.
- Part III real outputs: `llama3.2` (3B) for RAG drills, `qwen2.5:7b` for agent drills (a 3B model is too weak for multi-step tool use; its failures are shown as lessons). On a CPU laptop expect 20–60 s per call, so run model drills in the background. Keep small-model mistakes on the page when they teach something (invented actions, skipped citations, cross-language misses).
- The `openai` SDK must be recent (`client.chat.completions.parse` exists from 1.x late releases; tested with 3.29).
- Expected outputs: use real output where it can be produced offline (tokenizer, temperature, bigram, classic ML, dataset checker, tests); otherwise label "yours will differ".

---

## 5. The case: TrainCrest and Traincrest Assist (fictional)

- TrainCrest: global technical training company; ~25,000 learner-support requests a month; multilingual; 35-person team; 11-hour first response. Enrolment IDs `TC-12345`. Learners in examples: Mei, Diego, Asha, Omar, Lukas, Priya.
- Ticket categories: scheduling, billing, exam_voucher, certificate, lab_access, account, other. **House rules:** refund requests are billing even when they mention dates; more lab time is lab_access.
- Policies: reschedule free up to 7 days before start, then one reschedule for $50; cancellation 100% at 14+ days, 50% at 7–13, none under 7 (one free reschedule instead); vouchers issued within 3 business days of completion, valid 12 months; certificates within 48 h at ≥80% attendance, name fixes free within 30 days; labs 30 days after the course plus one free 7-day extension, then $49 for 14 more days; Retake Pass add-on = one free retake, 15% of course price, buy before the course ends, refunded in full if the course is cancelled.
- Milestones done: **M1** CLI + config + llm layer · **M2** FastAPI SSE chat, memory (6 pairs), friendly errors, SDK retries (3), JSON logs + cost, web UI · **M3** versioned prompt library (`assist_system@v2`, `triage@v1`, `ACTIVE`), Pydantic triage with one repair, output guard + tag neutralising, offline tests, `check_triage`.
- Built as draft: **M4** stand-in backend (`backend.py`: learners L-MEI, L-DIEGO, L-ASHA; enrolments TC-10293, TC-10477, TC-20877, TC-31002, TC-31188; vouchers; dates relative to today), `policy.py` (refund and reschedule quotes), `toolkit.py` registry, 7 strict tools with identity from session context, streaming tool loop (max 4 rounds, `parallel_tool_calls=False`, `tool` events), `assist_system@v3`, triage on `parse()` with validators (`triage@v2`) and JSON-repair fallback (`triage@v1`), demo sign-in in UI/CLI, 30 tests · **M5** `search.py` (chunk by heading, `LocalIndex` BM25 + cosine + RRF with pre-filters, `AzureIndex`, `SearchService`), `scripts/build_index.py`, `GET /api/search`, semantic `search_courses` with keyword fallback, 36 tests.
- Shared Part II data in `genai-labs/data/`: `courses.json` (20 courses C101–C120), `help/*.md` (10 help-centre articles; labs article has error codes LAB-409/503/440), `help_questions.json` (20 questions with source + required phrase). Module 06 should reuse them.
- Built as draft: **M6** help sections keep introductions (`headings-v2`, chunker version checked on load, 47 sections), `rag.py` (floor per embedding model, numbered sources within a budget, tag neutralising, `check_citations`, `ask()` with NOT_FOUND and "related" when uncited), `search_help` tool numbering sources across a turn, `assist_system@v4` (no policy text), `rag_answer@v1`, `POST /api/ask`, sources in UI/CLI, 45 tests · **M7** `backend` LABS/SESSIONS with idempotent logged writes (`data/actions.jsonl`), `actions.py` ActionStore (frozen proposals, one decision, 15-min expiry, re-check, execute once), tools `get_lab_access`, `list_course_dates`, `request_lab_extension`, `request_reschedule` (propose only), `assist_system@v5`, `POST /api/actions/{id}`, approval cards, repeated-call refusal, tool-call-as-text guard, 54 tests.
- Part III drill data: `genai-labs/data/internal/` (4 staff docs in md/html/txt/csv + a duplicate `support_playbook_FINAL.md`); agent drills use `desk.py` (in-memory systems, audit log `ACTIONS`, flaky mode) and `desk_tools.py` (tools + shared `SYSTEM`).
- Planned: M8 gateway, persistent sessions, tracing · M9 evaluation in CI · M10 Prompt Shields, least privilege · M11 routing, caching, batch · M12 containers, secrets, fallbacks, CI/CD.

---

## 6. QA before a page or module is done

- [ ] `python tools/build.py` succeeds; drill count looks right.
- [ ] All Python in `code/` compiles; drill unit tests pass (`pytest` in `code/genai-labs`); milestone tests pass (`pytest` in `code/traincrest-assist/mNN`) and the app passes an offline test with a fake OpenAI client (stream chunks incl. empty-choices chunks, usage chunk, and raised `RateLimitError`/`AuthenticationError`/`APIConnectionError`).
- [ ] Every `.py` block embedded in pages compiles; no unescaped tags inside `<pre>`; all internal links and anchors resolve.
- [ ] Rendered at desktop and 390 px, light and dark: no horizontal scroll, no SVG text spilling out of its box, no console errors.
- [ ] Model names, parameters and service names checked against current Microsoft Learn and provider docs.

---

## 7. Repository and publishing

- Repo: `https://github.com/raushan1107/Generative-AI-for-Developers-handbook` (branch `main`). Commits are authored by Raushan Ranjan only; no co-author lines.
- Site: GitHub Pages, deployed by `.github/workflows/pages.yml` on every push to `main`. The workflow runs `python tools/build.py`, then `python tools/stage_site.py`, and publishes only `_site/`.
- `tools/stage_site.py` copies the public files (`index.html`, `assets/`, `start/`, `setup/`, `modules/`, `project/`, `labs/`, `capstone/`, `code/`) and **leaves out**:
  - this guide and anything else in `docs/` (notes for me, not for learners);
  - `src/` and `tools/`;
  - every draft module: `modules/NN/` and `code/traincrest-assist/mNN/` for modules with `"draft": true` in `nav.json`.
  So removing `"draft": true` and pushing is what publishes a Part.
- Preview locally exactly what will go live: `python tools/build.py && python tools/stage_site.py`, then serve `_site/` (e.g. `python -m http.server -d _site 8000`). `_site/` is git-ignored.
- Publish a change: commit and `git push`. Check the run under the repo's **Actions** tab.

---

## 8. Open-source lab guide (Ollama track)

A second, separate track for learners without Azure or paid API access, written in the style of Microsoft hands-on labs: overview table (objectives, prerequisites, what you finish with), exercises > tasks > numbered steps, exact commands, expected output, a **Checkpoint** callout per exercise, a troubleshooting table, review and cleanup. One lab per Part, about **3 hours**, used after the trainer's demo. **Build one for every new Part** (standing request, 2026-10-12).

- Pages: `src/oss/` (`index.html`, `lab-0-setup.html`, `lab-1.html` …), kind `osslab`, in the nav section "Open-source lab guide".
- Code: `code/oss-labs/` is the learner's project folder `oss-genai-labs`: `client.py` (LLM_BASE_URL / LLM_API_KEY / CHAT_MODEL / AGENT_MODEL / EMBED_*), `.env.example`, `requirements.txt`, `lab0_check.py`, `lN_*.py` per lab, `data/` (courses, help articles, 3 internal docs). Programs are self-contained, simpler than the handbook drills, and Ollama-first.
- Keys: Ollama needs none (the placeholder `ollama` satisfies the OpenAI library). Option B, documented in Lab 0, is a hosted open-model provider with a free key (Groq, OpenRouter); embeddings stay on Ollama.
- Models: `llama3.2` (chat, 8 GB RAM), `nomic-embed-text` (embeddings), `qwen2.5:7b` (agents, 16 GB RAM).
- The whole section is a **draft** (`"draft": true` on the nav section, plus `"code_dirs": ["code/oss-labs"]`): its pages are hidden from live sidebars and `tools/stage_site.py` leaves its pages and code out of the site. To publish it, remove `"draft": true` from the section (Lab 2 and 3 pages link to nothing in draft modules, but check the build output).
- Draft sections work like draft modules: any nav section can carry `"draft": true`.
