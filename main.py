from decouple import config
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from telegram import KeyboardButton, ReplyKeyboardMarkup

tk = config('Token')
tasks = {}

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
    if user_id in tasks and tasks[user_id]:
        user_states[user_id] = 'edit_task'

        task_list = "\n".join(
            [f'{task_number}. {task["task"]} {"✔" if task["status"] == "done" else ""}' for task_number, task in
             tasks[user_id].items()])
        txt = '📝Please enter the editing task number'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id not in tasks:
        tasks[user_id] = {}

    user_input = update.effective_message.text.strip()
    if user_input in ['back', 'بازگشت']:
        user_states.pop(user_id)
        txt = "ok i'm back."
        await update.message.reply_text(txt)
        return

    if user_states.get(user_id) == 'adding_task':  # add task

        task_text = update.effective_message.text.strip()
        if task_text :

            task_counter = max(tasks[user_id].keys(), default=0) + 1

            task_text = task_text.replace('\u200c', '').strip()
            new_tasks = [task.strip() for task in task_text.splitlines() if task.strip()]
            for task in new_tasks:
                tasks[user_id][task_counter] = {'task': task.strip(), 'status': 'not done'}
                task_counter += 1

            user_states.pop(user_id)
            txt = '✔Your task has been saved.'
            await update.message.reply_text(txt)
        else:
            txt = '⚠ Please enter a valid task!'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'done task':  # done task
        task_number_done = update.effective_message.text.strip()
        if task_number_done.isdigit() :
            task_number_done = int(task_number_done)
            if task_number_done in tasks[user_id] :
                tasks[user_id][task_number_done]['status'] = 'done'
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
        task_number_edit = update.effective_message.text.strip()
        if task_number_edit.isdigit():
            task_number_edit = int(task_number_edit)
            if task_number_edit in tasks[user_id] :
                user_states[user_id] = 'editing_task'
                user_states[f'editing_task_{user_id}'] = task_number_edit
                txt = '✏️ Now, please enter the new text for the task.'
                await update.message.reply_text(txt)
            else:
                txt = '✖️Invalid task number.'
                await update.message.reply_text(txt)
        else:
            txt = '✖️Please enter an English number.'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'editing_task': # editing task
        new_task = update.effective_message.text.strip()
        task_number_edit = user_states[f'editing_task_{user_id}']
        if new_task and task_number_edit :
            if task_number_edit in tasks[user_id]:
                tasks[user_id][task_number_edit]['task'] = new_task
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
        task_number_deleted = update.effective_message.text.strip()

        if task_number_deleted.isdigit():
            task_number_deleted = int(task_number_deleted)
            if task_number_deleted in tasks[user_id]:
                del tasks[user_id][task_number_deleted]
                new_tasks = {i + 1: task for i, task in enumerate(tasks[user_id].values())}
                tasks[user_id] = new_tasks

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

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in tasks and tasks[user_id]:

        task_list = "\n".join([f'{task_number}.{task["task"].strip()}{"✔" if task["status"] == "done" else ""}' for task_number, task in tasks[user_id].items()])

        txt = '📋your tasks:'
        await update.message.reply_text(f'{txt} \n\n {task_list}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if user_id in tasks and tasks[user_id]:
        user_states[user_id] = 'done task'
        task_list = "\n".join(
            [f'{task_number}. {task["task"]} {"✔" if task["status"] == "done" else ""}' for task_number, task in
             tasks[user_id].items()])
        txt = '📝Enter the completed task number.'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if user_id in tasks and tasks[user_id]:
        user_states[user_id] = 'deleted_task'
        task_list = "\n".join(
            [f'{task_number}. {task["task"]} {"✔" if task["status"] == "done" else ""}' for task_number, task in
             tasks[user_id].items()])
        txt = '🗑Enter the task number you want to delete.'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
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
