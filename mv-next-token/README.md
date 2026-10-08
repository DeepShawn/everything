# 《下一个字 · Next Token》AI 世界 MV

九位 AI 大模型拟人角色的 MV：旋律、编曲、歌声、画面全部由代码生成。1920×1080，24fps，时长 3:25。

## 文件

| 文件 | 说明 |
|---|---|
| `NextToken_MV_1080p_web.mp4` | 单文件版，可直接下载播放（1080p，约 90MB，码率较低） |
| `full_quality/NextToken_MV_full.mp4.part1` ~ `part4` | 高码率完整版（1080p，12 Mbps，约 300MB）。GitHub 单文件上限 100MB，所以拆成 4 段，下载后需要合并 |
| `NextToken_lyrics.srt` | 歌词字幕（SRT） |

## 合并完整版

把 4 个分段下载到同一个文件夹，然后：

**Windows（命令提示符 cmd）**

```
copy /b NextToken_MV_full.mp4.part1 + NextToken_MV_full.mp4.part2 + NextToken_MV_full.mp4.part3 + NextToken_MV_full.mp4.part4 NextToken_MV_full.mp4
```

**macOS / Linux**

```
cat NextToken_MV_full.mp4.part1 NextToken_MV_full.mp4.part2 NextToken_MV_full.mp4.part3 NextToken_MV_full.mp4.part4 > NextToken_MV_full.mp4
```

合并后文件的 SHA-256 应为：`c9e2f8b69312fbecc8461eed2847600ffc4c741b0fcdb98b62329991848c9d2a`
