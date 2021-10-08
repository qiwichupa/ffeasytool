#!/usr/bin/env python3

import argparse
import ffmpeg
import glob
import os
import subprocess


def resize_single_video():
    infile = args.name
    outfile = os.path.splitext(infile)[0] + '_resized.mp4'
    for i in range(len(ffmpeg.probe(infile)['streams'])):
        if ffmpeg.probe(infile)['streams'][i]['codec_type'] == 'video':
            videoinfo = ffmpeg.probe(infile)['streams'][i]
            break
    height = videoinfo['height']
    width = videoinfo['width']

    input = ffmpeg.input(infile)
    audio = input.audio
    video = input.video

    if args.s != 1:
        newwidth = int(float(width * args.s))
        newheight = int(float(height * args.s))
        video = video.filter('scale', width=newwidth, height=newheight)
    elif args.r:
        width, height = args.r.split('x')
        video = video.filter('scale', width=int(float(width)), height=int(float(height)))
    out = ffmpeg.output(audio, video, outfile, qscale=0)
    out.run()


def cut_single_video():
    infile = args.name
    outfile = os.path.splitext(infile)[0] + '_cut.mp4'
    for i in range(len(ffmpeg.probe(infile)['streams'])):
        if ffmpeg.probe(infile)['streams'][i]['codec_type'] == 'video':
            videoinfo = ffmpeg.probe(infile)['streams'][i]
            break;
    height = videoinfo['height']
    width = videoinfo['width']

    startpoint = args.a
    endpoint = args.b

    input = ffmpeg.input(infile)
    audio = input.audio
    video = input.video

    if startpoint == '-1' and endpoint == '-1':
        print('use -a and(or) -b')
        exit(0)
    elif startpoint == '-1' and endpoint != '-1':
        video = video.trim(end=endpoint)
        audio = audio.filter_('atrim', end=endpoint)
    elif startpoint != '-1' and endpoint == '-1':
        video = video.trim(start=startpoint)
        audio = audio.filter_('atrim', start=startpoint)
    else:
        video = video.trim(start=startpoint, end=endpoint)
        audio = audio.filter_('atrim', start=startpoint, end=endpoint)
    video = video.setpts('PTS-STARTPTS')
    audio = audio.filter_('asetpts', 'PTS-STARTPTS')

    out = ffmpeg.output(audio, video, outfile, qscale=0)
    out.run()


def convert_to_gif():
    infile = args.name
    outfile = os.path.splitext(infile)[0] + '.gif'
    for i in range(len(ffmpeg.probe(infile)['streams'])):
        if ffmpeg.probe(infile)['streams'][i]['codec_type'] == 'video':
            videoinfo = ffmpeg.probe(infile)['streams'][i]
            break;

    height = videoinfo['height']
    width = videoinfo['width']

    input = ffmpeg.input(infile)
    video = input.video

    video = video.filter('fps', args.x)
    out = ffmpeg.output(video, outfile, loop=0)
    out.run()


def convert_to_webm():
    ext = args.name
    for f in os.listdir('.'):
        if f.lower().endswith(ext.lower()):
            outfile = os.path.splitext(f)[0] + '_converted.webm'
            for i in range(len(ffmpeg.probe(f)['streams'])):
                if ffmpeg.probe(f)['streams'][i]['codec_type'] == 'video':
                    videoinfo = ffmpeg.probe(f)['streams'][i]
                    break;
            if videoinfo['codec_name'] != 'libvpx' or args.force:
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
    mergeParams.add_argument('-f', type=str, default=None, metavar='F', help='video format string: 1024x768@30')

    actions.add_argument('--resize', action='store_true', help='resize single video')
    resizeParams = parser.add_argument_group('--resize options: -s OR -r ')
    resizeParams.add_argument('-s', type=float, default=1, metavar='S', help='scale multiplier: 0.5, 2, 3.4, etc')
    resizeParams.add_argument('-r', type=str, default=None, metavar='R', help='set resolution, ex.: 1280x720')

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

    if args.resize:
        resize_single_video()
    elif args.togif:
        convert_to_gif()
    elif args.to264:
        convert_to_x264()
    elif args.towebm:
        convert_to_webm()
    elif args.cut:
        cut_single_video()
    elif args.tomp3:
        convert_to_mp3()
    elif args.merge:
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
        avmerge(files, int(width), int(height), int(fps))
