import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re

# --- CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Key not found. Please set it in Streamlit Secrets.")

# --- HELPER: FIND THE JSON ---
def extract_json(text_response):
    pattern = r"\{[\s\S]*\}"
    match = re.search(pattern, text_response)
    if match:
        return match.group(0)
    return text_response

def analyze_image(image):
    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json"
    }
    
    # We turn off safety filters to prevent chemical names from being blocked
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # USING THE CORRECT MODERN MODEL
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    prompt = """
    Analyze the ingredient label in this image. 
    1. Identify the First 3 ingredients listed (Top by Mass).
    2. Classify EVERY ingredient into 'Simple_Processed' or 'Ultra_Processed'.
    3. Count total ingredients and calculate percentages.
    
    Return STRICT JSON:
    {
        "top_3_by_mass": ["item1", "item2", "item3"],
        "stats": {
            "total_count": 0,
            "simple_pct": 0,
            "ultra_processed_pct": 0
        },
        "lists": {
            "simple": ["item", "item"],
            "ultra": ["item", "item"]
        },
        "verdict": "One sentence summary."
    }
    """
    
    with st.spinner("🤖 AI is reading the label..."):
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"Error: {e}"

# --- THE APP INTERFACE ---
st.set_page_config(page_title="Ingredient Scanner", page_icon="🥦")

st.title("🥦 UPF Scanner")

# --- DEBUG INFO: This tells us if the server actually updated ---
st.caption(f"System Version: {genai.__version__}") 
# If this number is LESS than 0.7.0, the update failed.

uploaded_file = st.file_uploader("Choose a photo of ingredients", type=['jpg', 'jpeg', 'png', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)
    
    if st.button("Analyze Ingredients"):
        
        raw_response = analyze_image(image)
        cleaned_json = extract_json(raw_response)
        
        try:
            data = json.loads(cleaned_json)
            
            st.divider()
            st.subheader("💡 Verdict")
            st.success(data['verdict'])
            
            col1, col2 = st.columns(2)
            col1.metric("Simple", f"{data['stats']['simple_pct']}%")
            col2.metric("Ultra Processed", f"{data['stats']['ultra_processed_pct']}%")
            
            st.progress(data['stats']['simple_pct'] / 100)
            
            st.subheader("⚖️ Top 3 by Mass")
            for i, item in enumerate(data['top_3_by_mass'], 1):
                st.write(f"**{i}.** {item}")
                
            with st.expander("🔴 See Ultra-Processed List"):
                for item in data['lists']['ultra']:
                    st.write(f"- {item}")

            with st.expander("🟢 See Simple List"):
                for item in data['lists']['simple']:
                    st.write(f"- {item}")
                    
        except json.JSONDecodeError:
            st.error("⚠️ AI Error: The response was blocked or incomplete.")
            with st.expander("Debug View"):
                st.text(raw_response)
