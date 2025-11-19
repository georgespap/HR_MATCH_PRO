# -*- coding: utf-8 -*-
""" HR CV Matcher - Batch mode (ΟΛΟΚΛΗΡΩΜΕΝΗ ΚΑΙ ΤΕΛΙΚΗ ΕΚΔΟΣΗ - V121 - FIX: Forced Download Button Uniformity)
@author: g.papadopoulos + updates GPT 
"""
import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer, util
import re
import unicodedata
from io import BytesIO
import spacy
from langdetect import detect
import base64
import zipfile 
import numpy as np 
import math 

# --------------------------------------------------------------------------------------
# --- CUSTOM CSS ΓΙΑ BACKGROUND, ΜΑΥΡΗ ΓΡΑΜΜΑΤΟΣΕΙΡΑ & ΑΝΟΙΧΤΟΤΕΡΑ INPUT FIELDS ---
def get_base64_image(image_path):
    try:
        # Υποθέτουμε ότι το STAR_logo.jpg βρίσκεται στον ίδιο φάκελο
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

# V111: Callback function για Session State
def toggle_show_all():
    """Ενημερώνει τη state για το αν το Top N input πρέπει να είναι disabled."""
    # Αν το checkbox είναι τσεκαρισμένο, το Top N input θα γίνει disabled (True)
    st.session_state['top_n_disabled'] = st.session_state.get('show_all_checkbox_v111', False)


# !!! ΠΡΟΣΟΧΗ: Αν δεν υπάρχει το STAR_logo.jpg στον ίδιο φάκελο, θα εμφανιστεί σφάλμα στην κονσόλα
background_image_path = "STAR_logo.jpg"
encoded_image = get_base64_image(background_image_path)

LIGHT_RED = "#FF6666"
DARKER_GRAY = "#E0E0E0" 

# Ορισμός Flag για να εμφανιστεί το σφάλμα αργότερα (V105 Fix)
background_image_error = False 

