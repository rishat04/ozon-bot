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
                #print(self.db)
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

    def get_permission_from_user(self, user):
        if 'permission' not in self.db[user]:
            self.db[user]['permission'] = 0
            self.save()
        return self.db[user]['permission']

    def set_permission_to_user(self, user, perm):
        self.db[user]['permission'] = perm
        self.save()

    def get_phone_from_user(self, user):
        if 'phone' not in self.db[user]:
            self.db[user]['phone'] = ''
            self.save()
        return self.db[user]['phone']

    def set_phone_for_user(self, user, phone):
        self.db[user][phone] = phone
        self.save()

    def get_products_amount(self, chat_id):
        if 'permission' in self.db[chat_id]:
            return len(self.db[chat_id].keys()) - 1
        else:
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

@bot.message_handler(commands=['dragonfly'])
def remove_restrictions(msg):
    bot.send_message(msg.chat.id, 'Введите код доступа:')
    bot.register_next_step_handler(msg, restrictions_next_step)

def restrictions_next_step(msg):
    password = 'magic'
    if password == msg.text:
        bot.send_message(msg.chat.id, 'Верный пароль')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('Статистика', callback_data='command_stat'))
        keyboard.add(types.InlineKeyboardButton('Контроль ограничений', callback_data='command_rest'))
        bot.send_message(msg.chat.id,'Что делаем?', reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id,'Неверный пароль')

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
                if id in ['permission', 'phone']:
                    continue
                name = database.get_product_name(msg.chat.id, id)
                text = '{} - ID {}'.format(name, id)
                markup.add(types.InlineKeyboardButton(text, callback_data='id_' + id))
            bot.send_message(msg.chat.id, 'Выберите ID товара для удаления', reply_markup=markup)
    elif command == 'Подробный отчет по всем товарам':
        get_report(msg)
    elif command == 'show':
        bot.send_message(msg.chat.id, ' '.join(str(key) for key in database.getDB().keys()))

def add_product(msg):
    links = msg.text.split('\n')
    #if not database.get_phone_for_user(msg.chat.id):
     #   print(msg)
      #  phone = '@{}'.format(msg.from_user.username)
       # database.set_phone_from_user(msg.chat.id, phone)
    for link in links:
        if not database.get_permission_from_user(msg.chat.id):
            if database.get_products_amount(msg.chat.id) > 9:
                bot.send_message(msg.chat.id, 'На отслеживание можно поставить не более 10 товаров.')
                return
        
        id = get_id(link)
        chat_id = msg.chat.id
        quantity, name, prices = get_values(id)

        #print(quantity, name, prices)
        
        if [quantity, name, prices] != [0,0,0]:
            if database.exist(chat_id, id):
                bot.send_message(msg.chat.id, 'Товар {} уже отслеживается.'.format(name))      
            else:
                database.write(chat_id, id, name, int(prices), int(quantity))
                database.save()
                bot.send_message(msg.chat.id, 'Товар {} поставлен на отслеживание.'.format(name))
        else: 
            bot.send_message(msg.chat.id, 'Товар не найден.')

def get_id(url):
    proxy = {
        'http': 'http://185.162.228.100:80',
        'https': 'http://91.224.62.194:8080'
    }
    r =requests.get('https://www.ozon.ru', proxies=proxy)
    print('testing', r.status_code)
    if url.startswith('https://www.ozon'):
        resp = requests.get(url)
        print('get_id', resp.status_code)
        id = re.search(',"sku":(.+?)},"location"', resp.text).group(1)
        #print(id)
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
        print(html_cart.status_code)
        match = re.search('maxQuantity(.+?)minQuantity', html_cart.text).group(1)
        quantity = get_quantity(match)

        product_html = requests.get('https://www.ozon.ru/product/' + id)
        print('product_html', product_html.status_code)

        soup = BeautifulSoup(product_html.text, 'html.parser')
        name = soup.title.string
        if len(name) > 30:
            name = name[0:30]
            if '-' in name:
                name = name.split('--')[0]
        resp = requests.get('https://www.ozon.ru/product/{}'.format(id))
        price = re.search('InStock","price":"(.+?)","priceCurrency":"RUB"', resp.text).group(1)
        #print(name, price, quantity)
        return quantity, name, price
    except Exception as e:
        print('error', e)
        return [0,0,0]

