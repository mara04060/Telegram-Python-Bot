import pytest

from unittest.mock import (
    AsyncMock,
    MagicMock,
    patch
)

from bot import (
    State,
    math_score_quiz,
    add_question,
    get_gpt,
    menu_router,
    close_or_next_dialog,
    generation_profile,
    talk_dialog,
)

@pytest.fixture
def context():
    ctx = MagicMock()
    ctx.user_data = {}
    return ctx


@pytest.fixture
def update():
    upd = MagicMock()
    upd.message = MagicMock()
    upd.message.text = "test"
    upd.callback_query = MagicMock()
    upd.callback_query.data = "test"
    return upd


def test_math_score_quiz_correct_answer(context):

    score, count = math_score_quiz(context,"Правильно!")
    assert score == 1
    assert count == 1
    assert context.user_data["quiz_score"] == 1
    assert context.user_data["cuount_quiz"] == 1


def test_math_score_quiz_wrong_answer(context):
    score, count = math_score_quiz(context,"Неправильно!" )
    assert score == -1
    assert count == 1
    assert context.user_data["quiz_score"] == -1
    assert context.user_data["cuount_quiz"] == 1


def test_math_score_quiz_unknown_answer(context):
    score, count = math_score_quiz(context,"GPT ERROR")
    assert score == 0
    assert count == 0
    assert context.user_data["quiz_score"] == 0
    assert context.user_data["cuount_quiz"] == 0


def test_math_score_quiz_existing_score(context):
    context.user_data["quiz_score"] = 5
    context.user_data["cuount_quiz"] = 10
    score, count = math_score_quiz( context,"Правильно!" )
    assert score == 6
    assert count == 11


def test_add_question_first_question(context, update):
    context.user_data["resume_question_index"] = 0
    update.message.text = "Ivan Kyiv"
    resume_data = []
    index = add_question( context,update, resume_data)
    assert index == 1
    assert len(resume_data) == 1
    assert "Ivan Kyiv" in resume_data[0]
    assert context.user_data["resume_question_index"] == 1


def test_add_question_last_question(context, update):
    from bot import RESUME_QUESTIONS
    context.user_data["resume_question_index"] = len(RESUME_QUESTIONS )
    resume_data = []
    index = add_question( context,update,resume_data )
    assert index == len(RESUME_QUESTIONS)
    assert resume_data == []


@patch("bot.ChatGptService")
def test_get_gpt_create_instance( mock_gpt, context):
    result = get_gpt(context)
    mock_gpt.assert_called_once()
    assert result == mock_gpt.return_value
    assert context.user_data["gpt"] == result


@patch("bot.ChatGptService")
def test_get_gpt_return_existing( mock_gpt, context):
    existing = object()
    context.user_data["gpt"] = existing
    result = get_gpt(context)
    assert result is existing
    mock_gpt.assert_not_called()

@pytest.mark.asyncio
async def test_menu_router_random(update,context):
    update.message.text = "/random"
    with patch("bot.random",AsyncMock(return_value=State.RANDOM)) as mock_random:
        result = await menu_router(update,context)
        assert result == State.RANDOM
        mock_random.assert_awaited_once()

@pytest.mark.asyncio
async def test_menu_router_gpt(update,context):
    update.message.text = "/gpt"
    with patch("bot.gpt_start",AsyncMock(return_value=State.GPT)) as mock_gpt:
        result = await menu_router(update,context )
        assert result == State.GPT
        mock_gpt.assert_awaited_once()


@pytest.mark.asyncio
async def test_menu_router_talk( update, context):
    update.message.text = "/talk"
    with patch("bot.talk_start", AsyncMock(return_value=State.TALK_SELECT)) as mock_talk:
        result = await menu_router(update,context )
        assert result == State.TALK_SELECT
        mock_talk.assert_awaited_once()


