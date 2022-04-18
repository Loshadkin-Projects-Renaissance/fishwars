import uuid

class Database:
    def __init__(self, mongo_url):
        db = client.fishwars
        self.users = db.users
        self.seas = db.seas
    
    def drop(self):
        self.seas.update_many({},{'$set':{'score':0}})

    def score(self):
        seas = self.seas.find({})
        text=''
        for ids in seas:
            text+=sea_ru(ids['name'])+' море: '+str(ids['score'])+' очков\n'
        return text

    def wipe(self):
        self.drop()
        self.users.drop()

    def init_seas(self):
        self.seas.drop()
        for sea in sealist:
            allseas.insert_one(createsea(sea)[sea])

    def get_joinable_seas(self):
        result = list(self.seas.find({}).sort('score', 1))
        if len(set([result[2]['score'], result[1]['score'], result[0]['score']])) != 3:
            return result
        else:
            return result[:2]

    def get_user(self, tg_id):
        return self.users.find_one({'id': tg_id})

    def process_referal(self, referal, tg_user):
        if self.get_user(tg_user.id)['inviter']:
            return
        friend = self.users.find_one({'referal': ref})
        if not friend:
            return
        self.users.update_one({'id':friend['id']},{'$push':{'friends':tg_user.id}})
        self.users.update_one({'id':tg_user.id},{'$set':{'inviter':friend['id']}})
        return friend['id']

    def create_user(self, tg_user):
        self.users.insert_one(self.form_user_doc(tg_user))

    def choose_sea(self, user, sea):
        self.users.update_one({'id':user['id']},{'$set':{'sea': sea}})

    def defend(self, user):
        self.users.update_one({'id':user['id']},{'$set':{'battle.action':'def'}})

    def attack(self, user, sea):
        self.users.update_one({'id':user['id']},{'$set':{'battle.action':'attack', 'battle.target':sea}})

    def upgrade_attack(self, user):
        self.users.update_one({'id':user['id']},{'$inc':{'freestatspoints':-1, 'stats.attack':1}})

    def upgrade_defense(self, user):
        self.users.update_one({'id':user['id']},{'$inc':{'freestatspoints':-1, 'stats.def':1}})

    def form_user_doc(self):
        stats = {
            'attack':1,
            'def':1
        }
        battle = {
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

    def gen_referal(self, user):
        ref = str(uuid.uuid4()).replace('-', '')
        self.users.update_one({'id':user['id']},{'$set':{'referal':ref}})
        return ref

    def get_referal(self, user):
        if user['ref']:
            return user['ref']
        else:
            return gen_referal(user)

    def go_eating(self, user, strenght):
        self.users.update_one({'id':user['id']},{'$set':{'status':'eating'}})
        self.users.update_one({'id':user['id']},{'$inc':{'strenght':-strenght}})

    def change_name(user, name):
        self.users.update_one({'id':user['id']},{'$set':{'gamename':name}})
        self.users.update_one({'id':user['id']},{'$inc':{'changename':-1}})