import streamlit as st
import requests
import json
import base64
from PIL import Image
from io import BytesIO

# --- CONFIGURATION ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API Key not found. Please set it in Streamlit Secrets.")
    st.stop()

def analyze_image_direct(image):
    # 1. Convert Image to Base64 (Google needs text, not pixels)
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # 2. The Direct Link to Gemini 1.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    # 3. The Payload (The Message)
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [
                {"text": """
                    Analyze this image. 
                    STEP 1: Check if this is an INGREDIENTS list. If it's a Nutrition Table (Fat, Salt), return error.
                    
                    If Ingredients found:
                    1. Identify top 3 by mass.
                    2. Classify Simple vs Ultra Processed.
                    3. JSON format ONLY:
                    {
                        "top_3_by_mass": ["item1", "item2"],
                        "stats": {"simple_pct": 0, "ultra_processed_pct": 0},
                        "lists": {"simple": [], "ultra": []},
                        "verdict": "summary",
                        "error": "none"
                    }
                    If wrong image, return: {"error": "missing_ingredients"}
                """},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img_str
                }}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    # 4. Send the Request
    try:
        response = requests.post(url, headers=headers, json=data)
        
        # Check if Google blocked it
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"
            
        return response.json()
    except Exception as e:
        return f"Connection Error: {e}"

# --- APP INTERFACE ---
st.set_page_config(page_title="Ingredient Scanner", page_icon="🥦")
st.title("🥦 UPF Scanner (Direct Mode)")
st.info("Tip: Ensure you photograph the 'Ingredients' paragraph, not the Nutrition table.")

uploaded_file = st.file_uploader("Choose photo", type=['jpg', 'jpeg', 'png', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)
    
    if st.button("Analyze Ingredients"):
        with st.spinner("Talking to Gemini directly..."):
            result = analyze_image_direct(image)
        
        # --- PARSING THE DIRECT RESPONSE ---
        try:
            # If it's a string, it's an error message
            if isinstance(result, str):
                st.error(result)
            else:
                # Extract the text from the complex Google JSON structure
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(text_content)
                
                # LOGIC HANDLERS
                if data.get("error") == "missing_ingredients":
                    st.warning("⚠️ I see Nutrition Facts, but not Ingredients. Please rotate the bottle.")
                else:
                    # SUCCESS DISPLAY
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
                            
        except Exception as e:
            st.error("Could not parse the response.")
            with st.expander("Debug Info"):
                st.write(result)
