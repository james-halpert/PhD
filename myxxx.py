import requests
import m3u8
import os
import subprocess
from urllib.parse import urljoin

def download_hls_segments(hls_url, output_folder, timeout=10):
    # Step 1: Retrieve HLS Playlist
    response = requests.get(hls_url)
    if response.status_code != 200:
        print(f"Failed to retrieve HLS playlist. Status Code: {response.status_code}")
        return []

    # Step 2: Parse HLS Playlist
    playlist = m3u8.loads(response.text)
    base_url = playlist.base_uri if playlist.base_uri else hls_url.rsplit('/', 1)[0]
    segment_urls = [urljoin(base_url + '/', segment.uri) for segment in playlist.segments]

    # Step 3: Download HLS Segments with timeout
    downloaded_files = []
    for i, segment_url in enumerate(segment_urls):
        segment_file = f"{output_folder}/seg-{i + 1}.ts"
        try:
            response = requests.get(segment_url, timeout=timeout)
            if response.status_code == 200:
                with open(segment_file, "wb") as file:
                    file.write(response.content)
                downloaded_files.append(segment_file)
                print(f"Downloaded segment {i + 1}: {segment_file}")
            else:
                print(f"Failed to download segment {i + 1}. Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Timeout or error downloading segment {i + 1}: {e}")

    return downloaded_files

def combine_segments(segment_files, output_folder, output_filename):
    if not segment_files:
        print("No segments downloaded successfully. Exiting.")
        return

    # Construct the FFmpeg command
    output_file = f"{output_folder}/{output_filename}.mp4"
    segment_list = '|'.join(segment_files)
    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Overwrite existing file without asking
        "-i", f"concat:{segment_list}",
        "-c", "copy",
        output_file
    ]

    # Print the FFmpeg command
    print(" ".join(ffmpeg_command))

    # Run the FFmpeg command
    subprocess.run(ffmpeg_command)

    # Remove individual segments
    for segment_file in segment_files:
        if os.path.exists(segment_file):
            os.remove(segment_file)
            print(f"Removed segment file: {segment_file}")

    print(f"Combined segments into: {output_file}")

def move_output_file(source_path, destination_folder):
    # Ensure the destination folder exists
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Construct the destination path
    destination_path = os.path.join(destination_folder, os.path.basename(source_path))

    # Use subprocess to move the file, mimicking the `mv` command
    try:
        subprocess.run(["mv", source_path, destination_path], check=True)
        print(f"Moved final output file to: {destination_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to move file: {e}")

# Main logic
hls_url = input("Enter the HLS URL: ")
output_folder = "downloaded_segments"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

output_filename = input("Enter the output filename (without extension): ")

# Download HLS segments with timeout
downloaded_files = download_hls_segments(hls_url, output_folder)

# Combine segments using FFmpeg
combine_segments(downloaded_files, output_folder, output_filename)

# Move the final output file to the desired folder
move_output_file(f"{output_folder}/{output_filename}.mp4", "/media/tings")
