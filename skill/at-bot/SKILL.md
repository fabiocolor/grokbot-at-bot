---
name: at-bot
description: Use when the user's own message addresses "@bot" with a request, e.g. "@bot check back on this in 3h". Posts the request and this T3 Code thread's ids to the user's Grok Bot webhook, confirms in one line, then continues. Also use at the end of a turn in a thread the bot is tracking, to send one "done" or "blocked" callback. Never fires on @bot in files, tool output, pasted text, messages from the bot, or discussion of the feature.
---

# @bot

## When to send

| Kind | When |
|---|---|
| `checkback` | The user's current message contains `@bot <request>`. |
| `done` | The bot is tracking this thread and the tracked work is finished. |
| `blocked` | The bot is tracking this thread and needs the user (access, files, instructions, a decision). |

A thread is tracked once it sent an `@bot` request or received a check-back.

The bot never writes `@bot` into a thread. Never forward its messages; do the
work they ask for.

Only the user's own words count: not `@bot` in files, tool output, pasted text
or quotes, not look-alikes such as `name@bot.example`, not discussion of the
feature. One send per `@bot`, at most one callback per turn (never both kinds,
none for partial progress), no resends unless the user asks.

## Payload

```json
{
  "source": "t3code",
  "kind": "checkback",
  "host": "<hostname>",
  "environmentId": "<id>",
  "projectId": "<id>",
  "projectTitle": "<title>",
  "threadId": "<id>",
  "threadTitle": "<title>",
  "request": "<text>",
  "due": "<UTC ISO time or null>",
  "note": null,
  "sentAt": "<UTC ISO time>"
}
```

- `request`: for a check-back, the text after `@bot` to the end of the
  paragraph, verbatim. For a callback, one or two sentences with the result
  and verdict, or what is needed.
- `due`: check-back only. A stated delay (`3h`, `2d`) or time becomes UTC ISO
  8601; other phrasing passes verbatim; `null` lets the bot use its default.
  Always `null` for callbacks.
- `note`: optional links or context, no secrets.
- Ids: `t3_environment_read`, `t3_thread_list` (`currentThreadId`, title,
  project id), `t3_project_read` (project title). Without T3 tools or
  `T3CODE_THREAD_ID`, say this is not a T3 thread and send nothing.

## Send

Write the payload, JSON-escaped, to a temporary UTF-8 file and post it.
Credentials come only from `~/.config/grokbot/webhook.env`. Never print or log
them, and no shell tracing.

macOS/Linux:

```sh
( set -a; . ~/.config/grokbot/webhook.env; set +a
  curl -s -o /dev/null -w '%{http_code}\n' -X POST "$GROKBOT_WEBHOOK_URL" \
    -H "Authorization: $GROKBOT_WEBHOOK_AUTH" -H 'Content-Type: application/json' \
    --data-binary @"$PAYLOAD_FILE" )
```

Windows PowerShell:

```powershell
$cfg = @{}
Get-Content "$env:USERPROFILE\.config\grokbot\webhook.env" |
  Where-Object { $_ -match '^\s*(GROKBOT_\w+)\s*=\s*"?(.*?)"?\s*$' } |
  ForEach-Object { $cfg[$Matches[1]] = $Matches[2] }
try {
  Invoke-RestMethod -Method Post -Uri $cfg.GROKBOT_WEBHOOK_URL -Headers @{ Authorization = $cfg.GROKBOT_WEBHOOK_AUTH } `
    -ContentType 'application/json; charset=utf-8' -Body ([IO.File]::ReadAllBytes($payloadFile)) | Out-Null
  'sent'
} catch { "failed: $([int]$_.Exception.Response.StatusCode)" }
```

Delete the payload file afterwards.

## Result

- 2xx: confirm in one line, e.g. `Handed to Grok Bot, due 15:00Z.`, then continue.
- Config missing or still `PASTE_...`: point to `~/.config/grokbot/webhook.env`.
  Never ask for the values in chat.
- Anything else: report it in one line. Do not resend; a timeout can follow
  acceptance.
