from fastapi import FastAPI, HTTPException,Request
# from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import os
import uuid
from typing import Dict, Any
from src.Agent import generate_docker_yaml
from src.utils import validate_and_save_yaml, deploy_compose, get_service_urls
# app= FastAPI()
from dotenv import load_dotenv

load_dotenv(dotenv_path="path/to/.env")


app = FastAPI(title="Conversational Cloud Orchestrator API")


CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_API_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODEL = "llama-3.3-70b"  # or "llama3-70b", "gemma-7b", etc.

# In-memory store for Cerebras endpoints (hackathon-friendly)
cerebras_endpoints: Dict[str, dict] = {}

class DeployRequest(BaseModel):
    prompt: str
    user_prompt:str 

def call_cerebras_inference(user_prompt: str) -> str:
    if not CEREBRAS_API_KEY:
        raise Exception("CEREBRAS_API_KEY not set. Get one at https://inference.cerebras.ai/")
    
    try:
        response = requests.post(
            CEREBRAS_API_URL,
            headers={
                "Authorization": f"Bearer {CEREBRAS_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": CEREBRAS_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.0  # deterministic for demo
            },
            timeout=30
        )
        if response.status_code == 401:
            raise Exception("Invalid") 
        if response.status_code != 200:
            raise Exception(f"API Error ({response.status_code}): {response.text}")
        
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")

@app.post("/deploy")
async def deploy(request: DeployRequest):
    user_input = request.prompt.strip()
    user_lower = user_input.lower()

    # 🔥 CEREBRAS PATH: if user mentions AI/Cerebras/sentiment
    if any(kw in user_lower for kw in ["cerebras", "ai model", "sentiment", "llm", "inference", "neural"]):
        try:
            # Test Cerebras with a real call
            test_response = call_cerebras_inference(
                "What is the sentiment of: 'I love this product!'? Answer only POSITIVE or NEGATIVE."
            )
            
            # Create a unique endpoint ID
            endpoint_id = str(uuid.uuid4())[:8]
            endpoint_path = f"/cerebras-predict/{endpoint_id}"
            
            # Store metadata (in real system, use DB)
            cerebras_endpoints[endpoint_id] = {
                "model": CEREBRAS_MODEL,
                "created_from": user_input,
                "test_result": test_response
            }

            return {
                "status": "success",
                "type": "cerebras",
                "message": "✅ Cerebras AI endpoint deployed!",
                "endpoint": f"http://localhost:8000{endpoint_path}",
                "test_prediction": test_response,
                "model": CEREBRAS_MODEL,
                "note": "Powered by real Cerebras Inference API (free tier)",
                "how_to_use": f"POST {{\"text\": \"your input\"}} to {endpoint_path}"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cerebras deployment failed: {str(e)}")

    # 🐳 DOCKER PATH: generic app deployment
    else:
        try:
            yaml_str = generate_docker_yaml(user_input)
            if not validate_and_save_yaml(yaml_str):
                raise ValueError("Invalid YAML generated")

            success, log = deploy_compose()
            if not success:
                # Auto-fix attempt
                fix_prompt = f"Fix this docker-compose.yml. Error: {log[:200]}. Only output fixed YAML.\n{yaml_str}"
                fixed_yaml = generate_docker_yaml(fix_prompt)
                if not validate_and_save_yaml(fixed_yaml):
                    raise ValueError(f"YAML invalid even after fix: {log}")
                success, log = deploy_compose()
                if not success:
                    raise ValueError(f"Deployment failed after retry: {log}")
            urls = get_service_urls()
            return {
                    "status": "success",
                    "type": "docker",
                    "message": "✅ Docker app deployed!",
                    "endpoints": urls,
                    "yaml": yaml_str,
                    "logs": log[:500]
                }

        except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Docker deployment failed: {str(e)}")               

@app.post("/cerebras-predict/{endpoint_id}")
async def cerebras_predict(endpoint_id: str, payload: dict):
    if endpoint_id not in cerebras_endpoints:
        raise HTTPException(status_code=404, detail="Cerebras endpoint not found")
    
    user_text = payload.get("text", "")
    if not user_text:
        raise HTTPException(status_code=400, detail="Missing 'text' in request body")

    try:
        # Run real sentiment analysis via Cerebras
        cerebras_prompt = f"Analyze sentiment of this text. Respond with only 'POSITIVE' or 'NEGATIVE':\n\n{user_text}"
        result = call_cerebras_inference(cerebras_prompt)
        
        return {
            "input": user_text,
            "sentiment": result,
            "model": cerebras_endpoints[endpoint_id]["model"],
            "provider": "Cerebras (real API)",
            "note": "Using free 10k-token tier from cerebras.ai"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cerebras inference error: {str(e)}")


@app.get("/health")
def health():
    has_key = bool(CEREBRAS_API_KEY)
    return {
        "status": "ok",
        "cerebras_enabled": has_key,
        "docker_available": True
    }      
@app.get("/")
async def read_root():
    return {"message": "Welcome to Docker-Orchestrater!"}

def main():
    print("Hello from docker-orchestater!")


if __name__ == "__main__":
    main()
