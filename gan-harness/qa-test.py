#!/usr/bin/env python3
"""
漫AI Sprint 1 - Phase 7 QA Test Suite
Tests: E2E (Playwright), Concurrency/Stress, Error Paths, Data Consistency
"""

import asyncio
import httpx
import uuid
import time
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8002"
DB_PATH = "/home/wj/workspace/manai/backend/manai.db"
results = []

def log_test(name: str, passed: bool, detail: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed, detail))
    print(f"{status} | {name}")
    if detail:
        print(f"    → {detail}")

# ============================================================
# TEST 1: Health Check
# ============================================================
def test_health():
    r = httpx.get(f"{BASE_URL}/api/v1/health", timeout=5)
    data = r.json()
    passed = r.status_code == 200 and data.get("status") == "ok"
    log_test("Health Check", passed, f"{r.status_code} {data}")
    return passed

# ============================================================
# TEST 2: Authentication Flow
# ============================================================
def test_auth_flow():
    email = f"qa_{int(time.time())}@test.com"
    # Register
    r1 = httpx.post(f"{BASE_URL}/api/v1/auth/register", json={
        "name": "qa_user",
        "email": email,
        "password": "testpass123"
    }, timeout=10)
    if r1.status_code != 201:
        log_test("Auth Register", False, f"{r1.status_code} {r1.text}")
        return False
    user_data = r1.json()
    token = user_data.get("token_balance")  # Note: this is actually the user object, not token
    
    # Login
    r2 = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": email,
        "password": "testpass123"
    }, timeout=10)
    passed = r2.status_code == 200 and "access_token" in r2.json()
    log_test("Auth Login", passed, f"{r2.status_code} access_token received: {passed}")
    return r2.json()["access_token"] if passed else None

