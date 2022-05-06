#-*- coding: utf-8 -*-

import requests
import re
import telebot
from telebot import types
from bs4 import BeautifulSoup
import os
import pickle
from threading import Thread
import schedule
from openpyxl import Workbook

NoneType = type(None)

token = "5308846060:AAE4ishCZ3H0Z0K8DgJ9ZIRKGgCGIZnDVBs"

token_for_ozon = "5326675413:AAEsPlhta4gDx7QyNtXN_eCvjiGDcqaK4eY"

bot = telebot.TeleBot(token=token_for_ozon)

api_cart_url = 'https://www.ozon.ru/api/composer-api.bx/_action/addToCart'

class DataBase:
    def __init__(self):
        pass

    def init(self):
        self.load()

    def load(self):
        if not os.path.exists('database.db'):
            file = open('database.db', 'w+')
            file.close()
        
        if os.path.getsize('database.db') > 0:
            with open('database.db', 'rb') as f:
                self.db = pickle.load(f)
        else:
            self.db = {}

    def writeUsername(self, chat_id):
        if chat_id not in self.db:
            self.db[chat_id] = {}

    def writeID(self, chat_id, id):
        if id not in self.db[chat_id]:
            self.db[chat_id][id] = {}

    def writeName(self, chat_id, id, name):
        self.db[chat_id][id]['name'] = name

    def writeDay(self, chat_id, id, price, quantity):
        if 'days' not in self.db[chat_id][id]:
            self.db[chat_id][id]['days'] = []
        
        days_length = len(self.db[chat_id][id]['days'])

        if days_length == 0:
            self.db[chat_id][id]['days'].append([price, quantity])
        else:
            self.db[chat_id][id]['days'][days_length - 1].append(quantity)

    def get_products_amount(self, chat_id):
        return len(self.db[chat_id].keys())

    def get_days(self, chat_id, id):
        return self.db[chat_id][id]['days']

    def getDB(self):
        return self.db

    def get_users(self):
        return self.db.keys()

    def get_ids(self, chat_id):
        return self.db[chat_id].keys()

    def get_product_name(self, chat_id, id):
        return self.db[chat_id][id]['name']

    def get_last_day(self, chat, id):
        ld = len(self.db[chat][id]['days'])
        if ld > 1:
            ld = ld-2
        else:
            ld = ld - 1
        return self.db[chat][id]['days'][ld]

    def set_new_day(self, chat_id, id, price, quantity):
        self.db[chat_id][id]['days'].append([price, quantity])
    
    def write(self, chat_id, id, name, price, quantity):
        self.writeUsername(chat_id)
        self.writeID(chat_id, id)
        self.writeName(chat_id, id, name)
        self.writeDay(chat_id, id, price, quantity)

    def delete(self, chat_id, id):
        if id in self.db[chat_id]:
            self.db[chat_id].pop(id)
        
    def save(self):
        with open('database.db', 'wb') as f:
            pickle.dump(self.db, f)

    def exist(self, chat_id, id):
        if chat_id in self.db.keys():
            if id in self.db[chat_id].keys():
                return True
            return False

database = DataBase()
database.init()

def get_quantity(string):
    if len(string) > 10:
        string = string[-15:]
        
    return ''.join([i for i in string if i in '1234567890'])

@bot.message_handler(commands=['start'])
def start_bot(msg):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton('Продажи конкурентов за вчера'))
    keyboard.row(types.InlineKeyboardButton('Добавить товар'))
    keyboard.row(types.InlineKeyboardButton('Удалить товар'))
    keyboard.row(types.InlineKeyboardButton('Подробный отчет по всем товарам'))

    database.writeUsername(msg.chat.id)

    bot.send_message(msg.chat.id,
    'Привет!\n\n'+
    'Я помогаю селлерам, которые продают на OZON, вместе мы сможем увеличить твои продажи и обойти конкурентов.\n'+
    'Что я умею уже сейчас:\n'+
    '1) Отслеживать РЕАЛЬНЫЕ продажи конкурентов\n\n'+
    'Функции в разработке:\n'+
    '1) Отслеживание цен конкурентов',
    reply_markup=keyboard
    )

@bot.message_handler(commands=['снять'])
def remove_restrictions(msg):
    bot.send_message(msg.chat.id, 'Введите код доступа:')
    bot.register_next_step_handler(msg, restrictions_next_step)

