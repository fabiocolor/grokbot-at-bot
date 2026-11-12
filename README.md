# @bot for T3 Code threads

Lets a T3 Code thread hand requests to a Grok Bot, which checks back later and continues the thread.

## How it works

1. On an `@bot` message, a skill posts the request and the thread ids to a Grok Bot webhook.
2. A webhook routine queues it and confirms.
3. A scheduled routine (cadence is configurable) continues idle threads and reports progress on busy ones.
4. Finished threads report back with a result, and blocked threads are flagged right away.

The bot never writes `@bot` into a thread, so it cannot trigger itself.

Requests go to whichever Grok Bot owns the webhook routine. To use a different bot, create the routines there and point the config at its webhook.

## Files

- `skill/at-bot/SKILL.md`: the agent skill.
- `routines/`: the intake and check-back routine prompts.
- `REBUILD.md`: a short spec for rebuilding the setup.

## Setup note

Grok Bot cannot configure the webhook on its own. After creating the intake routine, copy its webhook URL and Authorization value into `~/.config/grokbot/webhook.env` on each machine, by hand or with an agent on that machine.

MIT license. Issues and PRs welcome.
