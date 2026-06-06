from __future__ import annotations

import os
import sys
import time

os.environ["XENGINEER_DATA_ROOT"] = os.path.join(os.environ["TEMP"], "xengineer-debug")

from app.main import create_app
from fastapi.testclient import TestClient

client = TestClient(create_app())

# Create project
r = client.post("/api/projects", json={"title": "Debug", "logline": "Test", "target_format": "web_series"})
print(f"Create project: {r.status_code}")
project_id = r.json()["id"]
print(f"Project ID: {project_id}")

# Save 2 chapters
chapters = {"chapters": [{"title": f"Ch{i}", "text": f"Text {i}"} for i in range(1, 3)]}
r = client.put(f"/api/projects/{project_id}/chapters", json=chapters)
print(f"2 chapters: {r.status_code}")
print(f"  IDs: {[c['id'] for c in r.json()]}")

# Reject 2 chapters
r = client.post(f"/api/projects/{project_id}/generate/screenplay", json={})
print(f"Reject 2 chapters: {r.status_code}")

# Save 3 chapters
chapters = {"chapters": [{"title": f"Ch{i}", "text": f"Text {i}"} for i in range(1, 4)]}
r = client.put(f"/api/projects/{project_id}/chapters", json=chapters)
print(f"3 chapters: {r.status_code}")

# Trigger generate
r = client.post(f"/api/projects/{project_id}/generate/screenplay", json={})
print(f"Generate: {r.status_code}")
print(f"  Response: {r.json()}")
job_id = r.json()["job_id"]

# Wait & poll
for i in range(20):
    time.sleep(0.3)
    r = client.get(f"/api/jobs/{job_id}")
    job_data = r.json()
    print(f"  Poll {i}: status={job_data['status']}, step={job_data['current_step']}, error={job_data.get('error')}")
    if job_data["status"] in ("succeeded", "failed"):
        break

print(f"\nFinal job: {job_data}")
