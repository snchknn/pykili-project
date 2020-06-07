import sys
import subprocess
import time
import numpy
import re
import os
from os import path
import gunicorn
import requests
#from flask import Flask, request

subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'praat-parselmouth'])
import parselmouth
from parselmouth.praat import call

subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytelegrambotapi'])
import telebot
from telebot import types, apihelper

apihelper.proxy = {'https':'socks5://220303327:u7WVqr6c@ss-01.s5.ynvv.cc:999'}

ik_dict = {
	'ик-1': (20,30,32,37,37,40,40,38,41,50,60,63,71,80,85,86,88,86,78,65,58,51,45,40,36,32,23,16,8,-1,-7,-15,-22,-27,-32,-38,-44,-49,-51,-52,-55,-54,-52,-49,-45,-47,-51,-54,-59,-62,-64,-66,-67,-67,-68,-69,-70,-71,-76,-79,-80,-81,-82,-82,-83),
	'ик-2': (-112,-111,-109,-106,-103,-101,-98,-95,-94,-90,-89,-89,-85,-81,-76,-71,-65,-59,-52,-44,-40,-28,-20,-10,-5,1,10,15,20,27,34,44,51,61,70,77,83,90,89,79,55,43,25,19,-10,-26,-47,-51,-53,-51,-42,-24,-11,-2,1,4,-13,-29,-49,-57,-61,-63,-67,-72,-74),
	'ик-3': (-82,-80,-78,-76,-74,-72,-70,-68,-66,-64,-62,-60,-58,-58,-57,-56,-55,-55,-55,-51,-49,-43,-39,-35,-20,3,40,70,88,106,116,123,127,123,116,106,88,70,40,3,-20,-35,-39,-43,-49,-51,-55,-55,-55,-56,-57,-58,-58,-60,-62,-64,-66,-68,-70,-72,74,-76,-78,-80,-82),
	'ик-4': (15,13,12,11,10,9,8,4,-2,-8,-17,-23,-29,-32,-36,-38,-44,-51,-55,-57,-62,-70,-72,-78,-83,-86,-89,-92,-96,-104,-107,-105,-102,-94,-82,-59,-39,-20,0,18,34,45,55,66,71,76,81,84,87,93,94,95,95,95,94,94,91,84,82,78,69,60,50,42,36),
	'ик-5': (-115,-113,-112,-112,-108,-100,-87,-59,-15,15,48,95,110,115,117,117,118,118,118,115,114,114,114,110,95,48,15,-15,-59,-87,-101,-108,-110,-105,-100,-95,-90,-80,-74,-80,-90,-95,-100,-105,-106,-107,-107,-107,-108,-108,-108,-108,-108,-108,-108,-108,-108,-109,-109,-110,-110,-110,-110,-110,-110),
	'ик-6': (-86,-80,-79,-78,-76,-74,-72,-70,-68,-66,-66,-66,-64,-64,-66,-68,-68,-70,-73,-76,-77,-78,-81,-84,-76,-61,-49,-19,15,42,72,92,98,106,110,112,112,112,112,110,110,104,104,101,100,97,95,93,91,89,86,84,80,75,70,60,60,59,58,57,56,50,49,47,47)
}

def vocalize(text, gender, username):
	if gender and text:
		if gender == 'мужской':
			speaker = 'ermil'
		else:
			speaker = 'oksana'
		url = 'https://tts.voicetech.yandex.net/tts'
		params = {
			'text': text,
			'format': 'wav',
			'quality': 'hi',
			'speaker': speaker
		}
		request = requests.get(url, params = params)
		with open(f'/home/a/progs/myapp/{username}/foo.wav', 'wb') as file:
			file.write(request.content)
	else:
		pass

def modify(ik, density, username):
	if os.path.exists(f'/home/a/progs/myapp/{username}/foo.wav') and ik and density:
		sound = parselmouth.Sound(f'/home/a/progs/myapp/{username}/foo.wav')
		manipulation = call(sound, 'To Manipulation', 0.01, 75, 600)
		old_pitch_tier = call(manipulation, 'Extract pitch tier')
		mean_frequency = call(old_pitch_tier, 'Get mean (curve)...', 0, 0)
		duration = sound.get_total_duration()
		pitch_tier = call('Create PitchTier', 'name', 0, duration)
		for i in range(0, 65, int(8/2**(int(density)-1))):
			call(pitch_tier, 'Add point', (i/64)*duration, float(mean_frequency/230*(230+ik_dict[ik][i]))) #<<<< решено! вроде должно будет работать
		call([pitch_tier, manipulation], "Replace pitch tier")
		new_sound = call(manipulation, "Get resynthesis (overlap-add)")
		new_sound.save(f'/home/a/progs/myapp/{username}/bar.wav', 'WAV')
	else:
		pass

global text
text = None

global gender
gender = None

global ik
ik = None

global density
density = None

