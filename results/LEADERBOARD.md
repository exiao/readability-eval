# Leaderboard

Score = clarity x (1 - slop tax). Each rule 0-10, higher is better. Prompts are real ChatGPT conversations sampled from WildChat-1M; see README for the sampling method.


## Full run (30 prompts)

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 🥇 **89.6** | `openai/gpt-5.6-terra` | 30 | 9.04 | 0.6 | 552 | 9.3 | 7.6 | 9.3 | 9.2 | 9.3 | 9.6 | 9.0 |
| 🥈 **88.5** | `openai/gpt-5.6-sol` | 30 | 8.96 | 0.8 | 453 | 8.7 | 7.8 | 9.1 | 9.3 | 9.2 | 9.5 | 9.0 |
| 🥉 **88.0** | `openai/gpt-5.6-luna` | 30 | 8.95 | 1.2 | 520 | 9.0 | 7.4 | 8.9 | 9.5 | 9.2 | 9.6 | 9.0 |
| **85.7** | `claude-opus-5` | 30 | 8.69 | 0.9 | 558 | 7.8 | 6.1 | 8.3 | 10.0 | 9.3 | 9.8 | 8.8 |
| **82.5** | `z-ai/glm-5.2` | 30 | 8.43 | 1.4 | 501 | 8.7 | 5.6 | 9.3 | 9.7 | 9.4 | 8.8 | 7.6 |
| **82.4** | `x-ai/grok-4.5` | 30 | 8.54 | 2.7 | 377 | 8.5 | 5.9 | 8.6 | 9.2 | 9.1 | 9.2 | 9.0 |
| **81.8** | `google/gemini-3.6-flash` | 30 | 8.37 | 1.6 | 543 | 7.8 | 5.7 | 9.1 | 9.8 | 8.7 | 8.8 | 8.0 |
| **81.7** | `google/gemini-3.5-flash` | 30 | 8.41 | 2.3 | 602 | 8.7 | 5.4 | 9.1 | 9.9 | 9.1 | 8.8 | 7.2 |
| **78.0** | `qwen/qwen3.8-max` | 30 | 7.92 | 1.2 | 946 | 8.8 | 5.2 | 8.9 | 9.2 | 9.2 | 9.3 | 6.3 |
| **76.2** | `claude-opus-4-6` | 30 | 7.96 | 2.8 | 571 | 8.5 | 5.2 | 8.6 | 9.5 | 9.5 | 7.9 | 6.7 |
| **75.3** | `claude-haiku-4-5` | 30 | 7.77 | 2.2 | 329 | 8.0 | 5.8 | 9.1 | 8.3 | 9.0 | 7.8 | 6.3 |
| **72.7** | `claude-sonnet-4-6` | 30 | 7.65 | 3.4 | 531 | 8.5 | 5.5 | 8.6 | 9.2 | 8.9 | 7.2 | 6.0 |


## Smoke sample (29 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **86.1** | `moonshotai/kimi-k3` | 29 | 8.93 | 2.5 | 430 | 9.5 | 6.2 | 9.2 | 10.0 | 9.3 | 9.5 | 8.8 |


## Smoke sample (9 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **75.2** | `anthropic/claude-fable-5` | 9 | 7.81 | 2.5 | 592 | 9.4 | 5.0 | 7.5 | 9.7 | 8.8 | 5.6 | 8.0 |
