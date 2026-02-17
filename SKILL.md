---
name: netflix-subtitle-processor
description: Process Whisper SRT files to Netflix Timed Text specifications. Validates timing, reading speed, character limits. Supports English, Chinese, Japanese, Korean, Spanish.
user_invocable: true
---

# Netflix Subtitle Processor

Post-process Whisper-generated SRT files to meet Netflix Timed Text Style Guide specifications.

## Quick Start

```bash
# Validate subtitle file (auto-detects language)
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate video.srt

# Fix issues automatically (keeps all entries)
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py fix video.srt video_fixed.srt

# Clean: remove unfixable entries (100% compliance)
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py clean video.srt video_clean.srt

# Generate detailed report
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py report video.srt
```

## Workflow Integration

This skill complements `openai-whisper-guide` for professional subtitle production:

```
Audio/Video → Whisper (transcription) → Netflix Processor (compliance) → Netflix-ready SRT
```

### Recommended Pipeline

```bash
# Step 1: Transcribe with Whisper (use openai-whisper-guide)
whisper audio.mp3 --model turbo --output_format srt --max_line_width 42 --max_line_count 2

# Step 2: Validate against Netflix specs
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate audio.srt

# Step 3: Auto-fix any issues
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py fix audio.srt audio_netflix.srt

# Step 4: Verify compliance
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate audio_netflix.srt
```

## Commands

### validate

Check SRT file against Netflix specifications.

```bash
python3 netflix_subs.py validate input.srt [--lang en] [--kids] [--json]
```

Options:
- `--lang`: Specify language (auto-detected if omitted)
- `--kids`: Use children's content limits (lower CPS)
- `--json`: Output results as JSON

Exit codes:
- `0`: All entries pass
- `1`: Issues found

### fix

Auto-fix common issues and write corrected SRT. Keeps all entries.

```bash
python3 netflix_subs.py fix input.srt output.srt [--lang en]
```

Fixes applied:
- Extends subtitles shorter than 833ms minimum
- Splits lines exceeding character limits (smart punctuation breaks for CJK)
- Fixes overlapping subtitles
- Adjusts gaps between subtitles
- Limits to 2 lines per subtitle

### clean

Remove unfixable entries, output only valid ones. Use when you need guaranteed compliance.

```bash
python3 netflix_subs.py clean input.srt output.srt [--lang en] [--kids]
```

Behavior:
- Applies all fixes from `fix` command
- Removes entries that still have issues (e.g., CPS too high)
- Re-indexes remaining entries
- Reports which entries were removed and why

### report

Generate detailed validation report.

```bash
python3 netflix_subs.py report input.srt [--lang en] [--kids]
```

## Netflix Specifications

| Language | Code | Max Chars/Line | Adult CPS | Kids CPS |
|----------|------|----------------|-----------|----------|
| English  | en   | 42             | 17        | 15       |
| Chinese  | zh   | 16             | 9         | 7        |
| Japanese | ja   | 13             | 4         | 4        |
| Korean   | ko   | 16             | 12        | 10       |
| Spanish  | es   | 42             | 17        | 15       |

**Common timing rules (all languages):**
- Min duration: 833ms (5/6 second)
- Max duration: 7 seconds
- Min gap between subtitles: 83ms (2 frames @ 24fps)
- Max lines per subtitle: 2

## Options

### Language Detection

Language is auto-detected from content. Override with `--lang`:

```bash
# Auto-detect (default)
python3 netflix_subs.py validate video.srt

# Force specific language
python3 netflix_subs.py validate video.srt --lang zh
python3 netflix_subs.py validate video.srt --lang ja
```

### Children's Content

Use `--kids` flag for stricter CPS limits:

```bash
python3 netflix_subs.py validate video.srt --kids
python3 netflix_subs.py clean video.srt output.srt --kids
```

### JSON Output

Get machine-readable results:

```bash
python3 netflix_subs.py validate video.srt --json
```

### Stdin/Stdout

Use `-` for piping:

```bash
cat video.srt | python3 netflix_subs.py validate -
python3 netflix_subs.py fix video.srt - > output.srt
```

## Troubleshooting

### "CPS too high" after fix

Some subtitles have too much text for their duration. Options:
1. Manually shorten the text
2. Use `clean` command to remove problematic entries
3. Extend the subtitle duration (may cause overlap)

### Overlapping subtitles

The `fix` command automatically resolves overlaps by shortening the previous subtitle. If this causes issues, manually adjust timing.

### Chinese/Japanese character counting

Full-width characters (CJK) count as 2 characters. Line breaks for CJK try to split at punctuation (。，！？) before falling back to midpoint.

### Remaining issues after fix

The auto-fix handles timing and line breaks. Issues requiring manual attention:
- Content too dense (high CPS with correct timing)
- Complex multi-line reformatting

## References

- [Netflix Timed Text Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)
- [Netflix English Subtitle Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-Timed-Text-Style-Guide)
- [Netflix Simplified Chinese Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/217351127-Simplified-Chinese-Timed-Text-Style-Guide)
