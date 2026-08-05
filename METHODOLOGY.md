# Methodology

Detail that would bloat the README. Read this before trusting a number.

## Scoring

```
clarity  = mean of the six rule scores (0-10 each)
slop_tax = min(0.30, slop_hits_per_1k / 20 * 0.30)
Score    = clarity * 10 * (1 - slop_tax)
```

Slop can only subtract. Clean writing earns nothing on its own; it avoids losing. The tax caps at 30% so a useful, warm, slop-ridden answer still outranks a cold clean useless one.

## Rule detail

**Rule 1, understandable.** Judge emits `clear` / `needs_a_reread` / `opaque` and must quote the hardest sentence. No quote, no penalty. Judged relative to the prompt's `audience` field: a precise term a backend engineer knows is not a clarity defect, and swapping it for vague everyday words would be worse.

**Rule 2, economy.** `words / facts_delivered`, then multiplied by coverage (`facts_delivered / facts_required`). 15 words per fact is tight, 80 is padded. The coverage multiplier is load-bearing; see the bugs section.

**Rule 3, jargon.** Undefined acronyms per 100 words. An acronym expanded on first use costs nothing. Each prompt lists `assumed` acronyms the declared audience already knows.

**Rule 4, imagery.** Judge emits `concrete` / `abstract_but_fine` / `needed_an_image`, and `needed_an_image` only counts if the judge names the concrete image it would have used. This is the most subjective axis and carries the least weight in practice because the evidence requirement suppresses most firings.

**Rule 5, simple words.** Frozen table of ~60 long-form to short-form substitutions. Purely mechanical, zero judgment, cheapest signal in the suite.

**Rule 6, filler.** Three counters: filler phrases, pretentious diction, euphemism. Euphemism is weighted 3x because the defect there is dishonesty rather than style. A layoff email saying "rightsizing" has failed to communicate on purpose.

## What is deliberately not scored

Wikipedia's editors list these as **ineffective indicators** that flag good human writers as AI:

- Perfect grammar
- Formal or academic prose in general
- Transition words in isolation (`Additionally`, `Consequently`)
- Mixed casual and formal register

Curly quotes were also removed after the first run. See below.

## Mention is not use

The scorer strips code spans, fenced blocks, and quoted strings before counting. Without this, any document *about* slop scores as slop. An early version rated this project's own spec at 27.6 hits per 1,000 words, and every hit was the spec quoting a banned term. After the fix: 0.0, while the slop control still scored 265.

If you build something like this, run it on its own documentation as test #1.

## Judge contamination

LLM judges [prefer their own writing](https://arxiv.org/abs/2504.07532), and frontier models barely beat a random baseline at ranking writing quality. That is why the judge here is confined to two of six rules and must quote its evidence.

The first run used a Gemini judge and Gemini won, which is exactly the failure mode. Re-judging the saved responses with `claude-fable-5`:

| Model | Gemini judge | Claude judge | Delta |
|---|---:|---:|---:|
| `gemini-3.5-flash` | 95.5 | 95.1 | -0.4 |
| `claude-opus-5` | 87.2 | 88.9 | +1.7 |
| `gpt-5.6-sol` | 87.0 | 89.3 | +2.3 |

The ranking holds and Gemini gains nothing from judging itself. Verify yourself:

```bash
python3 -m readability_eval.rejudge --label gemini-3.5-flash \
  --judge-model anthropic/claude-sonnet-4.5
```

`rejudge` re-scores saved responses without regenerating them, so a judge swap costs only judge calls.

## Two bugs the first run exposed

Both fixed. Both would have quietly invalidated the results.

**Economy rewarded omission.** Gemini answered prompt 1 in 44 words, delivered 2 of 4 required facts, and took the best economy score for it. Words-per-fact alone is not enough, because dropping a fact removes more words than it removes credit. Economy is now multiplied by coverage, so answering half the question caps the score at half.

**Curly quotes counted as slop.** They were 9 of GPT-5.6's 12 slop hits, costing it 6 points for correct typography. Removed from the pattern set.

## Conditions

`--condition` appends an instruction to every prompt, so you can separate a model property from a prompting artifact.

| Condition | Appended |
|---|---|
| `default` | nothing |
| `brief` | "Answer in 50 words or less." |
| `short` | "Give a short answer." |

Results are tagged with their condition and the leaderboard only compares within one, since mixing them compares different tests.

This exists because the default-condition ranking is largely a verbosity ranking. Opus gains 6.1 points under `brief` while Gemini loses 8.0, so "which model writes best" and "which model writes best when you don't ask it to be brief" are different questions with different answers. Report which one you ran.

## Adding prompts

Each entry in `data/prompts.json` needs:

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

`audience` sets the bar for rules 1 and 3. `facts` is the denominator for rule 2. `assumed` lists acronyms that reader already knows.

Genres covered: technical Q&A, explanation, bad news, decision, marketing, instruction, chat, postmortem, critique, summary, rejection, definition. Bad-news and diplomacy prompts pull the most slop out of a model, because that is where it retreats into euphemism.

## Known limits

- **12 prompts is small.** Differences under ~3 points are probably noise.
- **One sample per prompt, temperature unset.** No variance estimate.
- **English only.**
- **The judge is a single model.** A median-of-three panel would be better; `rejudge` is the workaround.
- **Rule 4 rarely fires.** The evidence requirement is doing its job, but it means imagery contributes little signal.
- **Scores are not comparable across prompt-set versions.** The set is versioned in `data/prompts.json` for this reason.
