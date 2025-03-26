# m3u-filter

## 简介
m3u-filter 是一个用于过滤 m3u 文件的工具，它可以根据用户提供的关键词过滤 m3u 文件中的条目，并生成一个新的 m3u 文件。

## 功能
- epg源订阅汇总
- m3u文件源(含m3u及txt格式)订阅汇总
- 支持创建过滤规则
- 支持创建规则筛选合集
- 支持基于筛选合集生成m3u文件
- 支持m3u生成时包含epg信息
## 后端运行
```bash
cd backend
pip install -r requirements.txt

uvicorn app:create_app --reload --factory
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

## 服务模式
```bash
m3u-filter-desktop.exe --service
```