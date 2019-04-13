# -*- coding: utf-8 -*-
import os
import telebot
import time
import random
import threading
from emoji import emojize
from telebot import types
from pymongo import MongoClient
import traceback
from datetime import datetime

token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(token)


client=MongoClient(os.environ['database'])
db=client.fishwars
users=db.users
allseas=db.seas

fighthours=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
sealist=['crystal', 'black', 'moon']
officialchat=441399484
rest=False


try:
    pass

except Exception as e:
    print('Ошибка:\n', traceback.format_exc())
    bot.send_message(441399484, traceback.format_exc())

 

@bot.message_handler(commands=['start'])
def start(m):
    user=users.find_one({'id':m.from_user.id})
    global rest
    if user==None:
        if rest==False:
            users.insert_one(createuser(m.from_user))
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            for ids in sealist:
                kb.add(types.KeyboardButton(sea_ru(ids)))
            bot.send_message(m.chat.id, 'Добро пожаловать! Выберите, за какое из морей вы будете сражаться.', reply_markup=kb)
        else:
            bot.send_message(m.chat.id, 'В данный момент идёт битва морей!')

        
def mainmenu(user):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton('🗡Атака'), types.KeyboardButton('🛡Защита'))
    kb.add(types.KeyboardButton('ℹ️Инфо по игре'))
    bot.send_message(user['id'], 'Главное меню.', reply_markup=kb)
        

@bot.message_handler()
def allmessages(m):
    global rest
    user=users.find_one({'id':m.from_user.id})
    if user!=None:
        if rest==False:
            if user['sea']==None:
                if m.text=='💎Кристальное':
                    users.update_one({'id':user['id']},{'$set':{'sea':'crystal'}})
                    bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию 💎Кристального моря!')
                    mainmenu(user)
                if m.text=='⚫️Чёрное':
                    users.update_one({'id':user['id']},{'$set':{'sea':'black'}})
                    bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию ⚫️Чёрного моря!')
                    mainmenu(user)
                if m.text=='🌙Лунное':
                    users.update_one({'id':user['id']},{'$set':{'sea':'moon'}})
                    bot.send_message(user['id'], 'Теперь вы сражаетесь за территорию 🌙Лунного моря!')
                    mainmenu(user)
            if m.text=='🛡Защита':
                users.update_one({'id':user['id']},{'$set':{'battle.action':'def'}})
                bot.send_message(user['id'], 'Вы вплыли в оборону своего моря! Ждите следующего сражения.')
            if m.text=='🗡Атака':
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
            if m.text=='ℹ️Инфо по игре':
                bot.send_message(m.chat.id, 'Очередной неоконченный проект Пасюка. Пока что можно только выбрать море и сражаться за него, '+
                                 'получая для него очки. Битвы каждый час.')
        else:
            bot.send_message(m.chat.id, 'В данный момент идёт битва морей!')
                
            
            

            
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
    rest=False
    
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
            sea['defpower']+=user['stats']['def']
        for idss in sea['attackers']:
            user=sea['attackers'][idss]
            sea['attackerspower']+=user['stats']['attack']
            
        if sea['defpower']<sea['attackpower']:
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
                    seas[atker['sea']]['score']+3
            text+='🗡'+sea_ru(sea['name'])+' море потерпело поражение в битве! Топ атакующих:\n'
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
            if i+1==top:
                text+=', '
            else:
                text+='.\n\n'
        i+=1
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
        'battle':battle
    }

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
    ctime=str(datetime.fromtimestamp(time.time()+3*3600)).split(' ')[1]
    global rest
    chour=int(ctime.split(':')[0])
    cminute=int(ctime.split(':')[1])
    if True:#chour in fighthours and rest==False and cminute==0:
        seafight()
        rest=True
        t=threading.Timer(120, endrest)
        t.start()
    t=threading.Timer(1, timecheck)
    t.start()
    

timecheck()
    
print('7777')
bot.polling(none_stop=True,timeout=600)

