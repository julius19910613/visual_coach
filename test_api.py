#!/usr/bin/env python3
"""Test script for Visual Coach API."""

import sys
from pathlib import Path

import requests

# API base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✓ Health check passed\n")


def test_root():
    """Test root endpoint."""
    print("Testing / endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Root endpoint passed\n")


def test_video_upload(video_path: str):
    """Test video upload and analysis."""
    print(f"Testing /api/analyze with video: {video_path}")

    video_file = Path(video_path)
    if not video_file.exists():
        print(f"Error: Video file not found: {video_path}")
        return False

    with open(video_file, "rb") as f:
        files = {"file": (video_file.name, f, "video/mp4")}
        response = requests.post(f"{BASE_URL}/api/analyze", files=files)

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("✓ Analysis successful!")
        print(f"Player summary: {result.get('player_summary', 'N/A')}")
        print(f"Content focus: {result.get('content_focus', 'N/A')}")
        print(f"Offense score: {result['dimensions']['offense'].get('score', 'N/A')}")
        print(f"Defense score: {result['dimensions']['defense'].get('score', 'N/A')}")
        print(f"Improvements: {len(result.get('improvements', []))} suggestions")
        return True
    else:
        print(f"✗ Analysis failed: {response.text}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Visual Coach API Test Suite")
    print("=" * 60)
    print()

    try:
        test_health()
        test_root()

        if len(sys.argv) > 1:
            # Test with provided video file
            video_path = sys.argv[1]
            success = test_video_upload(video_path)
            if not success:
                sys.exit(1)
        else:
            print("No video file provided. Skipping video upload test.")
            print("Usage: python test_api.py <video_file_path>")

        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server.")
        print(f"Make sure the server is running at {BASE_URL}")
        print("Start with: python run_api.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
