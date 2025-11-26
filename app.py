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

def extract_json(text_response):
    # Extracts text between the first '{' and the last '}'
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
    
    # Disable safety filters so food chemicals don't get blocked
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # We use 'gemini-1.5-flash'. If the Fresh Install worked, this WILL work.
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    prompt = """
    Analyze the image provided.
    
    STEP 1: CHECK FOR INGREDIENTS
    Does this image contain a list of ingredients (e.g., "Ingredients: Milk, Sugar...")? 
    Note: A "Nutrition" table (Energy, Fat, Salt) is NOT an ingredients list.
    
    IF NO INGREDIENTS LIST IS VISIBLE:
    Return exactly this JSON:
    {
        "error": "missing_ingredients",
        "message": "I see Nutrition Facts (Fat, Salt, etc.), but not the actual INGREDIENTS list. Please rotate the bottle to find the text starting with 'Ingredients:'."
    }

    IF INGREDIENTS ARE FOUND:
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

# --- APP INTERFACE ---
st.set_page_config(page_title="Ingredient Scanner", page_icon="🥦")
st.title("🥦 UPF Scanner")
st.info("Tip: Don't photograph the 'Nutrition' table (Fat/Salt). Photograph the **text paragraph** that lists ingredients.")

# Debug: Print version to confirm the fix
st.caption(f"System Version: {genai.__version__} (Should be 0.8.3+)")

uploaded_file = st.file_uploader("Choose photo", type=['jpg', 'jpeg', 'png', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)
    
    if st.button("Analyze Ingredients"):
        raw_response = analyze_image(image)
        cleaned_json = extract_json(raw_response)
        
        try:
            data = json.loads(cleaned_json)
            
            # CHECK FOR LOGICAL ERROR (Wrong image side)
            if "error" in data and data["error"] == "missing_ingredients":
                st.warning("⚠️ " + data["message"])
            else:
                # SUCCESS
                st.divider()
                st.subheader("💡 Verdict")
                st.success(data['verdict'])
                
                col1, col2 = st.columns(2)
                col1.metric("Simple", f"{data['stats']['simple_pct']}%")
                col2.metric("Ultra Processed", f"{data['stats']['ultra_processed_pct']}%")
                st.progress(data['stats']['simple_pct'] / 100)
                
                st.subheader("⚖️ Heaviest Ingredients")
                for i, item in enumerate(data['top_3_by_mass'], 1):
                    st.write(f"**{i}.** {item}")
                    
                with st.expander("🔴 See Ultra-Processed List"):
                    for item in data['lists']['ultra']:
                        st.write(f"- {item}")
        
        except json.JSONDecodeError:
            st.error("⚠️ AI Error.")
            with st.expander("Debug View"):
                st.write(raw_response)
