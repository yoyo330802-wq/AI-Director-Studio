"""
漫AI - 数据库索引优化
Sprint 5: S5-F2 数据库索引优化

PostgreSQL索引最佳实践:
1. 高频查询字段建立索引
2. 复合索引遵循最左前缀原则
3. 避免过多索引(影响写入性能)
4. 使用覆盖索引优化查询
"""
from sqlalchemy import Index, text
from sqlalchemy.orm import Session


class IndexOptimizer:
    """数据库索引优化器"""
    
    # 需要创建的索引
    INDEXES = [
        # === 用户表索引 ===
        ("idx_users_email", "users", ["email"]),
        ("idx_users_phone", "users", ["phone"]),
        ("idx_users_level", "users", ["level"]),
        ("idx_users_is_active", "users", ["is_active"]),
        ("idx_users_is_vip", "users", ["is_vip"]),
        ("idx_users_created_at", "users", ["created_at"]),
        # 用户复合索引
        ("idx_users_level_active", "users", ["level", "is_active"]),
        ("idx_users_vip_expires", "users", ["is_vip", "vip_expires_at"]),
        
        # === 订单表索引 ===
        ("idx_orders_user_id", "orders", ["user_id"]),
        ("idx_orders_order_no", "orders", ["order_no"]),
        ("idx_orders_status", "orders", ["status"]),
        ("idx_orders_created_at", "orders", ["created_at"]),
        # 订单复合索引
        ("idx_orders_user_status", "orders", ["user_id", "status"]),
        ("idx_orders_user_created", "orders", ["user_id", "created_at"]),
        ("idx_orders_package_status", "orders", ["package_id", "status"]),
        
        # === 套餐表索引 ===
        ("idx_packages_level", "packages", ["level"]),
        ("idx_packages_is_active", "packages", ["is_active"]),
        ("idx_packages_is_recommended", "packages", ["is_recommended"]),
        ("idx_packages_sort_order", "packages", ["sort_order"]),
        # 套餐复合索引
        ("idx_packages_active_sort", "packages", ["is_active", "sort_order"]),
        
        # === 任务表索引 ===
        ("idx_tasks_user_id", "tasks", ["user_id"]),
        ("idx_tasks_task_no", "tasks", ["task_no"]),
        ("idx_tasks_status", "tasks", ["status"]),
        ("idx_tasks_created_at", "tasks", ["created_at"]),
        ("idx_tasks_external_task_id", "tasks", ["external_task_id"]),
        # 任务复合索引
        ("idx_tasks_user_status", "tasks", ["user_id", "status"]),
        ("idx_tasks_user_created", "tasks", ["user_id", "created_at"]),
        ("idx_tasks_status_created", "tasks", ["status", "created_at"]),
        ("idx_tasks_channel_status", "tasks", ["channel", "status"]),
        
        # === 视频表索引 ===
        ("idx_videos_user_id", "videos", ["user_id"]),
        ("idx_videos_task_id", "videos", ["task_id"]),
        ("idx_videos_is_public", "videos", ["is_public"]),
        ("idx_videos_is_featured", "videos", ["is_featured"]),
        ("idx_videos_category", "videos", ["category"]),
        ("idx_videos_created_at", "videos", ["created_at"]),
        # 视频复合索引
        ("idx_videos_user_created", "videos", ["user_id", "created_at"]),
        ("idx_videos_public_created", "videos", ["is_public", "created_at"]),
        ("idx_videos_featured_public", "videos", ["is_featured", "is_public"]),
        ("idx_videos_category_public", "videos", ["category", "is_public"]),
        
        # === 支付交易表索引 ===
        ("idx_payment_transactions_order_id", "payment_transactions", ["order_id"]),
        ("idx_payment_transactions_transaction_no", "payment_transactions", ["transaction_no"]),
        ("idx_payment_transactions_status", "payment_transactions", ["status"]),
        ("idx_payment_transactions_created_at", "payment_transactions", ["created_at"]),
        # 交易复合索引
        ("idx_payment_transactions_order_status", "payment_transactions", ["order_id", "status"]),
        
        # === 渠道配置表索引 ===
        ("idx_channel_configs_channel_type", "channel_configs", ["channel_type"]),
        ("idx_channel_configs_is_enabled", "channel_configs", ["is_enabled"]),
        ("idx_channel_configs_is_primary", "channel_configs", ["is_primary"]),
        
        # === 系统配置表索引 ===
        ("idx_system_configs_key", "system_configs", ["key"]),
        ("idx_system_configs_is_public", "system_configs", ["is_public"]),
        
        # === 视频模板表索引 ===
        ("idx_video_templates_category", "video_templates", ["category"]),
        ("idx_video_templates_is_active", "video_templates", ["is_active"]),
        ("idx_video_templates_is_official", "video_templates", ["is_official"]),
        ("idx_video_templates_created_at", "video_templates", ["created_at"]),
        # 模板复合索引
        ("idx_video_templates_active_official", "video_templates", ["is_active", "is_official"]),
    ]
    
    @classmethod
    async def create_indexes(cls, db: Session) -> dict:
        """创建所有索引
        
        Returns:
            {"created": [index_names], "existing": [index_names], "failed": {name: error}}
        """
        result = {
            "created": [],
            "existing": [],
            "failed": {}
        }
        
        for index_name, table_name, columns in cls.INDEXES:
            try:
                # 检查索引是否已存在
                exists = cls._index_exists(db, index_name)
                
                if exists:
                    result["existing"].append(index_name)
                    continue
                
                # 创建索引
                index = Index(
                    index_name,
                    *[text(col) if isinstance(col, str) else col for col in columns]
                )
                
                # 为 PostgreSQL 使用 CONCURRENTLY 避免锁表
                if "postgresql" in str(db.bind.url):
                    db.execute(text(f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                        ON {table_name} ({', '.join(columns)})
                    """))
                else:
                    index.create(db.bind)
                
                result["created"].append(index_name)
                
            except Exception as e:
                error_msg = str(e)
                # 忽略已存在的索引错误
                if "already exists" in error_msg.lower():
                    result["existing"].append(index_name)
                else:
                    result["failed"][index_name] = error_msg
        
        db.commit()
        return result
    
    @classmethod
    def _index_exists(cls, db: Session, index_name: str) -> bool:
        """检查索引是否存在"""
        try:
            if "postgresql" in str(db.bind.url):
                result = db.execute(
                    text("SELECT 1 FROM pg_indexes WHERE indexname = :name"),
                    {"name": index_name}
                )
                return result.scalar() is not None
            else:
                # SQLite
                result = db.execute(
                    text("SELECT 1 FROM sqlite_master WHERE type='index' AND name=:name"),
                    {"name": index_name}
                )
                return result.scalar() is not None
        except Exception:
            return False
    
    @classmethod
    def analyze_tables(cls, db: Session) -> dict:
        """分析表统计信息(更新查询计划)"""
        try:
            if "postgresql" in str(db.bind.url):
                db.execute(text("ANALYZE"))
                return {"status": "success", "message": "Tables analyzed"}
            else:
                return {"status": "skipped", "message": "ANALYZE not supported for SQLite"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @classmethod
    def get_missing_indexes(cls, db: Session) -> list:
        """检测缺失的索引(基于查询慢日志分析)
        
        这是一个简化的实现，实际应该基于 pg_stat_user_indexes
        或慢查询日志来分析
        """
        try:
            if "postgresql" not in str(db.bind.url):
                return []
            
            # 查询被使用但不存在显式索引的列
            result = db.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 20
            """))
            
            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3],
                }
                for row in result
            ]
        except Exception:
            return []


# 全局索引优化器
index_optimizer = IndexOptimizer()
