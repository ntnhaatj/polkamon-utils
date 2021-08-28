# polkamon-utils
utilities for polkamon

## Instructions
### Installation
```shell script
$ pipenv install
$ cat .env
PYTHONPATH=${PWD}:${PYTHONPATH}
TELEGRAM_BOT_TOKEN="TOKEN_FROM_BOTFATHER"
DONATE_ADDR="0x4cC86a0848d51419933C8033171bb34F8efd0604"
#PRODUCTION=True # to deploy heroku
```

### Calculate rarity score
```shell script
$ pipenv run rarity <ID>
```

### Run telegram bot
```shell script
$ pipenv run bot
```

## Deployment
### Telegram bot
- Heroku
```shell script
$ heroku login
$ heroku config:set TELEGRAM_BOT_TOKEN="TOKEN_FROM_BOTFATHER" \
                    DONATE_ADDR="0x4cC86a0848d51419933C8033171bb34F8efd0604" \
                    PRODUCTION=True
$ git push heroku
```