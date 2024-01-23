ARG SOURCE_IMAGE=$SOURCE_IMAGE

FROM $SOURCE_IMAGE

ENV DEBIAN_FRONTEND="noninteractive"
ENV HF_HOME="/tmp"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu" \
    $(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

ARG NODE_MAJOR_VERSION
RUN curl -fsSL https://deb.nodesource.com/setup_$NODE_MAJOR_VERSION.x | bash -

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
    clang \
    containerd.io \
    docker-ce \
    docker-ce-cli \ 
    docker-buildx-plugin \
    docker-compose-plugin \
    git \
    libclang-dev \
    libopencv-dev \
    ninja-build \
    nodejs \
    openssh-client \
    python3-dev \
    python3-pip \
    python3-packaging \
    python3-venv \
    sqlite3 \
    unzip \
    vim \
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

LABEL sponsor="United Nations of Earth"

ARG DCE_VERSION
RUN curl --location --remote-header-name --remote-name https://github.com/Tyrrrz/DiscordChatExporter/releases/download/$DCE_VERSION/DiscordChatExporter.Cli.zip && \
    mkdir -p /usr/share/dce && \
    unzip DiscordChatExporter.Cli.zip -d /usr/share/dce && \
    chmod -R 755 /usr/share/dce && \
    rm DiscordChatExporter.Cli.zip

ARG ARCH
ARG HUGO_VERSION
RUN curl --location --remote-header-name --remote-name https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz && \
    mkdir -p /usr/share/hugo && \
    tar -zxf hugo_extended_${HUGO_VERSION}_linux-$ARCH.tar.gz -C /usr/share/hugo && \
    chmod -R 755 /usr/share/hugo && \
    rm hugo_extended_${HUGO_VERSION}_linux-$ARCH.tar.gz && \
    ln -s /usr/share/hugo/hugo /usr/bin/hugo && \
    hugo version

WORKDIR /src

COPY requirements.txt prepare.py ./

RUN pip install -r requirements.txt && \
    pip cache purge

RUN python3 prepare.py

RUN pip install flash-attn --no-build-isolation && \
    pip cache purge

ARG NODEMON_VERSION
RUN npm i -g nodemon@$NODEMON_VERSION

COPY lab/lightning-hivemind/ /lab/lightning-hivemind
COPY lab/ModuleFormer/ /lab/ModuleFormer

RUN python3 -m venv /venv/x \
    && chmod +x /venv/x/bin/activate \
    && . /venv/x/bin/activate

COPY requirements.x.txt ./

RUN pip install -r requirements.x.txt && \
    pip cache purge

RUN python3 -m venv /venv/y \
    && chmod +x /venv/y/bin/activate \
    && . /venv/y/bin/activate

COPY lab/ /lab

COPY requirements.y.txt ./

RUN pip install -r requirements.y.txt && \
    pip cache purge

COPY src/ /src
COPY book/ /book
COPY data/embeddings/ /embeddings
COPY data/adapters/ /adapters

RUN mkdir /env && \
    mkdir /.cache && \
    mkdir /.config && \
    mkdir /.triton && \
    mkdir /nltk_data && \
    mkdir -p /lab/discord && \
    mkdir -p /lab/discord/private && \
    chmod -R 777 /.cache && \
    chmod -R 777 /.config && \
    chmod -R 777 /.triton && \
    chmod -R 777 /nltk_data && \
    chmod -R 777 /lab/discord

ENV TZ="America/Chicago"
ENV PYTHONPYCACHEPREFIX='/tmp/__pycache__'
ENV CUDA_DEVICE_ORDER=PCI_BUS_ID
ENV FOCUS='toe'

CMD ["nodemon", "--watch", "/src", "--watch", "/env", "--ext", "*.py,*.yml", "--ignore", "models/*", "--ignore", "*.json", "--exec", "python3", "main.py"]

LABEL maintainer="R"