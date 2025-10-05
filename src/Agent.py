
import re
import os


CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODEL = "llama-3.3-70b"


BASE_PROMPT = """
You are an expert DevOps engineer. Convert the user's natural language request into a valid docker-compose.yml file.

RULES:
- ONLY output YAML. No explanations, no markdown, no ```yaml.
- Use service name: 'app'
- Default image: 'myapp:latest'
- Expose port 5000 from container to a host port (e.g., 8080:5000).
- For replicas: use 'deploy: {replicas: N}' (valid in Compose v3.8+).
- Always include 'version: "3.8"'

User request: 
"""

def generate_docker_yaml(user_prompt: str) -> str:
    import requests as req
    full_prompt = BASE_PROMPT + f'"{user_prompt}"'
    try:
        ollama_response = req.post(
             "http://localhost:11434/api/generate",
            json={"model": "llama", "prompt": full_prompt, "stream": False},
            timeout=60
        )
        raw = ollama_response.json()["response"]
        return re.sub(r"^```yaml\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    except Exception as e:
        raise Exception(f"LLM failed: {str(e)}")