if encoded_image:
    # ⚠️ ΔΙΟΡΘΩΣΗ CSS: Μείωση margin στο h3 για μικρότερο διάστημα μεταξύ των ενοτήτων.
    bg_style = f"""
    <style>
    /* Απόκρυψη Streamlit Default Widgets */
    div[data-testid="stStatusWidget"] {{ display: none !important; visibility: hidden !important; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stApp {{ background: none !important; }}
    
    /* Background Image */
    .stApp::before {{ content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-image: url("data:image/jpeg;base64,{encoded_image}"); background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed; z-index: -1; }}
    
    /* Κεντρικό Περιεχόμενο και Sidebar Background */
    /* Αφαιρούμε το padding από το block-container για να φαίνεται η εικόνα σε όλο το πλάτος */
    .main .block-container, [data-testid="stSidebarContent"] {{ background-color: rgba(255, 255, 255, 0.95) !important; border-radius: 5px; }}
    /* Τώρα το padding του block-container επηρεάζει μόνο την κεντρική στήλη, όχι όλο το πλάτος */
    .main .block-container {{ padding: 2rem; margin-top: 1rem; }} 
    
    /* Χρώμα Κειμένου: Μαύρο (Γενικά) */
    .main * {{ color: #000000 !important; opacity: 1 !important; }}
    
    /* ------------------------------ BUTTONS STYLING (General & Download) ------------------------------ */
    
    [data-testid="stFileUploader"] button:not([data-testid="stFileUploaderClearButton"]), 
    [data-testid="baseButton-secondary"] button, 
    .stButton button[kind="primary"], 
    [data-testid="baseButton-primary"] button,
    [data-testid^="stDownloadButton"] button {{ 
        background-color: {LIGHT_RED} !important; 
        border-color: {LIGHT_RED} !important; 
        color: #000000 !important; 
    }}
    
    [data-testid="stFileUploaderClearButton"] {{
        background-color: white !important; 
        border-color: #888888 !important; 
        color: #000000 !important; 
    }}

    [data-testid="stFileUploaderClearButton"] * {{
        color: #000000 !important; 
        fill: #000000 !important; 
        background-color: transparent !important; 
    }}
    
    /* ⚠️ ΔΙΟΡΘΩΣΗ: Εξαναγκασμός ίδιου μεγέθους στα Download Buttons */
    [data-testid^="stDownloadButton"] button {{
        font-size: 0.75em !important; /* Επαναφορά στο 0.75em για καλύτερη ανάγνωση */
        padding: 0.2em 0.8em !important; /* Ίδιο padding για ομοιομορφία */
        line-height: 1 !important; 
        margin: 0 !important; /* Αφαίρεση τυχόν margin από το container */
    }}
    
    [data-testid^="stDownloadButton"] button > span,
    [data-testid^="stDownloadButton"] button:hover > span, 
    [data-testid^="stDownloadButton"] button:focus > span {{
        color: #000000 !important; 
        font-size: 0.75em !important; 
        font-weight: bold !important; 
        line-height: 1 !important; 
        vertical-align: middle !important; 
    }}
    
    [data-testid^="stDownloadButton"] button > div > span:first-child {{
        font-size: 0.75em !important; 
        line-height: 1 !important; 
    }}

    /* --------------------------------------------------------------------------------------------------------- */
    
    .stButton>button {{ color: #000000 !important; }} 
    
    /* V108: Ορισμός γραμματοσειράς για το placeholder */
    .stTextArea textarea::placeholder {{ 
        font-size: 0.85em !important; 
        color: #000000 !important; 
        opacity: 0.5 !important; 
    }}
    
    [data-testid="stFileUploaderFileName"] {{
        background-color: {DARKER_GRAY} !important; 
        border: 1px solid #cccccc !important; 
        border-radius: 0.5rem;
    }}

    [data-testid="stFileUploaderFileName"] *,
    [data-testid="stFileUploaderSizeText"] {{
        color: #000000 !important; 
        opacity: 1 !important;
    }}
    
    .stTextArea textarea, .stTextArea > div > div, [data-testid="stNumberInput"] input, [data-testid="stNumberInput"] > div > div {{ 
        background-color: #F0F0F0 !important; 
        color: #000000 !important; 
        border: 1px solid #cccccc !important; 
    }}

    /* V109 FIX: Όταν το input είναι disabled, το background είναι πιο σκούρο/γκρι*/
    [data-testid="stNumberInput"] input:disabled {{
        background-color: #E9E9E9 !important; 
        color: #666666 !important;
    }}
    [data-testid="stNumberInput"] > div > div:has(input:disabled) {{
        background-color: #E9E9E9 !important;
        cursor: not-allowed;
    }}
    
    [data-testid="stFileUploaderDropzone"], .stSlider > div > div > div, .stSelectbox > div {{ 
        background-color: #F0F0F0 !important; 
        border: 1px solid #cccccc !important; 
    }}


    /* -------------------------------------------------------------- MAIN FONT SIZES -------------------------------------------------------------- */
    h1 {{ font-size: 2.2em !important; }} 
    
    p, span, div, .stMarkdown, .stSelectbox div, .stSlider, label {{ font-size: 1.05em !important; color: #000000 !important; }} 
    
    [data-testid="stAlert"] * {{ 
        font-size: 0.95em !important; 
    }}
    
    /* --------------------- INPUT HEADINGS (small) --------------------- */
    h6 {{
        font-size: 0.7em !important; 
        color: #000000 !important;
        margin-top: 0px !important;
        margin-bottom: 3px !important;
        line-height: 1.2 !important;
    }}

    /* ⚠️ ΔΙΟΡΘΩΣΗ: Μείωση του margin στο h3 για μικρότερο διάστημα μεταξύ των ενοτήτων */
    h3 {{ 
        font-size: 1.2em !important; 
        color: #000000;
        margin-top: 5px !important;    
        margin-bottom: 5px !important; 
    }}

    /* -------------------------------------------------------------- INPUT FIELDS & PLACEHOLDERS -------------------------------------------------------------- */
    .stTextArea textarea, [data-testid="stNumberInput"] input {{ font-size: 0.85em !important; }} 
    
    [data-testid="stSlider"] [data-testid="stNumberInput"] input {{ 
        font-size: 0.85em !important; 
        color: #000000 !important; 
    }} 
    
    /* V104: Διόρθωση επικάλυψης του Value Tooltip με τον τίτλο */
    [data-baseweb="slider"] [role="tooltip"] {{ 
        font-size: 0.7em !important; 
        padding: 2px 5px !important; 
        transform: translateY(-5px) !important; 
        min-width: 25px !important; 
        text-align: center;
    }}

    /* V96: Απόκρυψη των default min/max τιμών (ticks) */
    [data-testid="stSlider"] div[role="slider"] + div > div > span {{
        visibility: hidden !important; 
    }}

    [data-testid="stFileUploaderDropzone"] * {{ font-size: 0.85em !important; }} 

    /* -------------------------------------------------------------- VERY SMALL FONT FOR SPECIFIC INPUTS -------------------------------------------------------------- */
    [data-testid="stFileUploader"] > label, .stTextArea > label, [data-testid="stNumberInput"] > label, [data-testid="stCheckbox"] > label, [data-testid="stSlider"] > label {{ 
        font-size: 0.7em !important; 
        color: #000000 !important; 
    }}

    /* V106: Ο default τίτλος είναι πλέον κενός, οπότε αφαιρούμε το margin-top */
    [data-testid="stSlider"] > label {{
        margin-top: 0px !important; 
    }}

    /* V111: Μείωση του top margin στο number input όταν είναι disabled */
    [data-testid="stNumberInput"] {{
        margin-top: 0px !important; 
    }}
    
    /* V112 FIX: Αυξάνει το μέγεθος του checkbox */
    [data-testid="stCheckbox"] input[type="checkbox"] {{
        transform: scale(1.25); /* Αυξάνει το μέγεθος κατά 25% */
        margin-right: 5px; /* Προσθέτει λίγο χώρο δεξιά */
    }}

    [data-testid="stCheckbox"] label {{
        align-items: center; /* Κεντράρει οριζόντια το κείμενο με το κουμπί */
        margin-top: 0px !important; 
        margin-bottom: 0px !important;
    }}

    /* V111: Ειδική ρύθμιση για το checkbox να είναι κάτω από τον τίτλο */
    /* Δεν μπορούμε να το ελέγξουμε με CSS, οπότε στηριζόμαστε στην τοποθέτηση του κώδικα */
    
    .stButton button, 
    [data-testid="baseButton-primary"] button, 
    [data-testid="baseButton-secondary"] button {{ 
        font-size: 0.9em !important; 
        font-weight: bold !important; 
    }}
    
    .stProgress > div > div > div > div {{
        background-color: {LIGHT_RED} !important;
    }}
    
    /* --------------------- RESULTS SPECIFIC FONT SIZES (Vertical) --------------------- */
    
    .stContainer {{
        min-height: 100px; 
    }}
    
    /* Τίτλος CV μέσα στην κάρτα (filename) - (0.9em, bold) */
    .stContainer h6 > b {{
        font-size: 0.9em !important; 
        line-height: 1.2 !important;
        margin-top: 0px !important;
        margin-bottom: 2px !important;
    }}

    /* Κείμενο μέσα στο progress bar (π.χ., "Συμβατότητα: 70%") */
    .stProgress > div > div > div > div > div > span {{
        font-size: 0.9em !important; 
        color: #000000 !important;
        font-weight: bold !important;
    }}

    /* ⚠️ Σημασιολογικό και Keywords σκορ - (0.9em και bold, όπως το h6 > b) */
    .stContainer p {{
        font-size: 0.9em !important; 
        line-height: 1.1 !important;
        margin-top: 0px !important;
        margin-bottom: 2px !important;
        font-weight: bold; 
    }}

    /* Κείμενο μέσα στο Expander (Keywords) */
    [data-testid="stExpander"] div[data-testid="stMarkdownContainer"] p {{
        font-size: 0.8em !important; 
        line-height: 1.1 !important;
        font-weight: normal; /* Επαναφορά στο κανονικό */
    }}


    </style>
    """
