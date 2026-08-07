"""
NEXUS EDU — LLM Core Smoke Test.

Verifies the deterministic generation capabilities of the Instructor-patched
Groq client, enforcing the AI router matrix:
  1. Metadata Extraction (llama-3.1-8b-instant)
  2. JSON Output Generation (llama3-groq-70b-8192-tool-use-preview)
  3. Content Generation (llama-3.1-70b-versatile)
"""

import asyncio
import os
import sys
from typing import List

# Ensure we're running from the backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.llm import generate_structured_output, generate_content, LLMTaskType, StrictBaseModel
from pydantic import Field

# ── 1. Metadata Schema ───────────────────────────────────────
class ExtractedEntities(StrictBaseModel):
    """Schema for extracting named entities."""
    people: List[str] = Field(description="Names of people mentioned in the text")
    locations: List[str] = Field(description="Names of locations mentioned")

# ── 2. Complex JSON Schema ───────────────────────────────────
class QuizQuestion(StrictBaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 possible answers")
    correct_index: int = Field(description="0-based index of the correct answer")
    explanation: str = Field(description="Why the answer is correct")

class Quiz(StrictBaseModel):
    title: str = Field(description="Title of the quiz")
    difficulty: str = Field(description="easy, medium, or hard")
    questions: List[QuizQuestion] = Field(description="List of exactly 2 questions")


async def main():
    print("=" * 60)
    print("NEXUS EDU — LLM Core Smoke Test")
    print("=" * 60)

    try:
        # Test 1: Metadata Extraction (Fast Model)
        print("\n[1] Testing METADATA_EXTRACTION (llama-3.1-8b-instant)...")
        text = "Albert Einstein lived in Princeton, New Jersey, where he worked at the Institute for Advanced Study alongside Kurt Gödel."
        
        entities = await generate_structured_output(
            system_prompt="You are a precise entity extraction system.",
            user_prompt=f"Extract people and locations from this text:\n\n{text}",
            response_model=ExtractedEntities,
            task_type=LLMTaskType.METADATA_EXTRACTION
        )
        
        print(f"    [OK] Received Pydantic object: {type(entities).__name__}")
        print(f"    People: {entities.people}")
        print(f"    Locations: {entities.locations}")
        assert "Albert Einstein" in entities.people
        assert "Princeton" in [loc for loc in entities.locations if "Princeton" in loc]

        # Test 2: JSON Generation (Tool-use Model)
        print("\n[2] Testing JSON_GENERATION (llama3-groq-70b-8192-tool-use-preview)...")
        quiz = await generate_structured_output(
            system_prompt="You are an expert curriculum designer. Follow the schema exactly.",
            user_prompt="Generate a hard difficulty quiz about black holes with exactly 2 questions.",
            response_model=Quiz,
            task_type=LLMTaskType.JSON_GENERATION
        )
        
        print(f"    [OK] Received Pydantic object: {type(quiz).__name__}")
        print(f"    Title: {quiz.title} (Difficulty: {quiz.difficulty})")
        print(f"    Questions generated: {len(quiz.questions)}")
        assert len(quiz.questions) == 2
        for i, q in enumerate(quiz.questions):
            print(f"      Q{i+1}: {q.question}")
            assert len(q.options) == 4
            assert 0 <= q.correct_index < 4

        # Test 3: Content Generation (Versatile Model)
        print("\n[3] Testing CONTENT_GENERATION (llama-3.1-70b-versatile)...")
        content = await generate_content(
            system_prompt="You are an expert physicist. Be brief (max 2 sentences).",
            user_prompt="Explain Hawking radiation simply.",
            task_type=LLMTaskType.CONTENT_GENERATION
        )
        
        print(f"    [OK] Received string ({len(content)} chars)")
        print(f"    Content: {content.strip()}")

        print("\n" + "=" * 60)
        print("SMOKE TEST PASSED [OK]")
        print("=" * 60)

    except Exception as e:
        print("\n[!] SMOKE TEST FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
