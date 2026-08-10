# readability-eval

Most models answer a simple question with 500 words, three headings and a bulleted table. This benchmark measures that.

It scores model output on seven clarity rules, then subtracts a penalty for AI slop. The prompts are **real ChatGPT conversations**.

```
Score = clarity x (1 - slop tax)
```

## Results

30 real prompts per model, judged by `claude-opus-5`. Read [Limitations](#limitations) before you treat the order as settled.

| Score | Model | Slop/1k | Words | Filler | Form |
|:---:|---|---:|---:|---:|---:|
| 🥇 **89.6** | `openai/gpt-5.6-terra` | 0.6 | 552 | 9.6 | 9.0 |
| 🥈 **88.5** | `openai/gpt-5.6-sol` | 0.8 | 453 | 9.5 | 9.0 |
| 🥉 **88.0** | `openai/gpt-5.6-luna` | 1.2 | 520 | 9.6 | 9.0 |
| **86.1** | `moonshotai/kimi-k3` * | 2.5 | 430 | 9.5 | 8.8 |
| **85.7** | `claude-opus-5` | 0.9 | 558 | 9.8 | 8.8 |
| **82.5** | `z-ai/glm-5.2` | 1.4 | 501 | 8.8 | 7.6 |
| **82.4** | `x-ai/grok-4.5` | 2.7 | 377 | 9.2 | 9.0 |
| **81.8** | `google/gemini-3.6-flash` | 1.6 | 543 | 8.8 | 8.0 |
| **81.7** | `google/gemini-3.5-flash` | 2.3 | 602 | 8.8 | 7.2 |
| **78.0** | `qwen/qwen3.8-max` | 1.2 | 946 | 9.3 | 6.3 |
| **76.2** | `claude-opus-4-6` | 2.8 | 571 | 7.9 | 6.7 |
| **75.3** | `claude-haiku-4-5` | 2.2 | 329 | 7.8 | 6.3 |
| **72.7** | `claude-sonnet-4-6` | 3.4 | 531 | 7.2 | 6.0 |

\* Kimi is 29 prompts. One call returned malformed JSON on three separate attempts.

The Claude rows were judged through OpenRouter and the rest through a local Anthropic proxy, same judge model either way. All seven rules are in [`results/LEADERBOARD.md`](results/LEADERBOARD.md).

### Can you just ask for a short answer?

Yes, and it works. `--condition brief` appends *"Answer in 50 words or less"*:

| Model | Default | Brief | Change | Coverage |
|---|---:|---:|---:|---:|
| `claude-opus-5` | 85.7 (558w) | 87.2 (48w) | **+1.5** | 96% → 78% |
| `claude-opus-4-6` | 76.2 (571w) | 80.1 (47w) | **+3.9** | 92% → 65% |
| `claude-sonnet-4-6` | 72.7 (531w) | 77.2 (49w) | **+4.5** | 89% → 62% |
| `claude-haiku-4-5` | 75.3 (329w) | 74.7 (51w) | -0.6 | 82% → 60% |

Every model drops to about 48 words when told to, so the length is a default and not a limit. The further over budget a model runs on its own, the more the instruction helps it. It costs coverage, which falls 19 to 27 points.

## Where the prompts come from

Real first-turn English prompts from [WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M), a corpus of a million ChatGPT conversations. Copied verbatim, typos included.

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

Every rule gets judged by a model. Rules 2, 3, 5 and 6 are also counted mechanically, and the score is the worse of the two. Every judged verdict has to quote its evidence: no quote, no penalty. Length is weighted at 0.75 and the other six at 1.0.

## Slop detection

Three layers. A word list on its own catches maybe half of it.

| Layer | Weight | Catches |
|---|---|---|
| 175 terms | 1.0 | `delve`, `testament to`, `boasts`, `great question` |
| 12 patterns | 1.0 / 0.5 | `It's not X. It's Y.` · `not just X, but Y` · `serves as` |
| Structure | 1.0 / 0.5 | verbless noun-list fragments, staccato runs, rule-of-three padding |
| Formatting | 0.25 / 0.1 | labelled bullets, emoji bullets, hyphenated adjective pairs |

Hits are weighted rather than counted: an unambiguous tell scores 1.0, a formatting habit that is often the right choice scores 0.1. Slop only ever subtracts, capped at 30%, so clean writing earns nothing by itself. Code, fences and quotes are stripped first, so a document *about* slop does not score as slop.

Sources: [Wikipedia's Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), the [humanizer](https://github.com/blader/humanizer) pattern set, and a personal kill list.

## Limitations

**There is no system prompt.** Every model gets `"You are a helpful assistant."` and nothing else: no style guide, no harness, no skills. A prompt fixes most of what this measures, and that is the point. The question is whether you have to write one, not whether one would work. If you ship a product with a real system prompt, these scores do not describe what your users see.

**One judge scores everything, and it is `claude-opus-5`.** A model from one of the families being ranked grades all thirteen rows, including its own. It puts itself fifth, which is not what naive self-preference looks like, but nothing here rules the bias out. `rejudge.py` re-scores saved responses with a different judge and no regeneration:

```bash
python3 -m readability_eval.rejudge --label gpt-5.6-terra \
    --judge-model <a model outside this table> --judge-backend openrouter
```

A judge swap has already moved every score by 2 to 5 points and reordered the bottom of the table. Judge choice is part of the result here, not a detail. Run it before citing this ranking.

## Run it

```bash
git clone https://github.com/exiao/readability-eval
cd readability-eval
export OPENROUTER_API_KEY=sk-or-...

python3 -m readability_eval.run --model google/gemini-3.5-flash
python3 -m readability_eval.report
```

Standard library only, one key, no judge flags. A run is 30 prompts plus 30 judge calls, $4 to $6 per model against Opus as the judge. `--limit 5` gives you a cheap smoke run.

For Claude models use `--backend anthropic` with `ANTHROPIC_API_KEY`, and point `ANTHROPIC_BASE_URL` at a proxy if you have one. `run_all.sh` runs every model, `run_brief.sh` the brief condition.

Every run opens with a contamination probe: it asks the backend what tools it has and refuses to start if the answer looks like an agent rather than a bare model. Two full runs were thrown away before that existed.

## License

Apache 2.0.
