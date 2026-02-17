---
name: netflix-subtitle-processor
description: Process Whisper SRT files to Netflix Timed Text specifications. Validates timing, reading speed, character limits. Supports English and Chinese.
user_invocable: true
---

# Netflix Subtitle Processor

Post-process Whisper-generated SRT files to meet Netflix Timed Text Style Guide specifications.

## Quick Start

```bash
# Validate subtitle file
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate video.srt --lang en

# Fix issues automatically
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py fix video.srt video_fixed.srt --lang en

# Generate detailed report
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py report video.srt --lang en
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
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate audio.srt --lang en

# Step 3: Auto-fix any issues
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py fix audio.srt audio_netflix.srt --lang en

# Step 4: Verify compliance
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate audio_netflix.srt --lang en
```

## Commands

### validate

Check SRT file against Netflix specifications.

```bash
python3 netflix_subs.py validate input.srt --lang en
```

Exit codes:
- `0`: All entries pass
- `1`: Issues found

### fix

Auto-fix common issues and write corrected SRT.

```bash
python3 netflix_subs.py fix input.srt output.srt --lang en
```

Fixes applied:
- Extends subtitles shorter than 833ms minimum
- Splits lines exceeding character limits
- Adjusts gaps between subtitles
- Limits to 2 lines per subtitle

### report

Generate detailed validation report.

```bash
python3 netflix_subs.py report input.srt --lang en
```

Sample output:
```
==================================================
Netflix Subtitle Validation Report
==================================================
File: video_en.srt
Language: English (17 CPS max, 42 chars/line)

Summary:
  Total entries: 142
  Issues found: 12

Issue breakdown:
  Duration problems: 3
  Reading speed (CPS): 5
  Line too long: 4

Details (first 10):
  #23 [00:01:45,200 --> 00:01:45,800]
    - Duration 600ms < 833ms minimum
  #45 [00:03:12,100 --> 00:03:14,500]
    - CPS 21.3 > 17 maximum
==================================================
```

## Netflix Specifications

### English

| Parameter | Value |
|-----------|-------|
| Max chars per line | 42 |
| Max lines | 2 |
| Min duration | 833ms (5/6 second) |
| Max duration | 7 seconds |
| Reading speed (adult) | 17 CPS |
| Reading speed (children) | 15 CPS |
| Min gap between subtitles | 83ms (2 frames @ 24fps) |

### Chinese

| Parameter | Value |
|-----------|-------|
| Max chars per line | 16 (full-width counted as 2) |
| Max lines | 2 |
| Min duration | 833ms |
| Max duration | 7 seconds |
| Reading speed (adult) | 9 CPS |
| Reading speed (children) | 7 CPS |
| Min gap between subtitles | 83ms |

## Language Support

Specify language with `--lang`:

```bash
# English (default)
python3 netflix_subs.py validate video.srt --lang en

# Chinese
python3 netflix_subs.py validate video.srt --lang zh
```

## Troubleshooting

### "CPS too high" after fix

Some subtitles have too much text for their duration. Options:
1. Manually shorten the text
2. Extend the subtitle duration (may overlap with next)
3. Split into multiple subtitles

### Chinese character counting

Full-width characters (Chinese, Japanese, Korean) count as 2 characters for reading speed calculations.

### Remaining issues after fix

The auto-fix handles timing and line breaks. Issues requiring manual attention:
- Content too dense (high CPS with correct timing)
- Overlapping subtitles
- Complex multi-line reformatting

## References

- [Netflix Timed Text Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)
- [Netflix English Subtitle Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-Timed-Text-Style-Guide)
- [Netflix Simplified Chinese Style Guide](https://partnerhelp.netflixstudios.com/hc/en-us/articles/217351127-Simplified-Chinese-Timed-Text-Style-Guide)
