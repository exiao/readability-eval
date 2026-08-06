# Leaderboard

Score = clarity x (1 - slop tax). Each rule 0-10, higher is better. Prompts are real ChatGPT conversations sampled from WildChat-1M; see README for the sampling method.


## Full run (30 prompts)

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 🥇 **87.7** | `claude-opus-5` | 30 | 8.89 | 0.9 | 558 | 9.8 | 5.9 | 9.5 | 9.9 | 9.8 | 10.0 | 8.7 |
| 🥈 **81.9** | `claude-haiku-4-5` | 30 | 8.45 | 2.2 | 329 | 9.5 | 7.3 | 9.8 | 8.2 | 9.4 | 9.9 | 5.3 |
| 🥉 **80.9** | `claude-sonnet-4-6` | 30 | 8.53 | 3.4 | 531 | 9.8 | 6.8 | 9.7 | 9.4 | 9.6 | 9.8 | 6.8 |
| **80.6** | `claude-opus-4-6` | 30 | 8.42 | 2.8 | 571 | 9.5 | 6.3 | 9.8 | 9.7 | 9.8 | 9.8 | 7.2 |


## Smoke sample (5 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **93.2** | `moonshotai/kimi-k3` | 5 | 9.59 | 1.9 | 740 | 10.0 | 7.5 | 9.6 | 10.0 | 10.0 | 10.0 | 10.0 |
| **92.2** | `x-ai/grok-4.5` | 5 | 9.48 | 1.8 | 804 | 10.0 | 7.5 | 9.9 | 10.0 | 10.0 | 10.0 | 9.0 |
| **91.7** | `google/gemini-3.5-flash` | 5 | 9.25 | 0.6 | 989 | 10.0 | 5.0 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **85.2** | `openai/gpt-5.6-sol` | 5 | 8.59 | 0.5 | 1372 | 10.0 | 4.6 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **54.2** | `qwen/qwen3.8-max` | 5 | 5.5 | 1.0 | 2577 | 10.0 | 0.0 | 9.9 | 10.0 | 9.8 | 10.0 | 9.0 |
