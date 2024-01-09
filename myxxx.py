import requests
import m3u8
import os
import subprocess
from urllib.parse import urljoin

def download_hls_segments(hls_url, output_folder):
    # Step 1: Retrieve HLS Playlist
    response = requests.get(hls_url)
    if response.status_code != 200:
        print(f"Failed to retrieve HLS playlist. Status Code: {response.status_code}")
        return

    # Step 2: Parse HLS Playlist
    playlist = m3u8.loads(response.text)
    base_url = playlist.base_uri if playlist.base_uri else hls_url.rsplit('/', 1)[0]
    segment_urls = [urljoin(base_url + '/', segment.uri) for segment in playlist.segments]

    # Step 3: Download HLS Segments
    for i, segment_url in enumerate(segment_urls):
        response = requests.get(segment_url)
        if response.status_code == 200:
            segment_file = f"{output_folder}/seg-{i + 1}.ts"
            with open(segment_file, "wb") as file:
                file.write(response.content)
            print(f"Downloaded segment {i + 1}: {segment_file}")
        else:
            print(f"Failed to download segment {i + 1}. Status Code: {response.status_code}")

def combine_segments(segment_files, output_folder, output_filename):
    # Construct the FFmpeg command
    output_file = f"{output_folder}/{output_filename}.mp4"
    ffmpeg_command = [
        "ffmpeg",
        "-i", f"concat:{'|'.join(segment_files)}",
        "-c", "copy",
        output_file
    ]

    # Print the FFmpeg command
    print(" ".join(ffmpeg_command))

    # Run the FFmpeg command
    subprocess.run(ffmpeg_command)

    # Remove individual segments
    for segment_file in segment_files:
        os.remove(segment_file)
        print(f"Removed segment file: {segment_file}")

    print(f"Combined segments into: {output_file}")

# Prompt the user for HLS URL input
hls_url = input("Enter the HLS URL: ")

# Set the output folder
output_folder = "downloaded_segments"

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Prompt the user for output filename input
output_filename = input("Enter the output filename (without extension): ")

# Download HLS segments
download_hls_segments(hls_url, output_folder)

# List all segment files in the output folder
segment_files = [f"{output_folder}/seg-{i + 1}.ts" for i in range(len(os.listdir(output_folder)))]

# Combine segments using FFmpeg and remove individual segments
combine_segments(segment_files, output_folder, output_filename)
