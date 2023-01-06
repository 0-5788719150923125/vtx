FROM nvidia/cuda:12.0.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y python3-pip nodejs npm

MAINTAINER United Nations

RUN npm i -g nodemon

WORKDIR /vtx

COPY . ./

RUN pip3 install -r requirements.txt

RUN npm install --production

CMD ["python3", "main.py"]

MAINTAINER R