@pytest.mark.asyncio
async def test_menu_router_profile( update, context):
    update.message.text = "/profile"
    with patch("bot.profile_start",AsyncMock(return_value=State.PROFILE_DIALOG)) as mock_profile:
        result = await menu_router(update, context )
        assert result == State.PROFILE_DIALOG
        mock_profile.assert_awaited_once()


@pytest.mark.asyncio
async def test_menu_router_unknown_command(update,context):
    update.message.text = "/unknown"
    with patch("bot.send_text",AsyncMock()) as mock_send:
        result = await menu_router(update,context)
        mock_send.assert_awaited_once()
        assert result == State.MAIN


@pytest.mark.asyncio
async def test_menu_router_without_message(
        context
):
    update = MagicMock()
    update.message = None
    result = await menu_router( update, context )
    assert result == State.MAIN



# close_or_next_dialog

@pytest.mark.asyncio
async def test_close_or_next_dialog_finish( update, context):
    update.message.text = "закінчити"
    with patch("bot.start", AsyncMock(return_value=State.MAIN)):
        result = await close_or_next_dialog(update,context )
        assert result == State.MAIN

@pytest.mark.asyncio
async def test_close_or_next_dialog_invalid_text(update,context):
    update.message.text = "hello"
    with patch("bot.send_text", AsyncMock()) as send_text:
        result = await close_or_next_dialog(update,context)
        send_text.assert_awaited_once()
        assert result == State.VOICE_DIALOG

@pytest.mark.asyncio
async def test_close_or_next_dialog_without_voice( context):
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = None
    update.message.voice = None
    with patch("bot.send_text",AsyncMock()) as send_text:
        result = await close_or_next_dialog(update,context)
        send_text.assert_awaited_once()
        assert result == State.VOICE_DIALOG

# generation_profile
@pytest.mark.asyncio
async def test_generation_profile_success(update,context):
    message = AsyncMock()
    gpt = AsyncMock()
    gpt.send_question.return_value = ("READY CV" )
    context.user_data["gpt"] = gpt
    with (patch( "bot.load_prompt",return_value="prompt"), patch("bot.send_text", AsyncMock(return_value=message)), patch( "bot.send_text_buttons", AsyncMock() )):
        result = await generation_profile(update,context,["name","skills" ])
    message.edit_text.assert_awaited_once_with("READY CV" )
    assert context.user_data["resume_data"] == []
    assert (context.user_data[ "resume_question_index"] == 0)
    assert result == State.MAIN

@pytest.mark.asyncio
async def test_generation_profile_exception(update,context):
    message = AsyncMock()
    gpt = AsyncMock()
    gpt.send_question.side_effect = (Exception("GPT ERROR"))
    context.user_data["gpt"] = gpt
    with (patch("bot.load_prompt", return_value="prompt"), patch("bot.send_text",AsyncMock(return_value=message)),
          patch("bot.send_text_buttons",AsyncMock())):
        await generation_profile( update,context,["name"])
    message.edit_text.assert_awaited_once_with("Виникла помилка під час генерації резюме")

# talk_dialog
@pytest.mark.asyncio
async def test_talk_dialog_success(update,context):
    msg = AsyncMock()
    gpt = AsyncMock()
    gpt.add_message.return_value = ("GPT ANSWER")
    context.user_data["gpt"] = gpt
    with patch("bot.send_text", AsyncMock(return_value=msg)):
        result = await talk_dialog( update, context )
    msg.edit_text.assert_awaited_once_with("GPT ANSWER" )
    assert result == State.TALK_DIALOG

@pytest.mark.asyncio
async def test_talk_dialog_exception( update, context):
    msg = AsyncMock()
    gpt = AsyncMock()
    gpt.add_message.side_effect = ( Exception("GPT ERROR") )
    context.user_data["gpt"] = gpt
    with patch("bot.send_text", AsyncMock(return_value=msg) ):
        result = await talk_dialog(update, context )
    msg.edit_text.assert_awaited_once_with("Помилка при зверненні до GPT -крок talk_dialog" )
    assert result == State.TALK_DIALOG