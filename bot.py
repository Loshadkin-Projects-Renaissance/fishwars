# -*- coding: utf-8 -*-
import time
import random
import threading
from telebot import types, TeleBot
import traceback
from datetime import datetime

from config import token, mongo_url
from db import Database

from constants import *

bot = TeleBot(token)

db = Database(mongo_url)

creator = 792414733

officialchat = -1001721954459
rest=False
ban=[]

@bot.message_handler(commands=['init'])
def init_handler(m):
    if m.from_user.id != creator:
        return
    db.init_seas()
    bot.send_message(m.chat.id, 'Моря подключены!')

@bot.message_handler(commands=['wipe'])
def wipe_handler(m):
    if m.from_user.id != creator:
        return
    db.wipe()
    bot.send_message(m.chat.id, 'Вайп данных!')

@bot.message_handler(commands=['score'])
def score_handler(m):
    bot.send_message(m.chat.id, db.score())
            
            
@bot.message_handler(commands=['drop'])
def drop(m):
    if m.from_user.id != creator:
        return
    db.drop()
    bot.send_message(m.chat.id, 'Сбросил очки всем морям!')

@bot.message_handler(commands=['start'])
def start(m):
    user = db.get_user(m.from_user.id)
    if user or m.chat.type != 'private':
        return

    db.create_user(m.from_user)
    sea_choice(m)

    if m.text.count(' ') == 0:
        return

    ref = m.text.split(' ')[1]
    friend = db.process_referal(ref, m.from_user)
    if not friend:
        return
    bot.send_message(friend, m.from_user.first_name+' зашел в игру по вашей рефералке! Когда он поиграет немного, вы получите +1 к максимальной силе!')

def sea_choice(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for sea in db.get_joinable_seas():
        kb.add(types.KeyboardButton(sea_ru(sea['name'])))
    bot.send_message(m.chat.id, 'Добро пожаловать! Выберите, за какое из морей вы будете сражаться.', reply_markup=kb)

        
def mainmenu(user):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('💢Атака'), types.KeyboardButton('🛡Защита'))
    kb.add(types.KeyboardButton('🍖🥬Питание'), types.KeyboardButton('ℹ️Инфо по игре'))
    kb.add(types.KeyboardButton('🐟Обо мне'))

    needed = countnextlvl(user['lastlvl'])

    text=''
    text+='🐟Имя рыбы: '+user['gamename']+'\n'
    try:
        text += f"🌊Родное море: {sea_ru(user['sea'])}\n" if user['sea'] else ''
    except:
        pass
    text += f'💪Силы: {user["strenght"]}/{user["maxstrenght"]}\n'
    text += f'🏅Уровень эволюции: {user["lvl"]}\n'
    text += f"🧬Очки эволюции: {user['evolpoints']}/{needed}\n"
    text += f"💢Атака: {user['stats']['attack']}\n"
    text += f'🛡Защита: '+str(user['stats']['def'])+'\n'
    text += f'Реген сил: 1💪 / '+str(round(20*user['strenghtregencoef'], 2))+' минут\n'
    if user['freestatspoints'] > 0:
        text += 'Доступны очки характеристик! Для использования - /upstats \n'
    bot.send_message(user['id'], 'Главное меню.\n'+text, reply_markup=kb)

        