else:
    bg_style = """<style>body,p,label{color:#000}</style>"""
    background_image_error = True # Ορίζουμε τη Flag
    
st.markdown(bg_style, unsafe_allow_html=True)

# ⚠️ Εμφάνιση του σφάλματος μόνο αφού το st έχει αρχικοποιηθεί (V105 Fix)
if background_image_error:
    st.error(f"⚠️ Προσοχή: Δεν βρέθηκε η εικόνα φόντου ('{background_image_path}'). Βεβαιωθείτε ότι το αρχείο υπάρχει στον ίδιο φάκελο.")
# --------------------------------------------------------------------------------------
# --- Stopwords ---
GREEK_STOPWORDS = {
    'ο','η','το','οι','τα','του','της','των','και','με','σε','για','από','ως','ένα','μια','ένας','είναι',
    'δεν','να','θα','μετά','πριν','αλλά','ή','προς','ακόμη','πολύ','πιο','όπως','ότι','αν','μπορεί',
    'πρέπει','κάθε','όλο','όλη','όλα','τόσο','έτσι','μας','σας','μου','σου','του','της','τους','μα',
    'πως','διότι','γιατί','χωρίς','μέσα','έξω','αντί','μεταξύ','a','b','c','d','e','f','g','h','i','j','k',
    'l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','1','2','3','4','5','6','7','8','9','0','',
    'εμπειρία','γνώση','πρόγραμμα','ανάπτυξη','διαχείριση','υποχρέωση','ικανότητα','τεχνολογία','εργασία',
    'χρόνος','συνεργασία','ομάδα','πλαίσιο','θέση','έργο','πελάτη','λύση','πορεία','αποτέλεσμα','συμμετοχή',
    'περιβάλλον','σχεδιασμός','εκπαίδευση','προσόν','απαιτούμενος','υπηρεσία','συστήματος','τομέα','μέρος',
    'πλήρης','μισθός','παροχή','προσφορά','επίπεδο','χρήση','καθήκον','σχετικός','διαφορετικός','ελληνικός',
    'αγγλικός','τμήμα','απαιτείται','παροχή','προσφέρει','εταιρεία','πεδίο','κλάδος','κύριο','παρακολουθώ',
    'αναζητώ','ευθύνη','αίτημα','εφαρμογή','ανάγκη','συντήρηση','πρόκληση','βελτίωση','μεθοδολογία','εξέλιξη',
    'παρακολούθηση','δομή','σύστημα','αρχή','στόχος','διαδικασία','περίοδο','δυνατότητα','πρόσληψη','προϊόν',
    'διαρκής','συνεχής','σύγχρονος','απόφοιτος','σχολή','ενδιαφέρον','ιδέα','λογισμικό','μητρώο','οργάνωση','διαρκής'
}

