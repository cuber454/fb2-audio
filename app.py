import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import zipfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# --- КОНФИГУРАЦИЯ ---
API_URL = "https://api.teamsp.org/others/1.php"
API_KEY = "hxe4qaKDAQWhYXWQEE"
VOICE_ID = "OxtnTByceklF3rlnCNqe" 
MAX_CHARS = 900 

st.set_page_config(page_title="ТЕСТ СКОРОСТИ", page_icon="🧪")
st.title("🧪 ТЕСТ: Первые 5 фрагментов")

def parse_fb2_simple(uploaded_file):
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        paragraphs = ["".join(p.itertext()).strip() for p in root.iter() if p.tag.endswith('p')]
        return [p for p in paragraphs if len(p) > 5]
    except: return []

def download_audio(text, filename):
    url = f"{API_URL}?voice={VOICE_ID}&text={quote(text)}&key={API_KEY}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 100:
            with open(filename, "wb") as f: f.write(r.content)
            return filename
    except: pass
    return None

uploaded_file = st.file_uploader("Загрузите FB2 для теста", type="fb2")

if uploaded_file:
    if st.button("Начать быстрый тест"):
        temp_dir = "test_files"
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        all_text = parse_fb2_simple(uploaded_file)
        full_str = " ".join(all_text)
        fragments = [full_str[i:i+MAX_CHARS] for i in range(0, len(full_str), MAX_CHARS)][:5]
        
        st.info(f"Загружаю {len(fragments)} фрагментов...")
        downloaded = []
        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = {ex.submit(download_audio, t, os.path.join(temp_dir, f"part_{i:03d}.mp3")): i for i, t in enumerate(fragments)}
            for f in as_completed(futures):
                res = f.result()
                if res: downloaded.append(res)
        
        if downloaded:
            downloaded.sort()
            zip_name = "test_result.zip"
            with zipfile.ZipFile(zip_name, "w") as z:
                for f in downloaded: z.write(f, os.path.basename(f))
            st.success("Готово! Проверьте архив.")
            with open(zip_name, "rb") as f:
                st.download_button("📥 Скачать ZIP", f, file_name=zip_name)
