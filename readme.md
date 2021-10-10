# About
ffeasytool - is a wrapper for ffmpeg and ffprobe to make some routine operations easier. 

The main features are: 
1. merging files of different formats with converting to a common resolution 
2. converting specified audio track to mp3
3. video trimming
4. change of resolution
5. file conversion to gif, mp4 (h264), webm (vp8)

# EXAMPLES
#### merge my01.mp4, my02.mp4, my03.mp4

`ffeasytool.py --merge -f 1280x720 'my*.mp4'`

#### resize (to 1280x720)
`ffeasytool.py --resize -r 1280x720 myvideo.mp4`

#### resize (half-size):
`ffeasytool.py --resize -m 0.5 myvideo.mp4`

#### cut from 1 min 5 sec to 2 min 53 sec
`ffeasytool.py --cut -a 01:05 -b 02:53 myvideo.mp4`

#### convert all mp4 to gif (with 5 fps)
`ffeasytool.py --togif -x 5 'my*.mp4'`

# HELP
```
usage: ffeasytool.py [-h] [--merge] [-f F] [--resize] [-m M] [-r R] [--cut]
                     [-a A] [-b B] [--togif] [-x X] [--to264] [--towebm]
                     [--tomp3] [-t T]
                     name

positional arguments:
  name        filename or quoted wildcards (myvideo.mp4, 'vid*.mp4', etc.).
              Wildcards MUST be used with --merge key, or CAN be used with
              --to* keys.

optional arguments:
  -h, --help  show this help message and exit

MAIN ACTIONS:
  --merge     merge video files (use quoted wildcards). Ex.: "ffeasytool.py
              --merge -f 1280x720 'my*.mp4'"
  --resize    resize single video. Ex.: "ffeasytool.py --resize -m 0.5
              myvideo.mp4", "ffeasytool.py --resize -r 1280x720 myvideo.mp4"
  --cut       cut single video. Use -a and(or) -b parameters as start and end
              points. Ex.: "ffeasytool.py --cut -a 01:05 -b 02:53 myvideo.mp4"
  --togif     convert file(s) to gif. Ex.: "ffeasytool.py --togif -x 5
              'my*.mp4'"
  --to264     convert file(s) to mp4/h264. Ex.: "ffeasytool.py --to264
              'my*.wmv'"
  --towebm    convert file(s) to webm. Ex.: "ffeasytool.py --towebm 'my*.mp4'"
  --tomp3     extract audio to mp3. Ex.: "ffeasytool.py --tomp3 -t 2
              'my*.mp4'"

--merge options:
  -f F        video format string: 1280x720[@30]

--resize options (use -m or -r):
  -m M        multiplier: 0.5, 2, 3.4, etc.
  -r R        resolution: 1280x720, etc.

--cut options (use -a and(or) -b):
  -a A        start point in [HH:][MM:]SS[.m...] format
  -b B        end point in [HH:][MM:]SS[.m...] format

--togif options (optional):
  -x X        fps for gif (default: 10)

--tomp3 options (optional):
  -t T        track (default: 1)

```

