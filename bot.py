#-*- coding: utf-8 -*-

import requests
import telebot
from telebot import types
from bs4 import BeautifulSoup
import os
import pickle
from threading import Thread
import schedule
from openpyxl import Workbook
import time
import json
import random
from telebot import apihelper

NoneType = type(None)

token = "5308846060:AAE4ishCZ3H0Z0K8DgJ9ZIRKGgCGIZnDVBs"

token_for_ozon = "5326675413:AAEsPlhta4gDx7QyNtXN_eCvjiGDcqaK4eY"

bot = telebot.TeleBot(token=token_for_ozon)
#apihelper.proxy = {'https':'http://Yt3At8:TaJvyF9GaC4N@ee.mobileproxy.space:64315'}

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

    def clear_products_from_user(self, user):
        if user in self.db:
            self.db[user] = {}
        self.save()

    def writeUsername(self, user):
        if user not in self.db:
            self.db[user] = {}

    def writeProduct(self, user, product):
        if 'products' not in self.db[user]:
            self.db[user]['prodcuts'] = {}
        if product not in self.db[user]['products']:
            self.db[user]['products'][product] = {}

    def writeName(self, user, product, product_name):
        self.db[user]['products'][product]['name'] = product_name

    def writeDay(self, user, product, price, quantity):
        if 'days' not in self.db[user]['products'][product]:
            self.db[user]['products'][product]['days'] = []
        if self.db[user]['products'][product]['days'] == []:
            self.db[user]['products'][product]['days'].append({
                'prices': [],
                'quantity': []
                })
        self.db[user]['products'][product]['days'][-1]['prices'] += [price]
        self.db[user]['products'][product]['days'][-1]['quantity'] += [quantity]

    def set_new_day(self, user, product):
        self.db[user]['products'][product]['days'].append({
                'prices': [],
                'quantity': []
                })
    
    def write(self, user, product, product_name, price, quantity):
        self.writeUsername(user)
        self.writeProduct(user, product)
        self.writeName(user, product, product_name)
        self.writeDay(user, product, price, quantity)

    def get_permission_from_user(self, user):
        if 'permission' not in self.db[user]:
            self.db[user]['permission'] = 0
            self.save()
        return self.db[user]['permission']

    def set_permission_to_user(self, user, perm):
        self.db[user]['permission'] = perm
        self.save()

    def get_username_from_user(self, user):
        if 'username' not in self.db[user]:
            self.db[user]['username'] = ''
            self.save()
        return self.db[user]['username']

    def set_username_for_user(self, user, username):
        self.db[user]['username'] = username
        self.save()

    def get_products_amount(self, user):
        if 'products' not in self.db[user]:
            self.db[user]['products'] = {}
            self.save()
        return len(self.db[user]['products'].keys())

    def get_days(self, user, product):
        return self.db[user]['products'][product]['days']

    def getDB(self):
        return self.db

    def get_users(self):
        return self.db.keys()

    def get_products(self, user):
        try:
            return self.db[user]['products']
        except Exception as e:
            return {}

    def get_product_name(self, user, product):
        if 'name' not in self.db[user]['products'][product]:
            return ''
        return self.db[user]['products'][product]['name']

    def get_last_day(self, user, product):
        ld = len(self.db[user]['products'][product]['days'])
        if ld < 2:
            return 0
        return self.db[user]['products'][product]['days'][-2]

    def add_product(self, user, product):
        self.writeUsername(user)
        self.writeProduct(user, product)
        if 'days' not in self.db[user]['products'][product]:
            self.db[user]['products'][product]['days'] = []

    def delete(self, user, product):
        if product in self.db[user]['products']:
            self.db[user]['products'].pop(product)
        
    def save(self):
        with open('database.db', 'wb') as f:
            pickle.dump(self.db, f)

    def exist(self, user, product):
        if user in self.db.keys():
            try:
                if str(product) in self.db[user]['products']:
                    return True
                return False
            except Exception as e:
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
    keyboard.row(types.InlineKeyboardButton('Добавить товар'))
    keyboard.row(types.InlineKeyboardButton('Удалить товар'))
    keyboard.row(types.InlineKeyboardButton('Продажи конкурентов за вчера'))
    keyboard.row(types.InlineKeyboardButton('Подробный отчет по всем товарам'))

    database.writeUsername(msg.chat.id)

    #print(database.getDB())

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
        keyboard.add(types.InlineKeyboardButton('Отчистить товары пользователей', callback_data='command_clear'))
        bot.send_message(msg.chat.id,'Что делаем?', reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id,'Неверный пароль')

