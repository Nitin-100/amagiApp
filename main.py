# Author: Nitin Chaudhary
# Email: nitin.karan1990@hotmail.com

import os
import subprocess
from flask import Flask, request, jsonify, g
from pytube import YouTube
from concurrent.futures import ThreadPoolExecutor
import time

app = Flask(__name__)


class OverlayStitchingPipeline:
    input_number = 1  # class variable for internal naming of the downloaded and processed files

    def __init__(self):
        """
            Init the OverlayStitchingPipeline
        """
        self.video_resolution = None
        self.overlay_file = None
        self.project_directory = os.path.dirname(os.path.abspath(__file__))
        self.output_directory = os.path.join(self.project_directory, 'output')
        os.makedirs(self.output_directory, exist_ok=True)
        self.video_name = None

    def set_overlay_file(self, overlay_file):
        """
            Sets the path of the image which needs to be overlayed on the video.
        """
        self.overlay_file = overlay_file

    def set_video_resolution(self, video_resolution):
        """
            Sets the resolution of downloaded video.
            We are downloading 1280x720p for all urls right now.
        """
        self.video_resolution = video_resolution

    def download_video(self, url):
        """
            This function downloads the video from youtube url and save it in "output" folder in project directory.
            It renames the file as Input_"input_number" which keeps on incrementing on each request.
        """
        yt = YouTube(url)
        self.video_name = f"Input_{OverlayStitchingPipeline.input_number}.mp4"
        OverlayStitchingPipeline.input_number += 1
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video.download(self.output_directory, filename=self.video_name)

    def generate_video_chunks(self, chunk_duration):
        """
            This function uses FFMPEG to create the chunks of the downloaded video of specific duration{10,20,40}.
            It saves the chunks in "output"/chunk_Input_"input_number" folder.
            I have added h/w acceleration in FFMpeg command for it.
            Return: It returns the chunk directory towards the stitching overlay function.
        """
        chunks_directory = os.path.join(self.output_directory, f"chunk_{os.path.splitext(self.video_name)[0]}")
        os.makedirs(chunks_directory, exist_ok=True)
        command = f'ffmpeg -hwaccel auto -i "{os.path.join(self.output_directory, self.video_name)}" -c copy -map 0 -segment_time {chunk_duration} -f segment -loglevel debug {os.path.join(chunks_directory, "chunk%03d_output.mp4")}'
        subprocess.call(command, shell=True)

        # Debugging chunk lists
        print(f"Generated chunks in {chunks_directory}:")
        for file in os.listdir(chunks_directory):
            print(file)

        return chunks_directory  # Add this line to return the chunks_directory

    def stitch_overlay_on_chunks(self, input_directory):
        """
            This function uses FFMPEG to stitch an overlay of the png image shared.
            It creates a new folder with overlayed chunks.
            Here I have multithreading stitching , it's using threadpool and max_worker threads 10.
            We can benchmark and adjust the number of max_worker on the basis of machine cores and other parameters.
            returns: It returns overlayed chunks directory.
        """
        overlay_height = 96
        overlay_width = 576
        output_folder = f"{os.path.splitext(self.video_name)[0]}_Overlay_chunks"
        output_directory = os.path.join(self.output_directory, output_folder)
        os.makedirs(output_directory, exist_ok=True)
        futures = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for file in os.listdir(input_directory):
                if file.endswith(".mp4"):
                    input_file = os.path.join(input_directory, file)
                    video_name = os.path.basename(input_file).split(".")[0]
                    output_file = os.path.join(output_directory, f"{video_name}_output.mp4")
                    command = f'ffmpeg -hwaccel auto -loglevel debug -i {input_file} -i {self.overlay_file} -filter_complex "[1:v]scale={overlay_width}:{overlay_height}[ov];[0:v][ov]overlay=(W-{overlay_width})/2:H-h-{overlay_height},format=yuv420p[v]" -map "[v]" -map 0:a -c:a copy -preset veryfast -crf 22 -s {self.video_resolution} {output_file}'
                    futures.append(executor.submit(subprocess.call, command, shell=True))

            for future in futures:
                future.result()
        return output_directory

    def merge_video_chunks(self, input_directory):
        """
            It can merge any number of video chunks.
            For over use case which join the overlay chunks and create a new output video.
            returns: The path of new output video which has the overlay.
        """
        files = os.listdir(input_directory)
        print(input_directory)
        if not files:
            raise Exception("No video chunks found in the input directory")

        video_title = os.path.splitext(os.path.basename(files[0]))[0][6:]
        chunks_file = open(f'{input_directory}/chunks.txt', 'w')

        for file in files:
            if file.startswith("chunk") and file.endswith("_output.mp4"):
                chunks_file.write(f"file '{file}'\n")
        chunks_file.close()

        output_filename = f"{self.output_directory}/{os.path.splitext(self.video_name)[0]}_Overlayed_output.mp4"
        command = f'ffmpeg -f concat -safe 0 -i {input_directory}/chunks.txt -c copy {output_filename}'
        subprocess.call(command, shell=True)
        return output_filename

    def generate_hls_stream(self, input_file):
        """
            This functions creates a TS segments of the final output video with overlay and m3u8 playlist.
            returns: It returns a Hls url.
        """
        video_name = os.path.basename(input_file).split(".")[0]
        ts_directory = os.path.join(self.output_directory, f"{video_name}_ts_files")
        os.makedirs(ts_directory, exist_ok=True)
        command = f'ffmpeg -i {input_file} -codec:v libx264 -codec:a aac -map 0 -f hls -hls_time 4 -hls_playlist_type vod -hls_segment_filename {ts_directory}/{video_name}_%03d.ts {ts_directory}/{video_name}.m3u8'
        subprocess.call(command, shell=True)
        hls_url = f'http://localhost:8888/{video_name}_ts_files/{video_name}.m3u8'
        return hls_url


