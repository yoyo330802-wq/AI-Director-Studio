# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**漫AI (ManAI)** - Anime video generation Token platform. Uses a hybrid architecture combining self-hosted Wan2.1 on ComfyUI with SiliconFlow/Vidu commercial APIs, with an intelligent smart router that routes requests based on cost/balanced/quality modes.

## Architecture

```
Frontend (Next.js 14) → Nginx/Kong Gateway → Backend (FastAPI)
                                                   ↓
                          ┌────────────────────────┼────────────────────────┐
                          ↓                        ↓                        ↓
                    ComfyUI                  SiliconFlow                 Vidu
                   (Wan2.1 self-hosted)      (KLing, etc.)           (direct API)
```

### Backend Structure (`backend/app/`)
- `api/` - REST endpoints (generate, auth, billing, payment, moderation, hermes)
- `clients/` - Upstream API clients (comfyui, siliconflow, vidu, wan21)
- `router/` - Smart router that selects optimal generation channel
- `services/` - Business logic (cache, billing, oss, content_moderation, monitoring)
- `tasks/` - Celery async tasks for video generation
- `hermes/` - **Hermes multi-agent orchestration (GAN workflow executor)**
- `config.py` - All configuration via pydantic-settings

### Hermes Integration (`backend/app/hermes/`)
- `models.py` - HermesTask, HermesEvent data models
- `state.py` - State management (Redis realtime + PostgreSQL persistence)
- `router.py` - Task router (keywords → Agent type)
- `gan_runner.py` - **True GAN Runner, calls sub-agents to execute**
- `executor.py` - Docker container Agent executor
- `evolution.py` - Evolution mechanism (execution logs, decision library, Prompt optimization)

### Frontend Structure (`frontend/`)
- `app/studio/` - Main video generation page
- `app/gallery/` - Video gallery
- `app/pricing/` - Package purchase page
- `lib/api.ts` - API client with interceptors

## Common Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Celery worker (for async video generation)
celery -A app.tasks.video_generation worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Dev server on port 3000
npm run build    # Production build
npm run lint     # ESLint
```

### Docker (Production)
```bash
docker-compose -f deployment/docker-compose.yml up -d

# Build Hermes agent image
docker build -t manai/hermes-agent:latest hermes-company/
```

## API Conventions

- Base path: `/api/v1/`
- Auth: `Authorization: Bearer <JWT>`
- Error format: `{"detail": "error message"}`
- Pagination: `{"total": N, "items": [...], "page": N, "limit": N}`
- All video generation endpoints must have `response_model` defined

## Smart Router Modes

| Mode | Route | Price |
|------|-------|-------|
| `cost` | Wan2.1-1.3B via ComfyUI | ¥0.04/s |
| `balanced` | 70% Wan2.1 + 30% Vidu | ¥0.06/s |
| `quality` | Vidu/KLing via SiliconFlow | ¥0.09/s |

## Critical Issues (Auto-Fail Criteria)

The following issues will cause automatic rejection:
- Missing `response_model` on API endpoints
- JSON response serialized as string instead of proper JSON
- Data that should be deleted is instead soft-deleted or hidden
- Wrong execution path in smart router
- Hardcoded API keys or credentials

## GAN Evaluation Workflow

This project uses an 8-phase GAN workflow (executed by Hermes sub-agents):
1. **Phase 0**: PRD质疑 → **planner agent**
2. **Phase 1**: SPEC生成 → **planner agent**
3. **Phase 2**: Sprint Contract → **planner agent**
4. **Phase 3**: GAN评分 → **reviewer agent** (score < 7.0 = FAIL)
5. **Phase 4**: Fix loop → **coder agent**
6. **Phase 5**: Code review → **reviewer agent**
7. **Phase 6**: Knowledge consolidation → **writer agent**
8. **Phase 7**: QA testing
9. **Phase 8**: Git push

Pass threshold: **7.0** weighted average across 7 dimensions (Feature 25%, Functionality 20%, Code Quality 20%, Visual 15%, AI Integration 10%, Security 5%, Performance 5%).

## Configuration

All config via environment variables in `backend/app/config.py`. See `deployment/.env.example` for required variables. Never commit secrets.

## Upstream Clients

- `backend/app/clients/comfyui_client.py` - Self-hosted Wan2.1 on H100 cluster
- `backend/app/clients/siliconflow_client.py` - Multi-model proxy (Vidu, KLing, etc.)
- `backend/app/clients/vidu_client.py` - Direct Vidu API
