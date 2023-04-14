import requests
import os

list_yt_urls = [
    'https://www.youtube.com/watch?v=f7KCt8Qj5j0',
    'https://www.youtube.com/watch?v=NEtZYbKwP1A',
    'https://www.youtube.com/watch?v=T9WbLIAgZo0'
]

overlay_file_path = 'C:\\Users\\nchaudhary\\Desktop\\AmagiApp\\overlay.png'
video_resolution = '1280x720'
url = 'http://localhost:8888/overlay-stitching'

for youtube_url in list_yt_urls:
    data = {'url': youtube_url, 'video_resolution': video_resolution, 'overlay_file': overlay_file_path}
    response = requests.post(url, data=data)
    print(response.json())
