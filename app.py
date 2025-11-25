import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURATION ---
# We will set the API key in the next phase securely
# pulling it from Streamlit secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Key not found. Please set it in Streamlit Secrets.")

def analyze_image(image):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Look at the ingredient label in this image.
    1. Identify the First 3 ingredients listed (Top by Mass).
    2. Classify EVERY ingredient into 'Simple_Processed' or 'Ultra_Processed'.
    3. Count total ingredients and calculate percentages.
    
    Return ONLY this JSON:
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
st.write("Take a photo of the **ingredients list** to see what's really inside.")

# The Camera Input
img_file = st.camera_input("Take a Picture")

if img_file:
    # Display the image briefly
    image = Image.open(img_file)
    
    # Run Analysis
    json_text = analyze_image(image)
    
    try:
        # Clean Code block markers if AI adds them
        clean_json = json_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        # --- SHOW RESULTS ---
        st.divider()
        
        # 1. The Verdict
        st.subheader("💡 Verdict")
        st.info(data['verdict'])
        
        # 2. Scorecard
        col1, col2 = st.columns(2)
        col1.metric("Simple", f"{data['stats']['simple_pct']}%")
        col2.metric("Ultra Processed", f"{data['stats']['ultra_processed_pct']}%")
        
        # Visual Bar
        st.progress(data['stats']['simple_pct'] / 100)
        
        # 3. Mass Analysis
        st.subheader("⚖️ Heaviest Ingredients")
        st.write("*(Top 3 by weight)*")
        for i, item in enumerate(data['top_3_by_mass'], 1):
            st.write(f"**{i}.** {item}")
            
        # 4. The Bad List
        with st.expander("See Ultra-Processed Ingredients"):
            for item in data['lists']['ultra']:
                st.write(f"- 🔴 {item}")

        # 5. The Good List
        with st.expander("See Simple Ingredients"):
            for item in data['lists']['simple']:
                st.write(f"- 🟢 {item}")
                
    except:
        st.error("Could not read the label clearly. Please try again with better lighting!")
