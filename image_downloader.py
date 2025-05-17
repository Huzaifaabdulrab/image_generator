import os
import requests
from datetime import datetime
import streamlit as st

DOWNLOAD_FOLDER = "downloaded_images"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

class ImageDownloader:
    def __init__(self, api_key):
        self.api_key = api_key
        self.folder = DOWNLOAD_FOLDER

    def download_images(self, query):
        url = f"https://api.unsplash.com/search/photos?query={query}&page=1&per_page=1&client_id={self.api_key}"
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Unsplash API error: {response.text}")
            return None
        data = response.json()
        results = data.get("results", [])
        if not results:
            st.error("No images found for this query.")
            return None
        
        image_url = results[0]["urls"]["regular"]
        safe_query = "".join(x for x in query if x.isalnum() or x in (" ", "_")).rstrip()
        file_path = os.path.join(self.folder, f"{safe_query}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        img_data = requests.get(image_url).content
        with open(file_path, "wb") as handler:
            handler.write(img_data)
        return file_path
