import streamlit as st
import requests
import json

st.set_page_config(
    page_title="💬 Conversational Cloud Orchestrator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("💬 Conversational Cloud Orchestrator")
st.caption("Natural language → Live infrastructure. Powered by Mistral + **Real Cerebras API**")

# === Input ===
user_input = st.text_input(
    "Describe your deployment:",
    placeholder="e.g., Deploy sentiment AI with Cerebras, 2 replicas, public endpoint",
    key="user_prompt"
)

# === Deploy Button ===
if st.button("🚀 Deploy", type="primary", use_container_width=True):
    if not user_input:
        st.error("Please enter a deployment request.")
    else:
        with st.spinner("🧠 Processing your request..."):
            try:
                response = requests.post(
                    "http://localhost:8000/deploy",
                    json={"prompt": user_input},
                    timeout=60
                )
                
                if response.status_code != 200:
                    st.error(f"❌ Failed: {response.json().get('detail', 'Unknown error')}")
                else:
                    data = response.json()
                    
                    if data["type"] == "cerebras":
                        st.success("✅ **Cerebras AI Endpoint Deployed!**")
                        st.info("💡 This uses the **real Cerebras Inference API** (free tier).")
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.subheader("🔗 Your Cerebras Endpoint")
                            endpoint_url = data["endpoint"]
                            st.code(endpoint_url, language="bash")
                            st.markdown(f"**Try it**: `POST {{\"text\": \"your input\"}}` to this URL")
                            
                            # --- Live Test Box ---
                            st.subheader("🧪 Test It Live")
                            test_text = st.text_input("Enter text for sentiment analysis:", "I love this hackathon!")
                            if st.button("CallCheck Sentiment"):
                                try:
                                    test_resp = requests.post(
                                        endpoint_url.replace("http://localhost:8000", "http://localhost:8000"),
                                        json={"text": test_text}
                                    )
                                    if test_resp.status_code == 200:
                                        result = test_resp.json()
                                        sentiment = result["sentiment"]
                                        color = "green" if "POSITIVE" in sentiment.upper() else "red"
                                        st.markdown(f"### Sentiment: :{color}[**{sentiment}**]")
                                        st.json(result)
                                    else:
                                        st.error(f"Test failed: {test_resp.text}")
                                except Exception as e:
                                    st.error(f"Test error: {str(e)}")
                        
                        with col2:
                            st.subheader("📊 Details")
                            st.write(f"**Model**: `{data['model']}`")
                            st.write(f"**Test Result**: `{data['test_prediction']}`")
                            st.write("**Provider**: Cerebras (real API)")
                            st.write("**Tokens**: From free 10k/month tier")
                            st.image("https://images.cerebras.net/brand/Cerebras_Logo_Black.png", width=150)
                    
                    else:  # Docker deployment
                        st.success("✅ **Docker App Deployed!**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("🔗 Live Endpoints")
                            for url in data.get("endpoints", ["http://localhost:8080"]):
                                st.markdown(f"[{url}]({url})")
                        with col2:
                            st.subheader("⚙️ Generated YAML")
                            st.code(data.get("yaml", ""), language="yaml")
                        
                        with st.expander("📜 Deployment Logs"):
                            st.code(data.get("logs", ""), language="bash")

            except Exception as e:
                st.error(f"⚠️ Connection error: {str(e)}")
                st.info("Make sure the backend is running on http://localhost:8000")

# === Footer ===
st.markdown("---")
st.caption(
    "✨ **Hackathon Note**: Cerebras integration uses the official free API (10k tokens/month). "
    "No mocks — real Llama-3-8b inference on Cerebras infrastructure! "
    "[Get your key](https://inference.cerebras.ai/)"
)