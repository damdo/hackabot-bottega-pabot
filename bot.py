#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import ReplyKeyboardMarkup, File
from telegram.ext import (Updater,Handler, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import os
import logging
import requests
import json

# Get token bot from the corresponding environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", False)
NLP_BACKEND_ENDPOINT = "http://tgbot-nlp-backend:5000/"
ANALYTICS_ENDPOINT = "http://tgbot-dash:8888/api"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the states to fall into
CHOOSING, TYPING_REPLY, TYPING_CHOICE, WANT_FEEDBACK, SPECIFIED_FEEDBACK, RECOVER, RENDERING_PROCESS_CAT, RENDERING_PROCESS_REQ = range(8)

# Define the reply buttoned keyboards
# A row is a list of columns, rows are separated by a comma and contained in a list
choice_buttons = [
        ['DOMANDA LIBERA'],
        ['SFOGLIA PER CATEGORIE'],
        ['FINE']
]

feedback_buttons = [
        ['⭐', '⭐⭐'],
        ['⭐⭐⭐', '⭐⭐⭐⭐'],
        ['⭐⭐⭐⭐⭐'],
]

want_feedback_buttons = [
    ["No"],
    ["Si"]
]

feedback_keyboard = ReplyKeyboardMarkup(feedback_buttons, one_time_keyboard=True)
choice_keyboard = ReplyKeyboardMarkup(choice_buttons, one_time_keyboard=True)
want_feedback_keyboard = ReplyKeyboardMarkup(want_feedback_buttons, one_time_keyboard=True)


def send_to_analytics(bot, update, user_data, last_command):

    prof_pic_file_id = bot.get_user_profile_photos(update.message.from_user.id).photos[0][0].file_id
    profile_pic = bot.get_file(prof_pic_file_id)

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
    # Uncomment to add user analytics
    # send_to_analytics(bot, update, user_data, last_command)

    # emoji unicode definition
    proc_e = '\U0001F4DD'
    dom_e = '\U00002753'
    cert_e = '\U0001F5DE'

    update.message.reply_text(
        "Ciao "+update.message.from_user.first_name
        +" sono PAbot, il bot della Provincia di Trento!"
        +"Sono qui per aiutarti e guidarti nelle procedure"
        +"della pubblica amministrazione, sono esperto in: \n"
        +proc_e.decode('unicode-escape')+" PROCEDIMENTI \n"
        +dom_e.decode('unicode-escape')+" MODULI DI DOMANDA \n"
        +cert_e.decode('unicode-escape')+" CERTIFICAZIONI \n \n"
        +"Puoi chiedermi quello che ti serve in due modi: \n"
        +"- Clicca DOMANDA LIBERA per cercare tra le procedure \n"
        +"oppure \n"
        +"- Clicca SFOGLIA PER CATEGORIE e cerca quello che ti serve"
        ,reply_markup=choice_keyboard
    )
    return CHOOSING


def back_home(bot, update, user_data):
    update.message.reply_text(
        "Puoi chiedermi quello che ti serve in due modi:"+"\n"
        +" - Clicca DOMANDA LIBERA per cercare tra le procedure"+"\n"
        +"oppure"+"\n"
        +" - Clicca SFOGLIA PER CATEGORIE e cerca quello che ti serve"
        ,reply_markup=choice_keyboard
    )

    return CHOOSING


def regular_choice(bot, update, user_data):
    text = update.message.text
    update.message.reply_text(
        'Bene :) Hai scelto DOMANDA LIBERA, scrivimi pure qui'
        +'sotto quello che stai cercando, faro\' del mio meglio per aiutarti!'
    )

    return TYPING_REPLY


def want_feedback_process(bot, update, user_data):
    print "want_feedback_process"
    text = update.message.text

    if text == "Si" :
        update.message.reply_text(
            "Indica un punteggio per il bot da 1 a 5 star :)"
            ,reply_markup=feedback_keyboard
        )
        return SPECIFIED_FEEDBACK

    else:
        update.message.reply_text(
            'Grazie per aver utilizzato il bot, A presto!\n'
            +'Clicca qui: /start per ricominciare a parlare con me :)'
        )
        return ConversationHandler.END


def custom_choice(bot, update, user_data):
    cat_buttons = []

    r = requests.post(NLP_BACKEND_ENDPOINT+"cat")
    headers = {'Content-type': 'application/json'}
    cat_response = r.json()

    for k,v in cat_response["processes"].iteritems():
        cat_buttons.append([k])

    cat_keyboard = ReplyKeyboardMarkup(cat_buttons, one_time_keyboard=True)

    update.message.reply_text(
        'Bene :) Hai scelto SFOGLIA PER CATEGORIE, guarda i pulsanti delle categorie qui sotto'
        +' e scegli quella piu\' pertinente alle tue necessita\''
        ,reply_markup=cat_keyboard
    )

    return TYPING_CHOICE


def received_information(bot, update, user_data):
    user_free_text_request = update.message.text
    user_data["input_sequence"] = user_free_text_request

    r = requests.post(NLP_BACKEND_ENDPOINT+"req",json={"input_string": user_free_text_request})
    headers = {'Content-type': 'application/json'}
    response_procedures = r.json()

    if response_procedures["processes"]["ERROR"] == True:
        update.message.reply_text(
            "Mi dispiace :( non sono riuscito a trovare una risposta,"
            +"fai click su DOMANDA LIBERA e chiedimi qualcosa o prova a SFOGLIARE PER CATEGORIE"
            ,reply_markup=choice_keyboard
        )

    else:
        procedures_buttons = []
        for key,value in response_procedures["processes"].iteritems():
            if "ERROR" not in key:
                procedures_buttons.append([value["title"]])

        procedures_buttons.append(["INDIETRO"])
        procedures_keyboard = ReplyKeyboardMarkup(procedures_buttons, one_time_keyboard=True)

        update.message.reply_text(
            "Bene, questi sono i risultati più pertinenti che ho trovato per la tua domanda:\n"
            ,reply_markup=procedures_keyboard
        )
    return RENDERING_PROCESS_REQ


def done(bot, update, user_data):
    update.message.reply_text(
        "Ottimo, spero tu abbia trovato la risposta che stavi cercando. Desideri lasciarci un feedback?"
        ,reply_markup=want_feedback_keyboard
    )
    return WANT_FEEDBACK


def exit_process(bot, update, user_data):
    update.message.reply_text(
        'Grazie per aver utilizzato il bot, A presto!'+'\n'
        +'Clicca qui: /start per ricominciare a parlare con me :)'
    )
    return ConversationHandler.END


def cat_handler(bot, update, user_data):
    processes_buttons = []
    text = update.message.text

    user_data["current_cat"] = text;

    r = requests.post(NLP_BACKEND_ENDPOINT+"cat")
    headers = {'Content-type': 'application/json'}
    cat_response = r.json()

    if text in cat_response["processes"]:
        processes_list_for_single_cat = cat_response["processes"][text]
        for proc in processes_list_for_single_cat:
            processes_buttons.append([proc["NOME"]])

        processes_buttons.append(["INDIETRO"])
        processes_keyboard = ReplyKeyboardMarkup(processes_buttons, one_time_keyboard=True)

        update.message.reply_text(
            'Bene, questi sono i risultati più pertinenti che ho trovato per la tua domanda:\n'
            ,reply_markup=processes_keyboard
        )
        return RENDERING_PROCESS_CAT

    else:
        update.message.reply_text(
            'Categoria non presente, prova a scegliere una delle categorie qui sotto.'
        )
        return TYPING_CHOICE


def rendering_process_cat_handler(bot, update, user_data):
    input_proccess_name = update.message.text

    r = requests.post(NLP_BACKEND_ENDPOINT+"cat")
    headers = {'Content-type': 'application/json'}
    cat_response = r.json()

    extracted_process = {
        "NOME": "Mi dispiace :( non sono riuscito a trovare alcuna risposta",
        "URL DEL SITO": "",
        "DESCRIZIONE": ", fai click su DOMANDA LIBERA e chiedimi qualcosa o prova a SFOGLIARE PER CATEGORIE"
    }

    for process in cat_response["processes"][user_data["current_cat"]]:
        if process["NOME"] == input_proccess_name:
            extracted_process = process

    update.message.reply_text(
        extracted_process["NOME"]+"\n\n"
        +extracted_process["DESCRIZIONE"]+"\n"
        +"Ulteriori informazioni: "+extracted_process["URL DEL SITO"]+"\n"
        ,reply_markup=choice_keyboard
    )
    return CHOOSING


def rendering_process_req_handler(bot, update, user_data):
    input_proccess_name = update.message.text
    user_free_text_request = user_data["input_sequence"]

    r = requests.post(NLP_BACKEND_ENDPOINT+"req", json={"input_string": user_free_text_request})
    headers = {'Content-type': 'application/json'}
    req_response = r.json()

    extracted_process = {
        "title": "Mi dispiace :( non sono riuscito a trovare alcuna risposta",
        "url": "",
        "description": ", fai click su DOMANDA LIBERA e chiedimi qualcosa o prova a SFOGLIARE PER CATEGORIE"
    }

    for k,v in req_response["processes"].iteritems():
        if "ERROR" not in k:
            extracted_process = v

    update.message.reply_text(
        extracted_process["title"]+"\n\n"
        +extracted_process["description"]+"\n"
        +"Ulteriori informazioni: "+extracted_process["url"]+"\n"
        ,reply_markup=choice_keyboard
    )
    return CHOOSING


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def not_understood(bot, update, user_data):
    update.message.reply_text(
        'Scusa, non ho capito cosa intendi, clicca uno dei pulsanti qui sotto per scegliere cosa fare :)'
        ,reply_markup=choice_keyboard
    )
    return RECOVER


def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],
        states={

            CHOOSING: [
                RegexHandler('^(DOMANDA LIBERA)$', regular_choice, pass_user_data=True),
                RegexHandler('^SFOGLIA PER CATEGORIE$', custom_choice, pass_user_data=True),
                RegexHandler('^INDIETRO$', back_home, pass_user_data=True),
                RegexHandler('^FINE$', done, pass_user_data=True),
                MessageHandler(Filters.text, not_understood, pass_user_data=True),
            ],

            WANT_FEEDBACK: [
                RegexHandler('^(Si|No)$', want_feedback_process, pass_user_data=True),
                RegexHandler('^FINE$', done, pass_user_data=True),
                MessageHandler(Filters.text, not_understood, pass_user_data=True),
            ],

            SPECIFIED_FEEDBACK: [
                RegexHandler('^FINE$', done, pass_user_data=True),
                MessageHandler(Filters.text, exit_process , pass_user_data=True),
            ],

            TYPING_CHOICE: [
                RegexHandler('^FINE$', done, pass_user_data=True),
                MessageHandler(Filters.text, cat_handler, pass_user_data=True),
            ],

            RECOVER: [
                RegexHandler('^(DOMANDA LIBERA)$', regular_choice, pass_user_data=True),
                RegexHandler('^INDIETRO$', back_home, pass_user_data=True),
                RegexHandler('^SFOGLIA PER CATEGORIE$', custom_choice, pass_user_data=True),
                RegexHandler('^FINE$', done, pass_user_data=True),
                MessageHandler(Filters.text, not_understood, pass_user_data=True),
            ],

            TYPING_REPLY: [
                MessageHandler(Filters.text, received_information, pass_user_data=True),
            ],

            RENDERING_PROCESS_CAT: [
                RegexHandler('^INDIETRO$', back_home, pass_user_data=True),
                MessageHandler(Filters.text, rendering_process_cat_handler, pass_user_data=True),
            ],
            RENDERING_PROCESS_REQ: [
                RegexHandler('^INDIETRO$', back_home, pass_user_data=True),
                MessageHandler(Filters.text, rendering_process_req_handler, pass_user_data=True),
            ],
        },

        fallbacks=[
            RegexHandler('^FINE$', done, pass_user_data=True),
            MessageHandler(Filters.text, not_understood, pass_user_data=True),
        ]
    )

    dp.add_handler(conv_handler)

    # Log all errors
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