@bot.message_handler(commands=['senddata'])
def send_database(msg):
    bot.send_message(msg.chat.id, 'Пароль?')
    bot.register_next_step_handler(msg, send_database_two)

def send_database_two(msg):
    password = msg.text
    if password == 'super':
        
        with open('database.db', 'rb') as f:
            bot.send_document(msg.chat.id, f)

@bot.message_handler(commands=['sendall'])
def send_message_to(msg):
    bot.send_message(msg.chat.id, 'Пароль?')
    bot.register_next_step_handler(msg, send_message_to_get)

def send_message_to_get(msg):
    if msg.text == 'maxbel':
        bot.send_message(msg.chat.id, 'Верный пароль')
        bot.send_message(msg.chat.id, 'Введите текст для отправки:')
        bot.register_next_step_handler(msg, send_message_to_all)

def send_message_to_all(msg):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton('Добавить товар'))
    keyboard.row(types.InlineKeyboardButton('Удалить товар'))
    keyboard.row(types.InlineKeyboardButton('Продажи конкурентов за вчера'))
    keyboard.row(types.InlineKeyboardButton('Подробный отчет по всем товарам'))
    text = msg.text
    users = database.get_users()
    for user in users:
        bot.send_message(user, text, reply_markup=keyboard)
        

@bot.message_handler(content_types=['text'])
def get_commands(msg):
    command = msg.text
    if not database.get_username_from_user(msg.chat.id):
        database.set_username_for_user(msg.chat.id, msg.from_user.username)
    if command == 'Продажи конкурентов за вчера':
        text = ''.join('Мы проверяем продажи конкурентов в режиме онлайн и показывем реальные продажи\n'+
                'Начинаем собирать данные о продажах с момента отслеживания товара.\n' +
                'Добавьте ID конкурентов, чьи продажи вы хотите узнать.'+
                'Мы находимся в бета-тесте и пока что можно добавить не более 10 артикулов.')
        if database.get_products_amount(msg.chat.id) == 0:
            bot.send_message(msg.chat.id, 'У вас нет товаром на отслеживании')
            return
        showYesterdayReport(msg)
    elif command == 'Добавить товар':
        img = open('res/id_example.png', 'rb')
        bot.send_message(msg.chat.id, 'Введите ID товара или его ссылку\n'+
        'ID находится на странице с товаром'
        )
        bot.send_photo(msg.chat.id, img)
        bot.register_next_step_handler(msg, add_product)
    elif command == 'Удалить товар':
        if database.get_products_amount(msg.chat.id) == 0:
            bot.send_message(msg.chat.id, 'У вас нет товаром на отслеживании')
        else:
            markup = types.InlineKeyboardMarkup()
            for id in database.get_products(msg.chat.id):
                if id in ['permission', 'phone']:
                    continue
                if not database.get_product_name(msg.chat.id, id):
                    text = 'ID {}'.format(id)
                else:
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
    for link in links:
        if not database.get_permission_from_user(msg.chat.id):
            if database.get_products_amount(msg.chat.id) > 9:
                bot.send_message(msg.chat.id, 'На отслеживание можно поставить не более 10 товаров.')
                return

        user = msg.chat.id

        if database.exist(user, link):
            bot.send_message(msg.chat.id, 'Товар {} уже отслеживается.'.format(link))
        else:
            product_id = get_id(link)
            if product_id == '':
                continue
            if product_id[0] not in '0123456789':
                continue
            database.add_product(user, product_id)
            database.save()
            bot.send_message(msg.chat.id, 'Товар {} поставлен на отслеживание.'.format(link))

