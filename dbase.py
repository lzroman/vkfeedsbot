import time, json
from logger import log

class DBase:
    def __init__(self):
        self.userlist = {}

    def loaddb(self, path):
        with open(path, 'r') as f:
            rawdata = json.load(f)
        for rawuser in rawdata['users']:
            user = User()
            user.from_raw(rawdata['users'][rawuser])
            self.userlist.update({user.id: user})
        log('db loaded')

    def savedb(self, path):
        log('start save db')
        rawdata = {'users': {}}
        for user in self.userlist.values():
            rawdata['users'].update({user.id: user.to_raw()})
        log('users ready')
        with open(path, 'w') as outfile:
            json.dump(rawdata, outfile)
        log('db saved')

    def add_user(self, id_u):
        if not id_u in self.userlist.keys():
            self.userlist.update({id_u: User(id_u)})
            return 'done'
        else:
            return 'already'
    
    def user_add_sub(self, id_u, id_s):
        if id_u in self.userlist.keys():
            return self.userlist[id_u].add_sub(id_s)
        else:
            return 'no_user'
    
    def user_rm_sub(self, id_u, id_s):
        if id_u in self.userlist.keys():
            return self.userlist[id_u].rm_sub(id_s)
        else:
            return 'no_user'
    
    def user_set_last(self, id_u, id_s, val):
        if id_u in self.userlist.keys():
            return self.userlist[id_u].set_last(id_s, val)
        else:
            return 'no_user'

    def emptysubs(self, id_u):
        if id_u in self.userlist.keys():
            return self.userlist[id_u].emptysubs()
        else:
            return 'no_user'


class User:
    def __init__(self, idd = 0):
        self.id = idd
        self.subs = {}
        self.maxtext = 0
        self.pause = False
        self.status = 'regular'
        self.lang = 'en'
    
    def get_subs(self):
        val = []
        for sub in self.subs:
            val.append(self.subs[sub].id)
        return val
    
    def from_raw(self, val):
        self.id = val['id']
        for rawsub in val['subs']:
            sub = Sub()
            sub.from_raw(val['subs'][rawsub])
            self.subs.update({sub.id: sub})
        self.pause = val['pause']
        if 'maxtext' in val.keys():
            self.maxtext = val['maxtext']
        if 'status' in val.keys():
            self.status = val['status']
        if 'lang' in val.keys():
            self.lang = val['lang']

    def to_raw(self):
        val = {}
        val.update({'id': self.id})
        subs = {}
        for sub in self.subs.values():
            try:
                subs.update({sub.id: sub.to_raw()})
            except Exception as e:
                log(''.join(['fail: ', e]))
        val.update({'subs': subs})
        val.update({'pause': self.pause})
        val.update({'maxtext': self.maxtext})
        val.update({'status': self.status})
        val.update({'lang': self.lang})
        return val

    def add_sub(self, idd):
        if not idd in self.subs.keys():
            self.subs.update({idd: Sub(idd)})
            return 'done'
        else:
            return 'already'
    
    def rm_sub(self, idd):
        if idd in self.subs.keys():
            self.subs.pop(idd)
            return 'done'
        else:
            return 'already'
        
    def set_last(self, id_s, val):
        if id_s in self.subs.keys():
            self.subs[id_s].last_post = val
            return 'done'
        else:
            return 'no_sub'
        
    def emptysubs(self):
        self.subs.clear()
        return 'done'



class Sub:
    def __init__(self, idd = 0):
        self.id = idd
        self.last_post = 0
        self.is_memb = False
    
    def from_raw(self, val):
        self.id = val['id']
        self.last_post = val['last_post']
        self.is_memb = val['is_memb']

    def to_raw(self):
        val = {}
        val.update({'id': self.id})
        val.update({'last_post': self.last_post})
        val.update({'is_memb': self.is_memb})
        return val
