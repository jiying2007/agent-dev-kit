ARG BASE_IMAGE=python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93
FROM ${BASE_IMAGE}

ARG PYTHON_VERSION=3.11

LABEL org.opencontainers.image.title="agent-dev-kit-local-ci" \
      io.agent-dev-kit.local-ci.contract="v2"

ARG SETUPTOOLS_VERSION=80.9.0
ARG WHEEL_VERSION=0.45.1
ARG PYYAML_VERSION=6.0.3
ARG JSONSCHEMA_VERSION=4.26.0
ARG RUFF_VERSION=0.16.7
ARG PIP_AUDIT_VERSION=2.10.1
ARG MYPY_VERSION=2.3.1
ARG TYPES_JSONSCHEMA_VERSION=4.26.0.20260518
ARG TYPES_PYYAML_VERSION=6.0.12.20260906
ARG TOMLI_VERSION=

RUN if [ "$PYTHON_VERSION" = "3.8" ]; then \
        sed -i \
          -e 's|^deb http://deb.debian.org/debian bullseye main$|deb http://snapshot.debian.org/archive/debian/20240926T000000Z bullseye main|' \
          -e 's|^deb http://deb.debian.org/debian-security bullseye-security main$|deb http://snapshot.debian.org/archive/debian-security/20240926T000000Z bullseye-security main|' \
          -e 's|^deb http://deb.debian.org/debian bullseye-updates main$|deb http://snapshot.debian.org/archive/debian/20240926T000000Z bullseye-updates main|' \
          /etc/apt/sources.list; \
    fi \
    && apt-get -o Acquire::Check-Valid-Until=false update \
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
        "pip-audit==${PIP_AUDIT_VERSION}" \
        "mypy==${MYPY_VERSION}" \
        "types-jsonschema==${TYPES_JSONSCHEMA_VERSION}" \
        "types-PyYAML==${TYPES_PYYAML_VERSION}"

RUN if [ -n "$TOMLI_VERSION" ]; then \
        python -m pip install --no-cache-dir "tomli==${TOMLI_VERSION}"; \
    fi

RUN groupadd --gid 65532 adk-ci \
    && useradd --uid 65532 --gid 65532 --home-dir /work/home --shell /usr/sbin/nologin --no-create-home adk-ci

COPY entrypoint.sh /usr/local/bin/adk-local-ci-entrypoint
RUN chmod 0755 /usr/local/bin/adk-local-ci-entrypoint

WORKDIR /work
ENTRYPOINT ["/usr/local/bin/adk-local-ci-entrypoint"]
