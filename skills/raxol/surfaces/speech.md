---
title: Speech Surface
impact: LOW
impactDescription: Optional voice I/O surface over the same event model; heavy ML deps gate STT.
tags: raxol, speech, tts, stt, accessibility, voice
---

# Speech Surface (`raxol_speech`)

Voice I/O as another input/output surface over the same Raxol event model.
TTS reads `Raxol.Core.Accessibility` announcements aloud; STT captures a
recording, transcribes it (Bumblebee/Whisper), and injects the result as a
`Raxol.Core.Events.Event` -- the same struct a keypress produces. No agent code
changes: recognized speech arrives in `update/2` as ordinary events.

TTS is pure-Elixir (shells out to `say`/`espeak`). STT is opt-in and pulls
heavy ML deps (`bumblebee`, `nx`, `exla`) -- keep it off unless needed.

## Supervision

```elixir
# TTS only (default backend Raxol.Speech.TTS.OsSay)
{Raxol.Speech.Supervisor, tts_backend: Raxol.Speech.TTS.OsSay}

# TTS + STT (requires Bumblebee/Whisper deps)
{Raxol.Speech.Supervisor, enable_stt: true,
   recognizer_opts: [...], listener_opts: [dispatcher_pid: pid]}
```

`Supervisor` uses `:rest_for_one`. `enable_stt: true` starts `Recognizer` then
`Listener`; otherwise only `Speaker` runs. All three are `BaseManager`
GenServers registered under their module name.

## TTS -- `Raxol.Speech.Speaker`

```elixir
Raxol.Speech.Speaker.speak("Hello world")   # source: :api
Raxol.Speech.Speaker.stop_speaking()
```

On init the Speaker calls `Raxol.Core.Accessibility.subscribe_to_announcements/1`
(guarded by `Code.ensure_loaded?/1`). Incoming `{:announcement_added, ref, %{message, priority}}`
messages are spoken with `source: :announcement`. `priority: :high` interrupts
current speech (`backend.stop()` then speak). Speech is suppressed when
accessibility prefs set `screen_reader: false` or `silence_announcements: true`.

### Backend behaviour -- `Raxol.Speech.TTS.Backend`

```elixir
@behaviour Raxol.Speech.TTS.Backend
@impl true; def speak(text) :: :ok | {:error, term()}
@impl true; def stop :: :ok
@impl true; def speaking? :: boolean()
```

- `TTS.OsSay` -- ships default; detects `say` (macOS) / `espeak` / `espeak-ng`,
  runs it via a `Port`, sanitizes input first.
- `TTS.Noop` -- for tests.
- `TTS.Sanitize.strip_control_chars/1` -- strips C0/C1 control chars, keeps
  tabs/newlines. Reuse it in custom backends for the same input contract.

## STT -- `Raxol.Speech.Listener` + `Raxol.Speech.Recognizer`

```elixir
:ok = Raxol.Speech.Listener.start_recording()
{:ok, text} = Raxol.Speech.Listener.stop_recording()   # 30s call timeout
Raxol.Speech.Listener.recording?()
```

`Listener` spawns a recording binary via `Port` (`sox`/`rec`/`arecord`/
`parecord`/`ffmpeg`; allowlisted, or pass `record_command: {cmd, args}`).
Guards: `max_duration_ms` and `max_bytes` auto-stop recording. On stop it hands
the captured f32 PCM to `Recognizer.recognize/1`.

If a `dispatcher_pid` is configured, recognized text is translated to an Event
and cast as `{:dispatch, event}` -- this is the injection point into the TEA
loop. Non-command text becomes a `:paste` event.

`Recognizer` wraps a Bumblebee Whisper serving:

```elixir
@spec recognize(binary()) :: {:ok, String.t()} | {:error, term()}
Raxol.Speech.Recognizer.recognize(pcm_f32)  # {:error, :invalid_pcm} if not 4-byte-aligned
Raxol.Speech.Recognizer.available?()        # false if Bumblebee/model absent
```

Transcription runs in a `Task` with a timeout (`{:error, :timeout}` on
overrun). Input must be raw f32 PCM samples -- WAV/AIFF/OGG container bytes are
rejected, not decoded. When ML deps are missing, `available?/0` is `false` and
the surface degrades to TTS-only.

## Event mapping -- `Raxol.Speech.InputAdapter`

```elixir
Raxol.Speech.InputAdapter.translate("quit")        # key event, char "q"
Raxol.Speech.InputAdapter.translate("scroll down")  # key event, char "j"
Raxol.Speech.InputAdapter.translate("hello world")  # :paste event
Raxol.Speech.InputAdapter.default_commands()        # the vocabulary map
```

Single words matching the command vocabulary become key events; anything else
becomes a `:paste` event. Defaults cover navigation (`up`/`down`/`left`/
`right`/`enter`/`tab`/`escape`/`page up`/`page down`), `quit`/`exit`,
`scroll up`/`scroll down` (vim `k`/`j`), and `yes`/`no`/`help`. Extend via
`translate(text, commands: %{...})` (merged with defaults).

## Telemetry

Emits spans/events under `[:raxol_speech, ...]`: `:tts, :speak` (`:start` /
`:stop` / `:exception`, meta `source, backend, byte_size, priority, result`),
`:tts, :stopped`, `:tts, :interrupted`, `:recognize` (`:start` / `:stop`), and
`:listener, :recording` (`:started` / `:stopped`, stop reason `:explicit |
:max_duration_reached | :max_bytes_exceeded`). `source` is `:api` for direct
`speak/1`, `:announcement` for accessibility-driven speech.

## Where it fits

Speech is purely another surface over the core event/announcement model -- see
the accessibility announcements it consumes and the `Event` structs it emits.
It is independent of the agent-commerce surfaces (`raxol_payments` /
`raxol_earn`) and the Symphony orchestrator (`raxol_symphony`).
