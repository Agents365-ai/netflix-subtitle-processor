# Netflix Subtitle Processor

A Claude Code skill for processing Whisper-generated SRT files to meet Netflix Timed Text Style Guide specifications.

**探索未至之境**

[![GitHub](https://img.shields.io/badge/GitHub-Agents365--ai-blue?logo=github)](https://github.com/Agents365-ai)
[![Bilibili](https://img.shields.io/badge/Bilibili-441831884-pink?logo=bilibili)](https://space.bilibili.com/441831884)

## Features

- **Validate** SRT files against Netflix specifications
- **Auto-fix** common issues (timing, line breaks, gaps)
- **Detailed reports** with issue categorization
- **Multi-language** support (English, Chinese)

## Installation

This skill is designed for use with [Claude Code](https://claude.com/claude-code). Simply place it in your skills directory:

```bash
git clone https://github.com/Agents365-ai/netflix-subtitle-processor.git ~/.claude/skills/netflix-subtitle-processor
```

## Usage

### With Claude Code

Ask Claude to validate or fix your subtitles:

```
Please validate my_video.srt against Netflix specs
```

### Direct CLI

```bash
# Validate
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate video.srt --lang en

# Fix (keeps all entries)
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py fix video.srt video_fixed.srt --lang en

# Clean (removes unfixable entries)
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py clean video.srt video_clean.srt --lang en

# Report
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py report video.srt --lang en
```

## Netflix Specifications

| Language | Max Chars/Line | Max CPS | Min Duration | Max Duration | Min Gap |
|----------|----------------|---------|--------------|--------------|---------|
| English  | 42             | 17      | 833ms        | 7s           | 83ms    |
| Chinese  | 16             | 9       | 833ms        | 7s           | 83ms    |

## Workflow

Best used with [openai-whisper-guide](https://github.com/Agents365-ai/openai-whisper) for the complete transcription-to-Netflix pipeline:

```
Audio → Whisper → netflix-subtitle-processor → Netflix-ready SRT
```

## License

MIT License - see [LICENSE](LICENSE)

## Support

<div align="center">

If this project helps you, consider buying me a coffee!

| WeChat Pay | Alipay |
|:----------:|:------:|
| <img src="images/wechat-pay.png" width="200" alt="WeChat Pay"> | <img src="images/alipay.png" width="200" alt="Alipay"> |

</div>
