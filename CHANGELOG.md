# Changelog

## 0.2.1 (19 November 2026)

### New

- **Citations on Linux.** Setup steps for the official T3 Code 0.1.10
  AppImage. Tested from a fresh clone: the patched app started, showed the
  **@bot** button and delivered a citation through the relay.

### Fixed

- The builder keeps the original file permissions on the patched archive.
  Before, it was readable only by the user who built it.

## 0.2.0 (19 November 2026)

### New

- **Send a citation to @bot.** Select a passage in a T3 Code reply, type
  `@bot` and your instruction in the citation editor, and send it. The
  thread keeps working while the bot gets the quote, its source IDs and your
  instruction. A local relay forwards it, so the webhook credentials stay on
  your machine. Desktop customization for T3 Code (Beta) 0.1.10, with a
  setup and rollback guide in `citation/README.md`.
- **Timed check-backs at the requested minute.** An explicit future time
  becomes a one-time T3 task bound to the source thread. When it is due, the
  task sends the webhook and the intake posts back to the thread if it is idle.
- **New thread placement.** When the bot opens a T3 thread, it uses the
  machine and project you name or cite first, then the source thread's
  location, then a configured default. It reports the exact machine and
  project it used.
- **`cite` hand-offs** in the intake and runner routines, with the quote kept
  separate from your instruction.

### Changed

- Both senders read `webhook.env` as data, including quoted values and
  unquoted Authorization headers.
- On Windows, the payload is encoded in memory, with no temporary file to
  clean up.
- The intake posts a visible receipt for every valid hand-off.

## 0.1.0 (12 November 2026)

First public draft: the `at-bot` skill, the webhook config template and the
intake and check-back runner routines.
