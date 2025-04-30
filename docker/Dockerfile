FROM python:latest

# USER $USER

WORKDIR /usr/src/app

RUN apt upgrade -y && apt update -y

COPY ./config/script.sh /script.sh
COPY ./config/requirements.txt /requirements.txt

# COPY . .

# RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/bash" , "/script.sh"]