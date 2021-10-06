#!/usr/bin/env python3

"""
Script: avmerge.py
Author: Sergey "Qiwichupa" Pavlov
Version: 2.03

This script was created for merging stream parts from twitch.tv service (but should be versatile).
Sometimes it is very simple task, but sometimes resizing and reencoding is needed.
Ok, to the code. First of all this script was written for executing in current directory.
I use 'os.listdir' for searching files by extension ('fileExt' variable).
Then I use 'ffmpeg' for scaling to 'maxWidth' and 'maxHeight', adding black borders if it's needed,
and reencoding video to mp4 container with 'libx264' and 'aac' codecs.
In the end I merge temporary files into one 'out.mp4' with 'MP4Box' from GPAC package.

Thanks to Kevin Locke for his mighty scale options: http://kevinlocke.name/bits/2012/08/25/letterboxing-with-ffmpeg-avconv-for-mobile/

ChangeLog:
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

def avconvert(avconvPath, sourceFile, maxWidth, maxHeight, frameRate):
    # import os
    # import subprocess

    outFile = "tmp_" + sourceFile + ".mp4"
    scaleOptions = 'scale=iw*sar*min({maxWidth}/(iw*sar)\,{maxHeight}/ih):ih*min({maxWidth}/(iw*sar)\,{maxHeight}/ih),pad={maxWidth}:{maxHeight}:(ow-iw)/2:(oh-ih)/2'.format(maxWidth=maxWidth, maxHeight=maxHeight)
    convertCmdString = [avconvPath,
                        '-i', sourceFile,
                        '-map', '0',
                        '-vf', scaleOptions,
                        '-c:a', 'libmp3lame',  # aac, libmp3lame
                        '-ar', '48000',
#                        '-ab', '128k',
                        #                  '-async', '30',
                        '-c:v', 'libx264',
                        '-r', frameRate,
                        '-bf', '2',
                        '-g', frameRate,
                        '-profile:v', 'high',
                        '-preset', 'fast',
                        '-level', '42',
                        outFile]
    if os.path.isfile(outFile):
        print('File Exist: ' + outFile)
    else:
        output = subprocess.Popen(convertCmdString).communicate()
        print(output)
    return os.path.abspath(outFile)


def mp4boxmerge(MP4BoxCmd, inFiles, outFile):
    # import os
    # import subprocess

    if len(inFiles) > 1:
        MP4BoxCmdString = []
        MP4BoxCmdString.append(MP4BoxCmd)
        for i in range(0, len(inFiles)):
            MP4BoxCmdString.append('-cat')
            MP4BoxCmdString.append(inFiles[i])
        MP4BoxCmdString.append('-out')
        MP4BoxCmdString.append(outFile)
        try:
            p = subprocess.run(MP4BoxCmdString, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            print(p.stdout)
        except:
            print('removing first -cat')
            MP4BoxCmdString.remove('-cat')
            p = subprocess.run(MP4BoxCmdString, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            print(p.stdout)


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
    # Tool path
    # (Use absolute path in windows (for example: 'C:\Program Files\GPAC\MP4Box')
    # if MP4Box.exe and avconv.exe not in PATH-folders)
    MP4BoxCmd = 'MP4Box'
    avconvCmd = 'ffmpeg'
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
    convertedFiles = []

    for inFile in sorted(os.listdir('.')):
        if not inFile.endswith(fileExt):
            continue
        outFile = avconvert(avconvCmd, inFile, maxWidth, maxHeight, frameRate)
        convertedFiles.append(outFile)

    mp4boxmerge(MP4BoxCmd, convertedFiles, 'out.mp4')