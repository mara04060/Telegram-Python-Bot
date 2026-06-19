import tempfile

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, ConversationHandler, \
    MessageHandler, filters

import credentials
from gpt import ChatGptService
from log_info import logger
from state import State
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, voice_to_text, delete_file)

MENU = {
        '/start': 'Головне меню',
        '/random': 'Дізнатися випадковий цікавий факт 🧠',
        '/gpt': 'Задати питання чату GPT 🤖',
        '/talk': 'Поговорити з відомою особистістю 👤',
        '/quiz': 'Взяти участь у квізі ❓',
        '/voice': 'Голосовий ChatGPT 🎤',
        "/profile": "Генерація Резюме-IT 😎"
    }

MENU_TALK = {
        "talk_cobain": "Курт Кобейн",
        "talk_hawking": "Стівен Гокінг",
        "talk_nietzsche": "рідріх Ніцше",
        "talk_queen": "Королева Єлизавета II",
        "talk_tolkien": "Дж.Р.Р. Толкін",
    }

RESUME_QUESTIONS = [
    "ПІБ ТА МІСТО",
    "БАЖАНА ПОСАДА",
    "ДОСВІД В IT",
    "ТЕХНІЧНІ НАВИЧКИ",
    "ОСТАННЄ МІСЦЕ РОБОТИ",
    "ОСВІТА ТА ДОДАТКОВА ІНФОРМАЦІЯ"
]

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("menu_router")
    logger.info("message: %s", update.message.text)
    if not update.message or not update.message.text:
        return State.MAIN

    command = update.message.text.lower()
    logger.debug("command: %s", command)
    if "random" in command:
        return await random(update, context)
    elif "gpt" in command:
        return await gpt_start(update, context)
    elif "talk" in command:
        return await talk_start(update, context)
    elif "quiz" in command:
        return await quiz_start(update, context)
    elif "voice" in command:
        return await voice_start(update, context)
    elif "profile" in command:
        return await profile_start(update, context)
    else:
        await send_text(update, context, "Неіснуюча команда, оберіть будь-яку з меню.")
        return State.MAIN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("start")
    await send_image(update, context, 'main')
    menu = "\n".join(f"{key} - {value}" for key, value in MENU.items())
    await send_text(update, context, load_message('main') + menu)
    await show_main_menu(update, context, MENU)
    return State.MAIN

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("random")
    await send_image(update, context, 'random')
    answer = await get_gpt(context).send_question(load_prompt('random'), 'Давай рандомний факт')
    await send_text_buttons(update, context,answer,{
            'random_finish': 'Закінчити',
            'random_one_more': 'Хочу ще факт',
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
    return State.RANDOM

# GPT-Chat - module
async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("gpt_start")
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message("gpt"))
    return State.GPT

async def gpt_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("gpt_dialog")
    my_message = await send_text(update, context, "... друкую .. обережно ... чекай...")
    answer = await get_gpt(context).send_question(load_prompt('gpt'), update.message.text)
    await my_message.edit_text(answer)
    await send_text_buttons(update, context, "", {"start": "Повернутись в меню"})
    return State.GPT

# Talk in STARS - module
async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("talk_start")
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, load_message("talk"), MENU_TALK)
    return State.TALK_SELECT

async def talk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("talk_button")
    await update.callback_query.answer()
    await send_image(update, context, update.callback_query.data)
    text_message = f"{update.callback_query.from_user.first_name} ви починаєте діалог без привітання - відразу щось по темі."
    await send_text(update, context, text_message)
    await get_gpt(context).set_prompt(load_prompt(update.callback_query.data))
    return State.TALK_DIALOG

async def talk_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("talk_dialog")
    print_message = await send_text(update, context, "... щось друкуэ...")
    try:
        answer = await get_gpt(context).add_message(update.message.text)
        await print_message.edit_text(answer)
    except Exception as e:
        error_text = "Помилка при зверненні до GPT -крок talk_dialog"
        logger.error("%s: %s", error_text, e)
        await print_message.edit_text(error_text)
    return State.TALK_DIALOG

# Quiz - module
async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("quiz_start")
    context.user_data.setdefault("quiz_score", 0)
    context.user_data.setdefault("cuount_quiz", 0)
    if context.user_data.get("cuount_quiz") > 0:
        context.user_data["quiz_score"] = 0
        context.user_data["cuount_quiz"] = 0
    await send_image(update, context, 'quiz')
    await send_text_buttons(update, context, load_message("quiz"), {
        "quiz_prog": "Python3 - рулить - ти лише підрулюєш ",
        "quiz_math": "Математика без стресу",
        "quiz_biology": "Біологія - понад усе"
    })
    return State.QUIZ_SELECT

