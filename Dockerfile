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

# pip >= 26.2.2 drops the compromised emSign CA (eMudhra incident, Oct 2026).
# Installed from a hash-pinned wheel, so the old pip's CA bundle isn't trusted.
RUN pip install "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM --platform=linux/amd64 python:3.14-slim AS run-image

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# Refreshing system CA bundle (emSign CA removal), base image may lag behind
RUN apt-get update \
 && apt-get install -y --no-install-recommends --only-upgrade ca-certificates \
 && rm -rf /var/lib/apt/lists/*

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
