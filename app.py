import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re  # We use this for "Regular Expressions" to find the JSON

# --- CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Key not found. Please set it in Streamlit Secrets.")

# --- HELPER: FIND THE JSON ---
def extract_json(text_response):
    # This pattern finds the largest block of text starting with '{' and ending with '}'
    pattern = r"\{[\s\S]*\}"
    match = re.search(pattern, text_response)
    if match:
        return match.group(0)
    return text_response

def analyze_image(image):
    # 1. FORCE JSON OUTPUT
    generation_config = {
        "temperature": 0.0,         # 0.0 means "be exact, don't be creative"
        "response_mime_type": "application/json"
    }
    
    # 2. DISABLE SAFETY FILTERS (Crucial for chemical ingredients)
    # We turn off blocks for "Harmful" content because chemical names can trigger false positives
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    model = genai.GenerativeModel(
        'gemini-pro-vision',
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
    prompt = """
    Analyze the ingredient label in this image. 
    If the image is blurry, do your best to guess the words based on context.
    
    1. Identify the First 3 ingredients listed (Top by Mass).
    2. Classify EVERY ingredient into 'Simple_Processed' or 'Ultra_Processed'.
    3. Count total ingredients and calculate percentages.
    
    Return STRICT JSON. No markdown, no "Here is the result". Just the JSON:
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

uploaded_file = st.file_uploader("Choose a photo of ingredients", type=['jpg', 'jpeg', 'png', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)
    
    if st.button("Analyze Ingredients"):
        
        raw_response = analyze_image(image)
        
        # --- ROBUST PARSING ---
        # 1. Try to find the JSON hidden in the text
        cleaned_json = extract_json(raw_response)
        
        try:
            data = json.loads(cleaned_json)
            
            # --- SHOW RESULTS ---
            st.divider()
            
            # verdict
            st.subheader("💡 Verdict")
            st.success(data['verdict'])
            
            # scorecard
            col1, col2 = st.columns(2)
            col1.metric("Simple", f"{data['stats']['simple_pct']}%")
            col2.metric("Ultra Processed", f"{data['stats']['ultra_processed_pct']}%")
            
            st.progress(data['stats']['simple_pct'] / 100)
            
            # lists
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
            with st.expander("See what the AI actually said (Debug)"):
                st.text(raw_response)