def get_id(url):
    if url.startswith('https://www.ozon'):
        result = []
        s = ''
        for i in url:
            if i in '0123456789':
                s += i
            else:
                result.append(s)
                s = ''
        return max(result, key=len)
    else:
        return url

def get_values(data, with_proxy):
    try:
        proxy = {'https':'http://Yt3At8:TaJvyF9GaC4N@ee.mobileproxy.space:64315'}

        headers = {'User-Agent' : 'Mozilla/5.0 (Linux; Android 4.4.2; XMP-6250 Build/HAWK) AppleWebKit/537.36 (KHTML, like Gecko)'}
        
        if with_proxy:
            print('with_proxy', with_proxy)
            s = requests.Session()
            r = s.post(api_cart_url, json=data, proxies=proxy)
            print('r_with', r.status_code)
            html = s.get('https://www.ozon.ru/cart', proxies=proxy)
            print('get_values', html.status_code)
        else:
            s = requests.Session()
            r = s.post(api_cart_url, json=data)
            print('r_without', r.status_code)
            html = s.get('https://www.ozon.ru/cart')
            print('without proxy', with_proxy)
            print('get_values', html.status_code)
        
        time.sleep(5)
        soup = BeautifulSoup(html.text, 'html.parser')
        element = soup.find(id='state-split-1436758-default-1')['data-state']

        print('get element work')
        items = json.loads(element)
        products = {}

        for item in items['items']:
            product_id = item['products'][0]['id']
            product_name = item['products'][0]['titleColumn'][0]['text']['text']
            if len(product_name) > 30:
                product_name = product_name[:29]
            price_r = item['products'][0]['priceColumn'][0]['text']['text']
            price = ''.join(i for i in price_r if i in '0123456789')
            price = int(price)
            quantity = item['quantity']['maxQuantity']
            products[product_id] = {
                    'product_name' : product_name,
                    'price' : price,
                    'quantity' : quantity
                    }
        return products
        
    except Exception as e:
        print('error', e)
        return 0

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
            if not database.get_username_from_user(user):
                username = user
            else:
                username = database.get_username_from_user(user)
            if database.get_permission_from_user(user):
                text = '{} - {}'.format(username, 'Нет ограничений')
            else:
                text = '{} - {}'.format(username, 'Ограничение в 10 товаров')
            keyboard.add(types.InlineKeyboardButton(text, callback_data='user_{}'.format(user)))
        bot.send_message(call.message.chat.id, 'Списко пользователей', reply_markup=keyboard)

    if _ == 'command' and id == 'clear':
        bot.send_message(call.message.chat.id, 'Уверен что хочешь отчистить?\nДа/Нет')
        bot.register_next_step_handler(call.message, clear_database)

def clear_database(msg):
    if msg.text == 'Да':
        users = database.get_users()
        for user in users:
            database.clear_products_from_user(user)
        bot.send_message(msg.chat.id, 'Готово!')
        

def showYesterdayReport(msg):
    if msg == NoneType:
        chat_ids = database.getDB().keys()
    else:
        chat_ids = [msg.chat.id]

    workbook = Workbook()
    sheet = workbook.active
    fields = ['Товар', 'ID Товара', 'Ссылка на товар', 
        'Продажи вчера(шт.)', 'Выручка вчера(руб.)', 'Пополнение остатков вчера(шт.)'
    ]
    present_data = []
    present_data.append(fields)
    
    for chat in chat_ids:
        if database.get_permission_from_user(chat):
            id_list = database.get_products(chat)
        else:
            if database.get_products_amount(chat) > 9:
                id_list = list(database.get_products(chat))[:10]
            else:
                id_list = database.get_products(chat)
        if len(id_list) == 0:
            bot.send_message(chat, 'У вас нет товаров на отслеживании')
            return
        else:
            bot.send_message(chat, 'Отчет за вчерашний день:')
        for id in id_list:
            day = database.get_last_day(chat, id)
            name = database.get_product_name(chat, id)
            if day == 0:
                continue
            if len(day['prices']) < 2:
                continue
            price = sum(day['prices']) / len(day['prices'])
            total_quantity = 0
            recived_quantity = 0
            for i in range(1, len(day['quantity'])):
                quantities = day['quantity']
                size = quantities[i-1] - quantities[i]
                if  size > 0:
                    total_quantity += size
                else:
                    recived_quantity += size

            product_id = id
            product_link = 'https://www.ozon.ru/product/{}'.format(product_id)

            recived_quantity = abs(recived_quantity)
            present_data.append([name, product_id, product_link, total_quantity, total_quantity * price, recived_quantity])
        
        count = 1
        for pd in present_data:
            sheet['A' + str(count)] = pd[0]
            sheet['B' + str(count)] = pd[1]
            sheet['C' + str(count)] = pd[2]
            sheet['D' + str(count)] = pd[3]
            sheet['E' + str(count)] = pd[4]            
            sheet['F' + str(count)] = pd[5]
            count += 1  
        filename = 'Vchera-' + str(chat) + '.xlsx'
        workbook.save(filename=filename)
        with open(filename, 'rb') as f:
            bot.send_document(chat, f)
        os.remove(filename)
        
