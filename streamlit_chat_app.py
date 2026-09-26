# Import library yang dibutuhkan
import streamlit as st          # framework web app
from google import genai         # SDK Gemini dari Google
from google.genai import types

# ── 1. Konfigurasi Halaman Streamlit ──────────────────────────────────────────
st.set_page_config(page_title="AI EduTutor", page_icon="🎓", layout="wide")

st.title("🎓 AI EduTutor — Chatbot Edukasi Cerdas bySyaviri 🤖 ")
st.caption("Belajar interaktif dengan dukungan Asisten Belajar Cerdas & Interaktif Terintegrasi Gemini AI")

# ---- custimize tampilan chatbot -----
st.markdown("""
<style>
    /* 1. Background Aplikasi */
    .stApp {
        background-color: #4682B4;
    }
    
    /* 2. Kustomisasi Bubble Chat User */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #20B2AA;
        border-radius: 15px 15px 2px 15px;
        padding: 10px 15px;
        border: 1px solid #20B2AA;
    }
    
    /* 3. Kustomisasi Bubble Chat Assistant (Bot) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #E0FFFF;
        border-radius: 15px 15px 15px 2px;
        padding: 10px 15px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #778899;
    }

    /* 4. mempercantik Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFF5EE;
        border-right: 1px solid #778899;
    }

    /* 5. Efek Tombol */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        background-color: #87CEFA;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #45a049;
        border-color: #FFFFE0;
    }
</style>
""", unsafe_allow_html=True)

# ── 2. Sidebar: Pengaturan App & Modus ───────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    google_api_key = st.text_input("Google AI API Key", type="password")
    
    st.subheader("🎭 Persona & Gaya Bahasa")
    persona = st.radio(
        "Pilih Gaya Bahasa:",
        options=["santai", "formal"],
        format_func=lambda x: "😎 Santai & Friendly" if x == "santai" else "👔 Formal & Akademis"
    )
    
       
    reset_button = st.button("🗑️ Reset Percakapan", help="Hapus seluruh riwayat chat")

# ── 3. Validasi API Key ──────────────────────────────────────────────────────
if not google_api_key:
    st.info("Silakan masukkan **Google AI API Key** di sidebar untuk mulai menggunakan chatbot.", icon="🗝️")
    st.stop()

# ── 4. Inisialisasi Gemini Client & Detection Perubahan ──────────────────────
# Buat/perbarui client jika API Key berubah
if ("genai_client" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        st.session_state.genai_client = genai.Client(api_key=google_api_key)
        st.session_state._last_key = google_api_key
        st.session_state.pop("chat", None)
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"API Key tidak valid: {e}")
        st.stop()

# Re-inisialisasi chat session jika persona atau fitur search diubah oleh user
session_params = (persona)
if ("last_params" not in st.session_state) or (st.session_state.last_params != session_params):
    st.session_state.pop("chat", None)
    st.session_state.last_params = session_params

# ── 5. Inisialisasi Chat Session & Memory ────────────────────────────────────
if "chat" not in st.session_state:
    # Membangun System Instruction sesuai persona
    base_instruction = (
        "Kamu adalah Tutor & Edukator Cerdas AI yang sangat membantu. "
        "Tugasmu adalah membantu pengguna belajar berbagai topik (sains, matematika, sejarah, coding, dll)."
    )
    if persona == "formal":
        tone = "\n\nGAYA BAHASA: FORMAL & AKADEMIS. Gunakan Bahasa Indonesia baku, kata sapaan 'Anda', dan penjelasan terstruktur."
    else:
        tone = "\n\nGAYA BAHASA: SANTAI & FRIENDLY. Gunakan kata 'kamu/aku', analogi seru, dan gaya santai seperti teman belajar."

    # Config tanpa tools Google Search
    config = types.GenerateContentConfig(
        system_instruction=base_instruction + tone,
        temperature=0
    )
    
    # Inisialisasi chat session
    st.session_state.chat = st.session_state.genai_client.chats.create(
        model="gemini-3.6-flash",
        config=config
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset Manual
if reset_button:
    st.session_state.pop("chat", None)
    st.session_state.pop("messages", None)
    st.rerun()

# ── 6. Tampilkan Riwayat Percakapan ─────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── 7. Input & Respons Chatbot ───────────────────────────────────────────────
prompt = st.chat_input("Tanyakan materi pelajaran atau ketik 'rekomendasi [topik]'...")

if prompt:
    # 1. Simpan dan tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Cek apakah ini perintah khusus Rekomendasi atau Pertanyaan Biasa
    with st.chat_message("assistant"):
        try:
            # Fitur Khusus: Pemicu Rekomendasi Edukasi
            if prompt.lower().startswith("rekomendasi"):
                topik = prompt[11:].strip()
                if not topik:
                    topik = "umum/materi terkini"
                
                query_prompt = (
                    f"Berikan 3-5 rekomendasi sumber belajar terbaik tentang '{topik}'. "
                    f"Daftar dapat berupa judul buku, channel YouTube, atau website/artikel terpercaya."
                )
                
                with st.spinner(f"Sedang mencari rekomendasi materi untuk {topik}..."):
                    response = st.session_state.chat.send_message(query_prompt)
                    answer = response.text
                    st.markdown(answer)

            # Modus Percakapan Biasa (Streaming dengan Memory)
            else:
                response_stream = st.session_state.chat.send_message_stream(prompt)

                def get_stream_chunks():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text

                answer = st.write_stream(get_stream_chunks())

        except Exception as e:
            answer = f"Terjadi kesalahan: {e}"
            st.error(answer)

    # 3. Simpan jawaban ke riwayat pesan
    st.session_state.messages.append({"role": "assistant", "content": answer})
