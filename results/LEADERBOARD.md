# Leaderboard

Score = clarity x (1 - slop tax). Each rule 0-10, higher is better. Prompts are real ChatGPT conversations sampled from WildChat-1M; see README for the sampling method.


## Full run (30 prompts)

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 🥇 **84.1** | `claude-opus-5` | 30 | 8.89 | 3.7 | 558 | 9.8 | 5.9 | 9.5 | 9.9 | 9.8 | 10.0 | 8.7 |
| 🥈 **76.1** | `claude-opus-4-6` | 30 | 8.42 | 10.4 | 571 | 9.5 | 6.3 | 9.8 | 9.7 | 9.8 | 9.8 | 7.2 |
| 🥉 **75.4** | `claude-sonnet-4-6` | 30 | 8.53 | 13.3 | 531 | 9.8 | 6.8 | 9.7 | 9.4 | 9.6 | 9.8 | 6.8 |
| **74.7** | `claude-haiku-4-5` | 30 | 8.45 | 9.7 | 329 | 9.5 | 7.3 | 9.8 | 8.2 | 9.4 | 9.9 | 5.3 |


## Smoke sample (5 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **85.6** | `google/gemini-3.5-flash` | 5 | 9.25 | 5.0 | 989 | 10.0 | 5.0 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **83.6** | `moonshotai/kimi-k3` | 5 | 9.59 | 11.9 | 740 | 10.0 | 7.5 | 9.6 | 10.0 | 10.0 | 10.0 | 10.0 |
| **83.4** | `x-ai/grok-4.5` | 5 | 9.48 | 9.2 | 804 | 10.0 | 7.5 | 9.9 | 10.0 | 10.0 | 10.0 | 9.0 |
| **77.3** | `openai/gpt-5.6-sol` | 5 | 8.59 | 6.9 | 1372 | 10.0 | 4.6 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **50.3** | `qwen/qwen3.8-max` | 5 | 5.5 | 5.8 | 2577 | 10.0 | 0.0 | 9.9 | 10.0 | 9.8 | 10.0 | 9.0 |
