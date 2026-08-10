# readability-eval

Most models answer a simple question with 500 words, three headings and a bulleted table. This benchmark measures that.

It scores model output on seven clarity rules, then subtracts a penalty for AI slop. The prompts are **real ChatGPT conversations** rather than test cases someone wrote for the occasion.

```
Score = clarity x (1 - slop tax)
```

## Results

30 real prompts per model, judged by `claude-opus-5`, which is the same family as everything in the table including itself. Read [Limitations](#limitations) before you treat the order as settled.

| Score | Model | Slop/1k | Words | Filler | Form |
|:---:|---|---:|---:|---:|---:|
| 🥇 **85.7** | `claude-opus-5` | 0.9 | 558 | 9.8 | 8.8 |
| 🥈 **76.2** | `claude-opus-4-6` | 2.8 | 571 | 7.9 | 6.7 |
| 🥉 **75.3** | `claude-haiku-4-5` | 2.2 | 329 | 7.8 | 6.3 |
| **72.7** | `claude-sonnet-4-6` | 3.4 | 531 | 7.2 | 6.0 |

All seven rules are in [`results/LEADERBOARD.md`](results/LEADERBOARD.md).

**Length is not what separates these models. Shape and filler are.** Every one of them runs 1.5x to 2.5x over its word budget, so verbosity barely ranks anything. Form (6.0 to 8.8) and filler (7.2 to 9.8) account for 87% of the gap between first and last. Being long is what they all do wrong. Being padded and shaped like a report is what the losers do wrong.

A ten-prompt smoke sample of other families (GPT-5.6, Kimi, Gemini, Grok, GLM, Qwen) puts everyone inside a 9-point band, all of them writing long. Different prompts and different budgets, so it is not comparable to the table above.

### Can you just ask for a short answer?

Yes, and it works. `--condition brief` appends *"Answer in 50 words or less"*:

| Model | Default | Brief | Change | Coverage |
|---|---:|---:|---:|---:|
| `claude-opus-5` | 85.7 (558w) | 87.2 (48w) | **+1.5** | 96% → 78% |
| `claude-opus-4-6` | 76.2 (571w) | 80.1 (47w) | **+3.9** | 92% → 65% |
| `claude-sonnet-4-6` | 72.7 (531w) | 77.2 (49w) | **+4.5** | 89% → 62% |
| `claude-haiku-4-5` | 75.3 (329w) | 74.7 (51w) | -0.6 | 82% → 60% |

Every model drops to about 48 words when told to, so the length is a default and not a limit. The further over budget a model runs on its own, the more the instruction helps it. It costs something: coverage falls 19 to 27 points, which means a model answering fewer of the things the user asked for. Whether that trade is worth it depends on how this benchmark weights the rules.

## Where the prompts come from

Real first-turn English prompts from [WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M), a corpus of a million real ChatGPT conversations. Copied verbatim, typos included.

They are sampled to match the topic mix OpenAI reported across its 700M users ([NBER w34255](https://www.nber.org/papers/w34255)): practical guidance 29%, seeking information 24%, writing 24%, technical help 5%, self-expression 2%.

Two filter passes cut 881 candidates down to 30. Rejected: prompts that dictate their own output format, prompts that need private context, image-tag dumps, and anything NSFW or incoherent.

**This does not score whether the answer is true.** Real prompts arrive without ground truth. Each one carries a list of the things a response should engage with, and coverage exists only to stop a model winning on brevity by ignoring half the question.

## The seven rules

Rules 1 to 6 come from Orwell's *Politics and the English Language*. Rule 7 was added after clean but report-shaped answers kept scoring well.

| # | Rule | Scored by |
|---|------|-----------|
| 1 | Easy to understand? | Judge, relative to the inferred audience |
| 2 | As long as the question deserves? | Words against a per-prompt budget, gated by coverage |
| 3 | Avoids jargon and acronyms? | Undefined acronyms per 100 words |
| 4 | Would imagery make it clearer? | Judge, and it must name the image it wanted |
| 5 | Complex phrases where simple words work? | `utilize` → `use`, `in order to` → `to` |
| 6 | Filler, pretentious diction, euphemism? | Phrase list plus 20 grammar patterns |
| 7 | Shaped like the answer, or like a report? | Judge quote plus scaffolding density |

Every rule gets judged by a model. Rules 2, 3, 5 and 6 are also counted mechanically, and the score is the worse of the two, so the judge can fail an answer the counter waved through and the counter can fail one the judge enjoyed. Every judged verdict has to quote its evidence: no quote, no penalty. Length is weighted at 0.75 and the other six at 1.0.

## Slop detection

Three layers, because a word list on its own catches maybe half of it.

| Layer | Weight | Catches |
|---|---|---|
| 175 terms | 1.0 | `delve`, `testament to`, `boasts`, `great question` |
| 12 patterns | 1.0 / 0.5 | `It's not X. It's Y.` · `not just X, but Y` · `serves as` |
| Structure | 1.0 / 0.5 | verbless noun-list fragments, staccato runs, rule-of-three padding |
| Formatting | 0.25 / 0.1 | labelled bullets, emoji bullets, hyphenated adjective pairs |

Hits are weighted rather than counted. An unambiguous tell scores 1.0, and a formatting habit that is usually the right choice scores 0.1. Slop only ever subtracts, capped at 30%, so clean writing earns nothing by itself. Code, fences and quotes are stripped first, so a document *about* slop does not score as slop.

Sources: [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), the [humanizer](https://github.com/blader/humanizer) pattern set, and a personal kill list.

## Limitations

**Truncation still buys points, and this is the largest open problem here.** On the current 338-response corpus, cutting an answer in half improves its score 51% of the time, worst case by 38.1 points. Halving a response cannot make it better, so any gain is the benchmark measuring the wrong thing. Do not read small gaps in these tables as meaningful until it is fixed.

**The judge is biased.** `claude-opus-5` grades four Claude models including itself, and wins by 9.5 points. Treat first place as unproven. `rejudge.py` re-scores saved responses with a different judge, and a judge swap already moved every score by 2 to 5 points and reordered the bottom two.

**Most of the detector patterns never fire.** 18 of 21 filler patterns and 43 of 49 first-draft jargon terms appeared zero times on real responses, because they were written against textbook bad writing that current models do not produce. Treat a clean score on rules 3 and 6 as unproven rather than as evidence.

Also worth knowing: scores from before commit `cacf8cf` are not comparable, since rules 1, 3, 5 and 6 had no judged half then. The non-Claude table is a 10-prompt smoke test. The word budgets were set by a model and are not ground truth. 30 prompts is a small sample, so gaps under about 3 points are noise. English only.

## Run it

```bash
git clone https://github.com/exiao/readability-eval
cd readability-eval
export OPENROUTER_API_KEY=sk-or-...

python3 -m readability_eval.run --model google/gemini-3.5-flash
python3 -m readability_eval.report
```

Standard library only. A run is 30 prompts plus 30 judge calls, well under a dollar on most models, and `--limit 5` gives you a cheap smoke run.

| Variable | Used by | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` | `--backend openrouter` (default) | Required |
| `ANTHROPIC_API_KEY` | `--backend anthropic` | `ANTHROPIC_TOKEN` is also accepted |
| `ANTHROPIC_BASE_URL` | `--backend anthropic` | Optional, routes both the model and the judge through one endpoint |

**Keep a run on one backend.** The judge follows `--backend` unless you override it, and the saved summary records both, so a mixed run is visible afterwards instead of silent. Judging across model families is worth doing. Splitting one result across two providers by accident is not.

`run_all.sh` runs every model, `run_brief.sh` the brief condition, `run_claude.sh` the Claude family.

Every run opens with a contamination probe: it asks the backend what tools it has and refuses to start if the answer looks like an agent rather than a bare model. Two full runs were thrown away before that existed, scored through an agent CLI that had quietly attached a persona, memory and a toolset.

Use a judge from a different family than the model you are testing, and check it with `rejudge.py`.

## License

Apache 2.0.