def run_pipeline(url, video_resolution, overlay_file):
    pipeline = OverlayStitchingPipeline()
    pipeline.set_video_resolution(video_resolution)
    pipeline.set_overlay_file(overlay_file)
    yt = YouTube(url)
    video_title = yt.title
    print(f"Downloading video... '{video_title}'")
    start_time = time.time()
    pipeline.download_video(url)
    print(f"Downloaded video '{video_title}' in {time.time() - start_time:.2f} seconds")
    video_duration = yt.length

    # We can have more heuristic here to decide on the number of chunks
    if video_duration <= 300:
        chunk_duration = 10
    elif 300 < video_duration <= 600:
        chunk_duration = 20
    else:
        chunk_duration = 40

    print("Generating video chunks...'{video_title}'")
    start_time = time.time()
    chunks_directory = pipeline.generate_video_chunks(chunk_duration)
    print(f"Done Generating video chunks... '{video_title}' in {time.time() - start_time:.2f} seconds")

    print("Stitching overlay on chunks...'{video_title}'")
    start_time = time.time()
    overlay_chunk_directory = pipeline.stitch_overlay_on_chunks(chunks_directory)
    print(f"Done Stitching overlay on chunks... '{video_title}' in {time.time() - start_time:.2f} seconds")

    print("Merging video chunks...'{video_title}'")
    start_time = time.time()
    merged_video = pipeline.merge_video_chunks(overlay_chunk_directory)
    print(f"Done Merging video chunks...... '{video_title}' in {time.time() - start_time:.2f} seconds")

    print("Generating HLS stream...'{video_title}'")
    start_time = time.time()
    hls_url = pipeline.generate_hls_stream(merged_video)
    print(f"Done Generating HLS stream...... '{video_title}' in {time.time() - start_time:.2f} seconds")
    return hls_url


executor = ThreadPoolExecutor(max_workers=4)  # Set max_workers as needed


@app.route('/overlay-stitching', methods=['POST'])
def overlay_stitching():
    url = request.form.get('url')
    video_resolution = request.form.get('video_resolution')
    overlay_file = request.form.get('overlay_file')
    future = executor.submit(run_pipeline, url, video_resolution, overlay_file)
    hls_url = future.result()
    return jsonify({'hls_url': hls_url})


if __name__ == '__main__':
    app.run(debug=True, port=8888)
