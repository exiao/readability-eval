# Leaderboard

Score = clarity x (1 - slop tax). Each rule 0-10, higher is better. Prompts are real ChatGPT conversations sampled from WildChat-1M; see README for the sampling method.


## Full run (30 prompts)

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 🥇 **85.7** | `claude-opus-5` | 30 | 8.69 | 0.9 | 558 | 7.8 | 6.1 | 8.3 | 10.0 | 9.3 | 9.8 | 8.8 |
| 🥈 **76.2** | `claude-opus-4-6` | 30 | 7.96 | 2.8 | 571 | 8.5 | 5.2 | 8.6 | 9.5 | 9.5 | 7.9 | 6.7 |
| 🥉 **75.3** | `claude-haiku-4-5` | 30 | 7.77 | 2.2 | 329 | 8.0 | 5.8 | 9.1 | 8.3 | 9.0 | 7.8 | 6.3 |
| **72.7** | `claude-sonnet-4-6` | 30 | 7.65 | 3.4 | 531 | 8.5 | 5.5 | 8.6 | 9.2 | 8.9 | 7.2 | 6.0 |


## Smoke sample (10 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **78.2** | `openai/gpt-5.6-sol` | 10 | 7.85 | 0.3 | 965 | 10.0 | 5.8 | 6.5 | 9.7 | 9.1 | 6.9 | 6.8 |
| **76.9** | `openai/gpt-5.6-terra` | 10 | 7.72 | 0.3 | 1095 | 10.0 | 5.0 | 7.0 | 10.0 | 8.8 | 6.5 | 6.5 |
| **76.5** | `moonshotai/kimi-k3` | 10 | 7.91 | 2.3 | 512 | 9.5 | 5.5 | 6.0 | 9.7 | 9.0 | 6.5 | 8.6 |
| **75.4** | `openai/gpt-5.6-luna` | 10 | 7.56 | 0.2 | 1022 | 9.5 | 5.7 | 6.5 | 9.7 | 8.5 | 7.0 | 5.9 |
| **74.4** | `google/gemini-3.6-flash` | 10 | 7.5 | 0.6 | 642 | 9.5 | 5.0 | 7.0 | 10.0 | 8.0 | 6.0 | 6.5 |
| **72.9** | `anthropic/claude-opus-5` | 10 | 7.42 | 1.3 | 1205 | 9.5 | 4.4 | 5.5 | 10.0 | 8.4 | 6.0 | 7.4 |
| **72.1** | `x-ai/grok-4.5` | 10 | 7.36 | 1.4 | 678 | 9.0 | 5.0 | 5.5 | 9.7 | 8.4 | 6.0 | 7.3 |
| **72.0** | `z-ai/glm-5.2` | 10 | 7.35 | 1.4 | 724 | 9.0 | 5.3 | 6.9 | 10.0 | 7.8 | 5.5 | 6.5 |
| **69.5** | `qwen/qwen3.8-max` | 10 | 7.08 | 1.3 | 791 | 10.0 | 4.0 | 5.0 | 9.7 | 8.0 | 6.0 | 6.2 |


## Smoke sample (9 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **75.2** | `anthropic/claude-fable-5` | 9 | 7.81 | 2.5 | 592 | 9.4 | 5.0 | 7.5 | 9.7 | 8.8 | 5.6 | 8.0 |


## Smoke sample (5 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **94.5** | `google/gemini-3.5-flash` | 5 | 9.54 | 0.6 | 989 | 10.0 | 6.2 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **94.0** | `openai/gpt-5.6-sol` | 5 | 9.46 | 0.5 | 1372 | 10.0 | 5.5 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
