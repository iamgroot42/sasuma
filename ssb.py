# -*- coding: utf-8 -*-

import subprocess
import os
import uuid
import getpass


from subprocess import check_output
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Token for bot 
token = getpass.getpass("Enter API token for bot: ")
allowed_user = raw_input("Enter allowed user for bot: ")


def logger(ctype, command):
	print("[" + ctype + "] : " + command)


# Set up Bot
bot = None
updater = None
try:
	bot = Bot(token=token)
	updater = Updater(token=token)
except:
	logger("ERROR", "Invalid Token")
	exit()
running_jobs = {}
NOT_ALLOWED_MESSAGE = "Sorry, but you can't control this server 🙅🏻"
FREQUENCY=10


def screen_running(name):
	var = check_output(["screen -ls; true"],shell=True)
	if "."+name+"\t(" in var:
		return True
	return False


def unknown(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, but Sasuma didn't understand that command 👵🏻")


def unknown_text(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="Sasauma's very efficient, \
		she doesn't have time for small talk. Just give her a command, and she'll do it 👵🏻.\
		Have a look [here](https://github.com/iamgroot42/sasuma/) for a list of available commands",
		parse_mode = ParseMode.MARKDOWN)


def navigate_command(bot, update):
	if (update.message.from_user.username != allowed_user):
		bot.send_message(chat_id=update.message.chat_id, text=NOT_ALLOWED_MESSAGE)
		return
	req_path = update.message.text[4:]
	os.chdir(os.path.abspath(req_path))
	p = subprocess.Popen(["ls"], shell=True, stdout=subprocess.PIPE)
	output, error = p.communicate()
	logger("CD", req_path)
	bot.send_message(chat_id=update.message.chat_id, text=output)


def quick_command(bot, update):
	if (update.message.from_user.username != allowed_user):
		bot.send_message(chat_id=update.message.chat_id, text=NOT_ALLOWED_MESSAGE)
		return
	command = update.message.text[6:]
	# If top command, limit iterations
	if "top" in command.split(' '):
		command += " -n1" 
	p = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
	output, error = p.communicate()
	logger("QUICK", command)
	if error:
		bot.send_message(chat_id=update.message.chat_id, text="Command threw an error!")
	else:
		bot.send_message(chat_id=update.message.chat_id, text=output)


def long_command(bot, update, job_queue):
	global updater
	global running_jobs
	if (update.message.from_user.username != allowed_user):
		bot.send_message(chat_id=update.message.chat_id, text=NOT_ALLOWED_MESSAGE)
		return
	command = update.message.text[6:].rstrip().split(" ")
	screen_name, command = command[0], " ".join(command[1:])
	unique_filename = str(uuid.uuid4())
	wrapper = "screen -dmS %s sh -c '%s >> %s' " % (screen_name, command, unique_filename)
	p = subprocess.Popen([wrapper], shell=True, stdout=subprocess.PIPE)
	output, error = p.communicate()
	context_obj = {
		'userid': update.message.chat_id,
		'screename': screen_name,
		'filename': unique_filename
	}
	logger("LONG", command)
	job = job_queue.run_repeating(callback_screencheck, FREQUENCY, context=context_obj)
	running_jobs[screen_name] = job
	update.message.reply_text("Job started 👍🏻! Output will written to %s" %(unique_filename))


def callback_screencheck(bot, job):
	global running_jobs
	if not screen_running(job.context['screename']):
		if len(open(job.context['filename'], 'rb').read()) != 0:
			bot.send_message(chat_id=job.context['userid'], text="Sasuma's done with the job 👩🏻‍💻! Here's the log:")
			bot.send_document(chat_id=job.context['userid'], document=open(job.context['filename'], 'rb'))
		else:
			bot.send_message(chat_id=job.context['userid'], text="Sasuma's done with the job 👩🏻‍💻! There was no output, though")
		job = running_jobs[job.context['screename']]
		job.schedule_removal()
		del running_jobs[job.context['screename']]
		running_jobs[job.context['screename']].schedule_removal()


if __name__ == "__main__":

	# Add handlers to dispatcher
	dp = updater.dispatcher
	dp.add_handler(CommandHandler('cd', navigate_command))
	dp.add_handler(CommandHandler('quick', quick_command))
	dp.add_handler(CommandHandler('long', long_command, pass_job_queue=True))
	dp.add_handler(MessageHandler(Filters.command, unknown))
	dp.add_handler(MessageHandler(Filters.text, unknown_text))

	# Start polling Telegram
	print("Sasu maa is up!")
	updater.start_polling()
	updater.idle()
