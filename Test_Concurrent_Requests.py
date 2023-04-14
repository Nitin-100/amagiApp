import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

list_yt_urls = [
    'https://www.youtube.com/watch?v=f7KCt8Qj5j0',
    'https://www.youtube.com/watch?v=NEtZYbKwP1A',
    'https://www.youtube.com/watch?v=T9WbLIAgZo0'
]

overlay_file_path = 'C:\\Users\\nchaudhary\\Desktop\\AmagiApp\\overlay.png'
video_resolution = '1280x720'
url = 'http://localhost:8888/overlay-stitching'

def send_request(youtube_url):
    data = {'url': youtube_url, 'video_resolution': video_resolution, 'overlay_file': overlay_file_path}
    response = requests.post(url, data=data)
    return response.json()

with ThreadPoolExecutor() as executor:
    # Submit tasks to the ThreadPoolExecutor
    futures = [executor.submit(send_request, youtube_url) for youtube_url in list_yt_urls]

    # Process completed tasks
    for future in as_completed(futures):
        try:
            result = future.result()
            print(result)
        except Exception as e:
            print(f"An error occurred: {e}")
