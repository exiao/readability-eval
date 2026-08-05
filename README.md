# readability-eval

A readability evaluation benchmark.

Scores model output on six clarity rules, minus a penalty for AI slop. Runs on OpenRouter, so you can score any model in one command.

```
Score = clarity x (1 - slop tax)
```

## Results

| Score | Model | Slop/1k | Words | Economy |
|:---:|---|---:|---:|---:|
| 🥇 **95.5** | `gemini-3.5-flash` | 0.0 | 44 | 8.3 |
| 🥈 **90.0** | `claude-fable-5` | 1.1 | 138 | 6.4 |
| 🥉 **88.2** | `moonshotai/kimi-k3` | 3.5 | 132 | 6.4 |
| **87.3** | `grok-4.5` | 1.9 | 156 | 6.1 |
| **87.2** | `claude-opus-5` | 0.3 | 177 | 5.0 |
| **87.0** | `gpt-5.6-sol` | 5.6 | 102 | 7.7 |

12 prompts per model, judged by `gemini-3.5-flash`.

![Readability scores, and economy against answer length](results/chart.png)

**Length is the whole story.** Every model scored 10.0 on understandability and near-perfect on filler. Frontier models have largely stopped saying `delve`. What separates them is economy, and it tracks word count almost exactly: 44 words for first place, 177 for fifth. The remaining slop problem is volume, not vocabulary.

### Can you just ask for a short answer?

Mostly yes, and that is the most useful result here. Re-running with `--condition brief`, which appends *"Answer in 50 words or less"* to every prompt:

| Model | Default | Brief | Change |
|---|---:|---:|---:|
| `claude-opus-5` | 87.2 (177w) | **93.3** (53w) | **+6.1** |
| `grok-4.5` | 87.3 (156w) | 87.8 (34w) | +0.5 |
| `claude-fable-5` | 90.0 (138w) | 90.1 (48w) | +0.1 |
| `gemini-3.5-flash` | **95.5** (44w) | 87.5 (43w) | **-8.0** |

Opus cuts 177 words to 53 and gains 6.1 points. Most of what this benchmark measures in the default condition is **default verbosity, not capability**. If a one-line instruction recovers the gap, the model was never unable to write tightly; it just doesn't by default.

The flip side is the more interesting half. Gemini was already terse at 44 words, so "be brief" bought it nothing and cost it facts: coverage fell from 85% to 76%, and the score dropped 8 points. Its answers got no shorter, only emptier.

Brevity instructions help verbose models and hurt terse ones. This is exactly what rule 2's coverage gate exists to catch, and it is why raw word count is a bad proxy for good writing.

```bash
python3 -m readability_eval.run --model X --condition brief
```

Full per-prompt scores in [`results/`](results/). Methodology and known limits in [METHODOLOGY.md](METHODOLOGY.md).

## The six rules

From Orwell's *Politics and the English Language*. Each scored 0-10.

| # | Rule | Scored by |
|---|------|-----------|
| 1 | Easy to understand? | Judge, relative to a declared audience |
| 2 | Fewer words rather than more? | Words per fact delivered |
| 3 | Avoids jargon and acronyms? | Undefined acronyms per 100 words |
| 4 | Would imagery make it clearer? | Judge, must name the image it wanted |
| 5 | Complex phrases instead of simple words? | `utilize`→`use`, `in order to`→`to` |
| 6 | Filler, pretentious diction, euphemism? | Three counters, euphemism weighted 3x |

Rules 2, 3, 5, 6 are deterministic counters. Rules 1 and 4 use a judge that must quote its evidence.

**Rule 2 is the one that bites.** Scored as raw brevity it crowns the emptiest answer, so every prompt ships a checklist of facts a complete answer must deliver. You cannot win by saying less.

## Slop detection

Three layers. A word list alone catches maybe half.

| Layer | Catches |
|---|---|
| 173 terms | `delve`, `testament to`, `boasts`, `great question`, `headwinds` |
| 12 patterns | `It's not X. It's Y.` · `not just X, but Y` · `serves as` |
| Shape | em dashes, sentence-length variance, fragment ratio, bold density |

Sources: [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), the [humanizer](https://github.com/blader/humanizer) pattern set, a personal kill list.

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
