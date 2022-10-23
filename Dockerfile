FROM python:slim

ENV TZ Asia/Tokyo
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y git jq imagemagick && \
    apt-get clean
# prereq
RUN pip3 install --upgrade slack_sdk aiohttp requests bs4
# preinstall
RUN git clone https://github.com/sharl/geeklets.git
RUN mkdir -p /usr/local/bin
RUN mkdir -p /var/tmp
RUN cp geeklets/amedas geeklets/amesh /usr/local/bin

RUN useradd -m slackbot
RUN cp geeklets/.amedas /home/slackbot
WORKDIR /home/slackbot

USER slackbot

COPY app.py /home/slackbot
COPY entrypoint.sh /home/slackbot
COPY modules /home/slackbot/modules/

ENTRYPOINT ["./entrypoint.sh"]
