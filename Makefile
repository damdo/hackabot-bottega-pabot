build:
	docker build -t damdo/tgbot-hackabot .
run:
	docker run --rm -it -e BOT_TOKEN=539020128:AAGdBDE0b3BYa51R-qem7Xxlr1wT0Af8io8 --name tgbot-hackabot  damdo/tgbot-hackabot
