# -*- coding: utf-8 -*-
import os
import telebot
import time
import random
import threading
from telebot import types
from pymongo import MongoClient
import traceback
from datetime import datetime

from config import token, mongo_url

bot = telebot.TeleBot(token)

client = MongoClient(mongo_url)
db = client.fishwars
users = db.users
allseas = db.seas

creator = 792414733

fighthours = [12, 16, 20, 0]
sealist = ['crystal', 'black', 'moon']
officialchat = -1001418916571
rest=False
ban=[]
letters=['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
        'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

allletters=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
        'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 
           'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']

 
@bot.message_handler(commands=['update'])
def updd(m):
    if m.from_user.id != creator:
        return
    users.update_many({},{'$set':{'skills':{}, 'inventory':{}}})
    bot.send_message(creator, 'yes')

@bot.message_handler(commands=['init'])
def wipe(m):
    if m.from_user.id==creator:
        for sea in sealist:
            allseas.insert_one(createsea(sea))
        bot.send_message(m.chat.id, 'Моря подключены!')

@bot.message_handler(commands=['wipe'])
def wipe(m):
    if m.from_user.id==creator:
        allseas.update_many({},{'$set':{'score':0}})
        users.drop()
        bot.send_message(m.chat.id, 'Вайп данных!')
            
            
@bot.message_handler(commands=['drop'])
def drop(m):
    if m.from_user.id==creator:
        allseas.update_many({},{'$set':{'score':0}})
        bot.send_message(m.chat.id, 'Сбросил очки всем морям!')

@bot.message_handler(commands=['start'])
def start(m):
    user=users.find_one({'id':m.from_user.id})
    global rest
    if user or m.chat.type != 'private':
        return

    users.insert_one(createuser(m.from_user))
    
    sea_choice(m) 

    try:
        ref = m.text.split(' ')[1]
        friend = users.find_one({'referal': ref})
        if friend:
            users.update_one({'id':friend['id']},{'$push':{'friends':m.from_user.id}})
            users.update_one({'id':m.from_user.id},{'$set':{'inviter':friend['id']}})
            bot.send_message(friend['id'], m.from_user.first_name+' зашел в игру по вашей рефералке! Когда он поиграет немного, вы получите +1 к максимальной силе!')
    except Exception as e:
        bot.send_message(creator, traceback.format_exc())

def get_joinable_seas():
    print(list(allseas.find({})))
    print(list(allseas.find({}).sort('score', 1)))
    return list(allseas.find({}).sort('score', 1))[:2]

def sea_choice(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for sea in get_joinable_seas():
        kb.add(types.KeyboardButton(sea_ru(ids['name'])))
    bot.send_message(m.chat.id, 'Добро пожаловать! Выберите, за какое из морей вы будете сражаться.', reply_markup=kb)

        
def mainmenu(user):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('💢Атака'), types.KeyboardButton('🛡Защита'))
    kb.add(types.KeyboardButton('🍖🥬Питание'), types.KeyboardButton('ℹ️Инфо по игре'))
    kb.add(types.KeyboardButton('🐟Обо мне'))

    needed=countnextlvl(user['lastlvl'])

    text=''
    text+='🐟Имя рыбы: '+user['gamename']+'\n'
    try:
        text += f"🌊Родное море: {sea_ru(user['sea'])}\n"
    except:
        pass
    text += f'💪Силы: {user["strenght"]}/{user["maxstrenght"]}\n'
    text += f'🏅Уровень эволюции: {user["lvl"]}\n'
    text += f"🧬Очки эволюции: {user['evolpoints']}/{needed}\n"
    text += f"ss💢Атака: {user['stats']['attack']}\n"
    text += f'🛡Защита: '+str(user['stats']['def'])+'\n'
    text += f'Реген сил: 1💪 / '+str(round(20*user['strenghtregencoef'], 2))+' минут\n'
    if user['freestatspoints'] > 0:
        text += 'Доступны очки характеристик! Для использования - /upstats \n'
    bot.send_message(user['id'], 'Главное меню.\n'+text, reply_markup=kb)

        
