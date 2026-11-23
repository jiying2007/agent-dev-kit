ARG BASE_IMAGE=python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="agent-dev-kit-local-ci" \
      io.agent-dev-kit.local-ci.contract="v2"

ARG SETUPTOOLS_VERSION=80.9.0
ARG WHEEL_VERSION=0.45.1
ARG PYYAML_VERSION=6.0.3
ARG JSONSCHEMA_VERSION=4.26.0
ARG RUFF_VERSION=0.17.5
ARG PIP_AUDIT_VERSION=2.10.1
ARG MYPY_VERSION=2.4.1
ARG TYPES_JSONSCHEMA_VERSION=4.26.0.20261006
ARG TYPES_PYYAML_VERSION=6.0.12.20261113
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        binutils \
        bash \
        build-essential \
        ca-certificates \
        cmake \
        file \
        git \
        jq \
        ninja-build \
        ripgrep \
        shellcheck \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
        "setuptools==${SETUPTOOLS_VERSION}" \
        "wheel==${WHEEL_VERSION}" \
        "PyYAML==${PYYAML_VERSION}" \
        "jsonschema==${JSONSCHEMA_VERSION}" \
        "ruff==${RUFF_VERSION}" \
        "pip-audit==${PIP_AUDIT_VERSION}" \
        "mypy==${MYPY_VERSION}" \
        "types-jsonschema==${TYPES_JSONSCHEMA_VERSION}" \
        "types-PyYAML==${TYPES_PYYAML_VERSION}"

RUN groupadd --gid 65532 adk-ci \
    && useradd --uid 65532 --gid 65532 --home-dir /work/home --shell /usr/sbin/nologin --no-create-home adk-ci

COPY entrypoint.sh /usr/local/bin/adk-local-ci-entrypoint
RUN chmod 0755 /usr/local/bin/adk-local-ci-entrypoint

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/adk-local-ci-entrypoint"]
