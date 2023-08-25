FROM nvcr.io/nvidia/cuda:12.2.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip nodejs npm curl unzip

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    libc6 \
    libgcc1 \
    libgssapi-krb5-2 \
    libstdc++6 \
    python3-packaging \
    zlib1g \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

ARG DOTNET_VERSION

RUN curl -fSL --output dotnet.tar.gz https://dotnetcli.azureedge.net/dotnet/Runtime/$DOTNET_VERSION/dotnet-runtime-$DOTNET_VERSION-linux-x64.tar.gz \
    && dotnet_sha512='f15b6bf0ef0ce48901880bd89a5fa4b3ae6f6614ab416b23451567844448f2510cf5beeeef6c2ac33400ea013cda7b6d2a4477e7aa0f36461b94741161424c3e' \
    && echo "$dotnet_sha512 dotnet.tar.gz" | sha512sum -c - \
    && mkdir -p /usr/share/dotnet \
    && tar -zxf dotnet.tar.gz -C /usr/share/dotnet \
    && rm dotnet.tar.gz \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet

MAINTAINER United Nations

WORKDIR /tmp

ARG DCE_VERSION

RUN curl --location --remote-header-name --remote-name https://github.com/Tyrrrz/DiscordChatExporter/releases/download/$DCE_VERSION/DiscordChatExporter.Cli.zip && \
    unzip DiscordChatExporter.Cli.zip -d /dce && \
    chmod -R 755 /dce && \
    rm DiscordChatExporter.Cli.zip

WORKDIR /src

RUN npm i -g nodemon

COPY package*.json requirements.txt ./

RUN pip3 install -r requirements.txt

COPY src/ /src
COPY lab/ /lab

RUN pip install /lab/aitextgen

RUN mkdir /.cache && \
    mkdir /.triton
RUN chmod -R 777 /.cache && \
    chmod -R 777 /.triton

CMD ["python3", "src/main.py"]

MAINTAINER R
