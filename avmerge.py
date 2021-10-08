#!/usr/bin/env python3

"""
Script: avmerge.py
Author: Sergey "Qiwichupa" Pavlov
Version: 2.04
This script was created for merging stream parts from twitch.tv service (but should be versatile).
Sometimes it is very simple task, but sometimes resizing and reencoding is needed.
Ok, to the code. First of all this script was written for executing in current directory.
I use 'os.listdir' for searching files by extension ('fileExt' variable).
Then I use 'ffmpeg' for scaling to 'maxWidth' and 'maxHeight', adding black borders if it's needed,
and reencoding video to mp4 container with 'libx264' and 'mp3' codecs.
Thanks to Kevin Locke for his mighty scale options: http://kevinlocke.name/bits/2012/08/25/letterboxing-with-ffmpeg-avconv-for-mobile/

ChangeLog:
=== 2.04 ===
MP4Box replaced by ffmpeg
=== 2.03 ===
* First parameter for MP4Box (in 'mp4boxmerge' function, outside the cycle) was changed from '-add' to '-cat'. This part of code must be rewritten in the future.
=== 2.02 ===
* minor fix
=== 2.01 ===
* minor fix
=== 2.0 ===
+ default Width/Heigth options for wide resolution
+ params module with wide/resolution rewrite/extention rewrite options
= code rewrite and optimizing
"""

import os
import subprocess
import argparse


# # # # # # # #
# # FUNCTIONS #
# # # # # # # #
def avmerge(files, maxWidth=1920, maxHeight=1080, frameRate=30, ffmpegcmd='ffmpeg'):
    frameRate = str(frameRate)
    maxWidth = str(maxWidth)
    maxHeight = str(maxHeight)

    cmdoptions = []
    filteropt1 = ''
    filteropt2 = ''
    for i, file in enumerate(files):
        cmdoptions += ['-i']
        cmdoptions += [file]
        filteropt1 = '{filteropt1}[{i}:v]scale=iw*sar*min({maxWidth}/(iw*sar)\,{maxHeight}/ih):ih*min({maxWidth}/(iw*sar)\,{maxHeight}/ih),pad={maxWidth}:{maxHeight}:(ow-iw)/2:(oh-ih)/2,setsar=1[{i}v];'.format(
            filteropt1=filteropt1, i=i, maxWidth=maxWidth, maxHeight=maxHeight)
        filteropt2 = '{filteropt2}[{i}v] [{i}:a] '.format(filteropt2=filteropt2, i=i)
    filteropt3 = 'concat=n={}:v=1:a=1 [v] [a]'.format(len(files))
    filter = '{}{}{}'.format(filteropt1, filteropt2, filteropt3)

    convertCmdString = [ffmpegcmd] + cmdoptions + ['-filter_complex'
        , filter
        , '-map'
        , '[v]'
        , '-map'
        , '[a]'
        , '-c:a', 'libmp3lame'
        , '-ar', '48000'
        , '-c:v', 'libx264'
        , '-r', frameRate
        , '-bf', '2'
        , '-g', frameRate
        , '-profile:v', 'high'
        , '-preset', 'fast'
        , '-level', '42'
        , 'output.mp4'
                                                   ]
    print(convertCmdString)
    output = subprocess.Popen(convertCmdString).communicate()
    print(output)


if __name__ == '__main__':
    # SETTINGS  ================================
    # Width and Height default value
    maxWidth = '960'
    maxHeight = '720'
    # Width and Height default value for -w (--wide) option
    maxWidthWide = '1280'
    maxHeightWide = '720'
    # Framerate option
    frameRate = '30'
    # default extention of source files
    fileExt = '.flv'

    # HELP & PARAMS ================================
    parser = argparse.ArgumentParser(prog='avmerge.py',
                                     description='Script for merging video files with re-encoding. Run it from directory with video files. Use "Settings" section of script for tuning.')
    resolutionArgsGroup = parser.add_mutually_exclusive_group()
    resolutionArgsGroup.add_argument("-r", "--resolution", metavar=('W', 'H'), type=int, nargs=2, help="rewrite resolution settings with 'Width Height'")
    resolutionArgsGroup.add_argument("-w", "--wide", help="use wide resolution from in-script settings", action="store_true")
    parser.add_argument('-f', '--fps', type=str, help='rewrite FPS option (30 is default)')
    parser.add_argument('-e', '--extention', type=str, help='rewrite extention option (use "ext" or ".ext" format as you like)')
    args = parser.parse_args()

    if args.wide:
        maxWidth = maxWidthWide
        maxHeight = maxHeightWide
    if args.resolution:
        maxWidth = str(args.resolution[0])
        maxHeight = str(args.resolution[1])
    if args.extention:
        fileExt = args.extention
    if args.fps:
        frameRate = args.fps

    #  MAIN CODE ================================
    files = []
    for file in sorted(os.listdir('.')):
        if not file.endswith(fileExt):
            continue
        files.append(file)
    avmerge(files)
