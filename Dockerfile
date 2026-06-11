FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
# cowsay and fortune install to /usr/games on Debian/Ubuntu
ENV PATH="${PATH}:/usr/games"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       fortune-mod \
       cowsay \
       netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY wisecow.sh .
RUN chmod +x wisecow.sh

EXPOSE 4499

ENTRYPOINT ["./wisecow.sh"]
