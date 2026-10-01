#!/usr/bin/env python3

# ============================================================
# IMPORTS
# ============================================================
import sys
import subprocess
import re
from pathlib import Path
from yt_dlp import YoutubeDL
from datetime import datetime
from urllib.parse import (urlparse, parse_qs)
from yt_dlp.utils import DownloadError

# ============================================================
# DEBUG MODE
# ============================================================
def debug_log(*args):
    if DEBUG:
        print("[DEBUG]", *args)

def show_environment():
    try:
        import yt_dlp

        debug_log(
            "yt-dlp:",
            yt_dlp.version.__version__
        )
    except Exception as e:
        debug_log(
            "yt-dlp version error:",
            e
        )

    debug_log(
        "Python:",
        sys.version.split()[0]
    )

    debug_log(
        "Base Dir:",
        BASE_DIR
    )

    debug_log(
        "Base Download Dir:",
        BASE_DOWNLOAD_DIR
    )

    debug_log(
        "FFmpeg Dir:",
        FFMPEG_DIR
    )

# ============================================================
# CONFIG
# ============================================================
DEBUG = "--debug" in sys.argv

def get_base_dir():
    """
    Return project directory when running:
    - source code
    - pyinstaller executable
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent

    return Path(__file__).resolve().parent

def resource_path(relative):
    """
    Works for:
    source
    pyinstaller
    """

    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative

    return BASE_DIR / relative

BASE_DIR = get_base_dir()
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

FFMPEG_DIR = resource_path("yt_tools")

BASE_DOWNLOAD_DIR = (
    Path.home()
    / "Downloads"
    / "vid_downloads"
)

DOWNLOAD_DIR = None

# ============================================================
# GLOBAL VARIABLES FOR PROGRESS DISPLAY
# ============================================================
current_index = 1
total_items = 1
last_percent = -1

# ============================================================
# INPUT HELPERS
# ============================================================
def exit_if_requested(value):
    """
    Exit application when user enters:
    0 / q / quit / exit
    """
    value = value.strip()
    
    if value.lower() in (
        "0",
        "q",
        "quit",
        "exit"
    ):
        print("\nBye!")
        # sys.exit(0)
        raise SystemExit
        
    return value

def ask(prompt):
    """
    Wrapper around input() with built-in quit handling.
    """
    return exit_if_requested(
        input(prompt)
    )

def normalize_input(user_input):
    """
    Convert user input into a valid YouTube URL.
    Supports:
    - Full URLs
    - Video IDs
    - Playlist IDs
    """
    user_input = user_input.strip()

    if user_input.startswith(("http://", "https://")):
        return user_input

    # Playlist ID
    if (
        user_input.startswith(("PL", "RD", "UU", "OLAK", "LL", "WL", "FL"))
        and len(user_input) > 10
    ):
        return (
            "https://www.youtube.com/playlist?list="
            + user_input
        )

    # Video ID
    if len(user_input) == 11:
        return (
            "https://www.youtube.com/watch?v="
            + user_input
        )
    return user_input

def get_urls():
    print(
        "\nVideo URL / ID(s)"
        "\nSupported separators:"
        "\n- New line"
        "\n- Comma (,)"
        "\n- Space"
        "\n"
        "\nFinish with:"
        "\n- END"
        "\n- end"
        "\n- End"
        "\n- ;"
        "\n"
    )

    urls = []

    while True:
        line = ask("> ").strip()

        if line in (";",):
            break

        if line.lower() == "end":
            break

        if not line:
            continue

        items = re.split(
            r"[\s,]+",
            line
        )

        for item in items:
            item = item.strip()

            if not item:
                continue

            urls.append(
                normalize_input(item)
            )
    return urls

# ============================================================
# PLAYLIST HELPERS
# ============================================================
def url_has_playlist(url):
    """
    Detect whether URL contains a playlist parameter.
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        return "list" in params
    except:
        return False
    
def is_mix_playlist(info):
    """
    YouTube Mix playlists always start with RD.
    """
    playlist_id = info.get("id", "")
    return playlist_id.startswith("RD")

def is_playlist(info):
    """
    Check whether extracted info is a playlist.
    """
    return (
        isinstance(info, dict)
        and "entries" in info
    )

