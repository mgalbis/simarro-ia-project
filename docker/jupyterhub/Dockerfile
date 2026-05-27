ARG JUPYTERHUB_IMAGE
ARG PIP_TOOLS_VERSION

FROM ${JUPYTERHUB_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

COPY docker/jupyterhub/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir "jupyter_core>=5,<6" "jupyterlab>=4,<5"

COPY src/mlops /app/src/mlops
COPY config/ /app/config
COPY docker/jupyterhub/config.py /app/jupyterhub_config.py
COPY docker/jupyterhub/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]
