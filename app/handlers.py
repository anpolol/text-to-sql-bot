import os

from telegram import Update
from telegram import ReplyKeyboardMarkup, KeyboardButton

from telegram.ext import ContextTypes
from app.LangGraph import react_graph
from langfuse.langchain import CallbackHandler

ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])

langfuse_handler = CallbackHandler()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Нет доступа.")
        return

    user_text = update.message.text
    KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("kali"), KeyboardButton("analyse dreams")],
    ],
    resize_keyboard=True  # кнопки компактного размера
)

    if user_text == 'kali':
        context.user_data["database"] = "kali"
        await update.message.reply_text("Что вы хотите узнать из базы kali?")
    elif user_text == 'analyse dreams':
        context.user_data["database"] = "analyse dreams"
        await update.message.reply_text("Что вы хотите узнать из базы analyse dreams?")
    else:
        db = context.user_data.get("database")
        if not db:
            await update.message.reply_text("Привет! Выберите в меню к какой базе вы хотите обратиться?", reply_markup=KEYBOARD)
        else:
            result  = react_graph.invoke({
            "database": db,
            "user_input": user_text,
            "database_schema": "",
            "messages": []
            },
            config={"callbacks": [langfuse_handler]})
            answer = result["messages"][-1].content
            limit = 4096
            #for i in range(0, len(answer), limit):
                #await update.message.reply_text(answer[i:i+limit], reply_markup=KEYBOARD)            
            await update.message.reply_text(answer[:limit], reply_markup=KEYBOARD)            
