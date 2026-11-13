# @bot for T3 Code threads

Lets a T3 Code thread hand requests to a Grok Bot, which checks back later and continues the thread.

## How it works

1. On an `@bot` message, the skill resolves the request and the originating T3 thread.
2. For an explicit future time, a one-time T3 task sends the authenticated webhook when due. Other requests go straight to the webhook.
3. The intake posts due check-backs to the originating thread when it is idle and gives the owner a visible receipt.
4. The periodic runner handles queued work and retries. Finished or blocked threads can send a result back to the bot.

The due time starts dispatch. The time the reply appears depends on T3
availability, agent startup, and webhook processing. A busy thread can
wait for the periodic runner.

The bot never writes `@bot` into a thread, so it cannot trigger itself.

Requests go to whichever Grok Bot owns the webhook routine. To use a different bot, create the routines there and point the config at its webhook.

## Files

- `skill/at-bot/SKILL.md`: the agent skill.
- `routines/`: the intake and check-back routine prompts.
- `REBUILD.md`: a short spec for rebuilding the setup.

## Setup note

Grok Bot cannot configure the webhook on its own. After creating the intake routine, copy its webhook URL and Authorization value into `~/.config/grokbot/webhook.env` on each machine, by hand or with an agent on that machine.

MIT license. Issues and PRs welcome.
