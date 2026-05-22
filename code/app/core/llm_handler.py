import os
import logging
from groq import AsyncGroq
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LLMHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMHandler, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.groq_api_key:
            self.groq_client = AsyncGroq(api_key=self.groq_api_key)
        else:
            self.groq_client = None
            
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        self.system_prompt = "You are a helpful assistant for Cloud Counselage internship program. Answer concisely and professionally. If unsure, say so."

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_groq(self, messages, max_tokens):
        if not self.groq_client:
            raise ValueError("Groq client not initialized")
        response = await self.groq_client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
            max_tokens=max_tokens,
            temperature=0.7,
            timeout=30.0
        )
        return response.choices[0].message.content

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _call_openai(self, messages, max_tokens):
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        response = await self.openai_client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
            max_tokens=max_tokens,
            temperature=0.7,
            timeout=30.0
        )
        return response.choices[0].message.content

    async def generate(self, prompt: str, context_history: list = None, max_tokens: int = 500) -> str:
        if context_history is None:
            context_history = []
            
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for exchange in context_history:
            if "user" in exchange:
                messages.append({"role": "user", "content": exchange["user"]})
            if "bot" in exchange:
                messages.append({"role": "assistant", "content": exchange["bot"]})
                
        messages.append({"role": "user", "content": prompt})
        
        try:
            return await self._call_groq(messages, max_tokens)
        except Exception as e:
            logger.warning(f"Groq API failed: {e}. Falling back to OpenAI...")
            try:
                return await self._call_openai(messages, max_tokens)
            except Exception as e2:
                logger.error(f"OpenAI API also failed: {e2}")
                return "I apologize, but I am currently experiencing technical difficulties. Please try again later."
