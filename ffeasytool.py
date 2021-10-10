#!/usr/bin/env python3

import argparse
import glob
import os
import subprocess


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
        print(convertCmdString)
        output = subprocess.Popen(convertCmdString).communicate()
        print(output)

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
    parser = argparse.ArgumentParser()

    actions = parser.add_argument_group('MAIN ACTIONS')
    actions.add_argument('--merge', action='store_true', help='''merge video files (use quoted wildcards). Ex.: "{n} --merge -f 1280x720 'my*.mp4'" '''.format(n=parser.prog))
    mergeParams = parser.add_argument_group('--merge options')
    mergeParams.add_argument('-f', type=str, default=None, metavar='F', help='video format string: 1280x720[@30]')

    actions.add_argument('--resize', action='store_true', help='''resize single video. Ex.: "{n} --resize -m 0.5 myvideo.mp4",  "{n} --resize -r 1280x720 myvideo.mp4"'''.format(n=parser.prog))
    resizeParams = parser.add_argument_group('--resize options (use -m or -r)')
    resizeParams.add_argument('-m', type=float, default=1, metavar='M', help='multiplier: 0.5, 2, 3.4, etc.')
    resizeParams.add_argument('-r', type=str, default=None, metavar='R', help='resolution: 1280x720, etc.')

    actions.add_argument('--cut', action='store_true', help='''cut single video. Use -a and(or) -b parameters as 
                                                                                            start and end points. Ex.: "{n} --cut -a 01:05 -b 02:53 myvideo.mp4" '''.format(n=parser.prog))
    cutParams = parser.add_argument_group('--cut options (use -a and(or) -b)')
    cutParams.add_argument('-a', type=str, default='-1', help='start point in [HH:][MM:]SS[.m...] format')
    cutParams.add_argument('-b', type=str, default='-1', help='end point  in [HH:][MM:]SS[.m...] format')

    actions.add_argument('--togif', action='store_true', help='''convert file(s) to gif. Ex.: "{n} --togif -x 5  'my*.mp4'" '''.format(n=parser.prog))
    togifParams = parser.add_argument_group('--togif options (optional)')
    togifParams.add_argument('-x', type=int, default=10, metavar='X', help='fps for gif (default: 10)')

    actions.add_argument('--to264', action='store_true', help='''convert file(s) to mp4/h264. Ex.: "{n} --to264  'my*.wmv'" '''.format(n=parser.prog))
    actions.add_argument('--towebm', action='store_true', help='''convert file(s) to webm. Ex.: "{n} --towebm  'my*.mp4'" '''.format(n=parser.prog))
    actions.add_argument('--tomp3', action='store_true', help='''extract audio to mp3. Ex.: "{n} --tomp3 -t 2  'my*.mp4'" '''.format(n=parser.prog))
    tomp3Params = parser.add_argument_group('--tomp3 options (optional)')
    tomp3Params.add_argument('-t', type=int, default=1, metavar='T', help='track (default: 1)')

    parser.add_argument('name', type=str, help='''filename or quoted wildcards (myvideo.mp4, 'vid*.mp4', etc.). 
                                                                                Wildcards MUST be used with --merge key, or CAN be used with --to* keys.''')

    args = parser.parse_args()

    files = []
    for f in sorted(glob.glob(args.name)):
        files.append(f)

    videotool = VideoTool()

    if args.resize:
        infile = files[0]
        outfile = '{}_resized.mp4'.format(os.path.splitext(args.name)[0])
        if args.m != 1:
            videotool.resize_single_video(infile=infile, scale=args.m, outfile=outfile)
        elif args.r:
            videotool.resize_single_video(infile=infile, resolution=args.r, outfile=outfile)
    elif args.togif:
        for infile in files:
            outfile = '{}.gif'.format(os.path.splitext(infile)[0])
            fps = args.x
            videotool.convert_to_gif(infile, fps, outfile)
    elif args.to264:
        for infile in files:
            outfile = '{}.mp4'.format(os.path.splitext(infile)[0])
            videotool.convert_to_x264(infile, outfile)
    elif args.towebm:
        for infile in files:
            outfile = '{}.webm'.format(os.path.splitext(infile)[0])
            videotool.convert_to_webm(infile, outfile)
    elif args.cut:
        infile = files[0]
        outfile = '{}_cut.mp4'.format(os.path.splitext(infile)[0])
        if args.a == -1 and args.b == -1:
            print('use -a and(or) -b')
        else:
            videotool.cut_single_video(infile=infile, startpoint=args.a, endpoint=args.b, outfile=outfile)
    elif args.tomp3:
        tracknum = args.t - 1
        for infile in files:
            outfile = '{}.mp3'.format(os.path.splitext(infile)[0])
            videotool.convert_to_mp3(infile, tracknum, outfile)
    elif args.merge:
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
