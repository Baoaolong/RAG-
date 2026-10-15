# Hugging Face Spaces（Docker SDK）配置
# 只要仓库里存在这个文件，Spaces 就会用 Docker 构建，并按 app_port 暴露端口
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # 国内构建加速用的镜像源；HF 在海外，这里用官方源更稳
    PIP_INDEX_URL=https://pypi.org/simple

WORKDIR /app

# 依赖层单独一层，代码改动时不会重新装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install -U pip && pip install -r /app/requirements.txt

# 业务代码
COPY . /app

# Streamlit 默认跑在 7860（HF Spaces 的约定端口）
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7860/_stcore/health').status==200 else 1)"

CMD ["streamlit", "run", "app_qa.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--server.maxUploadSize=200"]
