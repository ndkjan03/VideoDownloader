# Video Downloader

Multi-platform video downloader powered by yt-dlp.

Supports:

- YouTube Video
- YouTube Playlist
- YouTube Mix Playlist
- TikTok Video
- Facebook Video / Reels

---

# Features

## Input Methods

Supports:

### Full URL

```text
https://www.youtube.com/watch?v=xxxxx
https://www.youtube.com/playlist?list=xxxxx
https://www.tiktok.com/@user/video/xxxxx
https://www.facebook.com/reel/xxxxx
```

### YouTube Video ID

```text
dQw4w9WgXcQ
```

### YouTube Playlist ID

```text
PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI
```

### Multiple URLs

Input one or more URLs.

Supported separators:

```text
New line
Comma (,)
Space
```

Example:

```text
https://youtu.be/xxxxx
https://youtu.be/yyyyy
https://www.tiktok.com/@user/video/zzzzz
;
```

Finish input with:

```text
END
end
End
;
```

---

# Download Modes

```text
1. MP4 Best Quality
2. MP4 1080p
3. MP4 720p
4. MP3
5. M4A
6. Original Audio
7. Show Available Formats
0. Quit
```

---

# Playlist Options

For YouTube playlists:

```text
1. First video only
2. Download ALL
3. First N videos
4. Select specific videos/ranges
0. Quit
```

Examples:

```text
1:20
```

Download first 20 videos.

```text
2,4,8
```

Download videos 2, 4 and 8.

```text
1-10
```

Download videos 1 through 10.

---

# YouTube Mix Support

Mix playlists are automatically detected.

Example:

```text
RDxxxxxxxx
```

Restrictions:

- Download ALL disabled
- First N limited to 50
- Custom selections limited to 50 videos

---

# Output Structure

```text
Downloads/
└── vid_downloads/
    └── 20260930_103000/
        ├── Playlist A/
        ├── Playlist B/
        └── Single Video/
```

Example:

```text
Downloads
└── vid_downloads
    └── 20260930_103000
        └── Single Video
            ├── video1.mp4
            ├── video2.mp4
            └── playlistDownload.txt
```

---

# Playlist Report

After download completes:

```text
playlistDownload.txt
```

is generated automatically.

Example:

```text
01 - Video A.mp4
02 - Video B.mp4
03 - Video C.mp4
```

---

# Debug Mode

Run with:

```bash
python3 main.py --debug
```

Displays:

- URL normalization
- Playlist detection
- Mix detection
- yt-dlp options
- Download format
- Playlist limits
- Download statistics

---

# Installation

## Create Virtual Environment

```bash
python3 -m venv .ytenv
```

Activate:

```bash
source .ytenv/bin/activate
```

---

## Install Dependencies

```bash
pip install -U yt-dlp
```

---

## FFmpeg

Create:

```text
yt_tools/
```

Place:

```text
ffmpeg
ffprobe
```

inside the folder.

Example:

```text
yt_tools/
├── ffmpeg
└── ffprobe
```

---

# Run

```bash
python3 main.py
```

Debug mode:

```bash
python3 main.py --debug
```

---

# Build Standalone Binary

Using PyInstaller:

Install:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller \
    --onefile \
    --name VideoDownloader \
    main.py
```

Output:

```text
dist/
└── VideoDownloader
```

Run:

```bash
./VideoDownloader
```

---

# Supported Platforms

| Platform         | Status                    |
| ---------------- | ------------------------- |
| YouTube Video    | ✅                        |
| YouTube Playlist | ✅                        |
| YouTube Mix      | ✅                        |
| TikTok Video     | ✅                        |
| Facebook Video   | ✅                        |
| Facebook Reels   | ✅                        |
| Instagram Reels  | Depends on yt-dlp support |
| Shorts           | ✅                        |

---

# Known Limitations

## Long File Names

Some platforms (especially Facebook) generate extremely long titles.

This may exceed macOS filename limits.

Recommended solution:

- Trim titles to 100–150 characters
- Sanitize invalid filename characters

Example:

```python
"%(title).120s.%(ext)s"
```

instead of:

```python
"%(title)s.%(ext)s"
```

---

# Future Improvements

Planned:

- Download archive support
- Skip already downloaded videos
- Preview before download
- Preview after download
- Subtitle download
- Thumbnail download
- Cookie support
- Batch file input
- Automatic filename cleanup
- Download history database
- GUI version

yt_tools

ffmpeg   -> xử lý/chuyển đổi media
ffprobe  -> đọc metadata media
ffplay   -> phát media

./yt_tools/ffplay video.mp4

1. Phát video

Ví dụ:

./yt_tools/ffplay video.mp4

Nó sẽ mở một cửa sổ player và phát video ngay.

2. Phát MP3
   ./yt_tools/ffplay music.mp3

Không cần VLC hay QuickTime.

3. Test nhanh URL stream

Ví dụ:

./yt_tools/ffplay https://....

hoặc:

yt-dlp -g URL

lấy URL stream rồi:

ffplay STREAM_URL

để xem thử mà không tải xuống.
