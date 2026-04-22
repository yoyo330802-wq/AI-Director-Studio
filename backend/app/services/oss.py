"""
漫AI - OSS/CDN 存储服务
Sprint 4: S4-F1 CDN/OSS
"""

import os
import uuid
from typing import Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.config import settings


class OSSService:
    """OSS/CDN 存储服务"""
    
    def __init__(self):
        self.enabled = bool(settings.OSS_ACCESS_KEY_ID and settings.OSS_SECRET_ACCESS_KEY)
        
        if self.enabled:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.OSS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.OSS_SECRET_ACCESS_KEY,
                endpoint_url=settings.OSS_ENDPOINT,
                region_name=settings.OSS_REGION or 'auto',
            )
            self.bucket_name = settings.OSS_BUCKET
            self.cdn_domain = settings.OSS_CDN_DOMAIN
        else:
            # 使用本地存储作为后备
            self.s3_client = None
            self.bucket_name = 'local'
            self.cdn_domain = None
    
    def _generate_video_key(self, user_id: str, task_id: str, extension: str = 'mp4') -> str:
        """生成存储路径"""
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        unique_id = str(uuid.uuid4())[:8]
        return f"videos/{date_prefix}/{user_id}/{task_id}_{unique_id}.{extension}"
    
    def _generate_thumbnail_key(self, user_id: str, task_id: str) -> str:
        """生成缩略图存储路径"""
        date_prefix = datetime.now().strftime('%Y/%m/%d')
        return f"thumbnails/{date_prefix}/{user_id}/{task_id}.jpg"
    
    def get_cdn_url(self, key: str) -> str:
        """获取 CDN URL"""
        if self.cdn_domain:
            return f"https://{self.cdn_domain}/{key}"
        elif self.enabled:
            return f"https://{self.bucket_name}.{settings.OSS_ENDPOINT.replace('https://', '')}/{key}"
        else:
            # 本地模式返回相对路径
            return f"/uploads/{key}"
    
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """获取预签名 URL（用于私有桶临时访问）"""
        if not self.enabled:
            return self.get_cdn_url(key)
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"生成预签名URL失败: {str(e)}")
    
    async def upload_video(
        self, 
        user_id: str, 
        task_id: str, 
        video_content: bytes,
        content_type: str = 'video/mp4'
    ) -> str:
        """
        上传视频到 OSS
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
            video_content: 视频内容
            content_type: MIME类型
            
        Returns:
            CDN URL
        """
        key = self._generate_video_key(user_id, task_id)
        
        if self.enabled:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=video_content,
                    ContentType=content_type,
                    # 公共读取
                    ACL='public-read',
                )
            except ClientError as e:
                raise HTTPException(status_code=500, detail=f"上传视频失败: {str(e)}")
        else:
            # 本地存储
            local_path = os.path.join(settings.LOCAL_UPLOAD_DIR or '/tmp/manai-uploads', key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(video_content)
        
        return self.get_cdn_url(key)
    
    async def upload_thumbnail(
        self,
        user_id: str,
        task_id: str,
        thumbnail_content: bytes
    ) -> str:
        """上传缩略图"""
        key = self._generate_thumbnail_key(user_id, task_id)
        
        if self.enabled:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=thumbnail_content,
                    ContentType='image/jpeg',
                    ACL='public-read',
                )
            except ClientError as e:
                raise HTTPException(status_code=500, detail=f"上传缩略图失败: {str(e)}")
        else:
            local_path = os.path.join(settings.LOCAL_UPLOAD_DIR or '/tmp/manai-uploads', key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(thumbnail_content)
        
        return self.get_cdn_url(key)
    
    def delete_object(self, key: str) -> bool:
        """删除对象"""
        if not self.enabled:
            # 本地删除
            local_path = os.path.join(settings.LOCAL_UPLOAD_DIR or '/tmp/manai-uploads', key)
            if os.path.exists(local_path):
                os.remove(local_path)
            return True
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False


# 全局单例
oss_service = OSSService()
