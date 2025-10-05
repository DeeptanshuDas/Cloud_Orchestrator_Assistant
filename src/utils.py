import yaml
import subprocess
import os
from typing import Dict, Any

YAML_PATH = "docker-compose.generated.yml"

def validate_and_save_yaml(yaml_str: str) -> bool:
    try:
        data = yaml.safe_load(yaml_str)
        if not isinstance(data, dict):
            return False
        with open(YAML_PATH, "w") as f:
            f.write(yaml_str)
        return True
    except Exception as e:
        print(f"YAML Error: {e}")
        return False

def deploy_compose():
    try:
        # Stop previous if exists
        subprocess.run(["docker-compose", "-f", YAML_PATH, "down"], capture_output=True)
        # Deploy new
        result = subprocess.run(
            ["docker-compose", "-f", YAML_PATH, "up", "-d", "--remove-orphans"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def get_service_urls() -> list:
    """Get published ports (assumes port 5000 mapped to host)"""
    try:
        result = subprocess.run(
            ["docker-compose", "-f", YAML_PATH, "port", "app", "5000"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and ":" in result.stdout:
            host_port = result.stdout.strip().split(":")[1]
            return [f"http://localhost:{host_port}"]
        # Try 'ai' service too
        result = subprocess.run(
            ["docker-compose", "-f", YAML_PATH, "port", "ai", "5000"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and ":" in result.stdout:
            host_port = result.stdout.strip().split(":")[1]
            return [f"http://localhost:{host_port}"]
    except:
        pass
    return ["http://localhost:8080"]  # fallback
