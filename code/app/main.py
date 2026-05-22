import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core import FAQEngine, LLMHandler, ContextManager, SpeechProcessor
from app.platforms import handle_whatsapp, handle_telegram, handle_messenger, handle_instagram

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Singletons
faq_engine = FAQEngine()
llm_handler = LLMHandler()
context_mgr = ContextManager()
speech_processor = SpeechProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    context_mgr.initialize()
    llm_handler.initialize()
    speech_processor.initialize()
    faq_engine.initialize()
    yield
    logger.info("Shutting down application...")

app = FastAPI(title="Multi-Platform AI Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/webhook/whatsapp")
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    return await handle_whatsapp(request, faq_engine, llm_handler, context_mgr, speech_processor)

@app.get("/webhook/telegram")
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    return await handle_telegram(request, faq_engine, llm_handler, context_mgr, speech_processor)

@app.get("/webhook/messenger")
@app.post("/webhook/messenger")
async def messenger_webhook(request: Request):
    return await handle_messenger(request, faq_engine, llm_handler, context_mgr, speech_processor)

@app.get("/webhook/instagram")
@app.post("/webhook/instagram")
async def instagram_webhook(request: Request):
    return await handle_instagram(request, faq_engine, llm_handler, context_mgr, speech_processor)
