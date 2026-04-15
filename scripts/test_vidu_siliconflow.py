#!/usr/bin/env python3
"""
Vidu via SiliconFlow 真实性验证脚本
验证步骤：
1. 提交 Vidu 视频生成任务
2. 轮询任务状态直到完成
3. 验证获得视频 URL
"""

import httpx
import asyncio
import time
import sys

# SiliconFlow 配置
API_KEY = "sk-eowsrtzbtuclrzxfnxsovicohkxnstpwgxoswsnjibchauji"
BASE_URL = "https://api.siliconflow.cn/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


async def submit_task(prompt: str, duration: int = 4, aspect_ratio: str = "16:9") -> str:
    """提交 Vidu 视频生成任务"""
    endpoint = f"{BASE_URL}/video/submit"
    
    payload = {
        "model": "vidu",
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "with_text": True,
    }
    
    print(f"[1] 提交任务到: {endpoint}")
    print(f"    Payload: {payload}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(endpoint, headers=HEADERS, json=payload)
        resp.raise_for_status()
        result = resp.json()
        
        task_id = result.get("task_id") or result.get("id")
        print(f"[1] ✓ 任务提交成功，task_id: {task_id}")
        return task_id


async def poll_status(task_id: str, max_wait: int = 300) -> dict:
    """轮询任务状态"""
    endpoint = f"{BASE_URL}/video/submit/{task_id}"
    
    print(f"[2] 开始轮询状态: {endpoint}")
    
    start_time = time.time()
    poll_count = 0
    
    while time.time() - start_time < max_wait:
        poll_count += 1
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(endpoint, headers=HEADERS)
            resp.raise_for_status()
            result = resp.json()
        
        status = result.get("status", "unknown")
        elapsed = int(time.time() - start_time)
        
        # 尝试多种可能的 video_url 字段
        video_url = (
            result.get("video_url") 
            or result.get("output", {}).get("video") 
            or result.get("url")
            or result.get("output", {}).get("url")
        )
        
        print(f"    [轮询 #{poll_count}] status={status}, elapsed={elapsed}s, video_url={video_url}")
        
        if status == "completed":
            print(f"[2] ✓ 任务完成！")
            return {
                "status": status,
                "video_url": video_url,
                "result": result,
            }
        elif status == "failed":
            error_msg = result.get("error", "未知错误")
            print(f"[2] ✗ 任务失败: {error_msg}")
            return {
                "status": status,
                "error": error_msg,
                "result": result,
            }
        
        # 根据状态调整等待时间
        wait_time = 5 if status in ("pending", "processing") else 10
        await asyncio.sleep(wait_time)
    
    print(f"[2] ✗ 轮询超时 ({max_wait}s)")
    return {"status": "timeout", "error": f"轮询超时 {max_wait}s"}


async def main():
    print("=" * 60)
    print("Vidu via SiliconFlow 真实性验证")
    print("=" * 60)
    
    # 测试 prompt
    test_prompt = "A beautiful anime girl walking in a cherry blossom garden, soft lighting, cinematic"
    
    try:
        # Step 1: 提交任务
        task_id = await submit_task(prompt=test_prompt, duration=4)
        
        # Step 2: 轮询状态
        result = await poll_status(task_id, max_wait=300)
        
        # Step 3: 验证结果
        print("\n" + "=" * 60)
        print("验证结果")
        print("=" * 60)
        
        if result["status"] == "completed" and result.get("video_url"):
            print(f"✓ Vidu 任务提交成功: task_id={task_id}")
            print(f"✓ 状态轮询到 completed")
            print(f"✓ 获得视频 URL: {result['video_url']}")
            print("\n验收标准全部通过！")
            return 0
        else:
            print(f"✗ 验收失败: {result}")
            return 1
            
    except httpx.HTTPStatusError as e:
        print(f"\n✗ HTTP 错误: {e.response.status_code} {e.response.text[:500]}")
        return 1
    except Exception as e:
        print(f"\n✗ 异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
