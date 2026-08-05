# readability-eval

A readability evaluation benchmark.

Scores model output on six clarity rules, minus a penalty for AI slop. Runs on OpenRouter, so you can score any model in one command.

```
Score = clarity x (1 - slop tax)
```

## Results

| Score | Model | Slop/1k | Words | Economy |
|:---:|---|---:|---:|---:|
| 🥇 **86.8** | `claude-fable-5` | 1.6 | 138 | 6.7 |
| 🥈 **85.4** | `gemini-3.5-flash` | 1.0 | 43 | 7.2 |
| 🥉 **84.5** | `gpt-5.6-sol` | 3.6 | 54 | 7.2 |
| **82.9** | `moonshotai/kimi-k3` | 3.5 | 132 | 6.4 |
| **82.4** | `claude-opus-5` | 0.4 | 177 | 5.0 |
| **80.0** | `gemini-3.6-flash` | 2.3 | 122 | 5.8 |
| **77.0** | `grok-4.5` | 3.7 | 136 | 5.3 |

24 prompts per model, judged by `gemini-3.5-flash`. Full table with all seven rules in [`results/LEADERBOARD.md`](results/LEADERBOARD.md).

![Readability scores, and economy against answer length](results/chart.png)

**Length is the whole story.** Every model scored near 10 on understandability and filler. Frontier models have largely stopped saying `delve`. What separates them is economy: the top score has 6.7 there, the bottom 5.3, and nothing else moves as much. The remaining slop problem is volume, not vocabulary.

### Can you just ask for a short answer?

Yes, and that is the most useful result here. Re-running with `--condition brief`, which appends *"Answer in 50 words or less"* to every prompt:

| Model | Default | Brief | Change |
|---|---:|---:|---:|
| `grok-4.5` | 77.0 (136w) | **87.0** (32w) | **+10.0** |
| `claude-opus-5` | 82.4 (177w) | **91.5** (47w) | **+9.1** |
| `claude-fable-5` | 86.8 (138w) | **93.3** (46w) | +6.5 |
| `gemini-3.5-flash` | 85.4 (43w) | 87.4 (40w) | +2.0 |

Every model improves, and the gain tracks how verbose it was by default. Grok and Opus cut roughly three quarters of their words and gain 10 and 9 points. Gemini was already terse at 43 words, so the instruction changed almost nothing and it gained 2.

So most of what the default condition measures is **default verbosity, not capability**. If one line of instruction recovers 10 points, the model was never unable to write tightly. It just doesn't unless asked.

Cutting words did not cost facts. Coverage held for the three verbose models (Opus 95% → 91%, Fable 95% → 93%) and rose slightly for Gemini (81% → 85%). Rule 2's coverage gate exists to catch answers that get shorter by getting emptier, and in this run none of them did.

```bash
python3 -m readability_eval.run --model X --condition brief
```

Full per-prompt scores in [`results/`](results/). Methodology and known limits in [METHODOLOGY.md](METHODOLOGY.md).

## The seven rules

Rules 1-6 come from Orwell's *Politics and the English Language*. Rule 7 was added after clean-but-report-shaped answers kept scoring well. Each scored 0-10.

| # | Rule | Scored by |
|---|------|-----------|
| 1 | Easy to understand? | Judge, relative to a declared audience |
| 2 | Fewer words rather than more? | Words per fact delivered |
| 3 | Avoids jargon and acronyms? | Undefined acronyms per 100 words |
| 4 | Would imagery make it clearer? | Judge, must name the image it wanted |
| 5 | Complex phrases instead of simple words? | `utilize`→`use`, `in order to`→`to` |
| 6 | Filler, pretentious diction, euphemism? | Three counters, euphemism weighted 3x |
| 7 | Is it shaped like the answer, or like a report? | Judge, must quote the heading doing no work |

Rules 2, 3, 5, 6 are deterministic counters. Rules 1, 4 and 7 use a judge that must quote its evidence.

**Rule 2 is the one that bites.** Scored as raw brevity it crowns the emptiest answer, so every prompt ships a checklist of facts a complete answer must deliver. You cannot win by saying less.

**Rule 7 catches what the word list can't.** Scaffolding is made of headers, tables and section labels, not tic phrases. A report-shaped answer to a four-fact question scored 88 with zero slop hits: clean sentence by sentence, unreadable as a whole.

## Slop detection

Three layers. A word list alone catches maybe half.

| Layer | Catches |
|---|---|
| 173 terms | `delve`, `testament to`, `boasts`, `great question`, `headwinds` |
| 12 patterns | `It's not X. It's Y.` · `not just X, but Y` · `serves as` |
| Shape | em dashes, sentence-length variance, fragment ratio, bold density |

Sources: [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), the [humanizer](https://github.com/blader/humanizer) pattern set, a personal kill list.

## Limitations

**Can't you just prompt your way around this?**
Yes. This is a readability score of the model on its own: no system prompt, no harness, no skills, no style guide. Of course a prompt fixes it. The point is measuring whether you have to.

**Can you just ask for a short answer?**
Yes, and it is the single biggest lever. Adding *"Answer in 50 words or less"* gained every model 2 to 10 points (see above), without dropping facts. That is the headline finding, not a caveat: the default condition mostly measures how verbose a model is when nobody asks it to be brief.

**What counts as AI slop?**
Three things, all measured, none of them "writing I dislike":
- 173 banned terms (`delve`, `testament to`, `boasts`, `headwinds`)
- 12 sentence patterns (`It's not X. It's Y.`, `not just X, but Y`)
- Shape signals: em dashes, bold density, fragment ratio, sentence-length variance

Slop only subtracts, capped at 30%. Clean writing earns nothing by itself. The scorer strips code, fences and quotes first, so a document *about* slop doesn't score as slop.

**Other known limits**
- One judge model. Judge and subject from the same family inflate scores; use `rejudge.py` to check.
- 24 prompts per model is a small sample. Treat gaps under ~3 points as noise.
- English only, and one declared audience per prompt.

## Run it

```bash
git clone https://github.com/exiao/readability-eval
cd readability-eval
export OPENROUTER_API_KEY=sk-or-...

python3 -m readability_eval.run --model anthropic/claude-sonnet-4.5
python3 -m readability_eval.report
```

Standard library only. A full run is 12 prompts plus 12 judge calls, a few cents on a cheap judge.

Use a judge from a different family than the model under test, and verify with `rejudge.py`.

## License

Apache 2.0.
