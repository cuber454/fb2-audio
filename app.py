import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import zipfile
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

# --- КОНФИГУРАЦИЯ ---
API_URL = "https://api.teamsp.org/others/1.php"
API_KEY = "hxe4qaKDAQWhYXWQEE"
VOICE_ID = "OxtnTByceklF3rlnCNqe" 
MAX_CHARS = 900 

st.set_page_config(page_title="FB2 Audio Maker", page_icon="🎙️")
st.title("🎙️ FB2 в Аудиокнигу")
st.write("Загрузите книгу, и я превращу её в архив с MP3-главами.")

def parse_fb2_universal(uploaded_file):
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        chapters = []
        sections = root.findall(".//{http://www.gribuser.ru/xml/fictionbook/2.0}section") or root.findall(".//section")
        
        if sections:
            for idx, sec in enumerate(sections, 1):
                title_elem = sec.find(".//{http://www.gribuser.ru/xml/fictionbook/2.0}title") or sec.find(".//title")
                title = "".join(title_elem.itertext()).strip() if title_elem is not None else f"Глава {idx}"
                paragraphs = ["".join(p.itertext()).strip() for p in (sec.findall(".//{http://www.gribuser.ru/xml/fictionbook/2.0}p") or sec.findall(".//p"))]
                paragraphs = [p for p in paragraphs if len(p) > 2]
                if paragraphs:
                    chapters.append({"title": title, "paragraphs": paragraphs})
        
        if not chapters:
            paragraphs = ["".join(p.itertext()).strip() for p in root.iter() if p.tag.endswith('p')]
            paragraphs = [p for p in paragraphs if len(p) > 2]
            if paragraphs:
                chapters.append({"title": "Книга целиком", "paragraphs": paragraphs})
        return chapters
    except:
        return []

def download_audio(text, filename):
    url = f"{API_URL}?voice={VOICE_ID}&text={quote(text)}&key={API_KEY}"
    try:
        r = requests.get(url, timeout=45)
        if r.status_code == 200 and len(r.content) > 100:
            with open(filename, "wb") as f:
                f.write(r.content)
            return filename
    except:
        pass
    return None

# --- ИНТЕРФЕЙС ---
uploaded_file = st.file_uploader("Выберите файл FB2", type="fb2")

if uploaded_file:
    if st.button("Начать озвучку"):
        book_name = os.path.splitext(uploaded_file.name)[0]
        work_dir, temp_dir = "audio_out", "temp_frags"
        
        for d in [work_dir, temp_dir]:
            if os.path.exists(d): shutil.rmtree(d)
            os.makedirs(d)

        chapters = parse_fb2_universal(uploaded_file)
        
        if not chapters:
            st.error("Текст не найден!")
        else:
            st.info(f"Найдено глав: {len(chapters)}. Обработка запущена...")
            progress_bar = st.progress(0)
            
            chapter_files = []
            for idx, ch in enumerate(chapters, 1):
                full_text = " ".join(ch["paragraphs"])
                fragments = [full_text[i:i+MAX_CHARS] for i in range(0, len(full_text), MAX_CHARS)]
                
                downloaded = []
                with ThreadPoolExecutor(max_workers=10) as ex:
                    futures = {ex.submit(download_audio, t, os.path.join(temp_dir, f"ch{idx}_f{i:04d}.mp3")): i for i, t in enumerate(fragments)}
                    for f in as_completed(futures):
                        res = f.result()
                        if res: downloaded.append(res)
                
                downloaded.sort()
                if downloaded:
                    ch_path = os.path.join(work_dir, f"Chapter_{idx:03d}.mp3")
                    with open("list.txt", "w") as f:
                        for d_file in downloaded: f.write(f"file '{os.path.abspath(d_file)}'\n")
                    
                    subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "-y", ch_path])
                    for d_file in downloaded: os.remove(d_file)
                    chapter_files.append(ch_path)
                
                progress_bar.progress(idx / len(chapters))

            # ZIP
            zip_name = f"{book_name}.zip"
            with zipfile.ZipFile(zip_name, "w") as z:
                for f in chapter_files:
                    z.write(f, os.path.basename(f))
            
            st.success("Готово!")
            with open(zip_name, "rb") as f:
                st.download_button("📥 Скачать архив", f, file_name=zip_name)