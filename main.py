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
        [KeyboardButton('➕add task'), KeyboardButton('📋show tasks')],
        [KeyboardButton('✔done task')],
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
    txt = '📝 Please enter your task'
    await update.message.reply_text(txt)

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_states.get(user_id) == 'adding_task':

        task_text = update.effective_message.text.strip()
        if task_text :
            if user_id not in tasks:
                tasks[user_id] = {}

            task_counter = max(tasks[user_id].keys(), default=0) + 1

            if '\n' in task_text:
                new_tasks = task_text.split('\n')
            else:
                new_tasks = [task_text]

            new_tasks = [task.strip() for task in new_tasks if task.strip()]
            for task in new_tasks:
                tasks[user_id][task_counter] = {'task': task.strip(), 'status': 'not done'}
                task_counter += 1

            user_states.pop(user_id)
            txt = '✔Your task has been saved'
            await update.message.reply_text(txt)
        else:
            txt = '⚠ Please enter a valid task!'
            await update.message.reply_text(txt)

    elif user_states.get(user_id) == 'done task':
        task_number_done = update.effective_message.text.strip()
        if task_number_done.isdigit() :
            task_number_done = int(task_number_done)
            if task_number_done in tasks[user_id] :
                tasks[user_id][task_number_done]['status'] = 'done'
                user_states.pop(user_id)
                txt = '✔Task done'
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
        txt = '📝Enter the completed task number'
        txt1 = '📋your tasks:'
        await update.message.reply_text(f'{txt1} \n\n {task_list} \n\n {txt}')
    else:
        txt = '📭 No tasks found!'
        await update.message.reply_text(txt)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = '''با استفاده از add task میتونید تسک اضافه کنید اگه چند تا تسک میخواید اضافه کنید هر کدوم رو توی یک خط بنویسید
همه تسک هاتون رو میتونید با استفاده از show tasks ببینید
وقتی تسکی رو انجام دادید done task رو بزنید و عدد اون تسکی که انجام دادید رو وارد کنید'''
    await update.message.reply_text(txt)

def main():
    app = Application.builder().token(tk).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Text('➕add task'), add_task))
    app.add_handler(MessageHandler(filters.Text('📋show tasks'), show_tasks))
    app.add_handler(MessageHandler(filters.Text('✔done task'), done_task))
    app.add_handler(MessageHandler(filters.Text('help!'),help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND , save_task))

    app.run_polling()

if __name__ == '__main__':
    main()
