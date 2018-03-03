build:
	docker build -t damdo/tgbot-hackabot .
run:
	docker run --rm -it -e BOT_TOKEN=fake --link tgbot-dash:tgbot-dash --link tgbot-nlp-backend:tgbot-nlp-backend --name tgbot-hackabot damdo/tgbot-hackabot

dev:
	docker build -f $(PWD)/Dockerfile.dev -t damdo/tgbot-hackabot-dev .
	docker run --rm -it -e BOT_TOKEN=fake -v "$(PWD):/usr/src/app" --link tgbot-dash:tgbot-dash --link tgbot-nlp-backend:tgbot-nlp-backend --name tgbot-hackabot-dev  damdo/tgbot-hackabot-dev;