# --- Φόρτωση SpaCy & SentenceTransformer ---
@st.cache_data(show_spinner=False)
def load_spacy_models():
    models = {}
    try: models['el'] = spacy.load("el_core_news_sm")
    except: models['el'] = None
    try: models['en'] = spacy.load("en_core_web_sm")
    except: models['en'] = None
    return models

@st.cache_data(show_spinner=False)
def load_sentence_transformer_model():
    try: return SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    except: return None

nlp_models = load_spacy_models()
nlp_gr = nlp_models.get('el')
nlp_en = nlp_models.get('en')
model = load_sentence_transformer_model()

ENGLISH_STOPWORDS = set()
if nlp_gr: GREEK_STOPWORDS = GREEK_STOPWORDS.union(nlp_gr.Defaults.stop_words)
if nlp_en: ENGLISH_STOPWORDS = nlp_en.Defaults.stop_words

try:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
except:
    pass 

# --- Βοηθητικές Συναρτήσεις ---
def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 1. 💾 Caching της Εξαγωγής Κειμένου
@st.cache_data(show_spinner=False)
def extract_text_from_pdf_cached(pdf_file_contents, file_name):
    """Εξάγει κείμενο από PDF."""
    text = ""
    pdf_file = BytesIO(pdf_file_contents)
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + " "
    except: pass
    text = text.strip()
    
    if not text:
        try:
            pdf_file.seek(0)
            images = convert_from_bytes(pdf_file.read(), dpi=300)
            ocr_text = [pytesseract.image_to_string(img, lang='ell+eng') for img in images]
            text = " ".join([t for t in ocr_text if t]).strip()
        except: 
            text = ""
            
    return normalize_text(text)

# 2. ⚡️ Caching Embeddings
@st.cache_data(show_spinner=False)
def get_embeddings_cached(text_list):
    """Κωδικοποιεί μια λίστα κειμένων."""
    if not model: return None
    return model.encode(text_list, convert_to_numpy=True)

# ΔΙΟΡΘΩΜΕΝΗ ΣΥΝΑΡΤΗΣΗ compute_similarity
def compute_similarity(cv_text, job_text, job_text_chunks, emb_job):
    if not model: return 0.0
    cv_text = normalize_text(cv_text)
    if not cv_text or not job_text: return 0.0
    
    splitter = r'[\.!\?\n;:]+'
    cv_chunks = [c.strip() for c in re.split(splitter, cv_text) if len(c.strip())>10]
    if not cv_chunks: cv_chunks = [cv_text]
    
    emb_cv = get_embeddings_cached(cv_chunks)
    
    # Χρησιμοποιούμε απευθείας τα NumPy arrays (emb_cv και emb_job)
    sim_matrix = util.cos_sim(emb_cv, emb_job).cpu().numpy()
    
    max_per_cv = sim_matrix.max(axis=1)
    
    return round(float(max_per_cv.max())*100,2)