@bot.message_handler()
def allmessages(m):
    global rest
    user = db.get_user(m.from_user.id)
    if not user:
        return
    if m.from_user.id in ban:
        return
    if m.chat.type != 'private':
        return
    if rest:
        bot.send_message(m.chat.id, 'В данный момент идёт битва морей!')
        return

    if not user['sea']:
        if m.text=='💎Кристальное':
            db.choose_sea(user, 'crystal')
            bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию 💎Кристального моря!')
            mainmenu(user)
        elif m.text=='⚫️Чёрное':
            db.choose_sea(user, 'black')
            bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию ⚫️Чёрного моря!')
            mainmenu(user)
        elif m.text=='🌙Лунное':
            db.choose_sea(user, 'moon')
            bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию 🌙Лунного моря!')
            mainmenu(user)
        else:
            sea_choice(m)
            return
    if m.text=='🛡Защита':
        db.defend(user)
        bot.send_message(user['id'], 'Вы вплыли в оборону своего моря! Ждите следующего сражения.')
    if m.text=='💢Атака':
        kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
        for ids in sealist:
            if ids!=user['sea']:
                kb.add(types.KeyboardButton(seatoemoj(sea=ids)))
        bot.send_message(user['id'], 'Выберите цель.', reply_markup=kb)
    if m.text=='🌙' or m.text=='💎' or m.text=='⚫️':
        atksea=seatoemoj(emoj=m.text)
        if user['sea']!=atksea:
            db.attack(user, atksea)
            bot.send_message(user['id'], 'Вы приготовились к атаке на '+sea_ru(atksea)+' море! Ждите начала битвы.')
            mainmenu(user)
    if m.text=='ℹ️Инфо по игре':
        bot.send_message(m.chat.id, 'Очередной неоконченный проект Пасюка. Пока что можно только выбрать море и сражаться за него, '+
                            'получая для него очки, повышать уровень и улучшать свои характеристики. Битвы в 12:00, 16:00, 20:00 и 24:00 по хуй его знает какому времени.')
        
    if m.text=='/menu':
        mainmenu(user)
        
    if m.text=='/upstats':
        if user['freestatspoints']>0:
            text='Свободные очки: '+str(user['freestatspoints'])+'.\nВыберите характеристику для прокачки.'
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton('💢'), types.KeyboardButton('🛡'))
            bot.send_message(user['id'], text, reply_markup=kb)
        else:
            bot.send_message(user['id'], 'Нет свободных очков!')
            
    if m.text=='💢':
        if user['freestatspoints']>0:
            db.upgrade_attack(user)
            bot.send_message(user['id'], 'Вы стали сильнее!')
        else:
            bot.send_message(user['id'], 'Нет свободных очков!')
        user = db.get_user(user['id'])
        mainmenu(user)
            
    if m.text=='🛡':
        if user['freestatspoints']>0:
            db.upgrade_defense(user)
            bot.send_message(user['id'], 'Вы стали сильнее!')
        else:
            bot.send_message(user['id'], 'Нет свободных очков!')
        user = db.get_user(user['id'])
        mainmenu(user)
        
    if m.text=='/referal':
        ref = db.get_referal(user)
        bot.send_message(user['id'], 'Вот ваша ссылка для приглашения друзей:\n'+'https://telegram.me/Fishwarsbot?start='+ref)
        
    if m.text=='🍖🥬Питание':
        kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton('🔝Мелководье'), types.KeyboardButton('🕳Глубины'))
        kb.add(types.KeyboardButton('⬅️Назад'))
        bot.send_message(m.chat.id, 'Выберите, где будете пытаться искать пищу. Чем больше вы питаетесь, тем быстрее идёт развитие!', reply_markup=kb)
        
    if m.text=='🔝Мелководье':
        strenght=1
        if user['strenght']>=strenght:
            if user['status']=='free':
                db.go_eating(user, strenght)
                bot.send_message(m.chat.id, 'Вы отправились искать пищу на побережье.')
                t=threading.Timer(random.randint(60, 90), coastfeed, args=[user])
                t.start()
            else:
                bot.send_message(user['id'], 'Вы уже заняты чем-то!')
        else:
            bot.send_message(user['id'], 'Недостаточно сил - даже рыбам нужен отдых!')
        user = db.get_user(user['id'])
        mainmenu(user)
        
    if m.text=='🕳Глубины':
        strenght=2
        if user['strenght']>=strenght:
            if user['status']=='free':
                db.go_eating(user, strenght)
                bot.send_message(m.chat.id, 'Вы отправились искать пищу в глубины моря.')
                t=threading.Timer(random.randint(60, 90), depthsfeed, args=[user])
                t.start()
            else:
                bot.send_message(user['id'], 'Вы уже заняты чем-то!')
        else:
            bot.send_message(user['id'], 'Недостаточно сил - даже рыбам нужен отдых!')
        user = db.get_user(user['id'])
        mainmenu(user)
        
    if '/fishname' in m.text:
        if m.text.count(' ') == 0:
            bot.send_message(m.chat.id, 'Сменить ник можно командой /fishname ник.')
            return
        if user['changename']>0:
            no=0
            name=m.text.split(' ')[1]
            if not 2<=len(name)<=20 or not name.isalnum():
                bot.send_message(m.chat.id, 'Длина ника должна быть от 2х до 20 символов и содержать только русские и английские буквы!')
                return
            db.change_name(user, name)
            bot.send_message(m.chat.id, 'Вы успешно сменили имя на "*'+name+'*"!', parse_mode='markdown')
        else:
            bot.send_message(m.chat.id, 'Попытки сменить ник закончились!')
        
    if m.text=='🐟Обо мне' or m.text=='⬅️Назад':
        mainmenu(user)
                


