"""
NEXUS EDU — Orchestrator Integration Test.

Runs a full AI pipeline end-to-end to verify that the Orchestrator
correctly manages conversations, calls the generation service, saves
metadata to JSONB, and emits structured logs.
"""

import asyncio
import sys
import uuid
import logging
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

# Add backend dir to sys.path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.database import get_engine
from app.database.session import _get_factory
from app.models.user import User
from app.models.course import Course
from app.ai.orchestrator import AIOrchestrator
from app.schemas.lecture_notes import LectureNotes, LectureSection, KeyTerm, NotesMetadata

# Configure standard logging to show telemetry output
logging.basicConfig(level=logging.INFO)


# Mock the Generation Service handler so we don't need real Groq/Chroma for the test
async def mock_lecture_handler(course_id: str, topic: str, **kwargs) -> LectureNotes:
    """Mock the RAG + LLM execution of LectureGenerationService."""
    # Simulate API latency
    await asyncio.sleep(0.5)
    
    # Return a valid Pydantic model
    return LectureNotes(
        title="Intro to AI",
        course_name="Computer Science 101",
        learning_objectives=["By the end of this lecture, students will be able to understand AI.", "By the end of this lecture, students will be able to use AI."],
        sections=[
            LectureSection(
                section_number=1,
                heading="Intro to AI",
                content="Artificial Intelligence is a field of computer science that focuses on creating intelligent machines. " * 2,
                key_takeaway="AI exists and is a very cool concept that everyone should learn."
            )
        ],
        key_terms=[KeyTerm(term="AI", definition="Artificial Intelligence is the simulation of human intelligence processes by machines, especially computer systems.")],
        summary="A mock lecture on AI that covers all the required fields and character limits to pass Pydantic validation successfully without raising errors.",
        metadata=NotesMetadata(
            source_document_ids=["doc_1"],
            word_count=150,
            topics_covered=["AI", "Computer Science"]
        )
    )


import pytest

@pytest.mark.asyncio
async def test_orchestrator():
    factory = _get_factory()
    
    async with factory() as session:
        print("\n--- 1. Seed Database with User and Course ---")
        user = User(email=f"test_{uuid.uuid4()}@nexus.edu", full_name="Test User", hashed_password="pwd")
        session.add(user)
        await session.flush()
        
        course = Course(owner_id=user.id, name="Test Course 101")
        session.add(course)
        await session.flush()
        
        print(f"Created User: {user.id}")
        print(f"Created Course: {course.id}")
        
        print("\n--- 2. Initialize Orchestrator ---")
        orchestrator = AIOrchestrator(db_session=session)
        
        # Register the mock service
        orchestrator.register_service(
            action_type="generate_lecture",
            handler=mock_lecture_handler,
            prompt_name="lecture_prompt_v1"
        )
        print("Registered 'generate_lecture' service.")

        print("\n--- 3. Execute Request (New Conversation) ---")
        result = await orchestrator.execute(
            user_id=user.id,
            course_id=course.id,
            action_type="generate_lecture",
            topic="Introduction to Neural Networks"
        )
        
        conv_id = result['conversation_id']
        print(f"\nExecution successful!")
        print(f"Conversation ID: {conv_id}")
        print(f"Generated Payload: {result['data']['title']}")

        print("\n--- 4. Verify Database Persistence ---")
        # Let's read the messages back
        from app.repositories.conversation_repository import ConversationRepository
        repo = ConversationRepository(session)
        history = await repo.get_recent_history(uuid.UUID(conv_id), limit=10)
        
        print(f"\nMessages in DB: {len(history)}")
        for msg in history:
            print(f"- Role: {msg.role}")
            if msg.role == 'user':
                print(f"  Content: {msg.content}")
            else:
                print(f"  Metadata Latency: {msg.generation_metadata.get('latency_ms', 0):.2f}ms")
                print(f"  Structured Output Keys: {list(msg.structured_response.keys())}")
                
        # Rollback so we don't pollute the dev DB with test data
        await session.rollback()
        print("\nTest complete (rolled back test data).")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
