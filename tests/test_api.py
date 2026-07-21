"""集成测试 - 测试 API 端点"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_root():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_voices():
    """测试语音列表端点"""
    response = client.get("/voices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "voice_id" in data[0]


def test_languages():
    """测试语言列表端点"""
    response = client.get("/languages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "auto" in data or "zh" in data


if __name__ == "__main__":
    test_root()
    test_health()
    test_voices()
    test_languages()
    print("All tests passed!")