def restrictions_next_step(msg):
    password = 'максим рулит'
    if password == msg.text:
        bot.send_message(msg.chat.id, 'Верный пароль')
        users = database.get_users()
        keyboard = types.InlineKeyboardMarkup()
        for user in users:
            keyboard.add(types.InlineKeyboardButton(user, callback_data='user_{}'.format(user)))
        bot.send_message(msg.chat.id,'Список пользователей', reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id,'Неверный пароль')

#@bot.callback_query_handler(func=lambda call: True)
#def change_restriction(call):
#    _, user = call.data.split('_')
#    bot.answer_callback_query(call.id, user)

@bot.message_handler(content_types=['text'])
def get_commands(msg):
    command = msg.text
    if command == 'Продажи конкурентов за вчера':
        text = ''.join('Мы проверяем продажи конкурентов в режиме онлайн и показывем реальные продажи\n'+
                'Начинаем собирать данные о продажах с момента отслеживания товара.\n' +
                'Добавьте ID конкурентов, чьи продажи вы хотите узнать.'+
                'Мы находимся в бета-тесте и пока что можно добавить не более 10 артикулов.')
        showYesterdayReport(msg)
    elif command == 'Добавить товар':
        img = open('res/id_example.png', 'rb')
        bot.send_message(msg.chat.id, 'Введите ID товара или его ссылку\n'+
        'ID находится на странице с товаром'
        )
        bot.send_photo(msg.chat.id, img)
        bot.register_next_step_handler(msg, add_product)
    elif command == 'Удалить товар':
        if len(database.getDB()[msg.chat.id].keys()) == 0:
            bot.send_message(msg.chat.id, 'У вас нет товаром на отслеживании')
        else:
            markup = types.InlineKeyboardMarkup()
            for id in database.get_ids(msg.chat.id):
                name = database.get_product_name(msg.chat.id, id)
                text = '{} - ID {}'.format(name, id)
                markup.add(types.InlineKeyboardButton(text, callback_data='id_' + id))
            bot.send_message(msg.chat.id, 'Выберите ID товара для удаления', reply_markup=markup)
            #bot.register_next_step_handler(msg, delete_product)
    elif command == 'Подробный отчет по всем товарам':
        get_report(msg)
    elif command == 'show':
        bot.send_message(msg.chat.id, ' '.join(str(key) for key in database.getDB().keys()))

def add_product(msg):
    links = msg.text.split('\n')
    for link in links:
        id = get_id(link)
        chat_id = msg.chat.id
        quantity, name, prices = get_values(id)

        #print(quantity, name, prices)
        
        if [quantity, name, prices] != [0,0,0]:
            if database.exist(chat_id, id):
                bot.send_message(msg.chat.id, 'Товар {} уже отслеживается.'.format(name))      
            else:
                if database.get_products_amount(msg.chat.id) > 9:
                    bot.send_message(msg.chat.id, 'На отслеживание можно поставить не более 10 товаров.')
                    return
                database.write(chat_id, id, name, int(min(prices)), int(quantity))
                database.save()
                bot.send_message(msg.chat.id, 'Товар {} поставлен на отслеживание.'.format(name))
        else: 
            bot.send_message(msg.chat.id, 'Товар не найден.')

def get_id(url):
    if url.startswith('https://www.ozon'):
        resp = requests.get(url)
        id = re.search('товара</span>: (.+?)</span>', resp.text).group(1)
        #soup = BeautifulSoup(resp.text, 'html.parser')
        #line = soup.find('span', {'class':'p9k qk'}).get_text()
        #id = ''
        #for i in line:
        #    if i in ['0','1','2','3','4','5','6','7','8','9','0']:
        #        id += i
        #return id[0:]
        return id
    else:
        return url

def get_values(id):
    try:
        data = [{ 'id' : int(id), 'quantity' : 1}]
        s = requests.Session()
        r = s.post(api_cart_url, json=data)
        html_cart = s.get('https://www.ozon.ru/cart')
        match = re.search('maxQuantity(.+?)minQuantity', html_cart.text).group(1)
        quantity = get_quantity(match)

        product_html = requests.get('https://www.ozon.ru/product/' + id)

        soup = BeautifulSoup(product_html.text, 'html.parser')
        name = soup.title.string
        if len(name) > 30:
            name = name[0:30]
            if '-' in name:
                name = name.split('--')[0]
        resp = requests.get('https://www.ozon.ru/product/{}'.format(id))
        price = re.search('InStock","price":"(.+?)","priceCurrency":"RUB"', resp.text).group(1)
        return quantity, name, price
    except Exception as e:
        print('error', e)
        return [0,0,0]

