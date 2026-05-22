import json
import logging
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

class FAQEngine:
    _instance = None
    _model = None
    _faq_data = []
    _faq_embeddings = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FAQEngine, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        if self._model is not None:
            return
        try:
            logger.info("Loading sentence-transformer model 'all-MiniLM-L6-v2'...")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Loading FAQ data...")
            with open("app/models/faq_data.json", "r", encoding="utf-8") as f:
                self._faq_data = json.load(f)
            
            questions = [item["question"] for item in self._faq_data]
            logger.info("Encoding FAQ questions...")
            self._faq_embeddings = self._model.encode(questions, convert_to_tensor=True)
            logger.info("FAQEngine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize FAQEngine: {e}")
            self._model = None

    def get_answer(self, query: str) -> dict:
        if self._model is None or self._faq_embeddings is None:
            return {"source": "error", "answer": "FAQ engine not available.", "confidence": 0.0}

        query_embedding = self._model.encode(query, convert_to_tensor=True)
        cosine_scores = util.cos_sim(query_embedding, self._faq_embeddings)[0]
        
        best_score_idx = cosine_scores.argmax().item()
        best_score = cosine_scores[best_score_idx].item()
        
        if best_score >= 0.7:
            return {
                "source": "faq",
                "answer": self._faq_data[best_score_idx]["answer"],
                "confidence": best_score
            }
        else:
            return {
                "source": "llm",
                "answer": None,
                "confidence": best_score
            }
