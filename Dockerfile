FROM nvidia/cuda:12.0.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip nodejs npm curl unzip

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        \
        # .NET dependencies
        libc6 \
        libgcc1 \
        libgssapi-krb5-2 \
        # libicu66 \
        # libssl1.1 \
        libstdc++6 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

ENV DOTNET_VERSION=7.0.0

RUN curl -fSL --output dotnet.tar.gz https://dotnetcli.azureedge.net/dotnet/Runtime/$DOTNET_VERSION/dotnet-runtime-$DOTNET_VERSION-linux-x64.tar.gz \
    && dotnet_sha512='f4a6e9d5fec7d390c791f5ddaa0fcda386a7ec36fe2dbaa6acb3bdad38393ca1f9d984dd577a081920c3cae3d511090a2f2723cc5a79815309f344b8ccce6488' \
    && echo "$dotnet_sha512 dotnet.tar.gz" | sha512sum -c - \
    && mkdir -p /usr/share/dotnet \
    && tar -zxf dotnet.tar.gz -C /usr/share/dotnet \
    && rm dotnet.tar.gz \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet

RUN npm i -g nodemon

MAINTAINER United Nations

WORKDIR /tmp

RUN curl --location --remote-header-name --remote-name https://github.com/Tyrrrz/DiscordChatExporter/releases/download/2.37.1/DiscordChatExporter.Cli.zip && \
    unzip DiscordChatExporter.Cli.zip -d /dce && \
    chmod -R 755 /dce

WORKDIR /vtx

COPY package*.json requirements.txt ./

RUN pip3 install -r requirements.txt

RUN npm install --production

COPY . ./

RUN pip install /vtx/aitextgen

CMD ["python3", "main.py"]

MAINTAINER R
