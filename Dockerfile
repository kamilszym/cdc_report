FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# we probably need build tools?
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    python3-dev
    chmod 777 "files/chromedriver"

WORKDIR /app

# if we have a packages.txt, install it
COPY packages.txt packages.txt
RUN xargs -a packages.txt apt-get install --yes

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8501

COPY . .

CMD ["streamlit", "run", "app.py"]

# docker build --progress=plain --tag selenium:latest .
# docker run -ti -p 8501:8501 --rm selenium:latest /bin/bash
# docker run -ti -p 8501:8501 --rm selenium:latest
# docker run -ti -p 8501:8501 -v ${pwd}:/app --rm selenium:latest
# docker run -ti -p 8501:8501 -v ${pwd}:/app --rm selenium:latest /bin/bash