def coastfeed(user):
    db.free_user(user)
    luckytexts=['На береге вы заметили стаю мальков и решили, что это будет отличным перекусом.',
                'На поверхности плавал труп какой-то неизвестной рыбы. Его вы и решили сьесть. Рыбы вообще едят всё, что видят.']
    falsetexts=['Пока вы добирались до берега, вы почувствовали активные вибрации неподалеку, означающие, что кого-то едят. Чтобы '+\
               'самим не стать кормом, вы вернулись в безопасное место.']
    chance=70*user['agility']
    if 'slow' in user['skills']:
        chance+=user['skills']['slow']['lvl']*0.5
    coef=1
    if random.randint(1,100)<=chance:
        i=user['recievepoints']*user['pointmodifer']*coef
        bottompoints=int(i*0.8)
        toppoints=int(i*1.2)
        points=random.randint(bottompoints, toppoints)
        if points<=0:
            points=1
        text=random.choice(luckytexts)
        text+='\nПолучено:\n'+'*Очки эволюции*: '+str(points)+'🧬'
        bot.send_message(user['id'], text, parse_mode='markdown')
        recieveexp(user, points)
    else:
        text=random.choice(falsetexts)
        bot.send_message(user['id'], text, parse_mode='markdown')
    
    
    
def depthsfeed(user):
    db.free_user(user)
    luckytexts=['В глубинах моря вы нашли стаю крабов. Пришлось потрудиться, чтобы не быть покусанными, но в итоге вы наелись.',
                'Вы нашли какие-то вкусные на вид растения. Для получения очков эволюции сойдёт.']
    falsetexts=['В один момент вашего заплыва вы ощутили, что давление становится слишком сильным. Если бы вы поплыли дальше, то вас просто сплющило бы.']
    chance=55*user['agility']
    if 'slow' in user['skills']:
        chance+=user['skills']['slow']['lvl']*0.5
    coef=2.5
    if random.randint(1,100)<=chance:
        i=user['recievepoints']*user['pointmodifer']*coef
        bottompoints=int(i*0.8)
        toppoints=int(i*1.2)
        points=random.randint(bottompoints, toppoints)
        if points<=0:
            points=1
        text=random.choice(luckytexts)
        text+='\nПолучено:\n'+'*Очки эволюции*: '+str(points)+'🧬'
        bot.send_message(user['id'], text, parse_mode='markdown')
        recieveexp(user, points)
    else:
        text=random.choice(falsetexts)
        bot.send_message(user['id'], text, parse_mode='markdown')
        

def recieveexp(user, exp):
    db.increase_exp(user, exp)
    c = int(countnextlvl(user['lastlvl']))
    if user['evolpoints']+exp>=c:
        db.user_evolve(user, c)
        bot.send_message(user['id'], 'Поздравляем! Вы эволюционировали! Прокачка скиллов - /skills (пока что недоступна).')
        user = db.get_user(user['id'])
        if user['lvl']==3 and user['inviter']!=None:
            db.achieve_referal_bonus(user)
            bot.send_message(user['inviter'], user['gamename']+' освоился в игре! Вы получаете +1 к выносливости.')

            
def seatoemoj(sea=None, emoj=None):
    if sea=='moon':
        return '🌙'
    if sea=='crystal':
        return '💎'
    if sea=='black':
        return '⚫️'
    if emoj=='⚫️':
        return 'black'
    if emoj=='💎':
        return 'crystal'
    if emoj=='🌙':
        return 'moon'

    
def endrest():
    global rest
    rest = False
    