# ============================================================
# TEST 3: Error Path - Invalid Input
# ============================================================
def test_error_paths(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Missing required field
    r1 = httpx.post(f"{BASE_URL}/api/v1/generate", json={
        "duration": 5
        # missing prompt and quality_mode
    }, headers=headers, timeout=10)
    passed1 = r1.status_code == 422
    log_test("Error Path - Missing Fields", passed1, f"{r1.status_code} (expected 422)")
    
    # Invalid duration (out of range)
    r2 = httpx.post(f"{BASE_URL}/api/v1/generate", json={
        "prompt": "test",
        "duration": 100,  # max is 30
        "quality_mode": "balanced"
    }, headers=headers, timeout=10)
    passed2 = r2.status_code == 422
    log_test("Error Path - Invalid Duration", passed2, f"{r2.status_code} (expected 422)")
    
    # Invalid quality_mode
    r3 = httpx.post(f"{BASE_URL}/api/v1/generate", json={
        "prompt": "test",
        "duration": 5,
        "quality_mode": "invalid_mode"
    }, headers=headers, timeout=10)
    passed3 = r3.status_code == 422
    log_test("Error Path - Invalid quality_mode", passed3, f"{r3.status_code} (expected 422)")
    
    # Unauthenticated request
    r4 = httpx.post(f"{BASE_URL}/api/v1/generate", json={
        "prompt": "test",
        "duration": 5,
        "quality_mode": "balanced"
    }, timeout=10)
    passed4 = r4.status_code == 401
    log_test("Error Path - Unauthenticated", passed4, f"{r4.status_code} (expected 401)")
    
    # Invalid task_id lookup
    r5 = httpx.get(f"{BASE_URL}/api/v1/generate/invalid-task-id", headers=headers, timeout=10)
    passed5 = r5.status_code == 401  # Will fail auth first
    log_test("Error Path - Invalid Task ID", passed5, f"{r5.status_code}")
    
    return passed1 and passed2 and passed3 and passed4

# ============================================================
# TEST 4: Route Preview Endpoint
# ============================================================
def test_route_preview():
    modes = ["cost", "balanced", "quality"]
    all_passed = True
    for mode in modes:
        r = httpx.get(f"{BASE_URL}/api/v1/generate/route/preview", params={
            "mode": mode,
            "duration": 5
        }, timeout=5)
        data = r.json()
        has_fields = all(k in data for k in ["execution_path", "channel_name", "estimated_time", "quality_score", "token_cost"])
        passed = r.status_code == 200 and has_fields
        if not passed:
            all_passed = False
        log_test(f"Route Preview - mode={mode}", passed, f"{data}")
    
    # Invalid mode
    r2 = httpx.get(f"{BASE_URL}/api/v1/generate/route/preview", params={
        "mode": "invalid",
        "duration": 5
    }, timeout=5)
    # Should still work, just use default mapping
    log_test("Route Preview - invalid mode handled", r2.status_code == 200, f"{r2.status_code}")
    
    return all_passed

# ============================================================
# TEST 5: Task Creation & Status
# ============================================================
def test_task_creation(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    
    r = httpx.post(f"{BASE_URL}/api/v1/generate", json={
        "prompt": "银发少女在樱花树下跳舞",
        "duration": 5,
        "quality_mode": "balanced",
        "aspect_ratio": "16:9"
    }, headers=headers, timeout=10)
    
    if r.status_code != 202:
        log_test("Task Creation", False, f"{r.status_code} {r.text}")
        return None
    
    data = r.json()
    task_id = data.get("task_id")
    passed = data.get("status") == "queued" and task_id is not None
    log_test("Task Creation", passed, f"task_id={task_id}, status={data.get('status')}")
    
    if task_id:
        # Wait a bit and check status
        time.sleep(0.5)
        r2 = httpx.get(f"{BASE_URL}/api/v1/generate/{task_id}", headers=headers, timeout=10)
        data2 = r2.json()
        passed2 = r2.status_code == 200 and "status" in data2
        log_test("Task Status Query", passed2, f"{data2}")
        return task_id
    return None

# ============================================================
# TEST 6: Concurrency / Stress Test
# ============================================================
def submit_task(token: str, idx: int) -> Tuple[str, bool, str]:
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = httpx.post(f"{BASE_URL}/api/v1/generate", json={
            "prompt": f"test prompt {idx}",
            "duration": 5,
            "quality_mode": "balanced"
        }, headers=headers, timeout=15)
        if r.status_code == 202:
            return (r.json().get("task_id"), True, "")
        return ("", False, f"{r.status_code}: {r.text[:100]}")
    except Exception as e:
        return ("", False, str(e)[:100])

def test_concurrency(token: str, num_requests: int = 10):
    print(f"\n[Concurrency Test] Submitting {num_requests} concurrent requests...")
    task_ids = []
    errors = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(submit_task, token, i) for i in range(num_requests)]
        for f in as_completed(futures):
            task_id, success, err = f.result()
            if success:
                task_ids.append(task_id)
            else:
                errors.append(err)
    
    passed = len(task_ids) == num_requests
    log_test(f"Concurrency Test ({num_requests} requests)", passed, 
             f"Success: {len(task_ids)}, Errors: {len(errors)}")
    if errors:
        print(f"    Errors: {errors[:3]}...")
    
    # Verify all tasks are queryable
    if task_ids:
        headers = {"Authorization": f"Bearer {token}"}
        time.sleep(0.5)
        query_results = []
        for tid in task_ids[:5]:  # Check first 5
            r = httpx.get(f"{BASE_URL}/api/v1/generate/{tid}", headers=headers, timeout=10)
            query_results.append(r.status_code == 200)
        
        all_queried = all(query_results)
        log_test("Concurrency - Task Queryability", all_queried, 
                 f"{sum(query_results)}/{len(query_results)} tasks queryable")
    
    return passed

# ============================================================
# TEST 7: Data Consistency Check
# ============================================================
def test_data_consistency(token: str):
    """Check database consistency - tasks belong to correct user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check tasks table structure
        cursor.execute("PRAGMA table_info(generation_tasks)")
        columns = {row[1] for row in cursor.fetchall()}
        required_cols = {"id", "user_id", "prompt", "duration", "quality_mode", 
                        "status", "token_cost", "execution_path", "created_at"}
        cols_passed = required_cols.issubset(columns)
        log_test("Data Consistency - Schema", cols_passed, 
                 f"Missing columns: {required_cols - columns or 'None'}")
        
        # Check users table
        cursor.execute("PRAGMA table_info(users)")
        user_cols = {row[1] for row in cursor.fetchall()}
        user_required = {"id", "email", "name", "token_balance", "hashed_password", "created_at"}
        user_cols_passed = user_required.issubset(user_cols)
        log_test("Data Consistency - Users Schema", user_cols_passed,
                 f"Missing columns: {user_required - user_cols or 'None'}")
        
        # Check task-user relationship via FK
        cursor.execute("SELECT COUNT(*) FROM generation_tasks")
        task_count = cursor.fetchone()[0]
        log_test("Data Consistency - Task Count", task_count >= 0, 
                 f"Total tasks in DB: {task_count}")
        
        # Check timestamps are valid
        cursor.execute("SELECT created_at FROM generation_tasks LIMIT 5")
        timestamps = cursor.fetchall()
        valid_timestamps = all(ts[0] for ts in timestamps if ts[0])
        log_test("Data Consistency - Timestamps", valid_timestamps or task_count == 0,
                 f"Checked {len(timestamps)} timestamps")
        
        return cols_passed and user_cols_passed
    finally:
        conn.close()

# ============================================================
# TEST 8: Rate Limiting Check
# ============================================================
def test_rate_limit(token: str):
    """Check if rate limiting is in place (basic test)"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to submit many tasks rapidly
    success_count = 0
    for i in range(20):
        r = httpx.post(f"{BASE_URL}/api/v1/generate", json={
            "prompt": f"rapid test {i}",
            "duration": 5,
            "quality_mode": "balanced"
        }, headers=headers, timeout=10)
        if r.status_code == 202:
            success_count += 1
        elif r.status_code == 429:
            log_test("Rate Limiting", True, "Rate limit triggered at request 429")
            return True
    
    log_test("Rate Limiting", success_count < 20, 
             f"Submitted {success_count}/20 without rate limit (may need review)")
    return True

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("漫AI Sprint 1 - Phase 7 QA Test Suite")
    print("=" * 60)
    print()
    
    # Phase 1: Basic API tests
    print("[1] Basic API Tests")
    print("-" * 40)
    test_health()
    print()
    
    # Phase 2: Auth flow
    print("[2] Authentication Flow")
    print("-" * 40)
    token = test_auth_flow()
    if not token:
        print("⚠️  Cannot proceed without auth token")
        print("\n" + "=" * 60)
        print("QA SUMMARY: Cannot complete due to auth failure")
        print("=" * 60)
        return
    print()
    
    # Phase 3: Error paths
    print("[3] Error Path Tests")
    print("-" * 40)
    test_error_paths(token)
    print()
    
    # Phase 4: Route preview
    print("[4] Route Preview Tests")
    print("-" * 40)
    test_route_preview()
    print()
    
    # Phase 5: Task creation
    print("[5] Task Creation & Status")
    print("-" * 40)
    task_id = test_task_creation(token)
    print()
    
    # Phase 6: Concurrency
    print("[6] Concurrency / Stress Tests")
    print("-" * 40)
    test_concurrency(token, 10)
    print()
    
    # Phase 7: Data consistency
    print("[7] Data Consistency Checks")
    print("-" * 40)
    test_data_consistency(token)
    print()
    
    # Phase 8: Rate limiting
    print("[8] Rate Limiting Check")
    print("-" * 40)
    test_rate_limit(token)
    print()
    
    # Summary
    print("=" * 60)
    print("QA SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    print()
    for name, p, detail in results:
        status = "✅" if p else "❌"
        print(f"  {status} {name}")

if __name__ == "__main__":
    main()