global main_markup
main_markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = False)
main_markup.row('/text', '/gender', '/listen')
main_markup.row('/ik', '/density', '/get')
#_______________________________________________________________________________
TOKEN = '1252149825:AAFdqnqN8_z8MkNVNGAje_Jpg1-fkp-fLlM'
bot = telebot.TeleBot(TOKEN)
'''
server = Flask(__name__)
#
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APPNAME = 'really-usable-bot'
'''
@bot.message_handler(commands = ['start'])
def start_message(message):
	global main_markup
	bot.send_message(message.chat.id, 'привет! я могу эмоционально окрасить твой маленький кусок текста.\n\nнажми /text, чтобы ввести текст.', reply_markup = main_markup)
	try:
		os.mkdir(f'/home/a/progs/myapp/{message.chat.username}/')
	except FileExistsError:
		pass

#
@bot.message_handler(commands = ['text'])
def change_text(message):
	sent = bot.send_message(message.chat.id, 'ну давай, вводи.\n\nя принимаю только кириллицу, запятые, пробелы, точку в конце и не больше 40 знаков:')#, reply_markup = types.ForceReply(selective=False))
	bot.register_next_step_handler(sent, text_input)
def text_input(message):
	global main_markup
	msg = message.text
	global gender, text
	if re.search('^([А-Яа-яЁё]+\,? )*[А-Яа-яЁё]+$\.?', msg) and len(msg) <= 40:
		text = msg
		vocalize(text, gender, message.chat.username)
		bot.send_message(message.chat.id, 'хорошо. теперь нажми /gender и выбери голос для синтеза речи, если еще не нажимал.', reply_markup = main_markup)
	else:
		bot.send_message(message.chat.id, 'к сожалению, не вышло.\n\nпожалуйста, проверь текст еще раз и нажми /text.', reply_markup = main_markup)
#
@bot.message_handler(commands = ['gender'])
def change_gender(message):
	gender_markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
	gender_markup.row('мужской', 'женский')
	sent = bot.send_message(message.chat.id, 'выбери голос:', reply_markup = gender_markup)
	bot.register_next_step_handler(sent, gender_input)
def gender_input(message):
	global main_markup
	msg = message.text
	global gender, text
	if msg == 'мужской' or  msg == 'женский':
		gender = msg
		vocalize(text, gender, message.chat.username)
		bot.send_message(message.chat.id, 'хорошо. теперь нажми /listen, если еще не нажимал.', reply_markup = main_markup)
	else:
		bot.send_message(message.chat.id, 'для чего люди придумали кнопки?\n\nнажми /gender еще раз.', reply_markup = main_markup)
#
@bot.message_handler(commands = ['listen'])
def listen_choose(message):
	listen_markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
	listen_markup.row('да', 'нет')
	sent = bot.send_message(message.chat.id, 'хочешь послушать озвученный текст без обработки?', reply_markup = listen_markup)
	bot.register_next_step_handler(sent, listen_input)
def listen_input(message):
	global main_markup
	msg = message.text
	global text
	global gender
	username = message.chat.username
	vocalize(text, gender, username)
	if os.path.exists(f'/home/a/progs/myapp/{username}/foo.wav'):
		raw_audio = open(f'/home/a/progs/myapp/{username}/foo.wav', 'rb')
		if msg == 'да':
			bot.send_voice(message.chat.id, raw_audio)
			bot.send_message(message.chat.id, 'нравится? если не очень, поменяй голос, нажав на /gender.\n\nа если все устраивает, нажми /ik, чтобы выбрать интонационную конструкцию, в которой ты хочешь слышать свой микротекст.', reply_markup = main_markup)
		elif msg == 'нет':
			bot.send_message(message.chat.id, 'ну ладно, как хочешь.\n\nнажми /ik, чтобы выбрать интонационную конструкцию, в которой ты хочешь слышать свой микротекст.', reply_markup = main_markup)
		else:
			bot.send_message(message.chat.id, 'для чего люди придумали кнопки?\n\nнажми /listen еще раз. или не нажимай, раз не хочешь.', reply_markup = main_markup)
	else:
		bot.send_message(message.chat.id, 'что-то пошло не так. скорее всего, ты не ввел значения в /text и/или /gender.\n\nнажми куда-нибудь туда.', reply_markup = main_markup)
#
@bot.message_handler(commands = ['ik'])
def change_ik(message):
	ik_markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
	ik_markup.row('ик-1', 'ик-2', 'ик-3')
	ik_markup.row('ик-4', 'ик-5', 'ик-6')
	sent = bot.send_message(message.chat.id, 'выбери интонационную конструкцию:', reply_markup = ik_markup)
	bot.register_next_step_handler(sent, ik_input)
def ik_input(message):
	global main_markup
	msg = message.text
	global ik
	ik_tuple = ('1', '2', '3', '4', '5', '6')
	if msg.startswith('ик-') and msg.endswith(ik_tuple):
		ik = msg
		bot.send_message(message.chat.id, 'круто. теперь нажми /density.', reply_markup = main_markup)
	elif msg.startswith('ик-') and msg.endswith('7'):
		bot.send_message(message.chat.id, 'увы... нам такого не говорили. или мы забыли. не важно.\n\nнажми /ik, чтобы выбрать из имеющихся.', reply_markup = main_markup)
	else:
		bot.send_message(message.chat.id, 'для чего люди придумали кнопки?\n\nнажми /ik еще раз.', reply_markup = main_markup)
