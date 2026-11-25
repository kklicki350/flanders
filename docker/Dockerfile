# FLANDERS image: FLANDERS itself plus one isolated micromamba environment per tool.
# No reference data and no redistribution-restricted predictor is included (NFR22).
FROM --platform=linux/amd64 mambaorg/micromamba:2.0.5

USER root
RUN apt-get update && apt-get install -y --no-install-recommends procps ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Tool environments, one layer each so a version bump rebuilds only that layer.
COPY docker/envs/env-ncbi.yml /tmp/envs/
RUN micromamba create -y -f /tmp/envs/env-ncbi.yml && micromamba clean -afy
COPY docker/envs/env-hmmer-mmseqs.yml /tmp/envs/
RUN micromamba create -y -f /tmp/envs/env-hmmer-mmseqs.yml && micromamba clean -afy
COPY docker/envs/env-cblaster.yml /tmp/envs/
RUN micromamba create -y -f /tmp/envs/env-cblaster.yml && micromamba clean -afy
COPY docker/envs/env-predictors.yml /tmp/envs/
RUN micromamba create -y -f /tmp/envs/env-predictors.yml && micromamba clean -afy
COPY docker/envs/env-antismash8.yml /tmp/envs/
RUN micromamba create -y -f /tmp/envs/env-antismash8.yml && micromamba clean -afy

# FLANDERS's own Python environment from uv.lock.
RUN micromamba create -y -n flanders -c conda-forge python=3.11 uv && micromamba clean -afy
WORKDIR /opt/flanders
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY schemas ./schemas
RUN UV_PROJECT_ENVIRONMENT=/opt/flanders/.venv /opt/conda/envs/flanders/bin/uv sync --frozen --no-dev \
        --python /opt/conda/envs/flanders/bin/python \
    && rm -rf /root/.cache

ENV FLANDERS_ENV_ROOT=/opt/conda/envs \
    FLANDERS_IN_CONTAINER=1 \
    PATH=/opt/flanders/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1

# Record exact tool environments for provenance and debugging.
RUN for e in /opt/conda/envs/env-*; do micromamba env export -p "$e" --explicit > "$e/explicit.lock"; done

ENTRYPOINT ["flanders"]
CMD ["--help"]
