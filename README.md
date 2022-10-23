# SlackbotApp

## How to setup

1. make app

- Open [https://api.slack.com/apps?new_app=1](https://api.slack.com/apps?new_app=1)
- [Create an App] -> [From scratch]
- Enter [App Name] and select [workspace]
- [Create App]

2. enable socket mode and generate slack app token

- Settings [Socket Mode] on left side column
- Connect using Socket Mode
 - Enable Socket Mode [On]
 - Enter [Token Name] ex. "socket mode"
 - [Generate]
  - xapp-........... **SLACK_APP_TOKEN**
 - [Done]

3. create global shortcut

- select Features [Interactivity & Shortcuts] on left side column
- Shortcuts [Create New Shortcut]
- select [Global] and [Next]
- fill [Name]
- fill [Short Description]
- fill [Callback ID]
- [Create]
- [Save Changes]

4. enable events

- select Features [Event Subscriptions] on left side column
 - Enable Events [On]
- select [Subscribe to bot events]
 - [Add Bot User Event]
 - fill [message.channels] in form
 - ... and/or handled event
- [Save Changes]

5. other settings

- select Featuers [oAuth & Permissions] on left side column
- Scopes
 - Bot Token Scopes
 - [Add an OAuth Scope]
 - fill [chat:write] in form and enable **MUST**
 - add proper scope...

6. App Home settings

- select Features [App Home] on left side column
- Your App's Presence in Slack
 - App Display Name [Edit]
 - fill Display Name (Bot Name)
 - [Save]

7. install app to workspace

- select Settings [Install App] on left side column
- [Install to Workspace]
- [Allow]
- Installed App Settings
 - OAuth Tokens for Your Workspace
  - Bot User OAuth Token
   - xoxb-...................... **SLACK_BOT_TOKEN**

## How to run

  $ pip install -U -r requirements.txt

  $ export SLACK_APP_TOKEN=xapp-..............
  $ export SLACK_BOT_TOKEN=xoxb-..............
  $ ./app.py

## Module usage

### message.switchbot.meter

- config.json
```
        "message.switchbot.meter": {
            "keyword": "wake word",
            "user": "user name (NOT display name)",
            "token": "<developer token>",
            "device": "<device ID>"
        }
```

### message.switchbot.plug

- config.json
```
        "message.switchbot.plug": {
            "on": "on wake word",
            "off": "off wake word",
            "user": "user name (NOT display name)",
            "token": "<developer token>",
            "device": "<device ID>"
        }
```
