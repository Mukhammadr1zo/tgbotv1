import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, ConversationHandler
from telegram.ext import filters
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

LANGUAGE, QUESTION = range(2)

user_language = {}

languages = {
    "uz": "O‘zbek tili 🇺🇿",
    "ru": "Русский язык 🇷🇺"
}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '116270824953017572763'  
def write_to_google_sheets(question, lang):
    """Google Sheets-ga savolni yozish"""
    try:
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        values = [[question, lang]]  
        body = {'values': values}
        sheet.values().append(spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1",
                              valueInputOption="RAW", body=body).execute()

    except Exception as e:
        logging.error(f"Google Sheetsga yozishda xato: {e}")

async def start(update: Update, context: CallbackContext):
    keyboard = [[languages["uz"], languages["ru"]]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык:", reply_markup=reply_markup
    )
    return LANGUAGE

async def set_language(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    if text == languages["uz"]:
        user_language[chat_id] = "uz"
        await update.message.reply_text("Siz O‘zbek tilini tanladingiz. Savol yoki murojaatingizni yozing:", reply_markup=ReplyKeyboardRemove())
    elif text == languages["ru"]:
        user_language[chat_id] = "ru"
        await update.message.reply_text("Вы выбрали русский язык. Напишите ваш вопрос или заявку:", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("Iltimos, menyudan tilni tanlang / Пожалуйста, выберите язык из меню.")
        return LANGUAGE

    return QUESTION

async def handle_question(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    lang = user_language.get(chat_id, "uz")
    question = update.message.text

    write_to_google_sheets(question, lang)

    await update.message.reply_text(f"Yuborgan savolingiz saqlandi.O'rganib chiqib javob beramiz! Rahmat!")

    return QUESTION

async def change_language(update: Update, context: CallbackContext):
    keyboard = [[languages["uz"], languages["ru"]]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "Tilni qayta tanlang / Выберите язык снова:", reply_markup=reply_markup
    )
    return LANGUAGE

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Muloqot bekor qilindi. Botni qayta boshlash uchun /start bosing.")
    return ConversationHandler.END

def main():
    application = Application.builder().token("7495544106:AAFvegEA0UGf0PqFZ791WRQnKCBwrI1QnDI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()