@bot.message_handler()
def allmessages(m):
    global rest
    user = users.find_one({'id':m.from_user.id})
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
            users.update_one({'id':user['id']},{'$set':{'sea':'crystal'}})
            bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию 💎Кристального моря!')
            mainmenu(user)
        elif m.text=='⚫️Чёрное':
            users.update_one({'id':user['id']},{'$set':{'sea':'black'}})
            bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию ⚫️Чёрного моря!')
            mainmenu(user)
        elif m.text=='🌙Лунное':
            users.update_one({'id':user['id']},{'$set':{'sea':'moon'}})
            bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию 🌙Лунного моря!')
            mainmenu(user)
        else:
            sea_choice(m)
            return
    if m.text=='🛡Защита':
        users.update_one({'id':user['id']},{'$set':{'battle.action':'def'}})
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
            users.update_one({'id':user['id']},{'$set':{'battle.action':'attack', 'battle.target':atksea}})
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
            users.update_one({'id':user['id']},{'$inc':{'freestatspoints':-1, 'stats.attack':1}})
            bot.send_message(user['id'], 'Вы стали сильнее!')
        else:
            bot.send_message(user['id'], 'Нет свободных очков!')
        user=users.find_one({'id':m.from_user.id})
        mainmenu(user)
            
    if m.text=='🛡':
        if user['freestatspoints']>0:
            users.update_one({'id':user['id']},{'$inc':{'freestatspoints':-1, 'stats.def':1}})
            bot.send_message(user['id'], 'Вы стали сильнее!')
        else:
            bot.send_message(user['id'], 'Нет свободных очков!')
        user=users.find_one({'id':m.from_user.id})
        mainmenu(user)
        
    if m.text=='/referal':
        if user['referal']==None:
            ref=genreferal(user)
            users.update_one({'id':user['id']},{'$set':{'referal':ref}})
        else:
            ref=user['referal']
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
                users.update_one({'id':user['id']},{'$set':{'status':'eating'}})
                users.update_one({'id':user['id']},{'$inc':{'strenght':-strenght}})
                bot.send_message(m.chat.id, 'Вы отправились искать пищу на побережье.')
                t=threading.Timer(random.randint(60, 90), coastfeed, args=[user])
                t.start()
            else:
                bot.send_message(user['id'], 'Вы уже заняты чем-то!')
        else:
            bot.send_message(user['id'], 'Недостаточно сил - даже рыбам нужен отдых!')
        user=users.find_one({'id':m.from_user.id})
        mainmenu(user)
        
    if m.text=='🕳Глубины':
        strenght=2
        if user['strenght']>=strenght:
            if user['status']=='free':
                users.update_one({'id':user['id']},{'$set':{'status':'eating'}})
                users.update_one({'id':user['id']},{'$inc':{'strenght':-strenght}})
                bot.send_message(m.chat.id, 'Вы отправились искать пищу в глубины моря.')
                t=threading.Timer(random.randint(60, 90), depthsfeed, args=[user])
                t.start()
            else:
                bot.send_message(user['id'], 'Вы уже заняты чем-то!')
        else:
            bot.send_message(user['id'], 'Недостаточно сил - даже рыбам нужен отдых!')
        user=users.find_one({'id':m.from_user.id})
        mainmenu(user)
        
    if '/fishname' in m.text:
        try:
            if user['changename']>0:
                no=0
                name=m.text.split(' ')[1]
                if len(name)<=20 and len(name)>1:
                    for ids in name:
                        if ids.lower() not in allletters:
                            no=1
                else:
                    no=1
                if no==0:
                    users.update_one({'id':user['id']},{'$set':{'gamename':name}})
                    users.update_one({'id':user['id']},{'$inc':{'changename':-1}})
                    bot.send_message(m.chat.id, 'Вы успешно сменили имя на "*'+name+'*"!', parse_mode='markdown')
                else:
                    bot.send_message(m.chat.id, 'Длина ника должна быть от 2х до 20 символов и содержать только русские и английские буквы!')
            else:
                bot.send_message(m.chat.id, 'Попытки сменить ник закончились!')
        except:
            pass
        
    if m.text=='🐟Обо мне' or m.text=='⬅️Назад':
        mainmenu(user)
        
    if m.text=='/score':
        seas=allseas.find({})
        text=''
        for ids in seas:
            text+=sea_ru(ids['name'])+' море: '+str(ids['score'])+' очков\n'
        bot.send_message(m.chat.id, text)
                
                