@bot.callback_query_handler(func=lambda call: True)
def delete_product(call):
    _, id = call.data.split('_')
    if _ == 'id':
        chat_id = call.message.chat.id
        if database.exist(chat_id, id):
            database.delete(chat_id, id)
            database.save()

            bot.answer_callback_query(call.id, 'Товар удален')
    if _ == 'user':
        id = int(id)
        if database.get_permission_from_user(id) == 0:
            database.set_permission_to_user(id, 1)
            bot.answer_callback_query(call.id, 'Пользователю {} убрали ограничения'.format(_))
            return
        if database.get_permission_from_user(id) == 1:
            database.set_permission_to_user(id, 0)
            bot.answer_callback_query(call.id, 'Пользователю {} поставили ограничения ограничения'.format(_))
            return
    if _ == 'command' and id == 'stat':
        users = database.get_users()
        users_count = len(users)
        products_count = 0
        for user in users:
            if user in ['permission', 'phone']:
                continue
            products_count += database.get_products_amount(user)

        bot.send_message(call.message.chat.id, 'Статистика: \n' +
                                'Количество пользователей: ' + str(users_count) + '\n' +
                                 'Товаров на отслеживании: ' + str(products_count)
                             )
    if _ == 'command' and id == 'rest':
        users = database.get_users()
        keyboard = types.InlineKeyboardMarkup()
        for user in users:
            #text = '{} - {}'.format(msg.from_user.first_name, user)
            if not database.get_phone_from_user(user):
                phone = user
            else:
                phone = database.get_phone_from_user(user)
            if database.get_permission_from_user(user):
                text = '{} - {}'.format(phone, 'Нет ограничений')
            else:
                text = '{} - {}'.format(phone, 'Ограничение в 10 товаров')
            keyboard.add(types.InlineKeyboardButton(text, callback_data='user_{}'.format(user)))
        bot.send_message(call.message.chat.id, 'Списко пользователей', reply_markup=keyboard)
        

def showYesterdayReport(msg):
    if msg == NoneType:
        chat_ids = database.getDB().keys()
    else:
        chat_ids = [msg.chat.id]
    for chat in chat_ids:
        
        if database.get_permission_from_user(chat):
            id_list = database.get_ids(chat)
        else:
            if database.get_products_amount(chat) > 10:
                id_list = list(database.get_ids(chat))[:11]
            else:
                id_list = database.get_ids(chat)
        if len(id_list) == 0:
            bot.send_message(chat, 'У вас нет товаров на отслеживании')
            return
        else:
            bot.send_message(chat, 'Отчет за вчерашний день:')
        for id in id_list:
            if id in ['permission', 'phone']:
                continue
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
                                'Пополнение остатков вчера(шт.): {}').format(name, total_quantity, total_quantity * price, recived_quantity)
            bot.send_message(chat, text)
        
def get_report(msg):
    workbook = Workbook()
    sheet = workbook.active
    fields = ['Код товара',
        'Ссылка на товар', 'Наимеование', 'Продажи(шт)', 'Период отслеживания(в днях)', 'Средняя цена'
    ]
    present_data = []
    present_data.append(fields)

    chat = msg.chat.id

    if database.get_permission_from_user(chat):
            id_list = database.get_ids(chat)
    else:
        if database.get_products_amount(chat) > 10:
            id_list = list(database.get_ids(chat))[:11]
        else:
            id_list = database.get_ids(chat)
    
    for id in id_list:
        if id in ['permission', 'phone']:
            continue
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
        if chat != 'permission':
            for id in database.get_ids(chat):
                if id in ['phone', 'permission']:
                    continue
                quantity, name, prices = get_values(id)
                database.write(chat, id, name, int(prices), int(quantity))
                if t == '00:00':
                    database.set_new_day(chat, id, int(prices), int(quantity))
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
