import subprocess
import os
import uuid

from subprocess import check_output
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Token for bot 
token = "BASHTOKENFORTELEGRAM"
allowed_user = "ALLOWEDUSER"

bot = Bot(token=token)
updater = Updater(token=token)
running_jobs = {}


def screen_running(name):
	var = check_output(["screen -ls; true"],shell=True)
	if "."+name+"\t(" in var:
		return True
	return False


def navigate_command(bot, update):
	if (update.message.from_user.username != allowed_user):
		bot.send_message(chat_id=update.message.chat_id, text="Sorry, but you can't control this server!")
		return
	req_path = update.message.text[4:]
	os.chdir(os.path.abspath(req_path))
	p = subprocess.Popen(["ls"], shell=True, stdout=subprocess.PIPE)
	output, error = p.communicate()
	bot.send_message(chat_id=update.message.chat_id, text=output)


def quick_command(bot, update):
	if (update.message.from_user.username != allowed_user):
		bot.send_message(chat_id=update.message.chat_id, text="Sorry, but you can't control this server!")
		return
	command = update.message.text[6:]
	p = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
	output, error = p.communicate()
	if error:
		bot.send_message(chat_id=update.message.chat_id, text="Command threw an error!")
	else:
		bot.send_message(chat_id=update.message.chat_id, text=output)


def long_command(bot, update, job_queue):
	if (update.message.from_user.username != allowed_user):
		bot.send_message(chat_id=update.message.chat_id, text="Sorry, but you can't control this server!")
		return
	command = update.message.text[6:].rstrip().split(" ")
	screen_name, command = command[0], " ".join(command[1:])
	unique_filename = str(uuid.uuid4())
	wrapper = "screen -dmS %s sh -c '%s >> %s' " % (screen_name, command, unique_filename)
	p = subprocess.Popen([wrapper], shell=True, stdout=subprocess.PIPE)
	output, error = p.communicate()
	bot.send_message(chat_id=update.message.chat_id, text="Job started!")
	context_obj = {
		'userid': update.message.chat_id,
		'screename': screen_name,
		'filename': unique_filename
	}
	job = job_queue.run_repeating(callback_screencheck, context=context_obj, interval=5, first=0)
	running_jobs[screename] = job


def callback_screencheck(bot, job):
	if not screen_running(job.context.screename):
		bot.send_message(chat_id=job.context.userid, text="Process completed! Here's the log:")
		bot.send_document(chat_id=job.context.userid, document=open(job.context.filename, 'rb'))
		running_jobs[job.context.screename].schedule_removal()


if __name__ == "__main__":
	# Map handlers
	navigate_handler = CommandHandler('cd', navigate_command)
	quick_handler = CommandHandler('quick', quick_command)
	long_handler = CommandHandler('long', long_command, pass_job_queue=True)
	# unknown_handler = MessageHandler(Filters.command, unknown)
	# Add handlers to dispatcher
	updater.dispatcher.add_handler(navigate_handler)
	updater.dispatcher.add_handler(quick_handler)
	updater.dispatcher.add_handler(long_handler)
	# Start polling Telegram
	updater.start_polling()
	updater.idle()
