FROM nvcr.io/nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV TRANSFORMERS_CACHE="/tmp"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    git \
    ninja-build \
    nodejs \
    npm \
    python3-dev \
    python3-pip \
    python3-packaging \
    python3-venv \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

ARG DOTNET_VERSION

RUN curl -fSL --output dotnet.tar.gz https://dotnetcli.azureedge.net/dotnet/Runtime/$DOTNET_VERSION/dotnet-runtime-$DOTNET_VERSION-linux-x64.tar.gz \
    && dotnet_sha512='f15b6bf0ef0ce48901880bd89a5fa4b3ae6f6614ab416b23451567844448f2510cf5beeeef6c2ac33400ea013cda7b6d2a4477e7aa0f36461b94741161424c3e' \
    && echo "$dotnet_sha512 dotnet.tar.gz" | sha512sum -c - \
    && mkdir -p /usr/share/dotnet \
    && tar -zxf dotnet.tar.gz -C /usr/share/dotnet \
    && rm dotnet.tar.gz \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet

MAINTAINER United Nations

ARG DCE_VERSION

RUN curl --location --remote-header-name --remote-name https://github.com/Tyrrrz/DiscordChatExporter/releases/download/$DCE_VERSION/DiscordChatExporter.Cli.zip && \
    mkdir -p /usr/share/dce && \
    unzip DiscordChatExporter.Cli.zip -d /usr/share/dce && \
    chmod -R 755 /usr/share/dce && \
    rm DiscordChatExporter.Cli.zip

ARG HUGO_VERSION

RUN curl --location --remote-header-name --remote-name https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz && \
    mkdir -p /usr/share/hugo && \
    tar -zxf hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz -C /usr/share/hugo && \
    chmod -R 755 /usr/share/hugo && \
    rm hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz && \
    ln -s /usr/share/hugo/hugo /usr/bin/hugo && \
    hugo version

WORKDIR /src

COPY requirements.txt ./

RUN pip install -r requirements.txt

ARG NODEMON_VERSION

RUN npm i -g nodemon@$NODEMON_VERSION

COPY src/ /src
COPY lab/ /lab

RUN python3 -m venv venv/x \
    && chmod +x venv/x/bin/activate \
    && venv/x/bin/activate

COPY requirements.x.txt ./

RUN pip install -r requirements.x.txt

RUN mkdir /.cache && \
    mkdir /.triton && \
    chmod -R 777 /.cache && \
    chmod -R 777 /.triton

ENV FOCUS='mind'

CMD ["nodemon", "--ext", "*.py", "*.yml", "--ignore", "models/*", "--ignore", "*.json", "--exec", "python3", "main.py"]

MAINTAINER R
