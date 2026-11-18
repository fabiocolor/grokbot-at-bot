# @bot for T3 Code threads

Send a request to Grok Bot from a T3 Code thread. Use a citation to send a selected passage while the thread keeps working, or use the agent skill to schedule a check-back from the chat composer.

## Send from a citation

1. Select a passage in an assistant reply and click **Cite** or **Comment**, depending on your T3 build.
2. Type `@bot summarize this finding in the bot chat`.
3. Press **Enter** or click **@bot**. **Sent to @bot** confirms webhook acceptance. Look in the owning bot conversation for the bot’s receipt or result.

The relay sends the selected passage, its source IDs and your instruction. T3
keeps the current run going and clears the temporary citation after sending. An ordinary comment still follows
T3's usual citation flow. To send work back to T3, name the destination in
your instruction, such as `@bot summarize this here when the thread is idle`.

The citation sender is a desktop customization for supported T3 Code (Beta)
0.1.10 builds. Existing users need the patch, the local relay and the updated
intake and runner prompts. See [citation setup and rollback](citation/README.md).

## Send from the chat composer

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
- `citation/`: the desktop patch builder, local relay and setup guide.
- `REBUILD.md`: a short spec for rebuilding the setup.

## Setup note

Grok Bot cannot configure the webhook on its own. After creating the intake routine, copy its webhook URL and Authorization value into `~/.config/grokbot/webhook.env` on each machine, by hand or with an agent on that machine.

MIT license. Issues and PRs welcome.