@bot.callback_query_handler(func=lambda call: True)
def delete_product(call):
    bot.answer_callback_query(call.id, 'Товар удален')
    _, id = call.data.split('_')
    chat_id = call.message.chat.id
    if database.exist(chat_id, id):
        database.delete(chat_id, id)
        database.save()

        bot.answer_callback_query(call.id, 'Товар удален')

def showYesterdayReport(msg):
    if msg == NoneType:
        chat_ids = database.getDB().keys()
    else:
        chat_ids = [msg.chat.id]
    for chat in chat_ids:
        
        id_list = database.get_ids(chat)
        if len(id_list) == 0:
            bot.send_message(chat, 'У вас нет товаров на отслеживании')
            return
        else:
            bot.send_message(chat, 'Отчет за вчерашний день:')
        for id in id_list:
            day = database.get_last_day(chat, id)
            name = database.get_product_name(chat, id)
            if len(day) < 3:
                bot.send_message(chat, 'Отчет по товару c ID {} будет доступен завтра.'.format(id))
                continue
            price = int(day[0])
            total_quantity = 0
            recived_quantity = 0
            for i in range(1, len(day[1:])):
                quantities = day[1:]
                size = quantities[i-1] - quantities[i]
                if  size > 0:
                    total_quantity += size
                else:
                    recived_quantity += size 

            recived_quantity = abs(recived_quantity)
            
            text = ''.join('Товар "{}"\n'+
                                'Продажи вчера(шт.): {}\n'+
                                'Выручка вчера(руб.): {}\n'+
                                'Пополнение остатков вчера(шт.): {}').format(name, total_quantity * price, total_quantity, recived_quantity)
            bot.send_message(chat, text)
        
def get_report(msg):
    workbook = Workbook()
    sheet = workbook.active
    fields = ['Код товара',
        'Ссылка на товар', 'Наимеование', 'Продажи(шт)', 'Период отслеживания(в днях)', 'Средняя цена'
    ]
    present_data = []
    present_data.append(fields)
    for id in database.get_ids(msg.chat.id):
        name = database.get_product_name(msg.chat.id, id)
        count_days = 0
        average_price = 0
        total_quantity = 0
        recived_quantity = 0
        
        for day in database.get_days(msg.chat.id, id)[:-1]:
            if len(day) < 3:
                continue
            average_price += int(day[0])
            for i in range(1, len(day[1:])):
                quantities = day[1:]
                size = quantities[i-1] - quantities[i]
                if  size > 0:
                    total_quantity += size
                else:
                    recived_quantity += size 
            count_days += 1
        product_url = 'https://www.ozon.ru/product/' + id
        if count_days == 0:
            present_data.append([id, product_url, name, 0, 0, 0])
        else:
            present_data.append([id, product_url, name, total_quantity, count_days, average_price/count_days])
        
    count = 1
    for pd in present_data:
        sheet['A' + str(count)] = pd[0]
        sheet['B' + str(count)] = pd[1]
        sheet['C' + str(count)] = pd[2]
        sheet['D' + str(count)] = pd[3]
        sheet['E' + str(count)] = pd[4]
        sheet['F' + str(count)] = pd[5]
        count += 1  
    filename = str(msg.chat.id) + '.xlsx'
    workbook.save(filename=filename)
    bot.send_message(msg.chat.id, 'Подробный отчет:')
    with open(filename, 'rb') as f:
        bot.send_document(msg.chat.id, f)
    os.remove(filename)

def get_second_quantity(t):
    chat_ids = database.getDB().keys()
    for chat in chat_ids:
        for id in database.get_ids(chat):
            quantity, name, prices = get_values(id)
            database.write(chat, id, name, int(min(prices)), int(quantity))
            if t == '00:00':
                database.set_new_day(chat, id, int(min(prices)), int(quantity))
    database.save()

def scheduler():
    schedule.every().day.at('00:00').do(get_second_quantity, '00:00')
    schedule.every().day.at('06:00').do(get_second_quantity, '06:00')
    schedule.every().day.at('13:00').do(get_second_quantity, '12:00')
    schedule.every().day.at('18:00').do(get_second_quantity, '18:00')
    schedule.every().day.at('12:15').do(showYesterdayReport, NoneType)
    while True:
        schedule.run_pending()

if __name__ == '__main__':
    t = Thread(target=scheduler)
    t.start()

    bot.infinity_polling()