# ============================================================
# FILE HELPERS
# ============================================================
def create_download_dir():
    global DOWNLOAD_DIR

    if DOWNLOAD_DIR:
        return DOWNLOAD_DIR

    DOWNLOAD_DIR = (
        BASE_DOWNLOAD_DIR
        / RUN_TIMESTAMP
    )

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return DOWNLOAD_DIR

def open_download_folder():
    subprocess.run([
        "open",
        str(DOWNLOAD_DIR)
    ])

def generate_playlist_reports():
    """
    Generate playlistDownload.txt for every folder containing media files.
    Executed once after download completes.
    """
    for report in DOWNLOAD_DIR.rglob(
        "playlistDownload.txt"
    ):
        report.unlink()

    for file in DOWNLOAD_DIR.rglob("*"):
        if not file.is_file():
            continue

        if file.name == "playlistDownload.txt":
            continue

        report = (
            file.parent
            / "playlistDownload.txt"
        )

        with open(
            report,
            "a",
            encoding="utf-8"
        ) as f:
            f.write(
                file.name + "\n"
            )

# ============================================================
# DISPLAY HELPERS
# ============================================================
def short_title(title, max_len=50):
    """
    Shorten long Youtube titles for cleaner terminal output.
    """
    if not title:
        return "Unknown"

    if len(title) <= max_len:
        return title

    return title[:max_len - 3] + "..."

def format_speed(speed):
    """
    Convert bytes/sec -> MB/sec
    """
    if not speed:
        return "-- MB/s"

    return f"{speed / 1024 / 1024:.1f} MB/s"

def format_eta(eta):
    """
    Convert seconds -> MM:SS
    """
    if eta is None:
        return "--:--"

    mins = eta // 60
    secs = eta % 60

    return f"{mins:02d}:{secs:02d}"

# ============================================================
# PROGRESS CALLBACK
# ============================================================
def progress_hook(d):
    global current_index
    global total_items
    global last_percent

    status = d.get("status")

    # --------------------------------------------------------
    # DOWNLOADING
    # --------------------------------------------------------
    if status == "downloading":
        try:
            percent_str = d.get("_percent_str")
            if not percent_str:
                return

            clean_percent = re.sub(
                r"\x1b\[[0-9;]*m",
                "",
                percent_str
            )

            percent = int(
                float(
                    clean_percent
                    .replace("%", "")
                    .strip()
                )
            )

            if percent == last_percent:
                return

            last_percent = percent

            title = short_title(
                d.get("info_dict", {}).get("title", "Unknown")
            )

            speed = format_speed(
                d.get("speed")
            )

            eta = format_eta(
                d.get("eta")
            )

            sys.stdout.write(
                f"\r[{current_index:02d}/{total_items:02d}] "
                f"{percent:3d}% "
                f"{title} "
                f"({speed}, ETA {eta})"
            )

            sys.stdout.flush()

        except Exception as e:
            debug_log(
                "progress_hook error:",
                repr(e)
            )

    # --------------------------------------------------------
    # FINISHED CURRENT VIDEO
    # --------------------------------------------------------
    elif status == "finished":
        title = short_title(
            d.get("info_dict", {}).get("title", "Unknown")
        )

        sys.stdout.write(
            f"\r[{current_index:02d}/{total_items:02d}] "
            f"100% "
            f"{title}\n"
        )

        sys.stdout.flush()

        # current_index += 1
        last_percent = -1

# ============================================================
# YT-DLP HELPERS
# ============================================================
def get_info(url, playlist_limit=None):
    """
    Retrieve metadata without downloading.
    """
    debug_log(
        "get_info()",
        url,
        playlist_limit
    )
    
    opts = {
        "quiet": not DEBUG,
        "extract_flat": True,
        "remote_components": [
            "ejs:github"
        ]
    }

    if playlist_limit:
        opts["playlist_items"] = (
            playlist_limit
        )

    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(
            url,
            download=False
        )

