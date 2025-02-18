from decouple import config
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram import Bot
import os
import mysql.connector
from urllib.parse import urlparse

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
    cursor.execute(query)
    db.commit()

creat_table()

tk = os.getenv('token')

def send_message():
    bot = Bot(token=tk)
    query = 'SELECT user_id FROM tasks'
    cursor.execute(query)
    users_id = cursor.fetchone()
    for user_id in users_id:
        try :
            users_id = users_id[0]
            txt = 'hey you bot is ready!'
            bot.send_message(chat_id=user_id, text=txt)
        except:
            break

send_message()
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

        query = "SELECT id, task, status FROM tasks WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f'{task[0]}. {task[1].strip()}{" ✔" if task[2] == "done" else ""}' for task in
                 tasks_db])
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

        query = "SELECT id, task, status FROM tasks WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f'{task[0]}. {task[1].strip()}{" ✔" if task[2] == "done" else ""}' for task in
                 tasks_db])
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

        query = "SELECT id, task, status FROM tasks WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f'{task[0]}. {task[1].strip()}{" ✔" if task[2] == "done" else ""}' for task in
                 tasks_db])
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

        query = "SELECT id, task, status FROM tasks WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        tasks_db = cursor.fetchall()

        if tasks_db:
            task_list = "\n".join(
                [f'{task[0]}. {task[1].strip()}{" ✔" if task[2] == "done" else ""}' for task in
                 tasks_db])

            txt = '📋your tasks:'
            await update.message.reply_text(f'{txt} \n\n {task_list}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

def task_exists(user_id, task_number):
    query = "SELECT COUNT(*) as count FROM tasks WHERE user_id = %s AND id = %s"
    cursor.execute(query, (user_id, task_number))
    result = cursor.fetchone()
    return result and result[0] > 0

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.effective_message.text.strip()

    if user_input in ['back', 'بازگشت']:
        user_states.pop(user_id)
        txt = "ok i'm back."
        await update.message.reply_text(txt)
        return

    if user_states.get(user_id) == 'adding_task':  # add task

        if user_input :

            user_tasks = user_input.splitlines()
            query = 'INSERT INTO tasks (user_id, task, status) VALUES (%s, %s, %s)'
            values = [(user_id, task, 'not done') for task in user_tasks]
            cursor.executemany(query, values)
            db.commit()

            user_states.pop(user_id)
            txt = '✔Your task has been saved.'
            await update.message.reply_text(txt)
        else:
            txt = '⚠ Please enter a valid task!'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'done task':  # done task

        if user_input.isdigit() :
            task_number = int(user_input)

            if task_exists(user_id, task_number):

                query = "UPDATE tasks SET status = 'done' WHERE user_id = %s AND id = %s"
                cursor.execute(query, (user_id, task_number))
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

    elif user_states.get(user_id) == 'edit_task': # edit task

        if user_input.isdigit():
            task_number = int(user_input)

            if task_exists(user_id, task_number):

                user_states[user_id] = 'editing_task'
                user_states.pop(f'editing_task_{user_id}', None)
                user_states[f'editing_task_{user_id}'] = task_number

                txt = '✏️ Now, please enter the new text for the task.'
                await update.message.reply_text(txt)

            else:
                txt = '✖️Invalid task number.'
                await update.message.reply_text(txt)
        else:
            txt = '✖️Please enter an English number.'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'editing_task': # editing task
        task_number = user_states[f'editing_task_{user_id}']

        if task_number and user_input :

            if task_exists(user_id, task_number):

                query = 'UPDATE tasks SET task = %s WHERE user_id = %s AND id = %s'
                cursor.execute(query, (user_input, user_id, task_number))
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

    elif user_states.get(user_id) == 'deleted_task': # deleted task

        if user_input.isdigit():
            task_number = int(user_input)

            if task_exists(user_id, task_number):

                query = 'DELETE FROM tasks WHERE user_id = %s AND id = %s'
                cursor.execute(query, (user_id, task_number))
                db.commit()
                cursor.execute("SET @new_id = 0")
                cursor.execute("UPDATE tasks SET id = (@new_id := @new_id + 1) WHERE user_id = %s ORDER BY id", (user_id,))
                cursor.execute("ALTER TABLE tasks AUTO_INCREMENT = 1")
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

2- با استفاده از edit task شماره تسک مد نظر را وارد کنید و ادیت شده رو بنویسید

3- با استفاده از delete task شماره تسکی که میخواید رو وارد کنید تا حذف بشه

4- با استفاده از done task شماره تسکی که تموم کردید رو وارد کنید (فعلا یک عدد وارد کنید)

5- با استفاده از show tasks همه تسک هاتون رو ببینید

6- اگه اشتباهی دکمه ای رو زدید کافیه عبارت back یا بازگشت رو تایپ کنید تا برگرده
    '''
    await update.message.reply_text(txt)

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

    app.run_polling()

if __name__ == '__main__':
    main()