def calculate_keyword_match(cv_text, job_text):
    if not nlp_gr and not nlp_en: return [],0.0
    POS_FILTERS = {"NOUN","ADJ","PROPN"}
    
    def get_filtered_lemmas(text):
        if not text: return set()
        try: lang=detect(text)
        except: lang='en'
        
        if lang=='el' and nlp_gr: nlp_model, stopwords = nlp_gr, GREEK_STOPWORDS
        elif nlp_en: nlp_model, stopwords = nlp_en, ENGLISH_STOPWORDS
        else: return set()
        
        doc = nlp_model(text)
        return set([ token.lemma_.lower() for token in doc if token.is_alpha and len(token)>1 and token.pos_ in POS_FILTERS and token.lemma_.lower() not in stopwords ])
        
    cv_lemmas = get_filtered_lemmas(cv_text)
    job_lemmas = get_filtered_lemmas(job_text)
    matched = cv_lemmas.intersection(job_lemmas)
    score = round(min((len(matched)/len(job_lemmas)*100 if job_lemmas else 0.0),100.0),2)
    return sorted(list(matched)), score

# --- Streamlit UI ---
st.set_page_config(page_title="HR Match Pro", layout="wide") 

# V111: Αρχικοποίηση Session State για το disabled state
if 'top_n_disabled' not in st.session_state:
    st.session_state['top_n_disabled'] = False
    
st.markdown("""
<div style="text-align: center; line-height: 1.2; margin-top: 1em;">
<h1 style="margin-bottom:0px; color:#000000;">HR Match Pro</h1>
<p style="margin-top:5px; font-weight:500; color:#000000;">Βρες τον Ιδανικό Υποψήφιο</p>
</div>
""", unsafe_allow_html=True)

try:
    st.sidebar.image(background_image_path, use_container_width=True)
    st.sidebar.markdown("---")
except: 
    pass

if not nlp_gr: st.error("⚠️ Το ελληνικό μοντέλο SpaCy δεν φορτώθηκε.")
if not model: st.error("⚠️ Αποτυχία φόρτωσης SentenceTransformer.")

st.markdown("---")

# ⚠️ ΔΙΟΡΘΩΣΗ: Αλλαγή της κατανομής των στηλών σε 30% / 40% / 30% για πιο ΜΑΖΕΜΕΝΗ εμφάνιση.
col_left, col_center, col_right = st.columns([0.3, 0.4, 0.3])

