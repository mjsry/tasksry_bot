from decouple import config
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from telegram import KeyboardButton, ReplyKeyboardMarkup

tk = config('Token')
tasks = {}
task_counter = 1
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keys = [
        [KeyboardButton('➕add task'), KeyboardButton('📋show tasks')],
        [KeyboardButton('✔done task')]
    ]
    key_markup = ReplyKeyboardMarkup(
        keyboard=keys,
        resize_keyboard=True
    )
    txt = "👋Hello! Are you ready to plan today's work?"
    await update.message.reply_text(txt, reply_markup=key_markup)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_chat.id] = 'adding_task'
    txt = '📝 Please enter your task'
    await update.message.reply_text(txt)

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global task_counter
    user_id = update.effective_chat.id
    if user_states.get(user_id) == 'adding_task':

        task_text = update.effective_message.text.strip()
        if task_text :
            new_tasks = [task.strip() for task in task_text.splitlines() if task.strip()]
            for task in new_tasks:
                tasks[task_counter] = {'task': task, 'status': 'not done'}
                task_counter += 1

            user_states.pop(user_id)
            txt = '✔Your task has been saved'
            await update.message.reply_text(txt)
        else:
            txt = '⚠ Please enter a valid task!'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'done task':
        task_number_done = update.effective_message.text.strip()
        if task_number_done.isdigit() and int(task_number_done) in tasks :
            task_number_done = int(task_number_done)
            tasks[task_number_done]['status'] = 'done'
            txt = '✔Task done'
            await update.message.reply_text(txt)
    else:
        txt = '✖️Please use the buttons'
        await update.message.reply_text(txt)


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if tasks :

        task_list = "\n".join([f'{task_number}.{task["task"]}{"✔" if task["status"] == "done" else ""}' for task_number, task in tasks.items()])
        txt = '📋your tasks:'
        await update.message.reply_text(f'{txt} \n\n {task_list}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_states[user_id] = 'done task'
    if tasks:
        task_list = "\n".join(
            [f'{task_number}. {task["task"]} {"✔" if task["status"] == "done" else ""}' for task_number, task in
             tasks.items()])
    else:
        task_list = ''

    txt = '📝Enter the completed task number'
    txt1 = '📋your tasks:'
    await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')

def main():
    app = Application.builder().token(tk).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Text('➕add task'), add_task))
    app.add_handler(MessageHandler(filters.Text('📋show tasks'), show_tasks))
    app.add_handler(MessageHandler(filters.Text('✔done task'), done_task))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND , save_task))

    app.run_polling()

if __name__ == '__main__':
    main()
