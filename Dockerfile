# Multi-stage build: dependencies are installed into a virtualenv in the
# build stage and copied as-is into a slim runtime stage without compilers.
# Pinned to linux/amd64 as the production target.
# For reproducible builds, pin the base image by digest, e.g.:
# FROM --platform=linux/amd64 python:3.14-slim@sha256:<digest>
FROM --platform=linux/amd64 python:3.14-slim AS build-image

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM --platform=linux/amd64 python:3.14-slim AS run-image

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# Unprivileged user; uid is fixed so volume/k8s securityContext can rely on it
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /home/app --shell /usr/sbin/nologin app \
 && mkdir -p /home/app \
 && chown app:app /home/app

COPY --from=build-image /opt/venv /opt/venv

WORKDIR /home/app

COPY --chown=app:app ./app/ ./app/

USER app

CMD ["python3", "-m", "app"]
