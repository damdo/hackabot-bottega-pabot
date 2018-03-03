build:
	docker build -t damdo/tgbot-hackabot .
run:
	docker run --rm -it -e BOT_TOKEN=539020128:AAGdBDE0b3BYa51R-qem7Xxlr1wT0Af8io8 --link tgbot-dash:tgbot-dash --name tgbot-hackabot  damdo/tgbot-hackabot

dev:
	docker build -f $(PWD)/Dockerfile.dev -t damdo/tgbot-hackabot-dev .
	docker run --rm -it -e BOT_TOKEN=539020128:AAGdBDE0b3BYa51R-qem7Xxlr1wT0Af8io8 -v "$(PWD):/usr/src/app" --link tgbot-dash:tgbot-dash --name tgbot-hackabot-dev  damdo/tgbot-hackabot-dev;