with col_center:
    # ----------------------------------------------------------------------------------
    # --- 1. INPUTS: (ΠΛΗΡΩΣ ΚΑΤΑΚΟΡΥΦΑ) ---
    # ----------------------------------------------------------------------------------

    # 1. CV Uploader
    st.markdown("<h3 style='font-size: 1.2em; color:#000000;'>1. Εισαγωγή Δεδομένων</h3>", unsafe_allow_html=True)
    st.markdown("<h6>Ανέβασμα Βιογραφικών (PDF)</h6>", unsafe_allow_html=True)
    cv_files = st.file_uploader("", type=["pdf"], accept_multiple_files=True, key="cv_upload") 
    cv_warning_placeholder = st.empty()

    # 2. JD Text Area
    st.markdown("<h6>Περιγραφή Θέσης Εργασίας (JD)</h6>", unsafe_allow_html=True)
    job_text = st.text_area("", height=150, placeholder="Εισάγετε εδώ την πλήρη περιγραφή της θέσης εργασίας...", key="jd_text_area") 
    jd_warning_placeholder = st.empty()

    # ⚠️ ΔΙΟΡΘΩΣΗ: Μικρότερο κενό αντί για st.markdown("---")
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) 

    # ----------------------------------------------------------------------------------
    # --- 2. ΡΥΘΜΙΣΗ ΒΑΡΥΤΗΤΑΣ (ΠΛΗΡΩΣ ΚΑΤΑΚΟΡΥΦΑ) ---
    # ----------------------------------------------------------------------------------

    st.markdown("<h3 style='font-size: 1.2em; color:#000000;'>2. Ρύθμιση Βαρύτητας</h3>", unsafe_allow_html=True)

    # V106: Αφαίρεση του default τίτλου του slider και αντικατάσταση με Markdown για να δώσουμε χώρο
    st.markdown("<h6>Βάρος Σημασιολογικής Ομοιότητας (%)<br><br></h6>", unsafe_allow_html=True)

    # Χρησιμοποιούμε όλο το πλάτος της κεντρικής στήλης
    weight_sem = st.slider("", min_value=0, max_value=100, value=70, step=5, key="weight_slider") 
    
    # V107: Προσθήκη κενού μετά τον slider και πριν το μήνυμα συνολικού σκορ
    st.markdown("<br>", unsafe_allow_html=True) 

    weight_kw = 100 - weight_sem
    st.markdown(f"<h6>(Συνολικό Σκορ = **{weight_sem}%** Σημασιολογικό + **{weight_kw}%** Keywords)</h6>", unsafe_allow_html=True)

    # ⚠️ ΔΙΟΡΘΩΣΗ: Μικρότερο κενό αντί για st.markdown("---")
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True) 

    # ----------------------------------------------------------------------------------
    # --- 3. ΕΠΙΛΟΓΕΣ ΕΜΦΑΝΙΣΗΣ (ΠΛΗΡΩΣ ΚΑΤΑΚΟΡΥΦΑ) ---
    # ----------------------------------------------------------------------------------

    st.markdown("<h3 style='font-size: 1.2em; color:#000000;'>3. Επιλογές Εμφάνισης</h3>", unsafe_allow_html=True)
    
    # V111 FIX: Σωστή οπτική σειρά (Top N πάνω, Checkbox κάτω) με Session State
    
    # 1. Number Input (Εμφανίζεται πρώτο)
    # ⚠️ Η ετικέτα είναι bold με Markdown.
    top_n_default = st.number_input(
        "**Εμφάνιση Top N Βιογραφικών**", 
        min_value=1, 
        value=5, 
        step=1, 
        key="top_n_input_v111",
        disabled=st.session_state.top_n_disabled # Χρησιμοποιεί την Session State
    )
    
    # 2. Checkbox (Εμφανίζεται δεύτερο - τώρα με on_change callback για να ενημερώσει το disabled state του Top N)
    show_all = st.checkbox(
        "Εμφάνιση Όλων", 
        value=False, 
        key="show_all_checkbox_v111", 
        on_change=toggle_show_all # Callback που τρέχει και ενημερώνει το disabled state
    )

    # 3. Ορίζουμε την τιμή του top_n με τη σωστή λογική
    top_n = 999999 if show_all else int(top_n_default)

    st.markdown("---")
        
    # 4. Κουμπί Εκτέλεσης (στο πλήρες πλάτος της κεντρικής στήλης)
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 
    analyze_button = st.button("Εκτέλεση Ανάλυσης", type="primary", key="analyze_button", use_container_width=True)

    # ----------------------------------------------------------------------------------
    # --- 5. ΑΠΟΤΕΛΕΣΜΑΤΑ: ΚΑΤΩ ΑΠΟ ΤΟ ΚΟΥΜΠΙ (ΠΛΗΡΩΣ ΚΑΤΑΚΟΡΥΦΑ) ---
    # ----------------------------------------------------------------------------------

    if analyze_button:
        
        # Επανεκκίνηση της μεταβλητής errors εντός του block
        errors = False
        
        # Εμφάνιση warning messages 
        if not cv_files:
            cv_warning_placeholder.warning("⚠️ **1. Ανέβασμα τουλάχιστον ενός Βιογραφικού (PDF)**")
            errors = True
        
        if not job_text.strip():
            jd_warning_placeholder.warning("⚠️ **2. Εισαγωγή της Περιγραφής Θέσης (JD) για να εκτελεστεί η ανάλυση.**")
            errors = True

        if not errors and nlp_gr and model:
            results = []
            
            # 1. Κωδικοποίηση JD μία φορά (Cached)
            splitter = r'[\.!\?\n;:]+'
            job_text_normalized = normalize_text(job_text)
            job_text_chunks = [c.strip() for c in re.split(splitter, job_text_normalized) if len(c.strip())>10]
            if not job_text_chunks: job_text_chunks = [job_text_normalized]
            
            emb_job = get_embeddings_cached(job_text_chunks)
            
            # 2. Ανάγνωση περιεχομένου CVs μία φορά
            cv_content_map = {cv_file.name: cv_file.read() for cv_file in cv_files} 
            
            st.markdown("---") # Διαχωριστικό πριν τα αποτελέσματα
            
            with st.spinner("⚙️ Εκτέλεση ανάλυσης... Παρακαλώ περιμένετε..."):
                for cv_file in cv_files:
                    cv_file_contents = cv_content_map[cv_file.name] # Αποθηκεύουμε το περιεχόμενο μία φορά

                    # 3. Εξαγωγή κειμένου CV (Cached)
                    cv_text = extract_text_from_pdf_cached(cv_file_contents, cv_file.name)
                    
                    # Υπολογισμοί
                    sem_score = compute_similarity(cv_text, job_text, job_text_chunks, emb_job)
                    matched_keywords, kw_score = calculate_keyword_match(cv_text, job_text)
                    final_score = round((sem_score*weight_sem + kw_score*weight_kw)/100,2)
                    
                    results.append({
                        "file_name": cv_file.name,
                        "sem_score": sem_score,
                        "kw_score": kw_score,
                        "matched_keywords": matched_keywords,
                        "final_score": final_score,
                        "content": cv_file_contents,
                    })
            
            if results:
                results = sorted(results, key=lambda x: x['final_score'], reverse=True)
                display_count = min(top_n,len(results))
                header_text = f"Όλα τα CVs ({len(results)})" if show_all else f"Top {display_count} Βιογραφικά"
                
                st.markdown("<h3 style='font-size: 1.2em; color:#000000;'>Αποτελέσματα Ταύτισης</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.05em; font-weight: bold; color:#000000;'>{header_text}</p>", unsafe_allow_html=True)
                
                # Download All Button
                if len(results) > 1:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for res in results:
                            zipf.writestr(res['file_name'], res['content'])
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ Download All CVs (ZIP)",
                        data=zip_buffer,
                        file_name="matched_CVs.zip",
                        mime="application/zip",
                        type="primary",
                        key="download_all_button"
                    )
                    st.markdown("---")

                
                # -------------------------------------------------------------
                # ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ (Μία ΣΤΗΛΗ)
                # -------------------------------------------------------------
                
                results_to_display = results[:display_count]
                
                for data_index in range(display_count):
                    res = results_to_display[data_index]
                    final_score_int = int(res['final_score']) 
                    
                    with st.container(border=True):
                        # 1. Πληροφορίες CV/Score (filename)
                        st.markdown(f"<h6><b>{data_index+1}. {res['file_name']}</b></h6>", unsafe_allow_html=True)
                        
                        # 2. Progress Bar
                        st.progress(final_score_int/100, text=f"**Συνολική Συμβατότητα: {final_score_int}%**")
                        
                        # 3. Σημασιολογικό/Keyword Score
                        st.markdown(f"<p>Σημασιολογικό: {res['sem_score']}% | Keywords: {res['kw_score']}%</p>", unsafe_allow_html=True)
                        
                        # 4. 🔑 Καλύτερη Εμφάνιση Keywords (Expander)
                        if res['matched_keywords']:
                            with st.expander("🔑 **Keywords που ταιριάζουν**"):
                                st.markdown(
                                    f"**Keywords:** {', '.join(res['matched_keywords'])}",
                                    unsafe_allow_html=True
                                )
                        
                        # 5. Κουμπί Download
                        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) 
                        
                        download_label = "📄 Download PDF"
                        
                        st.download_button(
                            label=download_label, 
                            data=res['content'], 
                            file_name=res['file_name'], 
                            mime="application/pdf",
                            key=f"dl_btn_{data_index}", 
                            help="Κατεβάστε το αρχείο PDF",
                            type="primary" 
                        )
                        
                    # Προσθήκη μιας μικρής απόστασης μεταξύ των αποτελεσμάτων
                    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            st.markdown("---")
        else:
            # Αυτό θα εμφανιστεί μόνο αν δεν υπήρξαν σφάλματα (errors=False) αλλά το results ήταν άδειο (π.χ. άδειο PDF)
            st.warning("⚠️ Δεν βρέθηκαν αποτελέσματα για ανάλυση.")
        pass