async def quiz_buttons_handler(update: Update, context):
    logger.info("quiz_buttons_handler")
    await update.callback_query.answer()
    query = update.callback_query.data
    if query == 'quiz_finish':
        return await quiz_start(update, context)
    else:
        return await quiz_button(update, context)

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("quiz_button")
    my_message = await send_text(update, context, "... друкую .. чекай...")
    answer = await get_gpt(context).send_question(load_prompt('quiz'), update.callback_query.data)
    await my_message.edit_text(answer)
    return State.QUIZ_DIALOG

async def quiz_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("quiz_dialog")
    print_message = None
    try:
        print_message = await send_text(update, context, "... перевіряю...")
        gpt_answer = await get_gpt(context).add_message(update.message.text)
        current_score, cuount_quiz = math_score_quiz(context, gpt_answer)
        await print_message.edit_text(f"{gpt_answer}\n Ваш поточний рахунок: {current_score}.\n Кількість питань: {cuount_quiz}")
    except Exception as e:
        error_text = "Помилка при зверненні до GPT -крок quiz_dialog"
        logger.error("%s: %s", error_text, e)
        if print_message:
            await print_message.edit_text(error_text)
        else:
            await send_text(update, context, error_text)
    await send_text_buttons(update, context,"відповідай або:",{
        'quiz_finish': 'Закінчити'
        }
    )
    return State.QUIZ_DIALOG

# Current score for Quiz
def math_score_quiz(context, gpt_answer):
    current_score = context.user_data.get("quiz_score", 0)
    cuount_quiz = context.user_data.get("cuount_quiz", 0)
    cuount_quiz +=1
    if "Правильно!" in gpt_answer:
        current_score += 1
    elif "Неправильно!" in gpt_answer:
        current_score -= 1
    else:
        cuount_quiz -= 1 # Якщо немає відповыді від ГПТ то не зараховуємо спробу
    context.user_data["quiz_score"] = current_score
    context.user_data["cuount_quiz"] = cuount_quiz
    return current_score, cuount_quiz

# Voice chat in GPT - module
async def voice_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("voice_start")
    await send_image(update, context, 'voice')
    await send_text(update, context, load_message("voice"))
    return State.VOICE_DIALOG

async def close_or_next_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        logger.info("message: %s", update.message.text.lower())
        if update.message.text.lower() in ["завершити", "закінчити", "close", "clear"]:
            return await start(update, context)
        else:
            await send_text(update, context, "Будь ласка, надішліть голосове повідомлення або натисніть кнопку.")
            return State.VOICE_DIALOG
    if not update.message or not update.message.voice:
        await send_text(update, context, "Будь ласка, надішліть голосове повідомлення.")
        return State.VOICE_DIALOG
    return None

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("voice_message_handler")
    await close_or_next_dialog(update, context)
    user_message_status = await send_text(update, context, "... розпізнаю мову ...")
    error_text = "Виникла помилка під час обробки голосового повідомлення. Спробуйте ще раз."
    try:
        temp_audio_file_path = await voice_to_text(tempfile, await update.message.voice.get_file())
        transcribed_text = await get_gpt(context).transcribe_audio(temp_audio_file_path)
        gpt_response_text = await get_gpt(context).add_message(transcribed_text)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_response_audio_file:
            await get_gpt(context).synthesize_speech(gpt_response_text, temp_response_audio_file.name)
            temp_response_audio_file_path = temp_response_audio_file.name

        with open(temp_response_audio_file_path, "rb") as audio_to_send:
            await update.message.reply_voice(voice=audio_to_send)
    except Exception as e:
        logger.error("Ошибка в voice_message_handler: %s", e)
        if user_message_status:
            await user_message_status.edit_text(error_text)
        else:
            await send_text(update, context, error_text)
    finally:
        delete_file('temp_audio_file_path' )
        delete_file('temp_response_audio_file_path')
    await send_text_buttons(update, context, "-", {
        'voice_finish': 'Закінчити голосовий чат'
    })
    return State.VOICE_DIALOG

async def voice_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("voice_buttons_handler")
    await update.callback_query.answer()
    if update.callback_query.data == 'voice_finish':
        return await start(update, context)
    return State.VOICE_DIALOG

