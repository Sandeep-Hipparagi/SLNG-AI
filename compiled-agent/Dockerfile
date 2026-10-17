FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
# --link-mode=copy is not a preference, it is load-bearing.
#
# uv installs by hardlinking out of its own cache, so every installed file has
# st_nlink=2. NLTK ships a path-hardening module that refuses to open any
# multiply-linked file, on the grounds that a hardlink can point at an inode
# outside the root (CWE-59), and llama-index-core reads its bundled stopword list
# through NLTK. The result is that indexing dies at startup, in every worker
# process, with a security error that names neither uv nor hardlinking as the cause:
#
#     PermissionError: Security Violation [pathsec.open]: refusing multiply-linked
#     file '.../llama_index/core/_static/nltk_cache/corpora/stopwords/english'
#     (st_nlink=2)
#
# A plain open() on that file succeeds, which is what makes it confusing: only
# NLTK's hardened opener refuses it. Copying instead of linking makes st_nlink=1 and
# the check passes. Verified 2026-08-26: without this the emitted image builds and
# then fails to index; with it, both bases index.
RUN uv pip install --system --link-mode=copy .

# LiveKit Cloud requires a non-root run user. It owns /app because the agent
# downloads model files on first run and would otherwise have nowhere to write:
# COPY runs as root, so without --chown this directory stays root-owned.
RUN useradd --home-dir /app --shell /usr/sbin/nologin appuser \
 && chown appuser:appuser /app
COPY --chown=appuser:appuser . .

USER appuser

# LiveKit Cloud and the worker runner both start this image. The module CLI
# (`python -m livekit.agents`) is the supported entry point; the older
# per-script form goes through a CLI upstream has deprecated.
CMD ["python", "-m", "livekit.agents", "start", "agent.py"]