#
@bot.message_handler(commands = ['density'])
def change_density(message):
	density_markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
	density_markup.row('1', '2')
	density_markup.row('3', '4')
	sent = bot.send_message(message.chat.id, 'выбери точность от 1 до 4. чем больше точность, тем плавнее интонационная кривая.\n\nхз зачем это надо, но пусть будет. это все будет развиваться в будущих версиях бота, так что stay tuned', reply_markup = density_markup)
	bot.register_next_step_handler(sent, density_input)
def density_input(message):
	global main_markup
	msg = message.text
	global density
	density_tuple = ('1', '2', '3', '4')
	if msg in density_tuple:
		density = msg
		bot.send_message(message.chat.id, 'круто. осталось только нажать /get...', reply_markup = main_markup)
	elif type(int(msg)) == int or type(float(msg)) == float:
		bot.send_message(message.chat.id, 'это не имеет смысла, поверь.\n\nнажми /density, чтобы выбрать из имеющихся.', reply_markup = main_markup)
	else:
		bot.send_message(message.chat.id, 'для чего люди придумали кнопки?\n\nнажми /density еще раз.', reply_markup = main_markup)
#
@bot.message_handler(commands = ['get'])
def get_choose(message):
	get_markup = types.ReplyKeyboardMarkup(resize_keyboard = True, one_time_keyboard = True)
	get_markup.row('да, капитан')
	get_markup.row('нет, капитан')
	sent = bot.send_message(message.chat.id, 'ты готов?', reply_markup = get_markup)
	bot.register_next_step_handler(sent, get_input)
def get_input(message):
	global main_markup
	msg = message.text
	global ik
	global density
	username = message.chat.username
	modify(ik, density, username)
	if os.path.exists(f'/home/a/progs/myapp/{username}/bar.wav'):
		final_audio = open(f'/home/a/progs/myapp/{username}/bar.wav', 'rb')
		if msg == 'да, капитан':
			bot.send_voice(message.chat.id, final_audio)
			bot.send_message(message.chat.id, 'молодец. теперь бегай по командам и меняй параметры сколько душе угодно.', reply_markup = main_markup)
		elif msg == 'нет, капитан':
			bot.send_message(message.chat.id, 'ну ладно, как хочешь.\n\nможешь еще раз проверить все параметры и потом запускать.', reply_markup = main_markup)
		else:
			bot.send_message(message.chat.id, 'для чего люди придумали кнопки?\n\nнажми /get еще раз. или не нажимай, раз не готов.', reply_markup = main_markup)
	else:
		bot.send_message(message.chat.id, 'что-то пошло не так. скорее всего, ты ввел не все параметры.\n\nпонажимай на /text, /gender, /ik и /density.', reply_markup = main_markup)
'''
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
	bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
	return "!", 200


@server.route('/')
def webhook():
	bot.remove_webhook()
	bot.set_webhook(url=f'https://{HEROKU_APPNAME}.herokuapp.com/' + TOKEN)
	return "!", 200

server.run(host="0.0.0.0", port=PORT)
'''

while True:
	try:
		bot.infinity_polling(True)
	except Exception:
		sys.exit(0)


'''
gender_list = ['мужской', 'женский']
density_list = ['1', '2', '3', '4']

@bot.message_handler(commands = ['gender'])                                               ______________
def change_gender(message):
    gender_markup = types.InlineKeyboardMarkup(row_width = 1)
    for gender in gender_list:
        gender_markup.add(types.InlineKeyboardButton(text = gender, callback_data = gender))
    bot.send_message(message.chat.id, 'выбери голос:', reply_markup = gender_markup)

@bot.message_handler(commands = ['density'])                                               <<< запасное
def change_density(message):
    density_markup = types.InlineKeyboardMarkup(row_width = 1)
    for density in density_list:
        density_markup.add(types.InlineKeyboardButton(text = density, callback_data = density))
    bot.send_message(message.chat.id, 'выбери точность:', reply_markup = density_markup)

@bot.callback_query_handler(func = lambda call: True)                                     ______________
def callback_inline(call):
    if call.message == 'выбери голос:':
        global gender
        global text
        gender = call.data
        vocalize(text, gender)
    elif call.message == 'выбери точность:':
        global density
        density = call.data
'''

"""
def main():
    tts = get_tts()
    speaker = get_speaker()
    vocalize(tts, speaker)
    listen('foo.wav')
    changebool = change()
    if changebool == True:
        speaker = get_speaker()
        vocalize(tts, speaker)
        listen('foo.wav')
    ik_number = get_ik()
    density = get_density()
    modify(ik_number, density)
    listen('bar.wav')

if __name__ == '__main__':
    main()
"""
