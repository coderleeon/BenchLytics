import os
import yaml
import time
from typing import Dict, Any, Tuple
from google import genai
from openai import AsyncOpenAI
import asyncio

class LLMManager:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            self.models_config = {m["id"]: m for m in config.get("models", [])}
            
        # Initialize clients
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

    def get_pricing(self, model_id: str) -> float:
        return self.models_config.get(model_id, {}).get("cost_per_1k_tokens", 0.0)
        
    async def generate_response(self, model_id: str, prompt: str) -> Tuple[str, int, float]:
        """
        Returns (response_text, token_count, latency_ms)
        """
        provider = self.models_config.get(model_id, {}).get("provider")
        if not provider:
            return f"Error: Model {model_id} not configured", 0, 0.0

        start_time = time.time()
        response_text = ""
        token_count = 0

        try:
            if provider == "openai":
                response = await self.openai_client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                response_text = response.choices[0].message.content
                token_count = response.usage.total_tokens
                
            elif provider == "google":
                response = self.gemini_client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                response_text = response.text
                
                if hasattr(response, 'usage_metadata') and response.usage_metadata and hasattr(response.usage_metadata, 'total_token_count'):
                    token_count = response.usage_metadata.total_token_count
                else:
                    # Raw mathematical approximation if the metadata doesn't track it immediately
                    token_count = len(prompt + response_text) // 4
                
            else:
                response_text = f"Unsupported provider: {provider}"
                
        except Exception as e:
            response_text = f"Generation Error: {str(e)}"
            
        latency_ms = (time.time() - start_time) * 1000
        return response_text, token_count, latency_ms

llm_manager = LLMManager()
