from glob import glob, escape as glob_escape
from tkinter.filedialog import askdirectory
from os.path import split as split_path, join as join_path, basename, splitext
from os import remove

from multiprocessing import Pool
import logging
import ffmpeg

def get_dir(initial_folder='.'):
  title = 'Selecione a pasta raiz:'
  dir = askdirectory(title=title, mustexist=True, initialdir=initial_folder)
  return dir

def compare_files(f1, f2):
  f1_name, _ = splitext(basename(f1))
  f2_name, _ = splitext(basename(f2))
  return f1_name == f2_name




def get_files(root_folder:str, ext='.mp4'):
  subdirs = glob(f'{root_folder}/**/', recursive=True)

  files = []
  for subdir in subdirs:
    subdir = glob_escape(subdir)
    vid_regex = join_path(subdir, f'*{ext}')
    videos = glob(vid_regex, recursive=True)

    srt_regex = join_path(subdir, '*.srt')
    srts = glob(srt_regex, recursive=True)

    if len(videos) > 1 or len(srts) > 1:
      paired_files = []
      for vid in videos:
        for sub in srts:
          if compare_files(vid, sub):
            paired_files.append( (vid, sub) )
            break
      
      #paired_files = [(vid, sub) for vid in videos for sub in srts if compare_files(vid, sub)]
      if len(paired_files) > 0:
        files.extend(paired_files)
      
    elif len(videos) == len(srts) == 1:
      vid = videos.pop()
      srt = srts.pop()
    
      files.append( (vid, srt) )
  return files

def rip_subtitles(files):
  mp4_path, srt_path = files

  srt, _ = splitext(srt_path)
  srt_content = open(srt_path, encoding='latin-1').read()

  srt_content = srt_content.encode('utf-8')
  tmp_utf8_srt = f'{srt}_utf8.srt'
  open(tmp_utf8_srt, 'wb').write(srt_content)
  

  output, ext = splitext(mp4_path)
  output += '_legendado' + ext

  vid_stream = ffmpeg.input(mp4_path).video
  audio_stream = ffmpeg.input(mp4_path).audio
  subtitled_vid_stream = vid_stream.filter('subtitles', tmp_utf8_srt)
  ffmpeg.output(subtitled_vid_stream, audio_stream, output).run()
  remove(tmp_utf8_srt)

def main(max_threads=5):
  dir = get_dir()
  files = get_files(dir)
  thread_qnty = min(max_threads, len(files))
  with Pool(thread_qnty) as pool:
    pool.map(rip_subtitles, files)

if __name__ == '__main__':
  main()