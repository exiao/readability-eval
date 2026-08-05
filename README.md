# readability-eval

**Does the model write like a person, or like a model?**

Most writing benchmarks measure whether the answer is *correct*. This one measures whether it is *readable*: whether a competent reader gets it on one pass, without wading through "leverage", "it's important to note", or "this isn't just X, it's Y".

It scores two things and combines them:

```
Score = clarity x (1 - slop tax)
```

**Clarity** is six rules, each 0-10. **Slop** is a penalty that subtracts up to 30% and can never add points. Clean writing earns nothing on its own; it only avoids losing.

Runs on [OpenRouter](https://openrouter.ai), so anyone can evaluate any model with one command.

## The six rules

Adapted from Orwell's rules in *Politics and the English Language*.

| # | Rule | How it is scored |
|---|------|------------------|
| 1 | Is it easy to understand for most people? | Judge, **audience-relative**. Must quote the hardest sentence or the penalty is dropped. |
| 2 | Fewer words rather than more? | **Words per fact delivered**, not raw length. See the landmine below. |
| 3 | Does it avoid jargon and acronyms? | Undefined acronyms per 100 words. A term the audience knows, or one defined inline, costs nothing. |
| 4 | Could imagery make it clearer? | Judge. Must name the concrete image it would have used, or the penalty is dropped. |
| 5 | Complex phrases instead of simple words? | Frozen substitution table: `utilize`→`use`, `in order to`→`to`, `due to the fact that`→`because`. |
| 6 | Filler, pretentious diction, euphemism? | Three counters. Euphemism weighted 3x, because the defect there is dishonesty, not style. |

Rules 2, 3, 5, 6 are deterministic counters. Rules 1 and 4 need a judge.

### The landmine in rule 2

Scored as raw brevity, rule 2 crowns the emptiest answer. Tested directly: a plain 70-word reply beat a jargon-stuffed 95-word reply on all six rules, and it was useless while the ugly one was actionable.

So every prompt ships with a checklist of facts a complete answer must deliver, the judge marks which ones landed, and rule 2 scores **words per delivered fact**. You cannot win by saying less.

## Slop detection

Three layers, because a word list alone misses most of it.

**173 terms in 18 families** — `delve`, `testament to`, `boasts`, `great question`, `headwinds`, `the future looks bright`.

**12 regex patterns** for structures no word list catches:

```
It's not X. It's Y.          antithesis
not just X, but Y            negative parallelism
serves as / stands as        copula avoidance
, highlighting its impact    trailing participle
from A to B, from C to D     false range
```

**Shape metrics** needing no list at all: em dashes per 100 words, sentence-length variation (below 0.5 is metronomic), fragment ratio, bold density.

Sources merged: [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), the [humanizer](https://github.com/blader/humanizer) pattern set, and a personal kill list.

### What is deliberately not scored

Wikipedia's editors list these as **ineffective indicators** that flag good human writers as AI:

- Perfect grammar
- Formal or academic prose in general
- Transition words in isolation (`Additionally`, `Consequently`)
- Mixed casual/formal register

They are excluded on purpose.

### Mention is not use

The scorer strips code spans, fenced blocks, and quoted strings before counting. Without this, any document *about* slop scores as slop. Running an early version on this project's own spec returned 27.6 hits per 1,000 words, and every single hit was the spec quoting a banned term. After the fix: 0.0, while the slop control still scored 265.

If you build something like this, run it on its own documentation as test #1.

## Results

12 prompts per model, judged by `gemini-3.5-flash`.

| # | Model | Score | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `gemini-3.5-flash` | **95.5** | 9.55 | 0.0 | 44 | 10.0 | 8.3 | 10.0 | 9.0 | 10.0 | 10.0 |
| 2 | `claude-fable-5` | **90.0** | 9.15 | 1.1 | 138 | 10.0 | 6.4 | 9.9 | 9.2 | 9.6 | 9.8 |
| 3 | `moonshotai/kimi-k3` | **88.2** | 9.10 | 3.5 | 132 | 10.0 | 6.4 | 9.3 | 9.2 | 9.7 | 10.0 |
| 4 | `grok-4.5` | **87.3** | 8.97 | 1.9 | 156 | 10.0 | 6.1 | 9.5 | 8.2 | 10.0 | 10.0 |
| 5 | `claude-opus-5` | **87.2** | 8.75 | 0.3 | 177 | 10.0 | 5.0 | 9.0 | 8.8 | 9.8 | 10.0 |
| 6 | `gpt-5.6-sol` | **87.0** | 9.23 | 5.6 | 102 | 10.0 | 7.7 | 10.0 | 8.2 | 9.5 | 10.0 |

Every response, every rule score, and every slop hit is in [`results/`](results/), so you can audit any grade you disagree with.

**Length is the whole story.** All six models score 10.0 on understandability and near-perfect on filler. Frontier models have largely stopped saying `delve`. What separates them is economy, which ranges from 5.0 to 8.3, and it tracks word count almost exactly: 44 words for the winner, 177 for last place. The remaining slop problem is volume, not vocabulary.

Opus scores lowest on economy at 5.0 and writes the longest answers at 177 words average. It also has near-zero lexical slop (0.3/1k). Nothing it says is banned; there is just too much of it.

### Judge contamination check

The judge was Gemini and Gemini won, which is exactly the failure mode this kind of eval falls into. Re-judging the saved responses with `claude-fable-5` instead:

| Model | Gemini judge | Claude judge | Delta |
|---|---:|---:|---:|
| `gemini-3.5-flash` | 95.5 | 95.1 | -0.4 |
| `claude-opus-5` | 87.2 | 88.9 | +1.7 |
| `gpt-5.6-sol` | 87.0 | 89.3 | +2.3 |

The ranking holds and Gemini gains nothing from judging itself. Run this yourself with `python3 -m readability_eval.rejudge`.

### Two scoring bugs the first run exposed

Both are fixed, and both are the kind that would have quietly invalidated the results.

**Economy rewarded omission.** Gemini answered prompt 1 in 44 words, delivered 2 of 4 required facts, and took the best economy score for it. Words-per-fact is not enough on its own, because dropping a fact removes more words than it removes credit. Economy is now multiplied by coverage, so answering half the question caps the score at half.

**Curly quotes counted as slop.** They were 9 of GPT-5.6's 12 slop hits, which knocked 6 points off its score for using correct typography. Removed from the pattern set.

## Run it

```bash
git clone https://github.com/exiao/readability-eval
cd readability-eval
export OPENROUTER_API_KEY=sk-or-...

python3 -m readability_eval.run --model anthropic/claude-sonnet-4.5
python3 -m readability_eval.run --model openai/gpt-5
python3 -m readability_eval.report          # rebuild the leaderboard
```

No dependencies beyond the Python standard library. A full run is 12 prompts plus 12 judge calls and costs a few cents on a cheap judge.

Use a judge from a different model family than the model under test. LLM judges [prefer their own writing](https://arxiv.org/abs/2504.07532), and frontier models barely beat a random baseline at ranking writing quality, which is exactly why the judge here is confined to two of the six rules and must quote its evidence.

```bash
python3 -m readability_eval.run \
  --model anthropic/claude-opus-4.5 \
  --judge-model google/gemini-2.5-flash
```

## Adding prompts

Each entry in [`data/prompts.json`](data/prompts.json) needs an `audience` (clarity is judged relative to it), a `facts` checklist (the denominator for rule 2), and `assumed` acronyms that reader already knows.

```json
{
  "id": 13,
  "genre": "technical_qa",
  "audience": "backend engineer",
  "prompt": "...",
  "facts": ["names the cause", "gives a specific fix", "says how to verify"],
  "assumed": ["API", "TTL"]
}
```

Genres currently covered: technical Q&A, explanation, bad news, decision, marketing, instruction, chat, postmortem, critique, summary, rejection, definition. Bad-news and diplomacy prompts pull the most slop out of a model, because that is where it retreats into euphemism.

## License

Apache 2.0. See [LICENSE.txt](LICENSE.txt).
