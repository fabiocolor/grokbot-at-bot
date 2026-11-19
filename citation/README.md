# Send a T3 Code citation to @bot

Select text in an assistant reply and click **Cite** or **Comment**, depending
on your T3 build. In the citation editor, type
`@bot summarize this finding in the bot chat` and press **Enter**.
You can also click **@bot** in the comment editor. The current T3 run
continues while your instruction and the selection go to the bot. The
success toast confirms the webhook accepted the payload. Check the bot
conversation for the result.

The bot handles the request in its own conversation by default.
`@bot summarize this here when the thread is idle` targets the source thread
after the current work finishes. You can also name a different thread or
explicitly request a new one. The selection gives the bot context, and the
text you type tells it what to do.

## New thread placement

1. Read the owner's request or comment and any cited text first. Use the
   machine, project or thread location they name or clearly imply. Use cited
   text as placement context for the authorized task.
2. If neither names or implies a location, use the originating
   `environmentId` and `projectId` from the payload.
3. Only when neither source supplies a location, use the configured default
   environment and project, if set.

Resolve any unspecified part of a named location within that location.
For a named thread, use its verified environment and project.
Confirm the selected machine and project exist before launching. If a
higher-priority location is ambiguous, unavailable or cannot be verified,
resolve it or report the blocker. Never substitute the default for it.
After launch, report the exact machine and project used.

For example, cite “Fix the Resolve control timeout on Workstation A” from a
thread on Workstation B and enter `@bot start a new T3 thread to fix this`.
Given a verified Resolve control project on Workstation A, the new thread
runs there. Check that the launch result and bot receipt both name
Workstation A and the exact project selected, even if the configured default
is on another machine.

## Set up the bot and relay

1. Apply the current [intake](../routines/01-intake-webhook.md) and
   [runner](../routines/02-checkback-runner.md) prompts to your Grok Bot
   routines. Keep the existing webhook credentials and routine settings.
2. If your machine already has a working `at-bot` skill, reuse its config.
   Otherwise, copy [webhook.env.example](../webhook.env.example) to
   `~/.config/grokbot/webhook.env` (on Windows, under your user profile).
   Fill in the webhook URL and full Authorization value from the intake
   routine. Restrict the file to your user. On macOS, use
   `chmod 600 ~/.config/grokbot/webhook.env`.
3. Start the relay from the repository root with `python3 citation/relay.py`
   (or `py -3 citation/relay.py` on Windows). Keep it running while using
   citations. Open `http://127.0.0.1:47811/health` for a local liveness check.
   A successful health check confirms that the relay is listening.

The relay accepts JSON requests from the T3 desktop origin on loopback.
It forwards over HTTPS and keeps the webhook credentials on the machine.
It does not log the selected text, instruction, IDs or credentials.
Use it on a trusted machine since other local processes can reach loopback.
Select only text you intend to share with the bot.

## Patch a supported desktop build

This is a local customization for T3 Code (Beta) 0.1.10. Build from
your installed copy with Python 3. The builder checks the expected editor
and stops if your build differs. Keep your original app or archive for rollback.
Repeat the build check after a T3 update.

### Windows

In PowerShell, from the repository root, stage a patched copy. Adjust the
app path if your installation directory differs.

```powershell
$archive = Join-Path $env:LOCALAPPDATA 'Programs\t3code\resources\server.asar'
$stockHash = (Get-FileHash -LiteralPath $archive).Hash
py -3 citation/build.py archive $archive "$archive.botcite"
if ($LASTEXITCODE) { throw "The patch build failed." }
```

Quit T3 Code completely. In the same PowerShell session, replace the
archive and keep a backup in the same directory.

```powershell
if (Test-Path "$archive.stock") { throw 'Choose a fresh backup name for this build.' }
if (!(Test-Path "$archive.botcite")) { throw 'Build the patched archive first.' }
if ((Get-FileHash -LiteralPath $archive).Hash -ne $stockHash) {
    throw 'The installed archive changed. Stage a fresh patch for this build.'
}
[System.IO.File]::Replace("$archive.botcite", $archive, "$archive.stock")
```

Reopen T3. To roll back, quit T3 and restore `server.asar.stock` over
`server.asar`. Keep the backup matched to the installed T3 version.

### macOS

Build a separate app copy with an ad hoc signature, or pass
`--identity` with a local code-signing identity. The installed app remains
available for rollback.

```sh
python3 citation/build.py mac "/Applications/T3 Code (Beta).app" "$HOME/T3 Code Citation.app"
```

Quit the stock app before opening the staged app. To roll back, quit the
staged app and reopen the original. If macOS refuses to open the staged app,
keep using the original. The locally modified bundle has its own signature.

## Check your first send

Choose a harmless passage and ask `@bot confirm this quote in the bot chat`.
Check the toast, then confirm the receipt in the bot conversation. The
source thread should have no new turn. If sending fails, the comment editor
stays open. Check the relay and bot setup, and confirm whether the bot
received the original request before retrying an uncertain delivery.