def build_opts(mode, download_dir):
    """
    Build yt-dlp download options
    based on selected download mode.
    """
    opts = {
        # FFmpeg location
        "ffmpeg_location": str(
            FFMPEG_DIR
        ),

        # Continue if one video fails
        "ignoreerrors": True,

        # Cleaner console output
        "quiet": not DEBUG,
        "no_warnings": not DEBUG,

        # Progress display
        "progress_hooks": [
            progress_hook
        ],
        
        "remote_components": [
            "ejs:github"
        ],
        
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,

        # Output folder structure
        "outtmpl": str(
            download_dir /
            "%(playlist_title|Single Video)s" /
            "%(playlist_index|)s%(playlist_index& - )s%(id)s - %(title).80s.%(ext)s"
        ),
    }

    # --------------------------------------------------------
    # MP4 BEST
    # --------------------------------------------------------
    if mode == "1":
        opts["format"] = (
            "bestvideo+bestaudio/best"
        )

        opts["merge_output_format"] = "mp4"

    # --------------------------------------------------------
    # MP4 1080P
    # --------------------------------------------------------
    elif mode == "2":
        opts["format"] = (
            "bestvideo[height<=1080]"
            "+bestaudio/best"
        )

        opts["merge_output_format"] = "mp4"

    # --------------------------------------------------------
    # MP4 720P
    # --------------------------------------------------------
    elif mode == "3":
        opts["format"] = (
            "bestvideo[height<=720]"
            "+bestaudio/best"
        )

        opts["merge_output_format"] = "mp4"

    # --------------------------------------------------------
    # MP3
    # --------------------------------------------------------
    elif mode == "4":
        opts["format"] = "bestaudio/best"

        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        ]

    # --------------------------------------------------------
    # M4A
    # --------------------------------------------------------
    elif mode == "5":
        opts["format"] = (
            "bestaudio[ext=m4a]/bestaudio"
        )

        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ]
        
    # --------------------------------------------------------
    # ORIGINAL AUDIO
    # --------------------------------------------------------
    elif mode == "6":
        opts["format"] = ("bestaudio")

    debug_log(
        "Download mode:",
        mode
    )

    debug_log(
        "Format:",
        opts.get("format")
    )

    debug_log(
        "FFmpeg location:",
        opts.get("ffmpeg_location")
    )
    
    debug_log(
        "Remote Components:",
        opts.get("remote_components")
    )
    debug_log(
        "Postprocessors:",
        opts.get("postprocessors")
    )
    return opts

def show_formats(url):
    """
    Display all formats supported by YouTube.
    """
    print("\nAvailable formats:\n")

    subprocess.run([
        str(BASE_DIR / ".ytenv" / "bin" / "yt-dlp"),
        "-F",
        url
    ])

# ============================================================
# MENU FUNCTIONS
# ============================================================
def get_download_mode():
    """
    Main format selection menu.
    """
    print("""
=================================================
1. MP4 Best Quality
2. MP4 1080p
3. MP4 720p
4. MP3
5. M4A (Recommended)
6. Original Audio (Best Quality)
7. Show Available Formats
0. Quit
=================================================
""")
    return ask("Choose: ").strip()

def get_playlist_download_limit(allow_all=True):
    """
    Playlist selection menu.
    Returns:
        None      -> ALL
        "1"       -> first video
        "1:20"    -> first 20 videos
        "2,4,9"   -> selected videos
    """
    print("\nPlaylist Download Options")
    print("1. First video only")

    if allow_all:
        print("2. Download ALL")
        print("3. First N videos")
        print("4. Select specific videos/ranges (2,4,5-10,20)")
        print("0. Quit")
    else:
        print("2. First N videos")
        print("3. Select specific videos/ranges (2,4,5-10,20)")
        print("0. Quit")

    choice = ask("\nChoose: ").strip()

    if allow_all:
        if choice == "1":
            return "1"

        elif choice == "2":
            return None

        elif choice == "3":
            n = ask(
                "First N videos (max 50): "
            ).strip()

            if n.isdigit():
                return f"1:{min(int(n),50)}"

        elif choice == "4":
            return ask(
                "Video numbers: "
            ).strip()
    else:
        if choice == "1":
            return "1"

        elif choice == "2":
            n = ask(
                "First N videos (max 50): "
            ).strip()

            if n.isdigit():
                return f"1:{min(int(n),50)}"

        elif choice == "3":
            items = ask("Video numbers: ").strip()

            if not allow_all:
                count = len(
                    [x for x in items.split(",") if x.strip()]
                )

                if count > 50:
                    print("\nMix playlist: maximum 50 videos.")

                    return None
            return items
        
        elif choice == "0":
            return None
    return None

def process_multi_video(urls):
    global total_items
    global current_index
    global last_percent

    total_items = len(urls)
    current_index = 1
    last_percent = -1

    print(
        f"\nDetected {total_items} videos"
    )

    mode = get_download_mode()

    if mode == "7":
        show_formats(urls[0])
        return

    download_dir = create_download_dir()

    opts = build_opts(
        mode,
        download_dir
    )

    try:
        with YoutubeDL(opts) as ydl:
            for url in urls:
                ydl.download([url])

                current_index += 1

        generate_playlist_reports()
    except Exception as e:
        print("\nDOWNLOAD FAILED")
        print(e)

