#!/usr/bin/env python3

import argparse
import glob
import os
import subprocess
import sys
import platform
import math
import string
import random
from shutil import which

class VideoTool:
    bins = {}

    # --------------------------------------------
    def __init__(self, ffmpeg='ffmpeg', ffprobe='ffprobe'):
        self.bins['ffmpeg'] = which(ffmpeg)
        self.bins['ffprobe'] = which(ffprobe)

        # check bins
        binsfailed = False
        if self.bins['ffmpeg'] is None:
            binsfailed = True
            print("ffmpeg not found in PATH directory.")
        if self.bins['ffprobe'] is None:
            binsfailed = True
            print("ffprobe not found in PATH directory.")
        if binsfailed:
            print('\nYou must install ffmpeg.')
            if platform.system() == "Windows":
                print(  '\nFOR WINDOWS:\n'
                        'You can download ffmpeg from:\n'
                        'https://github.com/GyanD/codexffmpeg/releases/\n'
                        'Copy ffmpeg.exe and ffprobe.exe to one of this folders:\n'
                        '{}'.format(os.environ['PATH']).replace(';',';\n'))
            sys.exit(1)

    # --------------------------------------------
    def _get_h264settings(self, quality):
        '''returns common encoder settings'''
        return [
            '-c:v', 'libx264'
            , '-sn'
            , '-crf', str(quality)
            , '-preset', 'fast'
            , '-g', '30'
            , '-force_key_frames', 'expr:gte(t,n_forced*18)'
            , '-pix_fmt', 'yuv420p'
            ]
    
    # --------------------------------------------
    def _lead_to_divisibility_by_2(self, pxls, enlargement=True):
        '''Function to lead video width/height to a divisible by 2. Necessary for encoding video with h264 codec.'''
        if pxls % 2 != 0:
            if enlargement:
                pxls += 1
            else:
                pxls -= 1
        return pxls

    # --------------------------------------------
    def _get_resolution(self, file):
        '''Returns tuple  (width, height) as int'''
        cmd = [self.bins['ffprobe']
                , '-v'
                , 'error'
                , '-select_streams'
                , 'v:0'
                , '-show_entries'
                , 'stream=width,height'
                , '-of'
                , 'csv=s=x:p=0'
                , file]
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        width, height = out.split('x')
        return( int(width),  int(height) )

    # --------------------------------------------
    def show_versions(self):
        out, err = subprocess.Popen([self.bins['ffmpeg'], '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        ffmpegver = '{}'.format(out.split('\n')[0].split(' ')[2])
        out, err = subprocess.Popen([self.bins['ffprobe'], '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        ffprobever = '{}'.format(out.split('\n')[0].split(' ')[2])
        return self.bins['ffmpeg'], ffmpegver, self.bins['ffprobe'], ffprobever

    # --------------------------------------------
    def avmerge(self, files, maxWidth=1920, maxHeight=1080, frameRate=30, quality=22, outfile='outfile.mp4'):
        frameRate = str(frameRate)
        maxWidth = str(self._lead_to_divisibility_by_2(int(maxWidth)))
        maxHeight = str(self._lead_to_divisibility_by_2(int(maxHeight)))

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

        cmd = [self.bins['ffmpeg']]
        cmd += cmdoptions
        cmd += [
            '-filter_complex', filter
            , '-map', '[v]'
            , '-map', '[a]'
            , '-c:a', 'libmp3lame'
            , '-ar', '48000'
            , '-r', frameRate
            , '-bf', '2'
            ]
        cmd += self._get_h264settings(quality)
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def compress_single_video(self, infile: str, targetsize: str, audiobitrate=None, containerfactor=10, outfile="outfile.mp4"):
        # platform check
        if platform.system() == "Linux":
            devnull = '/dev/null'
        elif platform.system() == "Windows":
            devnull = 'NUL'

        # convert target size to bytes
        sizeerror='Use size format: 1024 - 1024 bytes, 1K - 1 kilobyte, 1M - 1 megabyte, 1G - 1 gigabyte'
        if targetsize.endswith('K'):
            try:
                targetsize = int(targetsize[:-1]) * 1024
                sizein = 'Kb'
            except Exception as e:
                print('{}\n\n{}.'.format(e, sizeerror))
        elif targetsize.endswith('M'):
            try:
                targetsize = int(targetsize[:-1]) * (1024 ** 2)
                sizein = 'Mb'
            except Exception as e:
                print('{}\n\n{}.'.format(e, sizeerror))
        elif targetsize.endswith('G'):
            try:
                targetsize = int(targetsize[:-1]) * (1024 ** 3)
                sizein = 'Gb'
            except Exception as e:
                print('{}\n\n{}.'.format(e, sizeerror))
        else:
            try:
                targetsize = int(targetsize)
                sizein = 'B'
            except Exception as e:
                print('{}\n\n{}.'.format(e, sizeerror))

        # find video duration in seconds
        cmd = [self.bins['ffprobe']
             , '-v'
             , 'error'
             , '-show_entries'
             , 'format=duration'
             , '-of'
             , 'csv=p=0'
             , infile]
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        duration = float(out.strip())

        # get audio rate in bits per seconds
        if audiobitrate is None:
            cmd = [self.bins['ffprobe']
                , '-v'
                , 'error'
                , '-select_streams'
                , 'a:0'
                , '-show_entries'
                , 'stream=bit_rate'
                , '-of'
                , 'csv=p=0'
                , infile]
            out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
            try:
                audiobps = float(out.strip())
            except:
                # sometimes ffprobe return N/A
                audiobps = 128 * 1000
        else:
            audiobps = audiobitrate * 1000

        mp4overhead = math.floor( containerfactor *  (1024**2/3600) * duration ) # in bytes. The basic overhead is 1Mb per hour (really a random value). Some multiplier (containerfactor) is needed for tuning.
        # check if target size is smaller than audio size
        audiosize = duration * (audiobps/8) # bytes
        if targetsize <= ( audiosize + mp4overhead ):
            if sizein == 'B':
                errsize = math.ceil( audiosize + mp4overhead )
            elif sizein == 'Kb':
                errsize = math.ceil( (audiosize + mp4overhead) / 1024 )
            elif sizein == 'Mb':
                errsize = math.ceil(( audiosize + mp4overhead) / 1024**2 )
            elif sizein == 'Gb':
                errsize = math.ceil( (audiosize + mp4overhead) / 1024**3 )
            print("TARGET SIZE IS TOO SMALL!\nAudio track size: ~{asize} {sizein} with {audiokbps} kbps. \nTry target size {errsize} {sizein}. Increase it if an encoding error appears.".format(asize=errsize-1, audiokbps=math.ceil(audiobps/1000), errsize=errsize, sizein=sizein))
            sys.exit(1)

        # calculate bitrate
        videobps = math.floor( ( (targetsize - mp4overhead) * 8 / duration ) - math.floor(audiobps) )
        infotargetsize = targetsize / 1024 # Kb
        infovideosize = (videobps / (8 * 1024) ) * duration # Kb
        infomp4overhead = mp4overhead /  1024 # Kb
        infoaudiosize = (audiobps / (8 * 1024)) * duration # Kb
        print("Duration: {duration}\nTarget size: {targetsize} Kb\nVideo size: {videosize} Kb\nAudio size: {audiosize} Kb\nMP4 Overhead: {mp4overhead} Kb".format(duration=duration, targetsize=infotargetsize, videosize=infovideosize, audiosize=infoaudiosize, mp4overhead=infomp4overhead))
        ffmpeglogname = 'tmp-passlogfile-{}'.format(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
        # pass 1
        cmd = [self.bins['ffmpeg']
             , '-y'
             , '-i'
             , infile
             , '-c:v'
             , 'libx264'
             , '-b:v'
             , '{}k'.format(str(math.floor(videobps/1000)))
             , '-pass'
             , '1'
             , '-passlogfile'
             , ffmpeglogname
             , '-f'
             , 'mp4'
             , devnull]
        subprocess.Popen(cmd).communicate()
        # pass 2
        cmd = [self.bins['ffmpeg']
            , '-y' 
            , '-i'
             , infile
             , '-c:v'
             , 'libx264'
             , '-b:v'
             , '{}k'.format(str(math.floor(videobps/1000)))
             , '-pass'
             , '2'
             , '-passlogfile'
             , ffmpeglogname
             , '-c:a'
             , 'aac'
             , '-b:a'
             , '{}k'.format(str(math.floor(audiobps/1000)))
             , outfile]
        subprocess.Popen(cmd).communicate()

        try:
            os.remove("{}-0.log.mbtree".format(ffmpeglogname))
        except OSError:
            pass
        try:
            os.remove("{}-0.log".format(ffmpeglogname))
        except OSError:
            pass

    # --------------------------------------------
    def resize_single_video(self, infile: str, scale=None, resolution=None, quality=22, outfile='outfile.mp4'):
        if scale is None and resolution is None: return

        if scale is not None:
            scale = float(scale)
            width, height = self._get_resolution(infile)
            newwidth = int(width * scale)
            newheight = int(height * scale)
        elif resolution is not None:
            newwidth, newheight = resolution.split('x')
            newwidth = int(newwidth)
            newheight = int(newheight)
        
        newwidth = self._lead_to_divisibility_by_2(newwidth)
        newheight = self._lead_to_divisibility_by_2(newheight)

        # convert resolution
        cmd = [
            self.bins['ffmpeg']
            , '-i', infile
            , '-vf', 'scale={}:{}, setsar=1:1'.format(newwidth, newheight)
            ]
        cmd += self._get_h264settings(quality)
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def cut_single_video(self, infile: str, startpoint='-1', endpoint='-1', quality=22, outfile='outfile.mp4'):
        if startpoint == '-1' and endpoint == '-1': return

        cmd = [
            self.bins['ffmpeg']
            , '-i', infile
            ]
        if startpoint != '-1': cmd += ['-ss', startpoint]
        if endpoint != '-1':   cmd += ['-to', endpoint]

        cmd += self._get_h264settings(quality)
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def split_video(self, infile, time='0', chunks=0, quality=22) -> None:
        '''time in seconds (also in 1m/1h format)'''
        if chunks == 0 and time == '0': return

        infilebasename = os.path.basename(infile)
        outfile = '{}.split_%03d.mp4'.format(os.path.splitext(infilebasename)[0])

        cmd = [
            self.bins['ffmpeg']
            , '-i', infile
            ]

        if chunks != 0:
            pass
        elif time != '0':
            if time.endswith('m'):
                try:
                    time = int(time[:-1]) * 60
                except Exception as e:
                    print('{}\n\nUse time format: 1 - 1 sec, 1m - 1 min, 1h - 1 hour.'.format(e))
            elif time.endswith('h'):
                try:
                    time = int(time[:-1]) * 60 * 60
                except Exception as e:
                    print('{}\n\nUse time format: 1 - 1 sec, 1m - 1 min, 1h - 1 hour.'.format(e))
            else:
                time = int(time)

            cmd += [
                '-f', 'segment'
                , '-reset_timestamps', '1'
                , '-map', '0'
                , '-segment_time', str(time)
                ]

        cmd += self._get_h264settings(quality)
        cmd += ['-sc_threshold', '0']
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_gif(self, infile, fps, outfile='outfile.gif'):
        cmd = [
            self.bins['ffmpeg']
            , '-i', infile
            ]
        cmd += [
            '-vf', 'fps={},split[s0][s1];[s0]palettegen=stats_mode=single[p];[s1][p]paletteuse'.format(fps)
            , '-loop', '0'
            ]
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_webm(self, infile, quality=31, outfile='outfile.webm'):

        # check video codec
        cmdpv = [
            self.bins['ffprobe']
            , '-v', 'error'
            , '-select_streams', 'v:0'
            , '-show_entries', 'stream=codec_name'
            , '-of', 'default=noprint_wrappers=1:nokey=1'
            , infile
            ]
        out, err = subprocess.Popen(cmdpv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()

        if out.strip() == 'vp8':
            print('"{}" is already webm, skipped.'.format(infile))
            return

        # check if audio exists
        cmdpa = [
            self.bins['ffprobe']
            , '-i', infile
            , '-show_streams'
            , '-select_streams', 'a'
            , '-loglevel', 'error'
            ]
        out, err = subprocess.Popen(cmdpa, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        audioparams = []
        if len(out.strip()) > 1:  audioparams = ['-c:a', 'libvorbis']

        cmd = [
            self.bins['ffmpeg']
            , '-i', infile
            ]
        cmd += audioparams
        cmd += [
            '-c:v', 'libvpx-vp9'
            , '-row-mt', '1'
            , '-crf', str(quality)
            , '-b:v', '20M'
            , '-auto-alt-ref', '0'
            ]
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_x264(self, infile, quality=22, outfile='outfile.mp4'):

        # check video codec
        cmd = [
            self.bins['ffprobe']
            , '-v', 'error'
            , '-select_streams', 'v:0'
            , '-show_entries', 'stream=codec_name'
            , '-of', 'default=noprint_wrappers=1:nokey=1'
            , infile
            ]
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()

        if out.strip() == 'h264':
            print('"{}" is already h264, skipped.'.format(infile))
            return

        inwidth, inheight = self._get_resolution(infile)
        outwidth = self._lead_to_divisibility_by_2(inwidth)
        outheight = self._lead_to_divisibility_by_2(inheight)
        cmd = [
            self.bins['ffmpeg']
            , '-i', infile
            ]
        if inwidth != outwidth or inheight != outheight: cmd += ['-vf', 'scale={}:{}, setsar=1:1'.format(outwidth, outheight)]
        cmd += self._get_h264settings(quality)
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()

    # --------------------------------------------
    def convert_to_mp3(self, infile, track=0, quality=4, outfile='outfile.mp3'):
        cmd = [
            self.bins['ffmpeg']
            , '-i', infile]
        cmd += [
            '-map', '0:a:{}'.format(track)
            , '-c:a', 'libmp3lame'
            , '-q:a', str(quality)
            , '-ar', '48000'
            ]
        cmd += [outfile]
        subprocess.Popen(cmd).communicate()


if __name__ == '__main__':
    ver = '1.5.2'
    H264CRF = 22
    VP9CRF = 30
    LAMEQUAL = 4
    parser = argparse.ArgumentParser(description='%(prog)s - is a ffmpeg/ffprobe wrapper. https://github.com/qiwichupa/ffeasytool')
    subparser = parser.add_subparsers(title='COMMANDS', dest='command', required=True, help='''Check "%(prog)s COMMAND -h" for additional help''')
    compress = subparser.add_parser('compress', help='''compress single video to size. Ex.: "%(prog)s compress -s 8M myvideo.mp4"''')
    cut = subparser.add_parser('cut', help='''cut single video. Use -a and(or) -b parameters as  start and end points. Ex.: "%(prog)s cut -a 01:05 -b 02:53 myvideo.mp4" ''')
    merge = subparser.add_parser('merge', help='''merge video files. Ex.: "%(prog)s merge -f 1280x720 *.mp4" ''')
    resize = subparser.add_parser('resize', help='''resize single video. Ex.: "%(prog)s resize -m 0.5 myvideo.mp4",  "%(prog)s resize -r 1280x720 myvideo.mp4"''')
    split = subparser.add_parser('split', help='''split single video. Ex.: "%(prog)s split -t 5m myvideo.mp4" ''')
    to264 = subparser.add_parser('to264', help='''convert file(s) to mp4/h264. Ex.: "%(prog)s to264 *.wmv" ''')
    togif = subparser.add_parser('togif', help='''convert file(s) to gif. Ex.: "%(prog)s togif -x 5 *.mp4" ''')
    tomp3 = subparser.add_parser('tomp3', help='''extract audio to mp3. Ex.: "%(prog)s tomp3 -t 2 *.mp4" ''')
    towebm = subparser.add_parser('towebm', help='''convert file(s) to webm/vp9. Ex.: "%(prog)s towebm *.mp4" ''')
    version = subparser.add_parser('version', help='''show version''')

    merge.add_argument('-f', type=str, required=True, metavar='1280x720[@30]', help='output video format')
    merge.add_argument('-q', type=int, default=H264CRF, metavar='{}'.format(H264CRF), help='quality from 51 (worst), to 0 (best). Recommended: 28-17. Default: {}'.format(H264CRF))
    merge.add_argument('file', nargs='+', help='filenames (space-separated) or name with wildcards')

    compress.add_argument('-s', type=str,required=True, metavar='2M', help='target size (in bytes by default). Ex.: 1024, 512K, 2M, 1G')
    compress.add_argument('-a', type=int, metavar='128', help='audio bitrate in kbps. By default it is taken from the source file.')
    compress.add_argument('file', nargs='+', help='filename(s) (space-separated) or name with wildcards')

    resizegroup = resize.add_mutually_exclusive_group(required=True)
    resizegroup.add_argument('-m', type=float, default=1, metavar='1.5', help='multiplier. Ex.: 0.5, 2, 3.4, etc.')
    resizegroup.add_argument('-r', type=str, default=None, metavar='1280x720', help='resolution')
    resize.add_argument('-q', type=int, default=H264CRF, metavar='{}'.format(H264CRF), help='quality from 51 (worst), to 0 (best). Recommended: 28-17. Default: {}'.format(H264CRF))
    resize.add_argument('file', nargs=1, help='filename')

    cut.add_argument('-a', type=str, default='-1', metavar='[HH:][MM:]SS[.mmm]', help='start point. Ex.: 50:05.600 (50 min, 5 sec, 600 ms)')
    cut.add_argument('-b', type=str, default='-1', metavar='[HH:][MM:]SS[.mmm]', help='end point. Ex.: 01:05:00 (1 hour, 5 min)')
    cut.add_argument('-q', type=int, default=H264CRF, metavar='{}'.format(H264CRF), help='quality from 51 (worst), to 0 (best). Recommended: 28-17. Default: {}'.format(H264CRF))
    cut.add_argument('file', nargs=1, help='filename')

    split.add_argument('-t', type=str, required=True, metavar='20m', help='chunks length (in sec by default). Ex.: 15, 2m, 1h')
    split.add_argument('-q', type=int, default=H264CRF, metavar='{}'.format(H264CRF), help='quality from 51 (worst), to 0 (best). Recommended: 28-17. Default: {}'.format(H264CRF))
    split.add_argument('file', nargs=1, help='filename')

    togif.add_argument('-x', type=int, default=10, metavar='10', help='framerate for gif (default: 10)')
    togif.add_argument('file', nargs='+', help='filename(s) (space-separated) or name with wildcards')

    to264.add_argument('-q', type=int, default=H264CRF, metavar='{}'.format(H264CRF), help='quality from 51 (worst), to 0 (best). Recommended: 28-17. Default: {}'.format(H264CRF))
    to264.add_argument('file', nargs='+', help='filename(s) (space-separated) or name with wildcards')

    towebm.add_argument('-q', type=int, default=VP9CRF, metavar='{}'.format(VP9CRF), help='quality from 63 (worst), to 0 (best). Recommended: 35-15. Default: {}'.format(VP9CRF))
    towebm.add_argument('file', nargs='+', help='filename(s) (space-separated) or name with wildcards')

    tomp3.add_argument('-t', type=int, default=1, metavar='1', help='track number (default: 1)')
    tomp3.add_argument('-q', type=int, default=LAMEQUAL, metavar='{}'.format(LAMEQUAL), help='quality from 9 (worst), to 0 (best).  Default: {}'.format(LAMEQUAL))
    tomp3.add_argument('file', nargs='+', help='filename(s) (space-separated) or name with wildcards.')

    args = parser.parse_args()

    # some fuckup with code: two 'videotool = VideoTool()' - here and later
    # The VideoTool class checks for ffmpeg executables and
    # calls sys.exit() if they are not found. So, to display the version of this script,
    # if ffmpeg is not installed, an instance of the VideoTool class must be created AFTER printing the version.
    if args.command == 'version':
        print('ffeasytool: {}'.format(ver))
        videotool = VideoTool()
        binsinfo = videotool.show_versions()
        print('ffmpeg ({}): {}\nffprobe ({}): {}'.format(binsinfo[0], binsinfo[1],binsinfo[2],binsinfo[3]))
        sys.exit()

    # correct method to parse filenames with wildcards:
    # wildcards will be converted to filenames by shell in linux,
    # but not in windows. So we set  "nargs='+'" in argparse argument and...
    # ... if we have a list of filenames (maybe converted from wildcards by shell):
    if len(args.file) > 1 and args.command != 'version':
        files = sorted(args.file)
    # ... if argument is a one filename (or filename with wildcards in windows)
    elif len(args.file) == 1 and args.command != 'version':
        files = sorted(glob.glob(args.file[0]))

    videotool = VideoTool() # this instance is created AFTER the "version" command (see comment before "version")
    if args.command == 'resize':
        infile = files[0]
        infilebasename = os.path.basename(infile)
        outfile = '{}_resized.mp4'.format(os.path.splitext(infilebasename)[0])
        if args.m != 1:
            videotool.resize_single_video(infile=infile, scale=args.m, quality=args.q, outfile=outfile)
        elif args.r:
            videotool.resize_single_video(infile=infile, resolution=args.r, quality=args.q, outfile=outfile)
    elif args.command == 'compress':
        infile = files[0]
        infilebasename = os.path.basename(infile)
        outfile = '{}_compressed_{}.mp4'.format(os.path.splitext(infilebasename)[0], args.s)
        if args.a:
            videotool.compress_single_video(infile=infile, targetsize=args.s, audiobitrate=args.a, outfile=outfile)
        else:
            videotool.compress_single_video(infile=infile, targetsize=args.s, outfile=outfile)
    elif args.command == 'split':
        infile = files[0]
        infilebasename = os.path.basename(infile)
        videotool.split_video(infile=infile, time=args.t, quality=args.q)
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
            videotool.convert_to_x264(infile=infile, quality=args.q, outfile=outfile)
    elif args.command == 'towebm':
        for infile in files:
            infilebasename = os.path.basename(infile)
            outfile = '{}.webm'.format(os.path.splitext(infilebasename)[0])
            videotool.convert_to_webm(infile=infile, quality=args.q, outfile=outfile)
    elif args.command == 'cut':
        infile = files[0]
        infilebasename = os.path.basename(infile)
        outfile = '{}_cut.mp4'.format(os.path.splitext(infilebasename)[0])
        if args.a == -1 and args.b == -1:
            print('use -a and(or) -b')
        else:
            videotool.cut_single_video(infile=infile, startpoint=args.a, endpoint=args.b, quality=args.q, outfile=outfile)
    elif args.command == 'tomp3':
        tracknum = args.t - 1
        for infile in files:
            infilebasename = os.path.basename(infile)
            outfile = '{}.mp3'.format(os.path.splitext(infilebasename)[0])
            videotool.convert_to_mp3(infile=infile, track=tracknum, quality=args.q, outfile=outfile)
    elif args.command == 'merge':
        filestomerge = files
        resolution, *fps = args.f.split('@')
        if len(fps) < 1:
            fps = 30
        else:
            fps = int(fps[0])
        width, height = resolution.split('x')
        videotool.avmerge(filestomerge, int(width), int(height), int(fps), quality=args.q, outfile='outfile_merged.mp4')
