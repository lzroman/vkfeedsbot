from telegram.ext import Updater, CommandHandler, ConversationHandler, Filters, MessageHandler
import json, time, datetime
import dbase
from logger import log
import vk_api, telegram

class VKWorker:
    def __init__(self, vk_session):
        self.vk_session = vk_session
        self.vk_tools = vk_api.VkTools(self.vk_session)
        self.vk_upload = vk_api.VkUpload(self.vk_session)
        self.subsmax = 50
        self.posts_cache = {}


    def method(self, command, args):
        return self.vk_session.method(command, args)
    

    def get_user(self, id):
        return self.vk_session.method('users.get',{'user_id' : [id]})[0]


    def get_subs(self, lst):
        uids = ''
        pids = ''
        subs = []
        log(lst)
        for val in lst:
            if val[:2] == 'id':
                uids = ','.join([uids, val[2:]])
            else:
                pids = ','.join([pids, val[6:]])
        if len(uids):
            uids = uids[1:]
            raw = self.vk_session.method('users.get',{'user_ids': uids})
            for sub_u in raw:
                subs.append({'id': ''.join(['id', str(sub_u['id'])]), 'name': ' '.join([sub_u['first_name'], sub_u['last_name']]), 'is_closed': sub_u['is_closed']})
        if len(pids):
            pids = pids[1:]
            raw = self.vk_session.method('groups.getById',{'group_ids': pids})
            for sub_p in raw:
                subs.append({'id': ''.join(['public', str(sub_p['id'])]), 'name':  sub_p['name'], 'is_closed': sub_p['is_closed']})

        return subs


    def get_user_subs(self, id):
        subs_raw = self.vk_session.method('users.getSubscriptions', {'user_id' : id})
        subs = []
        if len(subs_raw['users']['items']) > self.subsmax:
            subs_raw['users']['items'] = subs_raw['user']['items'][:self.subsmax]
        elif len(subs_raw['users']['items']):
            raw = self.vk_session.method('users.get',{'user_ids': ','.join(str(val) for val in subs_raw['users']['items'])})
            for sub_u in raw:
                if 'deactivated' in sub_u.keys():
                    subs.append({'id': ''.join(['id', str(sub_u['id'])]), 'name': ' '.join([sub_u['first_name'], sub_u['last_name']]), 'is_closed': True})
                else:
                    subs.append({'id': ''.join(['id', str(sub_u['id'])]), 'name': ' '.join([sub_u['first_name'], sub_u['last_name']]), 'is_closed': sub_u['is_closed']})
        if len(subs_raw['groups']['items']) > self.subsmax:
            subs_raw['groups']['items'] = subs_raw['groups']['items'][:self.subsmax]
        raw = self.vk_session.method('groups.getById',{'group_ids' : ','.join(str(val) for val in subs_raw['groups']['items'])})
        for sub_p in raw:
            subs.append({'id': ''.join(['public', str(sub_p['id'])]), 'name': sub_p['name'], 'is_closed': sub_p['is_closed']})
        #print(subs)
        return subs


    def get_sub(self, val):
        if val[:2] == 'id':
            raw = self.get_user(int(val[2:]))
            if 'deactivated' in raw.keys():
                return {'id': ''.join(['id', str(raw['id'])]),'name': ' '.join([raw['first_name'], raw['last_name']]), 'is_closed': True}
            return {'id': ''.join(['id', str(raw['id'])]),'name': ' '.join([raw['first_name'], raw['last_name']]), 'is_closed': raw['is_closed']}
        else:
            raw = self.vk_session.method('groups.getById',{'group_id' : int(val[6:])})[0]
            return {'id': ''.join(['public', str(raw['id'])]),'name':  raw['name'], 'is_closed': raw['is_closed']}


    def resolve_link(self, link):
        return self.vk_session.method('utils.resolveScreenName', {'screen_name' : link})

    def makesub(self, link):
        sub = self.get_sub(link)
        return ''.join(['[', sub['name'], '](https://vk.com/', str(sub['id']), ')'])

    def makemlink(self, link):
        if link[:2] == 'id':
            return int(link[2:])
        else:
            return -int(link[6:])


    def clear_posts_cache(self):
        pass

    def get_posts(self, link, last_post):
        posts = []
        newlink = self.makemlink(link)
        is_loading = True
        if not last_post:
            wall0 = self.post_get(newlink, 0)
            wall1 = self.post_get(newlink, 1)
            if wall0['id'] > wall1['id']:
                return [wall0]
            else:
                return [wall1]
        offset = 0
        ids = []
        while is_loading:
            wall = self.post_get(newlink, offset)
            if wall:
                log(offset)
                if 'is_pinned' in wall.keys():
                    log(wall['is_pinned'])
                log(wall['id'])
                log(last_post)
                if wall['id'] not in ids:
                    ids.append(wall['id'])
                    if 'is_pinned' in wall.keys():
                        if wall['is_pinned']:
                            if wall['id'] > last_post:
                                posts.append(wall)
                    else:
                        if wall['id'] > last_post:
                            posts.append(wall)
                        else:
                            is_loading = False
                offset += 1

        return posts


    def post_get(self, sub_id, offset):
        '''if self.is_cached(sub_id, offset):
            return self.posts_cache[sub_id][offset]
        else:
            wall_raw = self.vk_session.method('wall.get', {'owner_id': sub_id, 'count': 1, 'offset': offset})
            if wall_raw:
                wall = wall_raw['items'][0]
                self.cache_update(sub_id, wall)
                return wall
            else:
                return {}'''
        wall_raw = self.vk_session.method('wall.get', {'owner_id': sub_id, 'count': 1, 'offset': offset})
        if wall_raw:
            try:
                wall = wall_raw['items'][0]
                return wall
            except Exception as e:
                log(e)
                log(wall_raw)


    def cache_update(self, sub_id, post):
        if not sub_id in self.posts_cache.keys():
            self.posts_cache.update({sub_id: []})
        self.posts_cache[sub_id].append(post)


    def is_cached(self, sub_id, offset):
        if sub_id in self.posts_cache.keys():
            if len(self.posts_cache[sub_id]) > offset:
                return True
            else:
                return False
        else:
            return False