# RESUME (CV) - Module
async def profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("profile_start")
    await send_image(update, context, 'profile')
    await send_text(update, context, load_message("profile"))
    context.user_data["resume_data"] = []
    context.user_data["resume_question_index"] = 0
    current_question_index = context.user_data["resume_question_index"]
    await send_text(update, context, RESUME_QUESTIONS[current_question_index])
    return State.PROFILE_DIALOG

def add_question(context, update, resume_data):
    current_question_index = context.user_data.get("resume_question_index", 0)
    if current_question_index < len(RESUME_QUESTIONS):
        resume_data.append(f"{RESUME_QUESTIONS[current_question_index]} {update.message.text}")
        context.user_data["resume_data"] = resume_data
        context.user_data["resume_question_index"] += 1
        current_question_index += 1
    return current_question_index

async def send_questions_in_dialog(update, context, resume_data, current_question_index):
    if current_question_index < len(RESUME_QUESTIONS):
        await send_text(update, context, RESUME_QUESTIONS[current_question_index])
        return State.PROFILE_DIALOG
    else:
        return await generation_profile(update, context, resume_data)

async def generation_profile(update, context, resume_data):
    prompt = load_prompt("profile")
    user_info = "\n".join(resume_data)
    my_message = await send_text(update, context, "...ChatGPT генерує Ваше резюме...")
    try:
        answer = await get_gpt(context).send_question(prompt, user_info)
        await my_message.edit_text(answer)
    except Exception as e:
        error_code = "Виникла помилка під час генерації резюме"
        logger.error("%s : %s", error_code, e)
        await my_message.edit_text(error_code)
    context.user_data["resume_data"] = []
    context.user_data["resume_question_index"] = 0
    await send_text_buttons(update, context, "Ваше резюме згенеровано. Повернутись в меню?", {
        "start": "Повернутись в меню"
    })
    return State.MAIN

async def profile_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("profile_dialog")
    resume_data = context.user_data.get("resume_data", [])
    current_question_index = add_question(context, update, resume_data)
    await send_questions_in_dialog(update, context, resume_data, current_question_index)

async def profile_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("profile_buttons_handler")
    await update.callback_query.answer()
    query = update.callback_query.data
    if query == 'profile_finish':
        context.user_data["resume_data"] = []
        context.user_data["resume_question_index"] = 0
        return await start(update, context)
    return State.PROFILE_DIALOG


def get_gpt(context):
    gpt = context.user_data.get("gpt")
    if gpt is None:
        gpt = ChatGptService(credentials.ChatGPT_TOKEN)
        context.user_data["gpt"] = gpt
    return gpt

main_command_handlers = [
    CommandHandler("start", start),
    CommandHandler("random", random),
    CommandHandler("talk", talk_start),
    CommandHandler("quiz", quiz_start),
    CommandHandler("gpt", gpt_start),
    CommandHandler("voice", voice_start),
    CommandHandler("profile", profile_start)
]

conv = ConversationHandler(
    entry_points=main_command_handlers,
    states={
        State.MAIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router),
            CallbackQueryHandler(start, pattern="^start$")
        ],
        State.RANDOM: [
            CallbackQueryHandler(random_buttons_handler, pattern="^random_.*$")
        ],
        State.GPT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_dialog),
        ],
        State.TALK_SELECT: [
            CallbackQueryHandler(talk_button, pattern="^talk_.*$")
        ],
        State.TALK_DIALOG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, talk_dialog)
        ],
        State.QUIZ_SELECT: [
            CallbackQueryHandler(quiz_buttons_handler, pattern="^quiz_.*$")
        ],
        State.QUIZ_DIALOG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_dialog),
            CallbackQueryHandler(quiz_buttons_handler, pattern="^quiz_(finish|new_quiz)$")
        ],
        State.VOICE_DIALOG: [
            MessageHandler(filters.VOICE, voice_message_handler),
            CallbackQueryHandler(voice_buttons_handler, pattern="^voice_.*$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, voice_message_handler)
        ],
        State.PROFILE_DIALOG: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, profile_dialog),
            CallbackQueryHandler(profile_buttons_handler, pattern="^profile_.*$")
        ]
    },
    fallbacks=main_command_handlers,
    per_chat=True,
    per_user=True,
    per_message=False
)

app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()
app.add_handler(conv)
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling(allowed_updates=Update.ALL_TYPES)