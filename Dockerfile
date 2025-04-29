FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && wget https://www.rarlab.com/rar/rarlinux-x64-711.tar.gz \
    && tar -xzf rarlinux-x64-711.tar.gz \
    && cd rar \
    && install -v -m755 unrar /usr/local/bin/ \
    && cd .. \
    && rm -rf rar rarlinux-x64-711.tar.gz \
    && apt-get remove -y wget \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p files/uploads files/extracted files/new_sessions

CMD ["python", "bot.py"]
