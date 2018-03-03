#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import ReplyKeyboardMarkup, File
from telegram.ext import (Updater,Handler, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import os
import logging
import requests
import json

# Get token bot from the corresponding environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
ANALYTICS_ENDPOINT = "http://tgbot-dash:8888/api"
ANALYTICS_ENDPOINT = "http://tgbot-dash:8888/api"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# define the states to fall into
CHOOSING, TYPING_REPLY, TYPING_CHOICE, WANT_FEEDBACK, FEEDBACK, SPECIFIED_FEEDBACK = range(6)

# define the reply buttoned keyboard
# a row is a list of columns, rows are separated by a comma and contained in a list
choice_buttons = [
        ['DOMANDA LIBERA'],
        ['SFOGLIA PER CATEGORIE'],
        ['Done']
]

feedback_buttons = [
        ['⭐'],
        ['⭐⭐']
]

want_feedback_buttons = [
    ["No"],
    ["Yes"]
]

feedback_keyboard = ReplyKeyboardMarkup(feedback_buttons, one_time_keyboard=True)
choice_keyboard = ReplyKeyboardMarkup(choice_buttons, one_time_keyboard=True)
want_feedback_keyboard = ReplyKeyboardMarkup(want_feedback_buttons, one_time_keyboard=True)


def send_to_analytics(bot, update, user_data, last_command):
    prof_pic_file_id = bot.get_user_profile_photos(update.message.from_user.id).photos[0][0].file_id
    profile_pic = bot.get_file(prof_pic_file_id)
    #profilePic.download(str(update.message.from_user.id)+".jpg")
    userinfo = {
        "user":str(update.message.from_user.first_name)+" "+str(update.message.from_user.last_name),
        "profile_pic" : str(profile_pic.file_path),
        "nickname":str(update.message.from_user.username)
     }
    requests.post(ANALYTICS_ENDPOINT, data=json.dumps(userinfo))


def facts_to_str(user_data):
    facts = list()

    for key, value in user_data.items():
        facts.append('{} - {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])


def start(bot, update, user_data):
    last_command = "start"
    send_to_analytics(bot, update, user_data, last_command)
    # pass the bot and the update
    # update.message.reply_text
    update.message.reply_text("Ciao "+update.message.from_user.first_name+" sono PAbot, il bot della Provincia di Trento! Sono qui per aiutarti e guidarti nelle procedure della pubblica amministrazione, sono esperto in: \n - PROCEDIMENTI \n - MODULI DI DOMANDA \n - CERTIFICAZIONI \n \n Puoi chiedermi quello che ti serve in due modi: \n - Clicca DOMANDA LIBERA per cercare tra le procedure \n oppure \n - Clicca SFOGLIA PER CATEGORIE e cerca quello che ti serve", reply_markup=choice_keyboard)
    # update.message.reply_text( """Ciao sono PAbot, il bot della Provincia di Trento! Come posso esserti utile?""", reply_markup=markup_things)
    return CHOOSING


def regular_choice(bot, update, user_data):
    text = update.message.text
    user_data['choice'] = text
    update.message.reply_text( 'Bene :) Hai scelto DOMANDA LIBERA, scrivimi pure qui sotto quello che stai cercando, faro\' del mio meglio per aiutarti!'.format(text.lower()))

    return TYPING_REPLY

def want_feedback_process(bot, update, user_data):
    print "want_feedback_process"
    text = update.message.text
    print text
    if text == "Yes" :
        print "setting FEEDBACK"
        update.message.reply_text("Indica un punteggio per il bot da 1 a 5 star :)", reply_markup=feedback_keyboard)
        return SPECIFIED_FEEDBACK
    else:
        update.message.reply_text('Grazie per aver utilizzato il bot, A presto!')
        return ConversationHandler.END

        return ConversationHandler.END

def custom_choice(bot, update):
    update.message.reply_text('Bene :) Hai scelto SFOGLIA PER CATEGORIE, guarda i pulsanti delle categorie qui sotto e scegli quella piu\' pertinente alle tue necessita\'')
    return TYPING_CHOICE


def received_information(bot, update, user_data):
    update.message.reply_text("TODO: (Questa sara\' la risposta alla domanda dell\'utente)", reply_markup=choice_keyboard)
    return CHOOSING


def done(bot, update, user_data):
    update.message.reply_text("Ottimo, spero tu abbia trovato la risposta che stavi cercando. Desideri lasciarci un feedback?", reply_markup=want_feedback_keyboard)
    return WANT_FEEDBACK

#def feedback(bot,update,user_data):
#    print "feedback fun"
#    update.message.reply_text("Indica un punteggio per il bot da 1 a 5 star :)", reply_markup=feedback_keyboard)
#    return SPECIFIED_FEEDBACK

def exit_process(bot, update, user_data):
    update.message.reply_text('Grazie per aver utilizzato il bot, A presto!')
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],
        states={
            CHOOSING: [RegexHandler('^(DOMANDA LIBERA|ALTRO)$', regular_choice, pass_user_data=True), RegexHandler('^SFOGLIA PER CATEGORIE$', custom_choice), ],
            WANT_FEEDBACK: [RegexHandler('^(Yes|No)$', want_feedback_process, pass_user_data=True)],
            SPECIFIED_FEEDBACK: [MessageHandler(Filters.text, exit_process , pass_user_data=True)],
            #FEEDBACK: [RegexHandler('No',feedback, pass_user_data=True), RegexHandler('Yes',feedback, pass_user_data=True)],
            TYPING_CHOICE: [MessageHandler(Filters.text, regular_choice, pass_user_data=True), ],
            TYPING_REPLY: [MessageHandler(Filters.text, received_information, pass_user_data=True), ],
        },
        fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    if(BOT_TOKEN):
        main()
    else:
        print "No Telegram Bot Token provided, quitting"

