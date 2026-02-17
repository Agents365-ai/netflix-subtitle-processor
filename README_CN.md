# Netflix 字幕处理器

一个 Claude Code 技能，用于将 Whisper 生成的 SRT 字幕处理成符合 Netflix Timed Text Style Guide 规范的专业字幕。

**探索未至之境**

[![GitHub](https://img.shields.io/badge/GitHub-Agents365--ai-blue?logo=github)](https://github.com/Agents365-ai)
[![Bilibili](https://img.shields.io/badge/Bilibili-441831884-pink?logo=bilibili)](https://space.bilibili.com/441831884)

## 功能

- **验证** SRT 文件是否符合 Netflix 规范
- **自动修复** 常见问题（时长、断行、间隔）
- **详细报告** 包含问题分类
- **多语言支持**（英文、中文）

## 安装

本技能专为 [Claude Code](https://claude.com/claude-code) 设计。将其放入 skills 目录即可：

```bash
git clone https://github.com/Agents365-ai/netflix-subtitle-processor.git ~/.claude/skills/netflix-subtitle-processor
```

## 使用方法

### 通过 Claude Code

让 Claude 验证或修复你的字幕：

```
请验证 my_video.srt 是否符合 Netflix 规范
```

### 直接命令行

```bash
# 验证
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py validate video.srt --lang zh

# 修复（保留所有条目）
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py fix video.srt video_fixed.srt --lang zh

# 清理（移除无法修复的条目）
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py clean video.srt video_clean.srt --lang zh

# 报告
python3 ~/.claude/skills/netflix-subtitle-processor/scripts/netflix_subs.py report video.srt --lang zh
```

## Netflix 规范

| 语言 | 每行最大字符 | 最大阅读速度 | 最短时长 | 最长时长 | 最小间隔 |
|------|-------------|-------------|---------|---------|---------|
| 英文 | 42          | 17 CPS      | 833ms   | 7秒     | 83ms    |
| 中文 | 16          | 9 CPS       | 833ms   | 7秒     | 83ms    |

## 工作流程

与 [openai-whisper-guide](https://github.com/Agents365-ai/openai-whisper) 配合使用，完成从转录到 Netflix 的完整流程：

```
音频 → Whisper 转录 → netflix-subtitle-processor → Netflix 级别字幕
```

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)

## 支持

<div align="center">

如果这个项目对你有帮助，欢迎请我喝杯咖啡！

| 微信支付 | 支付宝 |
|:-------:|:------:|
| <img src="images/wechat-pay.png" width="200" alt="微信支付"> | <img src="images/alipay.png" width="200" alt="支付宝"> |

</div>