# ============================================================
# MAIN
# ============================================================
def main():
    global total_items
    
    playlist_limit = None

    print("\nVideo Downloader\n")

    urls = get_urls()

    if not urls:
        print("No URL entered.")
        return
    
    if len(urls) > 1:
        process_multi_video(urls)
        return
    
    url = urls[0]
   
    debug_log(
        "Normalized URL:",
        url
    )

    playlist_limit = None

    if url_has_playlist(url):
        try:
            temp_info = get_info(
                url,
                "1"
            )
        except DownloadError as e:
            print("\nCannot access playlist.")
            print(e)
            return

        is_mix = (
            temp_info.get("id", "")
            .startswith("RD")
        )

        debug_log(
            "Is Mix Playlist:",
            is_mix
        )
        print("\nPlaylist detected from URL")
        
        # ----------------------------------------------------
        # NORMAL PLAYLIST ONLY
        # ----------------------------------------------------
        if not is_mix:
            try:
                full_info = get_info(url)

                print(
                    f"Videos : {len(full_info.get('entries', []))}"
                )
            except Exception as e:
                debug_log(
                    "Failed to get playlist count:",
                    e
                )

        # ----------------------------------------------------
        # MIX PLAYLIST
        # ----------------------------------------------------
        if is_mix:
            print("\nYouTube Mix detected")
            print("Download ALL disabled.")

        playlist_limit = (
            get_playlist_download_limit(
                allow_all=not is_mix
            )
        )
        
        debug_log(
            "Playlist limit:",
            playlist_limit
        )
    
    try:
        info = get_info(url, playlist_limit)
    except DownloadError as e:
        print("\nFailed to read URL")
        print(e)
        return

    # --------------------------------------------------------
    # DEBUG INFO
    # --------------------------------------------------------
    debug_log(
        "Info type:",
        info.get("_type")
    )

    debug_log(
        "Title:",
        info.get("title")
    )

    debug_log(
        "ID:",
        info.get("id")
    )
    
    debug_log(
        "Extractor:",
        info.get("extractor")
    )

    debug_log(
        "Extractor Key:",
        info.get("extractor_key")
    )

    # --------------------------------------------------------
    # PLAYLIST DETECTED
    # --------------------------------------------------------
    if is_playlist(info):
        total_items = len(
            info.get("entries", [])
        )

        print("\nPlaylist detected")
        print(
            f"Title  : {info.get('title')}"
        )

        print(
            f"Videos : {total_items}"
        )

        debug_log(
            "Total items:",
            total_items
        )

    # --------------------------------------------------------
    # SINGLE VIDEO
    # --------------------------------------------------------
    else:
        total_items = 1

    mode = get_download_mode()

    # --------------------------------------------------------
    # SHOW FORMATS ONLY
    # --------------------------------------------------------
    if mode == "7":
        show_formats(url)
        return

    # --------------------------------------------------------
    # BUILD OPTIONS
    # --------------------------------------------------------
    download_dir = create_download_dir()
    
    opts = build_opts(mode, download_dir)
    
    if playlist_limit:
        opts["playlist_items"] = playlist_limit

    # --------------------------------------------------------
    # START DOWNLOAD
    # --------------------------------------------------------
    print("\nStarting download...\n")
    debug_log(
        "DOWNLOAD START"
    )

    debug_log(
        "Options:",
        opts
    )

    try:
        debug_log(
            "Selected format:",
            opts.get("format")
        )
        
        with YoutubeDL(opts) as ydl:
            result = ydl.download([url])
        
        generate_playlist_reports()
        
        debug_log(
            "Playlist reports generated"
        )

        debug_log(
            "DOWNLOAD END",
            result
        )

    except Exception as e:
        print("\nDOWNLOAD FAILED")
        print(e)

        debug_log(
            "DOWNLOAD EXCEPTION",
            repr(e)
        )

    print("\nDone!")

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    if DEBUG:
        show_environment()
        
    while True:
        try:
            main()

        except KeyboardInterrupt:
            print("\n\nBye!")
            break

        print("\n" + "=" * 50)
        print("Ready for next download")
        print("=" * 50 + "\n")