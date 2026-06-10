import asyncio
import timeit
from email.headerregistry import MessageIDHeader
from http.client import responses

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, Dialog, send_html)

import credentials

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if dialog.mode == "gpt":
        await gpt_dialog(update, context)
    elif dialog.mode == "talk":
        await talk_dialog(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'random')
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, 'Давай рандомний факт')
    await send_text(update, context, response)
    await send_text_buttons(
        update, context,
        response,
        {
            'random_finish' : 'Закінчити',
            'random_one_more' :'Хочу ще факт',
        }
    )

async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = "gpt"
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message("gpt") )
                    # 'Питай у мене найбезглузныше питання. Я выдповым...')

async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    my_massage = await send_text(update, context, "... друкую .. обережно ... чекай...")
    answer = await chat_gpt.send_question(load_prompt('gpt'), update.message.text)
    await my_massage.edit_text(answer)

async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'random_finish':
        await start(update, context)
    elif query == 'random_one_more':
        await random(update, context)
    await update.callback_query.answer()

async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = 'talk'
    await send_image(update, context, 'talk')
    # await send_text(update, context, load_message("talk"))
    await send_text_buttons(update, context, load_message("talk"), {
        "talk_cobain": "Курт Кобейн",
        "talk_hawking": "Стівен Гокінг",
        "talk_nietzsche": "рідріх Ніцше",
        "talk_queen": "Королева Єлизавета II",
        "talk_tolkien": "Дж.Р.Р. Толкін",
    })

async def talk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await send_html(update, context, f"{update.callback_query.from_user.first_name} ви починаэте дыалог з  {update.callback_query.data} \r починай дыалог без привытання - выдразу щось по темы.")
    # await talk_dialog(update, context, file_name)


async def talk_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print_message = await send_text(update, context, "... щось друкуэ...")
    print(update.callback_query.data, update.message.text)
    answer = await chat_gpt.send_question(load_prompt(update.callback_query.data), update.message.text)
    await print_message.edit_text(answer)

dialog = Dialog()
dialog.mode = ""

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt_start))
app.add_handler(CommandHandler('talk', talk_start))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(talk_button, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
