# 🏢 Hermes Agent 服务公司

通用多任务Agent协作系统，支持技术开发、研究分析、内容创作三大业务类型。

## 组织架构

```
[用户/客户]
       ↓
[CEO - 主Agent扮演]
       ↓
┌─────────────────────────────────────┐
│  Engineer  │  Researcher  │ Creator  │
│   (开发)   │   (研究)     │  (创作)  │
└─────────────────────────────────────┘
```

## 业务类型

| Agent | 任务类型 | 工具 | 特殊规则 |
|-------|---------|------|---------|
| **Engineer** | 开发/代码/系统/网站 | terminal+file+web | **开发任务启用GAN Phase 0-8** |
| **Researcher** | 调研/资料/竞品/分析 | web+file | 搜索：GitHub/微信/头条/小红书/Google |
| **Creator** | 方案/文案/脚本/内容 | file+web | 创作流程：需求确认→创作→修订→定稿 |

## 任务路由

```
用户输入
    ↓
含"开发/代码/系统/网站" → Engineer（启用GAN）
含"调研/分析/竞品/资料" → Researcher
含"方案/文案/脚本/创作" → Creator
混合类型 → 并行分配多个执行者
```

## GAN开发流程（仅Engineer+开发任务）

```
Phase 0: PRD质疑 → Phase 1: 规格制定 → Phase 2: Sprint计划
Phase 3: 评分 → Phase 4: 修复(如有) → Phase 5: 代码审查
Phase 6: 知识沉淀 → Phase 7: QA → Phase 8: 发布
```

评分 < 7.0 自动进入修复循环，最多3次。

## 搜索范围（Researcher）

- **GitHub**：技术文档、开源项目、代码示例
- **微信公众号**：行业观察、产品动态、案例分析
- **今日头条**：国内热点、行业资讯、政策动向
- **小红书**：消费趋势、用户洞察、种草内容
- **Google/外网**：全球资讯、学术论文、竞品动态

## 项目追踪

项目状态：`NEW → IN_REVIEW → ASSIGNED → IN_PROGRESS → DELIVERED → COMPLETED`

满载时（3个执行者都在忙）：`QUEUED` 排队等待

状态文件：`hermes-company/shared/project-registry.json`

## 启动方式

```bash
# 输入任务即可，例如：
"帮我开发一个博客系统"
"调研一下竞品的产品功能"
"写一个产品发布会视频脚本"
```

## 交付物结构

```
projects/
└── {project_id}/
    ├── spec.md           # 项目规格
    ├── gan-harness/      # 仅开发类
    │   ├── spec.md
    │   ├── eval-rubric.md
    │   └── feedback/
    └── deliverable/      # 最终交付物
        ├── code/        # Engineer产出
        ├── report/     # Researcher产出
        └── content/    # Creator产出
```
