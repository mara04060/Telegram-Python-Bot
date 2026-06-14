from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, ConversationHandler, \
    MessageHandler, filters

import credentials
from gpt import ChatGptService
from log_info import logger
from state import State
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)


async def menu_router(update: Update,context: ContextTypes.DEFAULT_TYPE):
    logger.info("menu_router")
    logger.info(update.message.text)
    if not update.message or not update.message.text:
        return State.MAIN

    command = update.message.text.lower()
    if "random" in command:
        return await random(update, context)
    elif "gpt" in command:
        return await gpt_start(update, context)
    elif "talk" in command:
        return await talk_start(update, context)
    elif "quiz" in command:
        return await quiz_start(update, context)
    # else:
    #     return State.MAIN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("start")
    await send_image(update, context, 'main')
    await send_text(update, context, load_message('main'))
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
        # Додати команду в меню можна так:
        # 'command': 'button text'
    })
    return State.MAIN


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("random")
    await send_image(update, context, 'random')
    answer = await get_gpt(context).send_question(load_prompt('random'), 'Давай рандомний факт')
    await send_text_buttons(
        update, context,
        answer,
        {
            'random_finish' : 'Закінчити',
            'random_one_more' :'Хочу ще факт',
        }
    )
    return State.RANDOM

async def random_buttons_handler(update: Update, context):
    logger.info("random_buttons_handler")
    await update.callback_query.answer()
    query = update.callback_query.data
    if query == 'random_finish':
        return await start(update, context)
    elif query == 'random_one_more':
        return await random(update, context)

    # return State.RANDOM

async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("gpt_start")
    # context.user_data["mode"] = "gpt"
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message("gpt") )
    # return State.GPT

async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("gpt_dialog")
    my_message = await send_text(update, context, "... друкую .. обережно ... чекай...")
    answer = await get_gpt(context).send_question(load_prompt('gpt'), update.message.text)
    await my_message.edit_text(answer)
    await send_text_buttons(update, context,"",{"start": "Повернутись в меню"} )
    return State.GPT

async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("talk_start")
    # context.user_data["mode"] = 'talk'
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, load_message("talk"), {
        "talk_cobain": "Курт Кобейн",
        "talk_hawking": "Стівен Гокінг",
        "talk_nietzsche": "рідріх Ніцше",
        "talk_queen": "Королева Єлизавета II",
        "talk_tolkien": "Дж.Р.Р. Толкін",
    })
    return State.TALK_SELECT

async def talk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("talk_button")
    await update.callback_query.answer()
    await send_image(update, context, update.callback_query.data)
    text_message = f"{update.callback_query.from_user.first_name} ви починаєте діалог без привітання - відразу щось по темі."
    await send_text(update, context, text_message)
    await get_gpt(context).set_prompt(load_prompt(update.callback_query.data))
    # return State.TALK_DIALOG

async def talk_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("talk_dialog")
    print_message = await send_text(update, context, "... щось друкуэ...")
    try:
        answer = await get_gpt(context).add_message(update.message.text)
    except Exception as e:
        await send_text(update, context,"Помилка при зверненні до GPT" )
    await print_message.edit_text(answer)
    return State.TALK_DIALOG

async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("quiz_start")
    # context.user_data["mode"] = 'quiz'
    await send_image(update, context, 'quiz')
    await send_text_buttons(update, context, load_message("quiz"), {
        "quiz_prog": "Python3 - рулить - ти лише підрулюєш",
        "quiz_math": "Математика без стресу",
        "quiz_biology": "Біологія - понад усе"
    })
    return State.QUIZ_SELECT

async def quiz_buttons_handler(update: Update, context):
    logger.info("quiz_buttons_handler")
    await update.callback_query.answer()
    query = update.callback_query.data
    if query == 'quiz_finish':
        return await start(update, context)
    elif query == 'quiz_new_quiz':
        return await quiz_start(update, context)
    else:
        return await quiz_button(update, context)

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("quiz_button")
    answer = await get_gpt(context).send_question(load_prompt('quiz'), update.callback_query.data)
    await send_text(update, context, answer)
    # return State.QUIZ_DIALOG


async def quiz_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("quiz_dialog")
    print_message = await send_text(update, context, "... перевіряю...")
    answer = await get_gpt(context).add_message(update.message.text)
    await print_message.edit_text(answer)
    await send_text_buttons(
        update, context,
        "Обери подальшу дію:",
        {
            'quiz_finish': 'Закінчити',
            'quiz_new_quiz': 'Нове питання.',
        }
    )
    return State.QUIZ_DIALOG

def get_gpt(context):
    gpt = context.user_data.get("gpt")
    if gpt is None:
        gpt = ChatGptService(credentials.ChatGPT_TOKEN)
        context.user_data["gpt"] = gpt
    return gpt

conv = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CommandHandler("random", random),
        CommandHandler("gpt", gpt_start)
    ],
    states={State.MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router )],
        State.RANDOM: [CallbackQueryHandler(random_buttons_handler,pattern="^random_.*$")],
        State.GPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_dialog), ],
        State.TALK_SELECT: [CallbackQueryHandler(talk_button, pattern="^talk_.*$")],
        State.TALK_DIALOG: [MessageHandler(filters.TEXT & filters.COMMAND, talk_dialog),],
        State.QUIZ_DIALOG: [MessageHandler(filters.TEXT & filters.COMMAND, quiz_dialog),
                           CallbackQueryHandler(quiz_buttons_handler, pattern="^quiz_(finish|new_quiz)$")]
            },
    fallbacks=[CommandHandler("start", start)],
    per_chat=True,
    per_user=True,
    per_message=False
)

# Зареєструвати обробник колбеку можна так:
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()
app.add_handler(conv)
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling(allowed_updates=Update.ALL_TYPES)