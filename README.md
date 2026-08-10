# readability-eval

A readability benchmark for LLM writing.

Scores model output on seven clarity rules, minus a penalty for AI slop. Prompts are **real ChatGPT conversations**, not authored test cases.

```
Score = clarity x (1 - slop tax)
```

## Results

30 real user prompts per model. Judge: `claude-opus-5` — the same family as every model in this table, including itself. See [Isn't the judge biased?](#limitations) before reading the order as settled.

| Score | Model | Slop/1k | Words | Filler | Form |
|:---:|---|---:|---:|---:|---:|
| 🥇 **85.7** | `claude-opus-5` | 0.9 | 558 | 9.8 | 8.8 |
| 🥈 **76.2** | `claude-opus-4-6` | 2.8 | 571 | 7.9 | 6.7 |
| 🥉 **75.3** | `claude-haiku-4-5` | 2.2 | 329 | 7.8 | 6.3 |
| **72.7** | `claude-sonnet-4-6` | 3.4 | 531 | 7.2 | 6.0 |

Full table with all seven rules in [`results/LEADERBOARD.md`](results/LEADERBOARD.md).

```bash
python3 -m readability_eval.chart --limit 5   # every model on the same 5 prompts
```

`--limit N` re-scores each model over its first N prompts. Without it the chart plots 30-prompt and 5-prompt runs on one axis, which compares different tests; the command prints `MIXED n=[5, 30]` when that happens.

**Length is not what separates models. Shape and filler are.** Every prompt carries a word budget for what that question actually deserves, set from the ask alone: a two-line question gets ~60 words, a full lesson plan gets 500. Models still run 1.5x to 2.5x over, and that is a real defect — but it is a defect they *share*, so it does almost no separating. Economy spans just 5.2 to 6.1 across this table, the second-narrowest range of the seven rules.

The two rules that actually rank the models are form (6.0 to 8.8) and filler (7.2 to 9.8). Together they account for **87% of the 13-point gap** between first and last. Economy contributes 8%. Being long is what every model does wrong; being *shaped like a report* and *padded* is what the losers do wrong.

An earlier version of this README claimed the opposite, that economy did almost all the separating and the other rules sat near 10 for everyone. That was an artifact: those runs were scored before rules 1, 3, 5 and 6 had a judged half, so the mechanical counters graded them unopposed and passed almost everything. Once the judge scored them too, filler fell from 9.98 to a 7.2-9.8 spread and form from 8.67 to 6.0-8.8. The rules were never flat. They were unmeasured.


### Smoke sample: other families

Ten prompts only, judged by `claude-opus-5`. **Not comparable to the table above** and not a ranking.

| Score | Model | Words | Economy | Coverage |
|:---:|---|---:|---:|---:|
| 78.2 | `openai/gpt-5.6-sol` | 965 | 5.8 | 92% |
| 76.9 | `openai/gpt-5.6-terra` | 1095 | 5.1 | 98% |
| 76.5 | `moonshotai/kimi-k3` | 512 | 5.5 | 95% |
| 75.4 | `openai/gpt-5.6-luna` | 1022 | 5.7 | 95% |
| 74.4 | `google/gemini-3.6-flash` | 642 | 5.0 | 90% |
| 72.9 | `anthropic/claude-opus-5` | 1205 | 4.4 | 100% |
| 72.1 | `x-ai/grok-4.5` | 678 | 5.0 | 100% |
| 72.0 | `z-ai/glm-5.2` | 724 | 5.3 | 96% |
| 69.5 | `qwen/qwen3.8-max` | 791 | 4.0 | 98% |

Every model here lands in a 9-point band, and every one of them writes long. Economy spans 4.0 to 5.8 — worse than the Claude table, and just as flat. Verbosity is close to universal.

**The same model scores differently on different sample sizes, and that is the point of the warning.** `claude-opus-5` scores 85.7 on 30 prompts and 72.9 on these 10. Different prompts, different budgets, different difficulty. Never read a number from this table against a number from the one above.

### Can you just ask for a short answer?

Yes, and it works. `--condition brief` appends *"Answer in 50 words or less"*:

| Model | Default | Brief | Change | Coverage |
|---|---:|---:|---:|---:|
| `claude-opus-5` | 85.7 (558w) | 87.2 (48w) | **+1.5** | 96% → 78% |
| `claude-opus-4-6` | 76.2 (571w) | 80.1 (47w) | **+3.9** | 92% → 65% |
| `claude-sonnet-4-6` | 72.7 (531w) | 77.2 (49w) | **+4.5** | 89% → 62% |
| `claude-haiku-4-5` | 75.3 (329w) | 74.7 (51w) | -0.6 | 82% → 60% |

Every model collapses to ~48 words when told to. So **the length is a default, not a limit** — they can all write tightly, they just don't unless asked.

**Three of four score better under the instruction, and the worst writer gains the most.** Sonnet gains 4.5, Opus-4-6 gains 3.9, Opus-5 gains 1.5. The exception is Haiku, which loses 0.6 — it was already the tersest model at 329 words, so it had the least bloat to cut and still paid the coverage cost. The pattern is consistent: the further over budget a model runs by default, the more the instruction helps it.

**It is still not free.** Coverage falls 19 to 27 points for everyone, and that is a real loss the score only partly captures: a 60%-coverage answer is ignoring two of every five things the user asked for. What the numbers say is that for these models, at this weighting, cutting the padding buys more than the dropped coverage costs. That is a defensible trade, not a free upgrade, and it depends on the weights in this benchmark — economy is deliberately underweighted at 0.75, and coverage caps the score outright below a third. Move either and the sign could flip.

An earlier version of this README reported the opposite result, that every model scored worse under the brief condition, worst -8.3. Those runs lacked the judged half of rules 1, 3, 5 and 6. Once those axes scored, the *default* condition lost far more points than the brief one — long answers have more room to be padded and report-shaped — and the sign reversed.

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
| 6 | Filler, pretentious diction, euphemism? | Phrase list + 20 grammar patterns, euphemism 3x |
| 7 | Shaped like the answer, or like a report? | Judge quote + scaffolding density per budget |

Every rule is judged. Rules 2, 3, 5 and 6 are ALSO counted mechanically, and the score is the worse of the two — the judge can fail an answer the counter waved through, and the counter can fail one the judge found pleasant. Rules 1, 4 and 7 are judge-only. Every judged verdict must quote its evidence: no quote, no penalty.

The second opinion exists because the counters are precise but blind. They only see the phrases on their lists, and most of those lists never fire (see the caveat below). On a 20-response sample the judge was stricter than the counter in 36 of 79 rule-judgements, catching `tCO₂e`, `solar irradiance`, `borne by the sender` and "the unglamorous but critical layer" — none of which any list would have contained.

**Economy is weighted at 0.75, the other six at 1.0.** When the counters were scoring rules 1, 3, 5 and 6 unopposed, economy was the only rule with real variance, so at equal weight it quietly became the benchmark: 65% of saved answers scored *higher* when truncated to half their length, the worst by 41 points. Truncation cannot improve an answer, so a metric that rewards it is measuring the wrong thing. Three fixes, in order of size:

- **Economy no longer trips the conjunctive cap.** A rule under 2 caps the score at 55, which is right for an answer nobody can follow and wrong for one that is merely long. 15 of the 19 caps in the corpus were verbosity, costing ~31 points each.
- **The decay curve no longer bottoms out.** It hit exactly 0.0 at 3x budget and stayed there, so every word past that point was free and a 5000-word answer tied a 1050-word one. It now halves every 1.5x over: 2x → 6.3, 3x → 4.0, 5x → 1.6.
- **Coverage carries the empty case instead.** Economy multiplies length by coverage, so it read 0.0 both for an answer that said nothing and for one that answered fully at length. Coverage under a third now caps the score on its own.

Worst gain from halving an answer: **+41.3 → +4.4**.

**That fix has since decayed, and it is the largest open problem in this benchmark.** Re-measuring on the current 338-response corpus, halving an answer still improves its score **51% of the time**, worst case **+38.1**, mean +2.3. The three fixes above addressed the economy rule specifically, but truncation also removes padding, headings and slop, so it now buys points on rules 6 and 7 instead. Chopping a response in half cannot make it a better answer, so any score that rises is measuring the wrong thing. Do not read small gaps in these tables as meaningful until this is fixed.

**Rule 2 needs the coverage gate.** Scored as raw brevity it crowns the emptiest answer, so coverage multiplies in: answering half the question caps economy at half however tersely you did it. Under budget is free — terse is never punished.

**Rule 6 needed patterns, not a word list.** Filler is a grammatical shape, not a vocabulary: an exact-phrase list scores `worth noting` and lets `it is worth mentioning` through. Patterns now cover expletive subjects (`there are several factors that...`), wordy connectives, redundant causation and stacked hedges. Note the line it has to walk: `there is no index on user_id` states a fact and must not fire, while `there are several factors that matter` delays the real subject and must.

**Caveat, and it applies to rules 3 and 6 both: most of those patterns never fire on this corpus.** 18 of 21 filler patterns and 43 of 49 first-draft jargon terms appeared zero times in the 265 real responses saved at the time (the corpus is now 349). They were written against textbook bad writing that current models do not produce. Validating a detector on sentences you invented for it proves only that you can write to your own regex, so the jargon list was cut to terms actually observed, and the test fixtures are now verbatim corpus sentences. Treat a clean score on those rules as unproven, not as evidence.

The acronym half of rule 3 is the part with real evidence: `BATNA` and `ZOPA` dropped unexplained on a self-taught negotiator, `EMI` on someone planning a house purchase.

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
Yes, and this table has it in the worst form. `claude-opus-5` judges four Claude models including itself, and it wins by 9.5 points — a bigger gap than separates the other three combined. That is exactly where self-preference would show up, and nothing here rules it out. Treat first place as unproven.

The gap is not obviously *only* bias: Opus-5's win is concentrated in filler (9.8 vs 7.2-7.9) and form (8.8 vs 6.0-6.7), and those two rules are scored twice, with a mechanical counter that the judge cannot overrule upward. But a same-family judge grading its own output is the one result you should not take on trust.

`rejudge.py` re-scores saved responses with a different judge and no regeneration. Run it before citing this ranking:

```bash
python3 -m readability_eval.rejudge --label claude-opus-5 \
    --judge-model <a model outside this table> --judge-backend openrouter
```

A judge swap moved every score in this table by 2 to 5 points in earlier testing and changed the order of the bottom two. Judge choice is not a detail here; it is part of the result. Pick one that is not competing.

**Why did the numbers change?**
Every published score before commit `cacf8cf` was produced when rules 1, 3, 5 and 6 had no judged half — the mechanical counters scored them unopposed and passed nearly everything. Since the judge can only ever *lower* a rule (the score is the worse of judge and counter), those numbers were an upper bound. Rejudging with the same judge model dropped the table 6 to 11 points and reordered it. Scores from before that commit are not comparable to scores after it.

**Is the Claude table single-provider?**
No, and the saved files say so. The responses were generated against the Anthropic API (`backend: anthropic`), but the rejudge pass that produced the current scores ran `anthropic/claude-opus-5` over OpenRouter (`judge_backend: openrouter`) because the machine doing the rejudge had no working Anthropic credential at the time. Same judge model, two providers in one result. It is disclosed rather than hidden, but a clean re-run should keep subject and judge on one endpoint — `run_claude.sh` now does, and `ANTHROPIC_BASE_URL` points both at whatever gateway you use.

**Where do the word budgets come from?**
A model set them from each prompt. They are defensible per-prompt but they are not ground truth, so the absolute scores are softer than the relative ones.

**Other known limits**
- The non-Claude table is 10 prompts. It is a smoke test, not a result.
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
| `ANTHROPIC_API_KEY` | `--backend anthropic` | Required unless your endpoint handles auth. `ANTHROPIC_TOKEN` is accepted under the same rules, since gateways commonly export that name. |
| `ANTHROPIC_BASE_URL` | `--backend anthropic` | Optional. Defaults to `https://api.anthropic.com`; point it at a local proxy or gateway to route **all** Claude traffic, subject and judge alike, through one endpoint. |

**Keep a run on one backend.** The judge follows `--backend` unless you override it, and it should stay there: routing the subject through one provider and the judge through another splits a single result across two endpoints, and the saved summary records both (`backend`, `judge_backend`) so a mixed run is visible after the fact rather than silent. Cross-family judging is worth doing — cross-*provider* judging by accident is not.

Anthropic runs report real dollar cost, derived from the API's token counts and a per-million rate table in `providers.py`. Models not in that table report `0.0` rather than a guess.

`run_all.sh` runs every model on the default condition, `run_brief.sh` the brief condition, `run_claude.sh` the Claude family. All three take their credentials from the environment.

Every run starts with a **contamination probe**: it asks the backend what tools it has and refuses to run if the answer looks like an agent rather than a bare model. This exists because two full runs were thrown away after being scored through an agent CLI that silently attached a persona, memory and a full toolset. Scoring a harness and calling it a model is the easiest way to get this wrong.

Use a judge from a different family than the model under test, and verify with `rejudge.py`.

## License

Apache 2.0.
