# About
ffeasytool - is a wrapper for ffmpeg and ffprobe, simplifying some routine operations. 

The main features are: 
1. merging files of different formats with converting to a common resolution 
2. converting specified audio track to mp3
3. video trimming
4. change of resolution
5. file conversion to gif, mp4 (h264), webm (vp8)

# Examples
#### merge my01.mp4, my02.mp4, my03.mp4

`ffeasytool.py merge -f 1280x720 my*.mp4`

#### resize (to 1280x720)
`ffeasytool.py resize -r 1280x720 myvideo.mp4`

#### resize (half-size):
`ffeasytool.py resize -m 0.5 myvideo.mp4`

#### cut from 1 min 5 sec to 2 min 53 sec
`ffeasytool.py cut -a 01:05 -b 02:53 myvideo.mp4`

#### convert all mp4 to gif (with 5 fps)
`ffeasytool.py togif -x 5 *.mp4`

#### split file to chunks by 20 min
`ffeasytool.py split -t 20m myvideo.mp4`
