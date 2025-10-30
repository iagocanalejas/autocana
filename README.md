# Installation

```sh
sudo pacman -S python-pipx
pipx install git+https://github.com/iagocanalejas/autocana.git
pipx runpip autocana install git+https://github.com/iagocanalejas/pyutils.git@master
pipx runpip autocana install git+https://github.com/iagocanalejas/vscripts.git@master
```

# AutoCana Setup

Running any command will ensure a configuration file exists in `~/.config/autocana/config.yaml`.

You can run the setup command to update the configuration file.

### Examples

```sh
# run an interactive setup asking for all the required values
autocana setup -i
# set the last_invoice value in the config file to 42
autocana setup --last-invoice 42
# set the signature file to the provided path
autocana setup --signature ~/signature.png
```

# Projects

## Init library

Running the command will clone the template [repository](https://github.com/iagocanalejas/python-template) and make all the required changes to it.

### Examples

```sh
# create a new project named myproject with python versions between 3.13 and 3.14 and a virtual environment
autocana newlibrary myproject --minpy 3.13 --maxpy 3.14 --venv
```

# ARHS

## Invoicing

Running this command will generate an invoice for the specified month using the template in `templates/invoice.docx`.

### Examples

```sh
# generate an invoice for 20 days and save it as invoice.pdf in the ~/Downloads folder
autocana invoice -d 20 -o invoice.pdf --output-dir ~/Downloads
# generate an invoice for March applying a rate of 150
autocana invoice -m 3 -r 150
```

## TSH

Running the command will generate a (Time Sheet) for the specified month using the template in `templates/tsh.xlsx`.

### Examples

```sh
# generate a TSH for the current month skipping days 10, 11 and 12 and save it in the ~/Downloads folder
autocana tsh -s 10 11 12 --output-dir ~/Downloads
# generate a TSH for May and save it as tsh_may.xlsx
autocana tsh -m 5 -o tsh_may.xlsx
```

# Video

## Video editing

A tool to quickly edit videos using a set of predefined actions.

### Available actions

```py
# change the playback speed of an audio file using FFmpeg and save the result as a new file.
def atempo(file: Path, rates: tuple[float, float] = (PAL_RATE, NTSC_RATE)) -> Path: ...

# change the playback speed of an audio file using FFmpeg and save the result as a new file.
def atempo_with(file: Path, value: float) -> Path: ...

# change the playback speed of a video file using FFmpeg and save the result as a new file.
def atempo_video(file: Path, rate: float = NTSC_RATE) -> Path: ...

# append the contents of one multimedia file into another using FFmpeg and save the result as a new file.
def append(file: Path, into: Path) -> Path: ...

# append subtitles to a video file using FFmpeg and save it as a new file.
def append_subs(subs_file: Path, into: Path, lang: str = "spa") -> Path: ...

# adjust the playback speed of an audio or video file using FFmpeg and save it as a new file.
def delay(file: Path, delay: float = 1.0) -> Path: ...

# adjust the playback speed of an audio or video file using FFmpeg and save it as a new file.
def hasten(file: Path, hasten: float = 1.0) -> Path: ...

# extract a specific audio track from a video file using FFmpeg and save it as a new audio file.
def extract(file: Path, track: int = 0) -> Path: ...
```

### Examples

```sh
# extract the first audio track from myvideo.mp4, change it's tempo to NTSC_RATE and hasten it 4.8s
autocana vedit myvideo.mp4 extract atempo hasten=4.8
```

## Download

Tool to quickli download videos from a specified URL or from a file containing a list of URLs.

### Examples

```sh
# download a video from a YouTube URL and save it in the ~/Videos folder
autocana download https://www.youtube.com/watch?v=dQw4w9WgXcQ --output-dir ~/Videos
# download videos from a file containing a list of URLs and save them in the ~/Videos folder
autocana download ~/video_urls.txt --output-dir ~/Videos
```

## Reencode

Re-encode a multimedia file using HandBrakeCLI and save the result as a new file.

### Available qualities

- 2160p
- 1080p

### Examples

```sh
# re-encode a video file to quality 1080p and save it in the ~/Videos folder
autocana reencode ~/Videos/myvideo.mp4 -q 1080p --output-dir ~/Videos
# re-encode all video files in a directory and its subdirectories to quality 720p
autocana reencode ~/Videos -q AV1 -r --output-dir ~/Videos
```
