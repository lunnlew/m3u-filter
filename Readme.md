# m3u-filter

## 简介
m3u-filter 是一个专业的IPTV直播源管理工具，提供从订阅管理、智能过滤到质量检测的一站式解决方案。它不仅能根据关键词、正则表达式过滤m3u文件，还能自动测试频道质量、合并EPG信息，并生成优化后的播放列表。支持Web界面操作和API调用。

## 功能
- EPG源管理：支持多EPG源订阅、合并与更新
- 直播源管理：支持M3U/TXT格式源订阅、解析与去重
- 智能过滤：基于关键词、正则表达式的频道过滤规则
- 频道分组：支持按分类、语言、地区等创建频道合集
- 流媒体测试：自动检测频道可用性、缓冲速度和质量评分
- M3U生成：支持自定义模板生成包含EPG信息的M3U文件
- 多端支持：提供Web界面、API接口和Docker部署方式
- 任务调度：支持定时更新源、自动测试频道等后台任务

## 后端运行
```bash
cd backend
pip install -r requirements.txt

uvicorn app:create_app --reload --factory --port 3232 --host 0.0.0.0
# 或者
python main.py
```

## 构建web版镜像
```bash
docker build -t m3u-filter-web -f Dockerfile.web .
```

## 安装
```bash
docker pull lunnlew/m3u-filter
```

## 运行
```bash
docker run -d --name m3u-filter -p 3232:3232 -v /path/to/your/data:/app/data lunnlew/m3u-filter
```