"""
Test script for YouTube RAG endpoints.
"""

import sys
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.youtube import _get_youtube_service
from app.api.dependencies import get_current_user, get_user_workspace
from app.database.session import get_db_session
import uuid

client = TestClient(app)


def test_youtube_endpoints():
    mock_service = MagicMock()
    mock_service.process_youtube_video = AsyncMock(return_value={
        "message": "YouTube video processed successfully",
        "video_id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "source": "youtube",
    })
    mock_service.chat_with_youtube_video = AsyncMock(return_value={
        "answer": "The video is about never giving you up.",
        "sources": [{"video_id": "dQw4w9WgXcQ", "title": "Rick Astley", "url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}],
    })

    app.dependency_overrides[_get_youtube_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: MagicMock(id=uuid.uuid4(), is_active=True)
    app.dependency_overrides[get_user_workspace] = lambda: uuid.uuid4()
    app.dependency_overrides[get_db_session] = lambda: AsyncMock()

    # 1. Test POST /youtube/upload
    res_upload = client.post("/youtube/upload", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert res_upload.status_code == 200, res_upload.text
    data_upload = res_upload.json()
    assert data_upload["video_id"] == "dQw4w9WgXcQ"
    assert data_upload["source"] == "youtube"
    print("Upload test passed!")

    # 2. Test POST /youtube/chat
    res_chat = client.post("/youtube/chat", json={"video_id": "dQw4w9WgXcQ", "question": "What is the topic?"})
    assert res_chat.status_code == 200, res_chat.text
    data_chat = res_chat.json()
    assert "answer" in data_chat
    assert len(data_chat["sources"]) == 1
    print("Chat test passed!")

    app.dependency_overrides.clear()


if __name__ == "__main__":
    test_youtube_endpoints()
