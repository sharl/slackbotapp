#!/bin/bash
export SLACK_APP_TOKEN=${SLACK_APP_TOKEN}
export SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}

exec python3 ./app.py
