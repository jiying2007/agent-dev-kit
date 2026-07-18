ARG BASE_IMAGE=python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="agent-dev-kit-local-ci" \
      io.agent-dev-kit.local-ci.contract="v2"

ARG SETUPTOOLS_VERSION=80.9.0
ARG WHEEL_VERSION=0.45.1
ARG PYYAML_VERSION=6.0.3
ARG JSONSCHEMA_VERSION=4.26.0
ARG RUFF_VERSION=0.15.21
ARG PIP_AUDIT_VERSION=2.10.1

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        git \
        ripgrep \
        shellcheck \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
        "setuptools==${SETUPTOOLS_VERSION}" \
        "wheel==${WHEEL_VERSION}" \
        "PyYAML==${PYYAML_VERSION}" \
        "jsonschema==${JSONSCHEMA_VERSION}" \
        "ruff==${RUFF_VERSION}" \
        "pip-audit==${PIP_AUDIT_VERSION}"

RUN groupadd --gid 65532 adk-ci \
    && useradd --uid 65532 --gid 65532 --home-dir /work/home --shell /usr/sbin/nologin --no-create-home adk-ci

COPY entrypoint.sh /usr/local/bin/adk-local-ci-entrypoint
RUN chmod 0755 /usr/local/bin/adk-local-ci-entrypoint

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/adk-local-ci-entrypoint"]
