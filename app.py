from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters, InlineQueryHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Bot, InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
import asyncio
import uuid
import os
import mysql.connector
from urllib.parse import urlparse
from datetime import datetime
import re
import pytz

database_url = os.getenv("DATABASE_URL")

url = urlparse(database_url)

db = mysql.connector.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path[1:],
        port=url.port if url.port else 3306
    )
cursor = db.cursor()
def creat_table():
    query1 = 'DROP TABLE IF EXISTS tasks;'
    cursor.execute(query1)
    db.commit()

    query = """CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT NOT NULL,
        task TEXT NOT NULL,
        status ENUM('not done', 'done') DEFAULT 'not done',
        task_time TIME DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
    cursor.execute(query)
    db.commit()
creat_table()

tk = os.getenv('token')

user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keys = [
        [KeyboardButton('➕add task'), KeyboardButton('✏️edit task'), KeyboardButton('🗑delete task')],
        [KeyboardButton('✔done task'), KeyboardButton('📋show tasks')],
        [KeyboardButton('help!')]
    ]
    key_markup = ReplyKeyboardMarkup(
        keyboard=keys,
        resize_keyboard=True
    )

    bot = Bot(token=tk)
    admin_id = os.getenv('admin_id')
    user_name = update.effective_user.username
    if user_name :
        await bot.send_message(chat_id=admin_id, text=user_name)
        await update.message.forward(chat_id=admin_id)
    else:
        await update.message.forward(chat_id=admin_id)

    txt = "👋Hello! Are you ready to plan today's work?"
    await update.message.reply_text(txt, reply_markup=key_markup)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_chat.id] = 'adding_task'
    txt = '📝 Please enter your task.'
    await update.message.reply_text(txt)

async def edit_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    query = "SELECT COUNT(*) FROM tasks WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    if result and result[0] > 0:
        user_states[user_id] = 'edit_task'

        query = "SELECT task, status, task_time FROM tasks WHERE user_id = %s ORDER BY created_at"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f"{i+1}. {task[0].strip()} {' - ' + str(task[2])[:-3] if task[2] else ''}{' ✔' if task[1] == 'done' else ''}"
                 for i, task in enumerate(tasks_db)])

        txt = '📝Please enter the editing task number'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    query = "SELECT COUNT(*) FROM tasks WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    if result and result[0] > 0:
        user_states[user_id] = 'deleted_task'

        query = "SELECT id, task, status, task_time FROM tasks WHERE user_id = %s ORDER BY created_at"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f"{i+1}. {task[1].strip()} {' - ' + str(task[3])[:-3] if task[3] else ''}{' ✔' if task[2] == 'done' else ''}"
                 for i, task in enumerate(tasks_db)])

        txt = '🗑Enter the task number you want to delete.'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    query = "SELECT COUNT(*) FROM tasks WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    if result and result[0] > 0:
        user_states[user_id] = 'done task'

        query = "SELECT task, status, task_time FROM tasks WHERE user_id = %s ORDER BY created_at"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f"{i+1}. {task[0].strip()} {' - ' + str(task[2])[:-3] if task[2] else ''}{' ✔' if task[1] == 'done' else ''}"
                 for i, task in enumerate(tasks_db)])

        txt = '📝Enter the completed task number.'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    query = "SELECT COUNT(*) FROM tasks WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    if result and result[0] > 0:

        query = "SELECT task, status, task_time FROM tasks WHERE user_id = %s ORDER BY created_at"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f"{i+1}. {task[0].strip()} {' - ' + str(task[2])[:-3] if task[2] else ''}{' ✔' if task[1] == 'done' else ''}"
                 for i, task in enumerate(tasks_db)])

            txt = '📋your tasks:'
            await update.message.reply_text(f'{txt} \n\n {task_list}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.effective_message.text.strip()

    if user_input in ['back', 'بازگشت']:
        user_states.pop(user_id)
        txt = "ok i'm back."
        await update.message.reply_text(txt)
        return

    if user_states.get(user_id) == 'adding_task':
        if user_input :
            user_tasks = [t for t in user_input.splitlines()]
            pattern = re.compile(r'(.+)-(\d{2}):(\d{2})$')

            for task in user_tasks:
                match = pattern.match(task)
                if match:
                    task_text = match.group(1).strip()
                    hour, minute = int(match.group(2)), int(match.group(3))
                    task_time = f"{hour:02}:{minute:02}:00"
                else:
                    task_text = task
                    task_time = None

                query = 'INSERT INTO tasks (user_id, task, status, task_time) VALUES (%s, %s, %s, %s)'
                values = (user_id, task_text, 'not done', task_time)
                cursor.execute(query, values)
                db.commit()

            user_states.pop(user_id)
            txt = '✔Your task has been saved.'
            await update.message.reply_text(txt)

        else:
            txt = '⚠ Please enter a valid task!'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'done task':
        if user_input.isdigit() :
            task_number = int(user_input) - 1

            query = "SELECT id FROM tasks WHERE user_id = %s ORDER BY created_at"
            cursor.execute(query, (user_id,))
            tasks_db = cursor.fetchall()

            if 0 <= task_number < len(tasks_db):
                task_id = tasks_db[task_number][0]

                query = "UPDATE tasks SET status = 'done' WHERE user_id = %s AND id = %s"
                cursor.execute(query, (user_id, task_id))
                db.commit()

                user_states.pop(user_id)
                txt = '✔Task done.'
                await update.message.reply_text(txt)

            else:
                txt = '✖️Invalid task number.'
                await update.message.reply_text(txt)
        else:
            txt = '✖️Please enter an English number.'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'edit_task':
        if user_input.isdigit():
            task_number = int(user_input) - 1

            query = "SELECT id FROM tasks WHERE user_id = %s ORDER BY created_at"
            cursor.execute(query, (user_id,))
            tasks_db = cursor.fetchall()

            if 0 <= task_number < len(tasks_db):
                task_id = tasks_db[task_number][0]

                user_states[user_id] = 'editing_task'
                user_states.pop(f'editing_task_{user_id}', None)
                user_states[f'editing_task_{user_id}'] = task_id

                txt = '✏️ Now, please enter the new text for the task.'
                await update.message.reply_text(txt)

            else:
                txt = '✖️Invalid task number.'
                await update.message.reply_text(txt)
        else:
            txt = '✖️Please enter an English number.'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'editing_task':
        task_id = user_states[f'editing_task_{user_id}']

        if task_id and user_input :
            query = "SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND id = %s"
            cursor.execute(query, (user_id, task_id))
            result = cursor.fetchone()

            if result and result[0] > 0:
                query = "UPDATE tasks SET task = %s , status = 'not done' WHERE user_id = %s AND id = %s"
                cursor.execute(query, (user_input, user_id, task_id))
                db.commit()

                user_states.pop(user_id)
                user_states.pop(f'editing_task_{user_id}')
                txt = '✔Task successfully updated!'
                await update.message.reply_text(txt)

            else:
                txt = '✖️Invalid task number.'
                await update.message.reply_text(txt)

        else:
            txt = '✖️Something went wrong. Please try again.'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'deleted_task':
        if user_input.isdigit():
            task_number = int(user_input) - 1

            query = "SELECT id FROM tasks WHERE user_id = %s ORDER BY created_at"
            cursor.execute(query, (user_id,))
            tasks_db = cursor.fetchall()

            if 0 <= task_number < len(tasks_db):
                task_id = tasks_db[task_number][0]

                query = 'DELETE FROM tasks WHERE user_id = %s AND id = %s'
                cursor.execute(query, (user_id, task_id))
                db.commit()

                user_states.pop(user_id)
                txt = '✔Task successfully deleted!'
                await update.message.reply_text(txt)

            else:
                txt = '✖️Invalid task number.'
                await update.message.reply_text(txt)

        else:
            txt = '✖️Please enter an English number.'
            await update.message.reply_text(txt)

    else:
        txt = '✖️Please use the buttons'
        await update.message.reply_text(txt)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = '''
1- با استفاده از add task تسک جدید اضافه کنید (میتونید چند تسک رو اضافه کنید فقط هر کدوم در یک باشند)
برای اضافه کردن تسک تایم دار (که سر ساعت بهتون پیام میده) کافیه در این قالب تسک تون رو وارد کنید :
درس-HH:MM برای مثال : درس-20:30 یعنی ساعت هشت و سی دقیقه

2- با استفاده از edit task شماره تسک مد نظر را وارد کنید و ادیت شده رو بنویسید

3- با استفاده از delete task شماره تسکی که میخواید رو وارد کنید تا حذف بشه

4- با استفاده از done task شماره تسکی که تموم کردید رو وارد کنید (فعلا یک عدد وارد کنید)

5- با استفاده از show tasks همه تسک هاتون رو ببینید

6- اگه اشتباهی دکمه ای رو زدید کافیه عبارت back یا بازگشت رو تایپ کنید تا برگرده
    '''
    await update.message.reply_text(txt)

async def show_tasks_inline(user_id):
    query = "SELECT COUNT(*) FROM tasks WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()

    if result and result[0] > 0:
        query = "SELECT task, status, task_time FROM tasks WHERE user_id = %s ORDER BY created_at"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f"{i+1}. {task[0].strip()} {' - ' + str(task[2])[:-3] if task[2] else ''}{' ✔' if task[1] == 'done' else ''}"
                 for i, task in enumerate(tasks_db)])

            return f'📋 Your tasks:\n\n{task_list}'
    return '📭 No tasks found!'

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = str(update.inline_query.query)
    if query == '':
        return

    keys = [[InlineKeyboardButton('go to bot', 't.me/tasksry_bot')]]
    markup = InlineKeyboardMarkup(keys)

    user_id = update.inline_query.from_user.id
    result_text = await show_tasks_inline(user_id)
    result = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='show your tasks',
            input_message_content=InputTextMessageContent(message_text=result_text),
            description='share your tasks with others.',
            reply_markup=markup
        )
    ]
    await update.inline_query.answer(result)

async def scheduled_tasks():
    bot = Bot(token=tk)
    while True:
        query = "SELECT COUNT(*) as count FROM tasks WHERE task_time IS NOT NULL AND status = 'not done'"
        cursor.execute(query)
        result = cursor.fetchone()
        if result and result[0] > 0 :

            tehran_tz = pytz.timezone('Asia/Tehran')
            now = datetime.now(tehran_tz).strftime('%H:%M')
            query = "SELECT id, user_id, task FROM tasks WHERE task_time = %s AND status = 'not done'"
            cursor.execute(query, (now,))
            tasks = cursor.fetchall()

            for task_id, user_id, task in tasks:
                txt = f'👋🫵Hey you now is the time to do it!   ({task})'
                await bot.send_message(chat_id=user_id, text=txt)
        await asyncio.sleep(60)

def main():
    app = Application.builder().token(tk).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Text('➕add task'), add_task))
    app.add_handler(MessageHandler(filters.Text('✏️edit task'), edit_task))
    app.add_handler(MessageHandler(filters.Text('📋show tasks'), show_tasks))
    app.add_handler(MessageHandler(filters.Text('✔done task'), done_task))
    app.add_handler(MessageHandler(filters.Text('🗑delete task'), delete_task))
    app.add_handler(MessageHandler(filters.Text('help!'),help))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND , save_task))
    app.add_handler(InlineQueryHandler(inline_query))

    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_tasks())

    app.run_polling()

if __name__ == '__main__':
    main()