def get_report(msg):
    workbook = Workbook()
    sheet = workbook.active
    fields = ['Код товара',
        'Ссылка на товар', 'Наименование', 'Продажи(шт)', 'Период отслеживания(в днях)', 'Средняя цена'
    ]
    present_data = []
    present_data.append(fields)

    chat = msg.chat.id

    if database.get_permission_from_user(chat):
            id_list = database.get_products(chat)
    else:
        if database.get_products_amount(chat) > 9:
            id_list = list(database.get_products(chat))[:10]
        else:
            id_list = database.get_products(chat)
    
    for id in id_list:
        name = database.get_product_name(msg.chat.id, id)
        count_days = 0
        average_price = 0
        total_quantity = 0
        recived_quantity = 0
        
        for day in database.get_days(msg.chat.id, id):
            if len(day['prices']) < 2:
                continue
            average_price += sum(day['prices']) / len(day['prices'])
            for i in range(1, len(day['quantity'])):
                quantities = day['quantity']
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
    
    users = database.get_users()
    if t == '00:00':
        for user in users:
            products = database.get_products(user)
            for product in products:
                database.set_new_day(user, product)
                database.save()
                
    print('get second')

    list_of_products = []
    for user in users:
        list_of_products += database.get_products(user)

    list_of_products = list(set(list_of_products))

    data = []
    count = 0
    d = []
    for product in list_of_products:
        d.append({'id': int(product), 'quantity': 1})
        count += 1
        if count % 20 == 0:
            data.append(d)
            d = []
        if count == len(list_of_products):
            data.append(d)

    products_length = len(list_of_products)
    
    count = 0
    check = []
    with_proxy = True

    while True:
        for dt in data:
            if dt in check:
                continue
            products = get_values(dt, with_proxy)
            if not products:
                print('products', products)
                print('check', check)
                print('none product')
                print('sleeping 120s')
                with_proxy = not with_proxy
                time.sleep(120)
                break
            else:
                check += dt
                count += len(dt)
                #print('work check', check)
                print('work count', count)
            for user in users:
                for product in products:
                    if database.exist(user, product):
                        product_name = products[product]['product_name']
                        price = products[product]['price']
                        quantity = products[product]['quantity']
                        database.write(user, product, product_name, price, quantity)
                        database.save()
            time.sleep(random.randint(2,6))
        if count >= products_length:
            print('break while')
            break



def scheduler():
    schedule.every().day.at('23:45').do(get_second_quantity, '23:45')
    schedule.every().day.at('09:37').do(get_second_quantity, '00:00')
    schedule.every().day.at('09:33').do(get_second_quantity, '06:00')
    schedule.every().day.at('11:30').do(get_second_quantity, '12:00')
    schedule.every().day.at('18:00').do(get_second_quantity, '18:00')
    schedule.every().day.at('12:15').do(showYesterdayReport, NoneType)
    while True:
        schedule.run_pending()

if __name__ == '__main__':
    t = Thread(target=scheduler)
    t.start()

    bot.infinity_polling()
