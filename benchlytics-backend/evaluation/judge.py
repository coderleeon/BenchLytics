from google import genai
import json
import yaml
import os
from dotenv import load_dotenv
import re

load_dotenv()

class JudgeEngine:
    def __init__(self, config_path: str = "config/models.yaml"):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            self.judge_model_id = config.get("judge", {}).get("model_id", "gemini-1.5-pro")
            
        # Initialize the new genai client
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

    async def evaluate(self, task: str, response_text: str) -> dict:
        prompt = f'''
        You are an elite LLM evaluator. Your task is to judge an AI's response to the given prompt.
        
        [TASK/PROMPT]
        {task}
        
        [AI RESPONSE START]
        {response_text}
        [AI RESPONSE END]
        
        Evaluate the response on the following criteria. Return ONLY a valid JSON object matching this schema, completely unformatted (no markdown blocks or backticks):
        {{
            "correctness": <float 0.0 to 10.0 representing factual accuracy and instruction following>,
            "clarity": <float 0.0 to 10.0 representing readability, structure, and conciseness>,
            "reasoning": <float 0.0 to 10.0 representing logical soundness and step-by-step coherence>,
            "confidence_score": <float 0.0 to 10.0 representing YOUR confidence in this evaluation>,
            "hallucination_flag": <integer 0 or 1, where 1 means the response contains clear fabrications>
        }}
        '''
        
        try:
            # We use text output and parse JSON utilizing the new genai syntax
            eval_result = self.client.models.generate_content(
                model=self.judge_model_id,
                contents=prompt
            )
            # Find JSON block just in case there are markdown tags
            text = eval_result.text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                clean_json = match.group(0)
                scores = json.loads(clean_json)
                return {
                    "score_correctness": float(scores.get("correctness", 0)),
                    "score_clarity": float(scores.get("clarity", 0)),
                    "score_reasoning": float(scores.get("reasoning", 0)),
                    "confidence_score": float(scores.get("confidence_score", 0)),
                    "hallucination_flag": int(scores.get("hallucination_flag", 0))
                }
        except Exception as e:
            print(f"Eval Error: {e}")
            
        # Fallback empty metrics on failure
        return {
            "score_correctness": 0.0,
            "score_clarity": 0.0,
            "score_reasoning": 0.0,
            "confidence_score": 0.0,
            "hallucination_flag": 1
        }

judge_engine = JudgeEngine()
