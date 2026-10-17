import os
import json
import logging
from typing import Dict, Any, List, Optional
from backend.config import GEMINI_API_KEY, OPENROUTER_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.gemini_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.openrouter_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
        self.model = LLM_MODEL or "gemini-2.5-flash"
        
        self.genai_client = None
        if self.gemini_key:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.gemini_key)
                logger.info("Google GenAI client initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI client: {e}")

        self.openai_client = None
        if self.openrouter_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter_key
                )
                logger.info("OpenRouter OpenAI client initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter client: {e}")

    def _ensure_clients(self):
        from dotenv import load_dotenv
        from backend.config import ROOT_DIR
        load_dotenv(ROOT_DIR / ".env", override=True)
        key = os.getenv("GEMINI_API_KEY", "")
        model_env = os.getenv("LLM_MODEL", "")
        if model_env:
            self.model = model_env
        if key and (not self.genai_client or key != self.gemini_key):
            self.gemini_key = key
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.gemini_key)
                logger.info("Google GenAI client initialized dynamically.")
            except Exception as e:
                logger.warning(f"Failed to dynamically initialize GenAI client: {e}")

    def generate_chat_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.2
    ) -> Optional[str]:
        self._ensure_clients()
        # 1. Try Google GenAI Client
        if self.genai_client:
            from google.genai import types

            models_to_try = []
            if self.model and "gemma" not in self.model:
                models_to_try.append(self.model)
            models_to_try.append("gemini-3.8-flash")
            for fallback in ["gemini-2.0-flash", "gemini-1.5-flash", "gemma-4-26b-a4b-it", "gemma-4-31b-it"]:
                if fallback not in models_to_try:
                    models_to_try.append(fallback)

            # Build structured contents for multi-turn chat
            structured_contents = []
            for m in messages:
                role = "user" if m.get("role") == "user" else "model"
                content_text = m.get("content", "")
                structured_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=content_text)]
                    )
                )

            # Build flat prompt fallback for models that don't support system_instruction
            flat_prompt = f"{system_prompt}\n\n"
            for m in messages:
                flat_prompt += f"{m['role'].upper()}: {m['content']}\n"
            flat_prompt += "ASSISTANT:"

            for mdl in models_to_try:
                # Attempt 1: Native system_instruction + structured chat contents
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        max_output_tokens=2048
                    )
                    resp = self.genai_client.models.generate_content(
                        model=mdl,
                        contents=structured_contents,
                        config=config
                    )
                    if resp and resp.text:
                        return resp.text.strip()
                except Exception as e_structured:
                    logger.debug(f"GenAI structured chat with {mdl} note: {e_structured}")
                    # Attempt 2: Fallback to flat prompt
                    try:
                        resp = self.genai_client.models.generate_content(
                            model=mdl,
                            contents=flat_prompt
                        )
                        if resp and resp.text:
                            return resp.text.strip()
                    except Exception as e_flat:
                        logger.warning(f"Google GenAI call with {mdl} failed: {e_flat}")

        # 2. Try OpenRouter OpenAI Client
        if self.openai_client:
            try:
                formatted_msgs = [{"role": "system", "content": system_prompt}] + messages
                model_name = "google/gemma-4-31b-it:free" if "gemma" in self.model else self.model
                resp = self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=formatted_msgs,
                    temperature=temperature
                )
                if resp.choices and resp.choices[0].message.content:
                    return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"OpenRouter API call failed: {e}")

        return None