def genreferal(user):
    u=users.find({})
    ref=''
    allref=[]
    for ids in users.find({}):
        allref.append(ids['referal'])
    while len(ref)<32:
        ref+=random.choice(letters)
    while ref in allref:
        ref=''
        while len(ref)<32:
            ref+=random.choice(letters)
    return ref


def coastfeed(user):
    users.update_one({'id':user['id']},{'$set':{'status':'free'}})
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
    users.update_one({'id':user['id']},{'$set':{'status':'free'}})
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
    users.update_one({'id':user['id']},{'$inc':{'evolpoints':exp}})
    c=int(countnextlvl(user['lastlvl']))
    if user['evolpoints']+exp>=c:
        users.update_one({'id':user['id']},{'$set':{'lastlvl':c, 'recievepoints':countnextpointrecieve(user['recievepoints'])}})
        users.update_one({'id':user['id']},{'$inc':{'lvl':1, 'freeevolpoints':2, 'freestatspoints':1}})
        bot.send_message(user['id'], 'Поздравляем! Вы эволюционировали! Прокачка скиллов - /skills (пока что недоступна).')
        user=users.find_one({'id':user['id']})
        if user['lvl']==3 and user['inviter']!=None:
            users.update_one({'id':user['inviter']},{'$inc':{'maxstrenght':1}})
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
    cusers=users.find({})
    for ids in sealist:
        seas.update(createsea(ids))
    for ids in cusers:
        if ids['battle']['action']=='def':
            seas[ids['sea']]['defers'].update({ids['id']:ids})
        elif ids['battle']['action']=='attack':
            seas[ids['battle']['target']]['attackers'].update({ids['id']:ids})
    
    for ids in seas:
        sea=seas[ids]
        print(sea)
        for idss in sea['defers']:
            user=sea['defers'][idss]
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
        for idss in sea['attackers']:
            user=sea['attackers'][idss]
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
        allseas.update_one({'name':seas[ids]['name']},{'$inc':{'score':seas[ids]['score']}})
    users.update_many({},{'$set':{'battle.target':None, 'battle.action':None}})
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
            text+=intext['gamename']            
            text+=', '                            
        i+=1
    if len(sea[who])>0:
        text=text[:len(text)-2]
        text+='.'
    text+='\n\n'
    return text
            
            
def createuser(user):
    stats={
        'attack':1,
        'def':1
    }
    battle={
        'action':None,
        'target':None
    }
    return {
        'id':user.id,
        'name':user.first_name,
        'gamename':user.first_name,
        'stats':stats,
        'sea':None,
        'status':'free',
        'maxstrenght':8,
        'strenght':8,
        'agility':1,                     # 1 = 100%
        'battle':battle,
        'evolpoints':0,
        'lvl':1,
        'inventory':{},
        'freestatspoints':0,
        'freeevolpoints':0,
        'lastlvl':0,
        'strenghtregencoef':1,       # Чем меньше, тем лучше
        'laststrenghtregen':None,
        'recievepoints':1,                # 1 = 1 exp
        'pointmodifer':1,                 # 1 = 100%
        'referal':None,
        'changename':3,
        'skills':{}
    }

def regenstrenght(user):
    users.update_one({'id':user['id']},{'$inc':{'strenght':1}})
    users.update_one({'id':user['id']},{'$set':{'laststrenghtregen':time.time()+3*3600}})


def countnextlvl(lastlvl):
    if lastlvl!=0:
        nextlvl=int(lastlvl*2.9)
    else:
        nextlvl=10
    return nextlvl
        
def countnextpointrecieve(recievepoints):
    return recievepoints*2.1

def sea_ru(sea):
    if sea=='crystal':
        return '💎Кристальное'
    if sea=='black':
        return '⚫️Чёрное'
    if sea=='moon':
        return '🌙Лунное'

   
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
    for ids in users.find({}):
        user=ids
        if user['strenght']<user['maxstrenght']:
            if user['laststrenghtregen']==None:
                regenstrenght(user)
            elif globaltime>=user['laststrenghtregen']+20*60*user['strenghtregencoef']:
                regenstrenght(user)
    if csecond==0:
        global britmsgs
        britmsgs=0
        global ban
        ban=[]
    t=threading.Timer(1, timecheck)
    t.start()
    

timecheck()
    
    
users.update_many({},{'$set':{'status':'free'}})
print('7777')
bot.polling(none_stop=True,timeout=600)

