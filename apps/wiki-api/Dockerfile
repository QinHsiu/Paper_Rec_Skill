FROM python:3.11-slim
WORKDIR /workspace
COPY apps/wiki-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt pymupdf
COPY packages/wiki-bridge /workspace/packages/wiki-bridge
COPY apps/wiki-api /workspace/apps/wiki-api
RUN pip install -e /workspace/packages/wiki-bridge
ENV PYTHONPATH=/workspace/packages/wiki-bridge
ENV PAPER_REC_ROOT=/workspace
WORKDIR /workspace/apps/wiki-api
EXPOSE 8787
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8787"]
