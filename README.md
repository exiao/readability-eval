# readability-eval

A readability benchmark for LLM writing.

Scores model output on seven clarity rules, minus a penalty for AI slop. Prompts are **real ChatGPT conversations**, not authored test cases.

```
Score = clarity x (1 - slop tax)
```

## Results

30 real user prompts per model. Judge: `claude-opus-5`.

| Score | Model | Slop/1k | Words | Economy | Form |
|:---:|---|---:|---:|---:|---:|
| 🥇 **91.8** | `claude-opus-5` | 0.9 | 558 | 6.9 | 8.7 |
| 🥈 **85.9** | `claude-opus-4-6` | 2.8 | 571 | 7.1 | 7.2 |
| 🥉 **83.9** | `claude-sonnet-4-6` | 3.4 | 531 | 7.4 | 6.8 |
| **82.4** | `claude-haiku-4-5` | 2.2 | 329 | 7.4 | 5.3 |

Full table with all seven rules in [`results/LEADERBOARD.md`](results/LEADERBOARD.md).

```bash
python3 -m readability_eval.chart --limit 5   # every model on the same 5 prompts
```

`--limit N` re-scores each model over its first N prompts. Without it the chart plots 30-prompt and 5-prompt runs on one axis, which compares different tests; the command prints `MIXED n=[5, 30]` when that happens.

**Nobody writes to length.** Every prompt carries a word budget for what that question actually deserves, set from the ask alone: a two-line question gets ~60 words, a full lesson plan gets 500. Models run 1.5x to 2.5x over. The failure is not vocabulary, it is volume: understandability, filler and simple-word scores sit near 10 for everyone, while economy ranges 4.6 to 7.5 and does almost all the separating.

### Smoke sample: other families

Five prompts only, judged by `claude-opus-5`. **Not comparable to the table above** and not a ranking. Included because the length finding is so lopsided it survives the small sample.

| Score | Model | Words | Economy |
|:---:|---|---:|---:|
| 94.5 | `google/gemini-3.5-flash` | 989 | 6.2 |
| 94.4 | `moonshotai/kimi-k3` | 740 | 7.9 |
| 94.0 | `openai/gpt-5.6-sol` | 1372 | 5.5 |
| 93.5 | `x-ai/grok-4.5` | 804 | 8.0 |
| 87.9 | `qwen/qwen3.8-max` | 2577 | 2.0 |

Qwen wrote 2577 words on average against budgets of 55-550. That is not a scoring artifact; it is a 2500-word answer to a question that wanted sixty. It still lands within 7 points of the top, because being long is the only thing it does wrong.

### Can you just ask for a short answer?

Yes, and it is the biggest single lever. `--condition brief` appends *"Answer in 50 words or less"*:

| Model | Default | Brief | Change | Coverage |
|---|---:|---:|---:|---:|
| `claude-opus-5` | 91.8 (558w) | 91.2 (48w) | -0.6 | 97% → 78% |
| `claude-opus-4-6` | 85.9 (571w) | 82.1 (47w) | -3.8 | 91% → 66% |
| `claude-sonnet-4-6` | 83.9 (531w) | 78.5 (49w) | -5.4 | 89% → 60% |
| `claude-haiku-4-5` | 82.4 (329w) | 74.1 (51w) | -8.3 | 80% → 59% |

Every model collapses to ~48 words when told to. So **the length is a default, not a limit** — they can all write tightly, they just don't unless asked.

**But brevity is not free, and it is not even a win.** Look at the coverage column: the share of the request actually addressed falls 19 to 29 points. **Every model scores worse under the brief condition**, from -0.6 to -8.3, and the models that lose most are the ones that were already closest to budget. Haiku had no bloat left to cut, so it paid the full coverage cost for nothing.

So "just ask for 50 words" is not a free upgrade. It buys concision with completeness, and once verbosity is weighted honestly against the other six rules, that trade never comes out ahead. Length is a real defect, but it is a smaller one than not answering the question.

```bash
python3 -m readability_eval.run --model X --condition brief
```

## Prompts

Real first-turn English prompts from [WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M), a corpus of 1M real ChatGPT conversations. Verbatim, typos included.

