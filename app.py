import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURATION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API Key not found. Please set it in Streamlit Secrets.")

def analyze_image(image):
    # We use the specific configuration to FORCE JSON output
    # This prevents the AI from adding conversational text that breaks the app
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json"
    }
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config=generation_config
    )
    
    prompt = """
    Analyze the ingredient label in this image.
    1. Identify the First 3 ingredients listed (Top by Mass).
    2. Classify EVERY ingredient into 'Simple_Processed' or 'Ultra_Processed'.
    3. Count total ingredients and calculate percentages.
    
    Output strictly in this JSON structure:
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
st.info("Tip: Use your phone's native camera to take a clear, focused photo first, then upload it here.")

uploaded_file = st.file_uploader("Choose a photo of ingredients", type=['jpg', 'jpeg', 'png', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Label", use_container_width=True)
    
    if st.button("Analyze Ingredients"):
        
        # Run Analysis
        raw_response = analyze_image(image)
        
        # --- DEBUGGER: This helps you see what is wrong ---
        with st.expander("🛠️ View Raw AI Response (Debug)"):
            st.code(raw_response)
        
        try:
            # Parse JSON
            data = json.loads(raw_response)
            
            # --- SHOW RESULTS ---
            st.divider()
            
            # 1. The Verdict
            st.subheader("💡 Verdict")
            st.success(data['verdict'])
            
            # 2. Scorecard
            col1, col2 = st.columns(2)
            col1.metric("Simple", f"{data['stats']['simple_pct']}%")
            col2.metric("Ultra Processed", f"{data['stats']['ultra_processed_pct']}%")
            
            st.progress(data['stats']['simple_pct'] / 100)
            
            # 3. Mass Analysis
            st.subheader("⚖️ Heaviest Ingredients")
            st.caption("(Top 3 by weight)")
            for i, item in enumerate(data['top_3_by_mass'], 1):
                st.write(f"**{i}.** {item}")
                
            # 4. The Bad List
            with st.expander("See Ultra-Processed Ingredients"):
                if data['lists']['ultra']:
                    for item in data['lists']['ultra']:
                        st.write(f"- 🔴 {item}")
                else:
                    st.write("None found!")

            # 5. The Good List
            with st.expander("See Simple Ingredients"):
                for item in data['lists']['simple']:
                    st.write(f"- 🟢 {item}")
                    
        except json.JSONDecodeError:
            st.error("⚠️ The AI saw the text but formatted it poorly.")
            st.write("Please look at the 'View Raw AI Response' box above to see what happened.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
