import requests
import concurrent.futures
from bs4 import BeautifulSoup
import os
import urllib.parse
from tqdm import tqdm

# Directory to save downloaded files
DOWNLOAD_DIR = './downloads'

# Create directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Function to extract and download the file
def download_file(link):
    try:
        # Get the HTML content of the page
        response = requests.get(link)
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the 'script' tag containing the download function
        scripts = soup.find_all('script')
        download_url = None

        # Extract the download URL from the 'window.open' statement
        for script in scripts:
            if script.string and 'window.open' in script.string:
                start_index = script.string.find('window.open("') + len('window.open("')
                end_index = script.string.find('"', start_index)
                download_url = script.string[start_index:end_index]
                break

        if download_url:
            # Request the file
            file_response = requests.get(download_url, stream=True)
            file_response.raise_for_status()

            # Extract the filename from the Content-Disposition header
            filename = None
            if 'Content-Disposition' in file_response.headers:
                content_disposition = file_response.headers['Content-Disposition']
                if "filename*=" in content_disposition:
                    filename = content_disposition.split("filename*=")[1].split("''")[1]
                    filename = urllib.parse.unquote(filename)
                elif "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('\"')

            # Fallback to the last part of the URL if filename is not found
            if not filename:
                filename = download_url.split('/')[-1]

            # Save the file with progress tracking
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            total_size = int(file_response.headers.get('content-length', 0))
            block_size = 1024  # 1 KB
            
            with open(file_path, 'wb') as f, tqdm(
                total=total_size, unit='B', unit_scale=True, desc=filename, ncols=100
            ) as progress_bar:
                for chunk in file_response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))

            print(f"Downloaded: {file_path}")
        else:
            print(f"Download URL not found for {link}")

    except Exception as e:
        print(f"Failed to download from {link}: {e}")

# Main function to download files in parallel
def download_files_in_parallel(links, max_workers=5):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(download_file, links)

if __name__ == "__main__":
    # Read the links from links.txt
    try:
        with open('links.txt', 'r') as file:
            links = [line.strip() for line in file.readlines() if line.strip()]
        
        if links:
            # Start downloading files in parallel
            download_files_in_parallel(links)
        else:
            print("No links found in links.txt")
    except FileNotFoundError:
        print("links.txt file not found.")