Sampled to the topic distribution OpenAI reported for its own 700M users ([NBER w34255](https://www.nber.org/papers/w34255)):

| Share | Category | n |
|---:|---|---:|
| 29% | Practical guidance (how-to, tutoring, ideation) | 9 |
| 24% | Seeking information | 6 |
| 24% | Writing — mostly *editing text the user pasted* | 11 |
| 5% | Technical help | 3 |
| 2% | Self-expression | 1 |

Two filter passes before selection: classify into the taxonomy, then vet each prompt for scorability. Rejected: prompts that prescribe their own output format (which confounds form scoring), depend on private context, are image-generation tag dumps, or are NSFW/incoherent. 881 candidates → 30.

**This benchmark does not score factual correctness.** Real prompts do not come with ground truth. Each prompt carries an `asks` list — the parts of the request a response should engage with — and the judge is explicitly told a confidently wrong but clear answer still counts as addressing the item. Coverage exists to stop a model winning on brevity by ignoring half the question, nothing more.

## The seven rules

Rules 1-6 come from Orwell's *Politics and the English Language*. Rule 7 was added after clean-but-report-shaped answers kept scoring well.

| # | Rule | Scored by |
|---|------|-----------|
| 1 | Easy to understand? | Judge, relative to the inferred audience |
| 2 | Is it as long as the question deserves? | Words against a per-prompt budget, gated by coverage |
| 3 | Avoids jargon and acronyms? | Undefined acronyms per 100 words |
| 4 | Would imagery make it clearer? | Judge, must name the image it wanted |
| 5 | Complex phrases instead of simple words? | `utilize`→`use`, `in order to`→`to` |
| 6 | Filler, pretentious diction, euphemism? | Three counters, euphemism weighted 3x |
| 7 | Shaped like the answer, or like a report? | Judge quote + scaffolding density per budget |

Rules 2, 3, 5, 6 are deterministic counters. Rules 1, 4 and 7 use a judge that must quote its evidence — no quote, no penalty.

**Economy is weighted at 0.75, the other six at 1.0.** It is the only rule with real variance, so at equal weight it quietly became the benchmark: 65% of saved answers scored *higher* when truncated to half their length, the worst by 41 points. Truncation cannot improve an answer, so a metric that rewards it is measuring the wrong thing. Three fixes, in order of size:

- **Economy no longer trips the conjunctive cap.** A rule under 2 caps the score at 55, which is right for an answer nobody can follow and wrong for one that is merely long. 15 of the 19 caps in the corpus were verbosity, costing ~31 points each.
- **The decay curve no longer bottoms out.** It hit exactly 0.0 at 3x budget and stayed there, so every word past that point was free and a 5000-word answer tied a 1050-word one. It now halves every 1.5x over: 2x → 6.3, 3x → 4.0, 5x → 1.6.
- **Coverage carries the empty case instead.** Economy multiplies length by coverage, so it read 0.0 both for an answer that said nothing and for one that answered fully at length. Coverage under a third now caps the score on its own.

Worst gain from halving an answer: **+41.3 → +4.4**.

**Rule 2 needs the coverage gate.** Scored as raw brevity it crowns the emptiest answer, so coverage multiplies in: answering half the question caps economy at half however tersely you did it. Under budget is free — terse is never punished.

**Rule 7 catches what the word list can't.** Scaffolding is headers, tables and section labels, not tic phrases, so a report-shaped answer to a simple question can score clean sentence-by-sentence and still be unreadable as a whole.

Rule 7 is scored twice and takes the worse result. The judge grades shape subjectively and must quote the heading it objects to; a counter measures heading and list-item density against the prompt's *budget*, not against the answer's own length. Scoring density against its own length is circular, since a 2500-word answer with 90 headings looks normally structured for its size, which is exactly the failure. The counter exists because the judge is forgiving: it quotes one bad heading and passes the rest. Fourteen responses here scored a perfect 10 on form while carrying up to 69 headings and 134 list items. Modest structure is free, so a list-shaped answer to a list-shaped question is never punished.

## Slop detection

Three layers. A word list alone catches maybe half.

| Layer | Weight | Catches |
|---|---|---|
| 175 terms | 1.0 | `delve`, `testament to`, `boasts`, `great question`, `load-bearing` |
| 12 patterns | 1.0 / 0.5 | `It's not X. It's Y.` · `not just X, but Y` · `serves as` |
| Structure | 1.0 / 0.5 | verbless noun-list fragments, staccato runs, rule-of-three padding |
| Formatting | 0.25 / 0.1 | labelled bullets, emoji bullets, hyphenated adjective pairs |

**Hits are weighted, not counted.** An unambiguous tell scores 1.0, a construction that also appears in correct writing scores 0.5, and a formatting habit that is usually the right choice scores 0.1 to 0.25. Flat counting let ordinary formatting outweigh real slop: labelled bullets like `- **Kernel version**: 6.1` fired 231 times across 265 responses, more than every other signal combined.

**Two triple rules, and the difference is the conjunction.** `Rent, transportation, and food.` is a list and scores nothing. `Rent, transportation, food.` is a verbless noun-list fragment: it has the rhythm of a sentence and none of the content, because nothing acts on anything. Rule-of-three padding is narrower still, requiring all three items to be adjectival *and* to sit in a running sentence, since in a heading the triple is the content. The naive version matched any three-item list, fired 262 times, and cost some answers the entire slop cap for writing normally.

**Staccato** is period-spam: three or more consecutive short declarative sentences that refuse to join a clause. *"Little words. Short sentences. Cut the fat. Redo it."* reads like a drill sergeant and contains no banned vocabulary at all, so the word list cannot see it. Only declaratives count, because rhetorical question pairs and classroom exclamations are cadence a reader expects; an earlier version that ignored this flagged 25 runs in the corpus and nearly all were lesson plans. Its contribution is capped, since a rate per 1000 words would let one tic in a 50-word answer outweigh every vocabulary offence combined.

Sources: [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), the [humanizer](https://github.com/blader/humanizer) pattern set, a personal kill list.

Slop only subtracts, capped at 30%. Clean writing earns nothing by itself. The scorer strips code, fences and quotes first, so a document *about* slop doesn't score as slop.

## Limitations

**Can't you just prompt your way around this?**
Yes. This scores the model on its own: no system prompt beyond "You are a helpful assistant", no harness, no skills, no style guide. Of course a prompt fixes it. The point is measuring whether you have to.

**Isn't the judge biased?**
Yes, and this table has it. `claude-opus-5` judges the four Claude models including itself, and it comes first. That is exactly where self-preference would show up. `rejudge.py` re-scores saved responses with a different judge and no regeneration; run it before trusting any cross-family ranking here.

**Where do the word budgets come from?**
A model set them from each prompt. They are defensible per-prompt but they are not ground truth, so the absolute scores are softer than the relative ones.

**Other known limits**
- The non-Claude table is 5 prompts. It is a smoke test, not a result.
- 30 prompts is still a small sample. Treat gaps under ~3 points as noise.
- English only.
- Scores are not comparable across prompt-set versions; the set is versioned in `data/prompts.json`.

## Run it

```bash
git clone https://github.com/exiao/readability-eval
cd readability-eval
export OPENROUTER_API_KEY=sk-or-...

python3 -m readability_eval.run --model google/gemini-3.5-flash
python3 -m readability_eval.report
```

That is the whole setup: one key, no judge flags. The judge defaults to a model on whichever backend you picked, so nothing points at a host you don't have.

Standard library only. A run is 30 prompts plus 30 judge calls, well under a dollar on most models. Add `--limit 5` for a cheap smoke run.

**Backends and environment**

| Variable | Used by | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` | `--backend openrouter` (default) | Required. Any model OpenRouter serves. |
| `ANTHROPIC_API_KEY` | `--backend anthropic` | Required unless your endpoint handles auth. |
| `ANTHROPIC_BASE_URL` | `--backend anthropic` | Optional. Defaults to `https://api.anthropic.com`; point it at a local proxy or gateway to route Claude traffic through one. |

`run_all.sh` runs every model on the default condition, `run_brief.sh` the brief condition, `run_claude.sh` the Claude family. All three take their credentials from the environment.

Every run starts with a **contamination probe**: it asks the backend what tools it has and refuses to run if the answer looks like an agent rather than a bare model. This exists because two full runs were thrown away after being scored through an agent CLI that silently attached a persona, memory and a full toolset. Scoring a harness and calling it a model is the easiest way to get this wrong.

Use a judge from a different family than the model under test, and verify with `rejudge.py`.

## License

Apache 2.0.
