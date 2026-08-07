import asyncio
from app.ai.llm.llm_service import LLMService
from app.ai.rag.pipeline import RAGPipeline
from app.core.config import get_settings
from app.services.ppt.presentation_generation_service import PresentationGenerationService
from app.models.course import Course
import time

async def main():
    settings = get_settings()
    pipeline = RAGPipeline(settings)
    llm = LLMService()
    
    ppt_service = PresentationGenerationService(pipeline, llm)
    
    # We will mock the retrieve part since we don't have a DB/VectorDB setup here easily.
    # Actually, the user asked me to "fix this chek with small contents and number of slides get from user ... check with 3 slides and let me know"
    # To truly run this I might need a running API.
    # I can just start a test using httpx or requests against the local dev server if it's running.
    print("Test script ready.")

if __name__ == "__main__":
    asyncio.run(main())
