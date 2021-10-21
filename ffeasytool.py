#!/usr/bin/env python3

import argparse
import glob
import os
import subprocess
import sys


class VideoTool:
    bins = {}

    # --------------------------------------------
    def __init__(self, ffmpeg='ffmpeg', ffprobe='ffprobe'):
        self.bins['ffmpeg'] = ffmpeg
        self.bins['ffprobe'] = ffprobe

    # --------------------------------------------
    def avmerge(self, files, maxWidth=1920, maxHeight=1080, frameRate=30, outfile='outfile.mp4'):
        frameRate = str(frameRate)
        if int(maxWidth) % 2 != 0: maxWidth = int(maxWidth) + 1
        if int(maxHeight) % 2 != 0: maxHeight = int(maxHeight) + 1
        maxWidth = str(maxWidth)
        maxHeight = str(maxHeight)

        if outfile in files: files.remove(outfile)

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

        convertCmdString = [self.bins['ffmpeg']] + cmdoptions + [
            '-filter_complex', filter
            , '-map', '[v]'
            , '-map', '[a]'
            , '-c:a', 'libmp3lame'
            , '-ar', '48000'
            , '-c:v', 'libx264'
            , '-r', frameRate
            , '-bf', '2'
            , '-g', frameRate
            , '-profile:v', 'high'
            , '-preset', 'fast'
            , '-level', '42'
            , outfile]
        subprocess.Popen(convertCmdString).communicate()

    # --------------------------------------------
    def resize_single_video(self, infile: str, scale=None, resolution=None, outfile='outfile.mp4'):
        if scale is None and resolution is None: return

        if scale is not None:
            scale = float(scale)

            # find current resolution
            cmd = [self.bins['ffprobe']
                , '-v'
                , 'error'
                , '-select_streams'
                , 'v:0'
                , '-show_entries'
                , 'stream=width,height'
                , '-of'
                , 'csv=s=x:p=0'
                , infile]
            out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
            width, height = out.split('x')
            width = int(width)
            height = int(height)

            newwidth = int(width * scale)
            newheight = int(height * scale)
        elif resolution is not None:
            newwidth, newheight = resolution.split('x')
            newwidth = int(newwidth)
            newheight = int(newheight)

        if newwidth % 2 != 0: newwidth += 1
        if newheight % 2 != 0: newheight += 1

        # convert resolution
        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile
            , '-vf', 'scale={}:{}, setsar=1:1'.format(newwidth, newheight)
            , '-profile:v', 'high'
            , '-preset', 'fast'
            , '-level', '42'
            , outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def cut_single_video(self, infile: str, startpoint='-1', endpoint='-1', outfile='outfile.mp4'):
        if startpoint == '-1' and endpoint == '-1': return

        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile]
        if startpoint != '-1': cmd += ['-ss', startpoint]
        if endpoint != '-1':   cmd += ['-to', endpoint]

        cmd += ['-profile:v', 'high'
            , '-preset', 'fast'
            , '-level', '42'
            , outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_gif(self, infile, fps, outfile='outfile.gif'):
        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile
            , '-vf', 'fps={},split[s0][s1];[s0]palettegen=stats_mode=single[p];[s1][p]paletteuse'.format(fps)
            , '-loop', '0'
            , outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_webm(self, infile, outfile='outfile.webm'):

        # check video codec
        cmd = [self.bins['ffprobe']
            , '-v', 'error'
            , '-select_streams', 'v:0'
            , '-show_entries', 'stream=codec_name'
            , '-of', 'default=noprint_wrappers=1:nokey=1'
            , infile]
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()

        if out.strip() == 'vp8':
            print('"{}" is already webm, skipped.'.format(infile))
            return

        # check if audio exists
        cmd = [self.bins['ffprobe']
            , '-i', infile
            , '-show_streams'
            , '-select_streams', 'a'
            , '-loglevel', 'error']
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        audioparams = []
        if len(out.strip()) > 1:  audioparams = ['-c:a', 'libvorbis']

        cmd = [self.bins['ffmpeg']
                  , '-i'
                  , infile
                  , '-c:v', 'libvpx'
               ] + audioparams + [
                  '-q:v', '10'
                  , '-crf', '10'
                  , '-b:v', '1M'
                  , '-auto-alt-ref', '0'
                  , outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_x264(self, infile, outfile='outfile.mp4'):

        # check video codec
        cmd = [self.bins['ffprobe']
            , '-v', 'error'
            , '-select_streams', 'v:0'
            , '-show_entries', 'stream=codec_name'
            , '-of', 'default=noprint_wrappers=1:nokey=1'
            , infile]
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()

        if out.strip() == 'h264':
            print('"{}" is already h264, skipped.'.format(infile))
            return

        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile
            , '-c:v', 'libx264'
            , '-profile:v', 'high'
            , '-preset', 'fast'
            , '-level', '42'
            , '-pix_fmt', 'yuv420p'
            , outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_mp3(self, infile, track=0, outfile='outfile.mp3'):
        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile
            , '-map', '0:a:{}'.format(track)
            , '-c:a', 'libmp3lame'
            , '-ar', '48000'
            , outfile]
        subprocess.Popen(cmd).communicate()


if __name__ == '__main__':
    ver = '1.3'
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title='COMMANDS', dest='command', required=True, help='''Use: '%(prog)s COMMAND -h' for additional help''')
    merge = subparser.add_parser('merge', help='''Merge video files. Ex.: "%(prog)s merge -f 1280x720 *.mp4" ''')
    resize = subparser.add_parser('resize', help='''Resize single video. Ex.: "%(prog)s resize -m 0.5 myvideo.mp4",  "%(prog)s resize -r 1280x720 myvideo.mp4"''')
    cut = subparser.add_parser('cut', help='''Cut single video. Use -a and(or) -b parameters as  start and end points. Ex.: "%(prog)s cut -a 01:05 -b 02:53 myvideo.mp4" ''')
    togif = subparser.add_parser('togif', help='''Convert file(s) to gif. Ex.: "%(prog)s togif -x 5 *.mp4" ''')
    to264 = subparser.add_parser('to264', help='''Convert file(s) to mp4/h264. Ex.: "%(prog)s to264 *.wmv" ''')
    towebm = subparser.add_parser('towebm', help='''Convert file(s) to webm. Ex.: "%(prog)s towebm *.mp4" ''')
    tomp3 = subparser.add_parser('tomp3', help='''Extract audio to mp3. Ex.: "%(prog)s tomp3 -t 2 *.mp4" ''')
    version = subparser.add_parser('version', help='''Show version''')

    merge.add_argument('-f', type=str, default=None, metavar='F', help='video format string: 1280x720[@30]')
    merge.add_argument('file', nargs='+', help='files (space-separated) or name with wildcards.')

    resize.add_argument('-m', type=float, default=1, metavar='M', help='multiplier: 0.5, 2, 3.4, etc.')
    resize.add_argument('-r', type=str, default=None, metavar='F', help='resolution: 1280x720, etc.')
    resize.add_argument('file', nargs=1, help='file')

    cut.add_argument('-a', type=str, default='-1', help='start point in [HH:][MM:]SS[.m...] format')
    cut.add_argument('-b', type=str, default='-1', help='end point  in [HH:][MM:]SS[.m...] format')
    cut.add_argument('file', nargs=1, help='file')

    togif.add_argument('-x', type=int, default=10, metavar='X', help='fps for gif (default: 10)')
    togif.add_argument('file', nargs='+', help='file(s) (space-separated) or name with wildcards.')

    to264.add_argument('file', nargs='+', help='file(s) (space-separated) or name with wildcards.')

    towebm.add_argument('file', nargs='+', help='file(s) (space-separated) or name with wildcards.')

    tomp3.add_argument('-t', type=int, default=1, metavar='T', help='track (default: 1)')
    tomp3.add_argument('file', nargs='+', help='file(s) (space-separated) or name with wildcards.')

    args = parser.parse_args()

    if args.command == 'version':
        try:
            out, err = subprocess.Popen(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
            ffmpegver = '{}'.format(out.split('\n')[0].split(' ')[2])
        except:
            ffmpegver = 'ffmpeg not found (check PATH environment variable)'
        try:
            out, err = subprocess.Popen(['ffprobe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
            ffprobever = '{}'.format(out.split('\n')[0].split(' ')[2])
        except:
            ffprobever = 'ffprobe not found (check PATH environment variable)'
        print('version: {}\nffmpeg: {}\nffprobe: {}'.format(ver, ffmpegver, ffprobever))
        sys.exit()

    # correct method to parse filenames with wildcards:
    # wildcards will be converted to filenames by shell in linux,
    # but not in windows. So we set  "nargs='+'" in argparse argument and...
    # ... if we have a list of filenames (maybe converted from wildcards by shell):
    if len(args.file) > 1:
        files = sorted(args.file)
    # ... if argument is a one filename (or filename with wildcards in windows)
    elif len(args.file) == 1:
        files = sorted(glob.glob(args.file[0]))

    videotool = VideoTool()

    if args.command == 'resize':
        infile = files[0]
        infilebasename = os.path.basename(infile)
        outfile = '{}_resized.mp4'.format(os.path.splitext(infilebasename)[0])
        if args.m != 1:
            videotool.resize_single_video(infile=infile, scale=args.m, outfile=outfile)
        elif args.r:
            videotool.resize_single_video(infile=infile, resolution=args.r, outfile=outfile)
    elif args.command == 'togif':
        for infile in files:
            infilebasename = os.path.basename(infile)
            outfile = '{}.gif'.format(os.path.splitext(infilebasename)[0])
            fps = args.x
            videotool.convert_to_gif(infile, fps, outfile)
    elif args.command == 'to264':
        for infile in files:
            infilebasename = os.path.basename(infile)
            outfile = '{}.mp4'.format(os.path.splitext(infilebasename)[0])
            videotool.convert_to_x264(infile, outfile)
    elif args.command == 'towebm':
        for infile in files:
            infilebasename = os.path.basename(infile)
            outfile = '{}.webm'.format(os.path.splitext(infilebasename)[0])
            videotool.convert_to_webm(infile, outfile)
    elif args.command == 'cut':
        infile = files[0]
        infilebasename = os.path.basename(infile)
        outfile = '{}_cut.mp4'.format(os.path.splitext(infilebasename)[0])
        if args.a == -1 and args.b == -1:
            print('use -a and(or) -b')
        else:
            videotool.cut_single_video(infile=infile, startpoint=args.a, endpoint=args.b, outfile=outfile)
    elif args.command == 'tomp3':
        tracknum = args.t - 1
        for infile in files:
            infilebasename = os.path.basename(infile)
            outfile = '{}.mp3'.format(os.path.splitext(infilebasename)[0])
            videotool.convert_to_mp3(infile, tracknum, outfile)
    elif args.command == 'merge':
        if args.f is None:
            print('use -f to set resolution (-f 1280x720[@30])')
            exit(1)
        filestomerge = files
        resolution, *fps = args.f.split('@')
        if len(fps) < 1:
            fps = 30
        else:
            fps = int(fps[0])
        width, height = resolution.split('x')
        videotool.avmerge(filestomerge, int(width), int(height), int(fps), outfile='myout.mp4')
