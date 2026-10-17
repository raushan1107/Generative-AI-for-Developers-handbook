# Handoff: finance retrofit, where to continue

Last local session: 2026-10-17. Read this first, then docs/FINANCE-USE-CASE.md (the approved design) and
docs/HANDBOOK-GUIDE.md (page structure, callouts, house style).

## The goal (agreed with the author)

- Learners are mostly from banking and investment. Every lab, drill, milestone, open-source lab and demo
  solves a finance problem: **RR Finance Bank**, a retail bank, and its support assistant **RR Finance Assist**
  (project folder `code/rrfinance-assist/m01..m07`). Capstone: **RR Finance Capital**, an investment research copilot.
- Notes keep their generic explanation and examples, and every topic gets a mandatory
  `<div class="callout finance">` ("In finance") example.
- Parts I–III are retrofitted in place. Parts IV–V and the capstone are then written finance-first.
- Modules 04–07 are `"draft": true` in tools/nav.json. Keep drafts as drafts unless the author says otherwise.

## Rules

- Commits are authored by **Raushan Ranjan <raushanr1107@gmail.com>** only, with **no Co-Authored-By lines**.
- Don't push or publish without asking the author.
- Real outputs only: pages show output from actual runs (local Ollama: llama3.2, qwen2.5:7b for tool/agent
  drills, nomic-embed-text). If you can't run Ollama, use the saved outputs in `docs/handoff/outputs/` and
  don't invent output. Small-model failures are shown honestly as lessons.

## Done

- Data kit (`code/genai-labs/data`): products.json (P101–P120), help/*.md (10 articles, 44 heading sections),
  help_questions.json, train/eval tickets, statement.png, internal/ docs.
- All drills (lab01–lab07) and milestones m01–m07 are rewritten for the bank. 127 drill tests and
  10/29/35/44/54 milestone tests pass.
- Part I pages, the concept map (tools/maps/part-1.json, with a `finance` field per topic) and the OSS lab-0/1
  are fully updated.
- All Part II–III topic pages have finance callouts.
- Module 04 topic pages are done. Module 05 topic pages, index.html and recap.html are done.

## To do, in order

1. **src/modules/05/build.html** (Milestone 5): still about courses. Change it to products and help:
   - meta description, lead and chips: "Index: 20 products + 44 sections".
   - Diagram: lines 17–34, with filters `kind, family, audience, max_annual_fee_usd` and `search_products`.
   - Tree line 52 and goal line 68.
   - build_index prompt (lines 83–86): schema fields kind/family/audience, annual_fee_usd as Int32.
   - Output: `Local index: 20 products + 44 help sections, 768-dimension vectors from nomic-embed-text.` and `Done in 9.8s.`
   - Tool prompt: `search_products`, filters family/audience/max_annual_fee_usd, return id, name, family,
     audience, annual_fee_usd, rate_pct, rate_type. Done when "card for spending abroad" returns P111 Voyager first.
   - `data-lines` for the tool is now about **84–118** of app/tools.py (the class at 85, the function at 97); check it.
   - Test count: **35 passed**.
   - Real query results are in outputs/m05_queries.txt. Lesson: "card I can use on holiday" ranks the
     Business Card above Voyager (noise on a tiny catalogue). With family=cards and max fee $0, "spending
     abroad" returns $0 cards with no travel benefit: the filter worked, but the bank has no such product, so
     Assist should say so rather than oversell.
   - Verify list: change to "card for spending abroad" and "cards with no annual fee".
2. **src/modules/04/build.html**: the real-turn block still shows the old `[tool] quote_refund`. The
   outputs/m04_turn.txt run **failed** ("couldn't reach the AI service"), so re-run it with
   `docs/handoff/turn_m04.py` (PYTHONPATH=., run from code/rrfinance-assist/m04, Ollama qwen2.5:7b, 900 s timeout).
   The question: customer Mei, RR-10293, asking "Which of my overdraft fees will you refund?". The expected
   tool is quote_fee_refund, which gives $87 for AC-5512.
3. **Module 06** pages (src/modules/06/*): replace course and help-centre examples using outputs/lab06_*.txt.
   build.html covers M6 (search_help, rag_answer@v1, citations), and the recap needs the same update.
4. **Module 07** pages: use outputs/q_lab07_*.txt (07n/07y are the declined and approved runs). build.html
   covers M7 (request_card_freeze, request_dispute, approval and idempotency), and the recap needs the same update.
5. **src/oss/lab-2.html and lab-3.html**: run code/oss-labs/l2_*.py and l3_*.py for real outputs and update the pages.
6. Small leftovers:
   - The M3 SAFE_REPLY still says "ticket".
   - Check the paths in docs/HANDBOOK-GUIDE.md.
   - grep src/ for `course|voucher|enrol|LAB-|TrainCrest|Docker`.
7. Run `python tools/concept_map.py && python tools/build.py`, then all tests. Commit, then ask before pushing.
8. Next: **Part IV** (Modules 08–10 plus open-source Lab 4) as drafts, finance-first, then Part V and the
   capstone brief. Add part-2/part-3 concept maps with `finance` fields.

## Helpers

`docs/handoff/ed.py` holds the editing helpers used for the retrofit. Write edit scripts as files, not heredocs,
because heredocs mangle `\n`.
- `sub(path, [(old, new), ...])`: all-or-nothing exact replacements.
- `finance_after(path, anchor, html)`
- `replace_between(path, start, end, new)`

Page meta is JSON in `<!--meta ... -->`, so watch out for stray quotes, which break tools/build.py.
