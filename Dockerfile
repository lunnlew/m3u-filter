# 构建前端
FROM --platform=$BUILDPLATFORM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend .
RUN corepack enable && pnpm install && pnpm run build

# 构建后端
FROM --platform=$BUILDPLATFORM python:3.11-slim
WORKDIR /app

# 复制后端代码
COPY backend/requirements.txt .
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir -r requirements.txt

# 复制前后端构建结果
COPY backend .
COPY --from=frontend-builder /app/dist ./static

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

VOLUME /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]