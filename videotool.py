#!/usr/bin/env python3

import argparse
import ffmpeg
import glob
import os





def resize_single_video():
    infile = args.inpt
    outfile = os.path.splitext(infile)[0] + '_resized.mp4'
    for i in range(len(ffmpeg.probe(infile)['streams'])):
        if ffmpeg.probe(infile)['streams'][i]['codec_type'] == 'video':
            videoinfo = ffmpeg.probe(infile)['streams'][i]
            break;
    height = videoinfo['height']
    width = videoinfo['width']

    input = ffmpeg.input(infile)
    audio = input.audio
    video = input.video

    if args.scale!=1:
        newwidth = width*args.scale
        newheight = height*args.scale
        video = video.filter('scale', width=newwidth, height=newheight)
    elif args.resolution:
        video = video.filter('scale', width=args.width, height=args.height)
    out = ffmpeg.output(audio, video, outfile, qscale=0)
    out.run()

def cut_single_video():
    infile = args.inpt
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
    infile = args.inpt
    outfile = os.path.splitext(infile)[0] + '.gif'
    for i in range(len(ffmpeg.probe(infile)['streams'])):
        if ffmpeg.probe(infile)['streams'][i]['codec_type'] == 'video':
            videoinfo = ffmpeg.probe(infile)['streams'][i]
            break;

    height = videoinfo['height']
    width = videoinfo['width']

    input = ffmpeg.input(infile)
    video = input.video

    #optional scaling
    if args.scale!=1:
        newwidth = width*args.scale
        newheight = height*args.scale
        video = video.filter('scale', width=newwidth, height=newheight)
    elif args.resolution:
        video = video.filter('scale', width=args.width, height=args.height)

    video = video.filter('fps', args.fps)
    out = ffmpeg.output(video, outfile, loop=0)
    out.run()

def convert_to_webm():
    ext = args.inpt
    for f in  os.listdir('.'):
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
    ext = args.inpt
    for f in  os.listdir('.'):
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
    infile = args.inpt
    outfile = os.path.splitext(infile)[0] + '.mp3'

    input = ffmpeg.input(infile)
    audio = input.audio

    out = ffmpeg.output(audio, outfile)
    out.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    actions = parser.add_argument_group('MAIN ACTIONS')
    actions.add_argument('--merge', action='store_true', help='merge video files')
    actions.add_argument('--resize', action='store_true', help='resize single video')
    actions.add_argument('--cut', action='store_true', help='cut single video. Use -a and(or) -b ')
    actions.add_argument('--togif', action='store_true', help='convert single video to gif')
    actions.add_argument('--to264', action='store_true', help='convert all files with specified extension to mp4/h264. H264-video will be skipped')
    actions.add_argument('--towebm', action='store_true', help='convert single video to webm')
    actions.add_argument('--tomp3', action='store_true', help='extract audio to mp3')

    resizeMethod1 = parser.add_argument_group('resize method #1 (used with: --resize, --togif)')
    resizeMethod1.add_argument('--scale', type=float,  default=1, metavar='S', help='scale multiplier: 0.5, 2, 3.4, etc')
    
    resizeMethod2 = parser.add_argument_group('resize method #2 (used with: --resize, --togif)')
    resizeMethod2.add_argument('--resolution', action='store_true', help='change resolution. Use with --width and(or) --height')
    resizeMethod2.add_argument('--width', '-x', type=int,  default=-1, metavar='X', help='outfile width')
    resizeMethod2.add_argument('--height', '-y', type=int,  default=-1, metavar='Y', help='outfile height')

    cutParams = parser.add_argument_group('--cut options')
    cutParams.add_argument('-a', type=str, default='-1', help='start point in [HH:][MM:]SS[.m...] format')
    cutParams.add_argument('-b', type=str, default='-1', help='end point  in [HH:][MM:]SS[.m...] format')

    togifParams = parser.add_argument_group('--togif options')
    togifParams.add_argument('--fps', type=int,  default=10, help='fps for gif (default: 10)')

    to264Params = parser.add_argument_group('--to264 options')
    to264Params.add_argument('--force', action='store_true', help='reencode h264 video')

    parser.add_argument('inpt', type=str, help='file or extension to operate')

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
