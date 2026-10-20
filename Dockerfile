FROM python:slim

ENV TZ=Asia/Tokyo
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y git jq imagemagick wget fonts-migmix && \
    apt-get clean
# prereq
COPY requirements.txt .
RUN pip3 install --upgrade -r requirements.txt --root-user-action ignore

# preinstall
RUN git clone https://github.com/sharl/geeklets.git
RUN mkdir -p /usr/local/bin
RUN mkdir -p /var/tmp
RUN cp geeklets/amedas.py /usr/local/bin/amedas
RUN cp geeklets/amesh geeklets/tenkijp /usr/local/bin

RUN useradd -m slackbot
RUN cp geeklets/.amedas /home/slackbot
WORKDIR /home/slackbot

USER slackbot

COPY app.py *.txt entrypoint.sh /home/slackbot/
COPY modules /home/slackbot/modules/

ENTRYPOINT ["./entrypoint.sh"]
