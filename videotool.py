#!/usr/bin/env python3

import argparse
import ffmpeg
import glob
import os
import subprocess


class VideoTool():
    bins = {}

    def __init__(self, ffmpeg='ffmpeg', ffprobe='ffprobe'):
        self.bins['ffmpeg'] = ffmpeg
        self.bins['ffprobe'] = ffprobe

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
            , '-preset', 'slow'
            , '-crf', '18'
            , outfile]
        subprocess.Popen(cmd).communicate()

    def cut_single_video(self, infile: str, startpoint='-1', endpoint='-1', outfile='outfile.mp4'):
        if startpoint == '-1' and endpoint == '-1': return

        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile]
        if startpoint != '-1': cmd += ['-ss', startpoint]
        if endpoint != '-1':   cmd += ['-to', endpoint]

        cmd += ['-preset', 'slow'
            , '-crf', '18'
            , outfile]
        subprocess.Popen(cmd).communicate()

    def convert_to_gif(self, infile, fps, outfile):
        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile
            , '-vf', 'fps={},split[s0][s1];[s0]palettegen=stats_mode=single[p];[s1][p]paletteuse'.format(fps)
            , '-loop', '0'
            , outfile]
        subprocess.Popen(cmd).communicate()

    def convert_to_webm(self, infile, outfile):

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
        cmd = [self.bins['ffmpeg']
            , '-i'
            , infile
            , '-c:v', 'libvpx'
            , '-c:a', 'libvorbis'
            , '-q:v', '10'
            , outfile]
        subprocess.Popen(cmd).communicate()


def convert_to_x264():
    ext = args.name
    for f in os.listdir('.'):
        if f.lower().endswith(ext.lower()):
            outfile = os.path.splitext(f)[0] + '_converted.mp4'
            for i in range(len(ffmpeg.probe(f)['streams'])):
                if ffmpeg.probe(f)['streams'][i]['codec_type'] == 'video':
                    videoinfo = ffmpeg.probe(f)['streams'][i]
                    break;
            if videoinfo['codec_name'] != 'h264' or args.force:
                input = ffmpeg.input(f)
                video = input.video
                audio = None
                # searching audio
                for i in range(len(ffmpeg.probe(f)['streams'])):
                    if ffmpeg.probe(f)['streams'][i]['codec_type'] == 'audio':
                        audio = input.audio
                        break;
                if audio is not None:
                    out = ffmpeg.output(audio, video, outfile, qscale=0)
                else:
                    out = ffmpeg.output(video, outfile, qscale=0)
                out.run()


def convert_to_mp3():
    infile = args.name
    outfile = os.path.splitext(infile)[0] + '.mp3'

    input = ffmpeg.input(infile)
    audio = input.audio

    out = ffmpeg.output(audio, outfile)
    out.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    actions = parser.add_argument_group('MAIN ACTIONS')
    actions.add_argument('--merge', action='store_true', help='merge video files')
    mergeParams = parser.add_argument_group('--merge options:')
    mergeParams.add_argument('-f', type=str, default=None, metavar='F', help='video format string: 1280x720[@30]')

    actions.add_argument('--resize', action='store_true', help='resize single video')
    resizeParams = parser.add_argument_group('--resize options: -s OR -r ')
    resizeParams.add_argument('-m', type=float, default=1, metavar='M', help='multiplier: 0.5, 2, 3.4, etc.')
    resizeParams.add_argument('-r', type=str, default=None, metavar='R', help='resolution: 1280x720, etc.')

    actions.add_argument('--cut', action='store_true', help='cut single video. Use -a and(or) -b ')
    cutParams = parser.add_argument_group('--cut options')
    cutParams.add_argument('-a', type=str, default='-1', help='start point in [HH:][MM:]SS[.m...] format')
    cutParams.add_argument('-b', type=str, default='-1', help='end point  in [HH:][MM:]SS[.m...] format')

    actions.add_argument('--togif', action='store_true', help='convert single video to gif')
    togifParams = parser.add_argument_group('--togif options')
    togifParams.add_argument('-x', type=int, default=10, metavar='X', help='fps for gif (default: 10)')

    actions.add_argument('--to264', action='store_true', help='convert all files with specified extension to mp4/h264. H264-video will be skipped')
    to264Params = parser.add_argument_group('--to264 options')
    to264Params.add_argument('--force', action='store_true', help='reencode h264 video')

    actions.add_argument('--towebm', action='store_true', help='convert single video to webm')
    actions.add_argument('--tomp3', action='store_true', help='extract audio to mp3')

    parser.add_argument('name', type=str, help='file or extension to operate')

    args = parser.parse_args()

    videotool = VideoTool()
    if args.resize:
        infile = args.name
        outfile = '{}_resized.mp4'.format(os.path.splitext(args.name)[0])
        if args.m != 1:
            videotool.resize_single_video(infile=infile, scale=args.m, outfile=outfile)
        elif args.r:
            videotool.resize_single_video(infile=infile, resolution=args.r, outfile=outfile)
        # resize_single_video()
    elif args.togif:
        infile = args.name
        outfile = '{}.gif'.format(os.path.splitext(args.name)[0])
        fps = args.x
        videotool.convert_to_gif(infile, fps, outfile)
    elif args.to264:
        convert_to_x264()
    elif args.towebm:
        infile = args.name
        outfile = '{}.webm'.format(os.path.splitext(args.name)[0])
        videotool.convert_to_webm(infile, outfile)
    elif args.cut:
        infile = args.name
        outfile = '{}_cut.mp4'.format(os.path.splitext(args.name)[0])
        if args.a == -1 and args.b == -1:
            print('use -a and(or) -b')
        else:
            videotool.cut_single_video(infile=infile, startpoint=args.a, endpoint=args.b, outfile=outfile)
    elif args.tomp3:
        convert_to_mp3()
    elif args.merge:
        if args.f is None:
            print('use -f to set resolution (-f 1280x720[@30])')
            exit(1)
        files = []
        for file in sorted(os.listdir('.')):
            if not file.endswith(args.name):
                continue
            files.append(file)
        resolution, *fps = args.f.split('@')
        if len(fps) < 1:
            fps = 30
        else:
            fps = int(fps[0])
        width, height = resolution.split('x')
        videotool.avmerge(files, int(width), int(height), int(fps), outfile='myout.mp4')
