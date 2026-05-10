FROM python:3.13-slim

WORKDIR /app

# =========================
# System Packages
# =========================
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    wget \
    git \
    unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# =========================
# Install Deno
# =========================
RUN curl -fsSL https://deno.land/install.sh | sh

ENV DENO_INSTALL="/root/.deno"
ENV PATH="${DENO_INSTALL}/bin:${PATH}"

# =========================
# Install UV
# =========================
RUN curl -Ls https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

# =========================
# Copy Dependency Files
# =========================
COPY pyproject.toml uv.lock ./

# =========================
# Install Python Packages
# =========================
RUN uv sync --frozen

# =========================
# Install latest yt-dlp
# =========================
RUN uv pip install -U yt-dlp

# =========================
# Copy Project Files
# =========================
COPY . .

# =========================
# Create folders
# =========================
RUN mkdir -p downloads anony/cookies

# =========================
# Start Bot
# =========================
CMD ["bash", "start"]