def seafight():
    seas={}
    cusers=db.users.find({})

    for ids in sealist:
        seas.update(createsea(ids))

    for ids in cusers:
        if ids['battle']['action'] == 'def':
            seas[ids['sea']]['defers'].update({ids['id']:ids})
        elif ids['battle']['action']=='attack':
            seas[ids['battle']['target']]['attackers'].update({ids['id']:ids})
    
    for ids in seas:
        sea=seas[ids]

        for sea_defer in sea['defers']:
            user=sea['defers'][sea_defer]
            defpower=user['stats']['def']
            if 'fat' in user['skills']:
                defpower+=defpower*user['skills']['fat']['lvl']*0.01
            if 'steelleather' in user['skills']:
                if random.randint(1,1000)<=user['skills']['steelleather']['lvl']*0.5*10:
                    if len(seas[ids]['attackers'])>0:
                        trgt=random.choice(seas[ids]['attackers'])
                        trgt['attack']=trgt['attack']/2
                        bot.send_message(user['id'], 'Своей кожей вы заблокировали рыбу '+trgt['gamename']+', снизив ее характеристики на 50%!')
            sea['defpower']+=defpower
        for sea_attacker in sea['attackers']:
            user=sea['attackers'][sea_attacker]
            if 'sharpteeth' in user['skills']:
                user['stats']['attack']+=user['stats']['attack']*user['skills']['sharpteeth']['lvl']*0.01
            sea['attackerspower']+=user['stats']['attack']
            
        if sea['defpower']<sea['attackerspower']:
            sea['saved']=False
    text=''
    for ids in seas:
        sea=seas[ids]
        if sea['saved']==False:
            sea['score']+=0
            scores=[]
            for idss in sea['attackers']:
                atker=sea['attackers'][idss]
                if atker['sea'] not in scores:
                    scores.append(atker['sea'])
                    seas[atker['sea']]['score']+=3
            text+='💢'+sea_ru(sea['name'])+' море потерпело поражение в битве! Топ атакующих:\n'
            who='attackers'
            stat='attack'
            text+=battletext(sea, who, stat)
            text+='Топ защитников:\n'
            who='defers'
            stat='def'
            text+=battletext(sea, who, stat)
        else:
            sea['score']+=8
            text+='🛡'+sea_ru(sea['name'])+' море отстояло свою территорию! Топ защитников:\n'
            who='defers'
            stat='def'
            text+=battletext(sea, who, stat)
            text+='Топ атакующих:\n'
            who='attackers'
            stat='attack'
            text+=battletext(sea, who, stat)
    text+='Начисленные очки:\n\n'
    for ids in seas:
        text+=sea_ru(seas[ids]['name'])+' море: '+str(seas[ids]['score'])+' очков\n'
        db.add_sea_score(self, seas[ids])
    db.reset_battle_actions()
    bot.send_message(officialchat, 'Результаты битвы:\n\n'+text)
            
            
         
        
def battletext(sea, who, stat):
    top=5
    i=0
    text=''
    alreadyintext=[]
    while i<top:
        intext=None
        maxstat=0
        for idss in sea[who]:
            user=sea[who][idss]
            if user['stats'][stat]>maxstat and user['id'] not in alreadyintext:
                maxstat=user['stats'][stat]
                intext=user
        if intext!=None:
            alreadyintext.append(intext['id'])
            text+=seatoemoj(intext['sea'])
            text+=intext['gamename']            
            text+=', '                            
        i+=1
    if len(sea[who])>0:
        text=text[:len(text)-2]
        text+='.'
    text+='\n\n'
    return text


def countnextlvl(lastlvl):
    if lastlvl!=0:
        nextlvl=int(lastlvl*2.9)
    else:
        nextlvl=10
    return nextlvl

   
def createsea(sea):
    return {sea:{
        'name':sea,
        'defpower':0,
        'attackerspower':0,
        'defers':{},
        'attackers':{},
        'saved':True,
        'score':0
    }
           }

def timecheck():
    globaltime=time.time()+3*3600
    ctime=str(datetime.fromtimestamp(globaltime)).split(' ')[1]
    global rest
    chour=int(ctime.split(':')[0])
    cminute=int(ctime.split(':')[1])
    csecond=float(ctime.split(':')[2])
    csecond=round(csecond, 0)
    if chour in fighthours and rest==False and cminute==0:
        seafight()
        rest=True
        t=threading.Timer(120, endrest)
        t.start()
    db.global_strength_regen(globaltime)
    if csecond==0:
        global britmsgs
        britmsgs=0
        global ban
        ban=[]
    t=threading.Timer(1, timecheck)
    t.start()
    

timecheck()
    
db.free_all_users()    

print('7777')
bot.polling(none_stop=True,timeout=600)

