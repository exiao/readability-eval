# Leaderboard

Score = clarity x (1 - slop tax). Each rule 0-10, higher is better. Prompts are real ChatGPT conversations sampled from WildChat-1M; see README for the sampling method.


## Full run (30 prompts)

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 🥇 **91.8** | `claude-opus-5` | 30 | 9.31 | 0.9 | 558 | 9.8 | 6.9 | 9.5 | 9.9 | 9.8 | 10.0 | 8.7 |
| 🥈 **85.9** | `claude-opus-4-6` | 30 | 8.97 | 2.8 | 571 | 9.5 | 7.1 | 9.8 | 9.7 | 9.8 | 9.8 | 7.2 |
| 🥉 **83.9** | `claude-sonnet-4-6` | 30 | 8.83 | 3.4 | 531 | 9.8 | 7.4 | 9.7 | 9.4 | 9.6 | 9.8 | 6.8 |
| **82.4** | `claude-haiku-4-5` | 30 | 8.51 | 2.2 | 329 | 9.5 | 7.4 | 9.8 | 8.2 | 9.4 | 9.9 | 5.3 |


## Smoke sample (5 prompts) — NOT comparable to the full run

Too few prompts to rank. Treat gaps under ~5 points as noise.

| Score | Model | n | Clarity | Slop/1k | Words | Understand | Economy | Jargon | Imagery | Simple | Filler | Form |
|:---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **94.5** | `google/gemini-3.5-flash` | 5 | 9.54 | 0.6 | 989 | 10.0 | 6.2 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **94.4** | `moonshotai/kimi-k3` | 5 | 9.71 | 1.9 | 740 | 10.0 | 7.9 | 9.6 | 10.0 | 10.0 | 10.0 | 10.0 |
| **94.0** | `openai/gpt-5.6-sol` | 5 | 9.46 | 0.5 | 1372 | 10.0 | 5.5 | 9.8 | 10.0 | 9.9 | 10.0 | 10.0 |
| **93.5** | `x-ai/grok-4.5` | 5 | 9.61 | 1.8 | 804 | 10.0 | 8.0 | 9.9 | 10.0 | 10.0 | 10.0 | 9.0 |
| **87.9** | `qwen/qwen3.8-max` | 5 | 8.92 | 1.0 | 2577 | 10.0 | 2.0 | 9.9 | 10.0 | 9.8 | 10.0 | 9.0 |
