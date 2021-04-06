from telegram.ext import Updater, CommandHandler, ConversationHandler, Filters, MessageHandler
import json, time, datetime
import telegram
import dbase
from status import statuses
from vkworker import VKWorker
from logger import log
import vk_api, telegram
from threading import Thread
from parsing import Parser
from datetime import datetime

class TGHandlers:
    def __init__(self, conf, vk_session):
        self.path = 'db.json'

        try:
            self.tg_updater = Updater(token=conf['token_tg'], use_context=True)
            self.tg_updater.start_polling()
            time.sleep(5)
            self.tg_updater.stop()
        except Exception as e:
            log('Failed to connect, start using proxy…')
            #self.tg_updater = Updater(token=conf['token_tg'], use_context=True, request_kwargs={'proxy_url': 'http://zabavno:gR1bO4ek@185.246.153.144:41488'})
            self.tg_updater = Updater(token=conf['token_tg'], use_context=True)
            self.tg_updater.start_polling()
            time.sleep(5)
            self.tg_updater.stop()

        # self.tg_updater = Updater(token=conf['token_tg'], use_context=True, request_kwargs={'proxy_url': 'http://zabavno:gR1bO4ek@185.246.153.144:41488'})
        self.dispatcher = self.tg_updater.dispatcher
        self.db = dbase.DBase()
        self.db.loaddb(self.path)
        self.vk = VKWorker(vk_session)
        self.parser = Parser()
        self.sleep_time = 60
        self.bot = self.tg_updater.bot
        self.subs_max = 10


    def handlers(self):

        
        '''self.conv_handler = ConversationHandler(entry_points=[CommandHandler('start0', self.start0)],
                                                states={0: [MessageHandler(Filters.sticker, self.s0),CommandHandler('stop',self.s01)],
                                                        1: [MessageHandler(Filters.text, self.s1)]
                                                },
                                                fallbacks=[CommandHandler('cancel', self.cancel)])
        self.dispatcher.add_handler(self.conv_handler)'''

        self.copysubs_handler = ConversationHandler(entry_points=[CommandHandler('copysubs', self.copysubs0)],
                                                states={0: [MessageHandler(Filters.text, self.copysubs1)]
                                                },
                                                fallbacks=[CommandHandler('cancel', self.cancel)])
        self.dispatcher.add_handler(self.copysubs_handler)
        self.start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(self.start_handler)

        self.addsub_handler = ConversationHandler(entry_points=[CommandHandler('addsub', self.addsub0)],
                                                states={0: [MessageHandler(Filters.text, self.addsub1)]
                                                },
                                                fallbacks=[CommandHandler('cancel', self.cancel)])
        self.dispatcher.add_handler(self.addsub_handler)

        self.rmsub_handler = ConversationHandler(entry_points=[CommandHandler('rmsub', self.rmsub0)],
                                                states={0: [MessageHandler(Filters.text, self.rmsub1)]
                                                },
                                                fallbacks=[CommandHandler('cancel', self.cancel)])
        self.dispatcher.add_handler(self.rmsub_handler)

        self.setmaxtext_handler = ConversationHandler(entry_points=[CommandHandler('setmaxtext', self.setmaxtext0)],
                                                states={0: [MessageHandler(Filters.text, self.setmaxtext1)]
                                                },
                                                fallbacks=[CommandHandler('cancel', self.cancel)])
        self.dispatcher.add_handler(self.setmaxtext_handler)

        self.showsubs_handler = CommandHandler('showsubs', self.showsubs)
        self.dispatcher.add_handler(self.showsubs_handler)

        self.emptysubs_handler = CommandHandler('emptysubs', self.emptysubs)
        self.dispatcher.add_handler(self.emptysubs_handler)

        self.help_handler = CommandHandler('help', self.help)
        self.dispatcher.add_handler(self.help_handler)


        log('start handling')
        self.tg_updater.start_polling()

        self.sender_thread = Thread(target=self.sender)
        self.sender_thread.start()


    def cancel(self, update, context):
        return ConversationHandler.END


    def sender(self): # main function
        while True:
            log('feeds')
            for user in list(self.db.userlist.keys()):
                for sub in self.db.userlist[user].subs.values():
                    posts = self.vk.get_posts(sub.id, sub.last_post)
                    if len(posts):
                        posts = sorted(posts, key = lambda i: i['id'])
                        self.db.userlist[user].subs[sub.id].last_post = posts[-1]['id']
                        sub_data = self.vk.makesub(sub.id)
                        for post in posts:
                            self.posts_send(user, post, sub, sub_data)

            self.db.savedb(self.path)
            self.vk.clear_posts_cache()
            time.sleep(self.sleep_time)


    def setmaxtext0(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Send me max size limit (integer).')
        return 0
    
    def setmaxtext1(self, update, context):
        if update.effective_message.text.isdigit():
            val = int(update.effective_message.text)
            if val == 0:
                self.db.userlist[update.effective_user.id].maxtext = val
                context.bot.send_message(chat_id=update.effective_chat.id, text='Text limit is off.')
                self.db.savedb(self.path)
            elif val > 0:
                self.db.userlist[update.effective_user.id].maxtext = val
                context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(['Text limit is ', str(val), '.']))
                self.db.savedb(self.path)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='Wrong value.')
        return ConversationHandler.END


    def copysubs0(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Send me link to your page.')
        return 0
    
    def copysubs1(self, update, context):
        ans = {}
        try:
            ans = self.vk.resolve_link(self.makelink(update.effective_message.text))
        except Exception as e:
            log(''.join(['fail: ', e]))
        if len(ans):
            if ans['type'] == 'user':
                user = self.vk.get_user(ans['object_id'])
                name = user['first_name']
                if user['is_closed']:
                    context.bot.send_message(chat_id=update.effective_chat.id, text=''.join([name, ', account is private, can\'t access subs list.']))
                else:
                    context.bot.send_message(chat_id=update.effective_chat.id, text='Please, wait, reading data..')
                    failed = False
                    failed_text = "Some subs are closed/private and can't be added:\n"
                    subs = self.vk.get_user_subs(ans['object_id'])
                    log(subs)
                    text = "Your subs are ready!\n"
                    for sub in subs:
                        #print(text)
                        if sub['is_closed']:
                            failed = True
                            failed_text = ''.join([failed_text, '[', sub['name'], '](https://vk.com/', sub['id'], ')\n'])
                        else:
                            if len(self.db.userlist[update.effective_user.id].subs) > self.subs_max:
                                break
                            else:
                                self.db.user_add_sub(update.effective_user.id, sub['id'])
                                text = ''.join([text, '[', sub['name'], '](https://vk.com/', sub['id'], ')\n'])
                    if failed:
                        text = '\n'.join([text, failed_text])
                    context.bot.send_message(chat_id=update.effective_chat.id, text=text,parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
                    self.db.savedb(self.path)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='Not user link!')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Incorrect link!')
        return ConversationHandler.END


    def rmsub0(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Send me link to remove.')
        return 0
    
    def rmsub1(self, update, context):
        try:
            ans = self.vk.resolve_link(self.makelink(update.effective_message.text))
        except Exception as e:
            log(''.join(['fail: ', e]))
            context.bot.send_message(chat_id=update.effective_chat.id, text='Wrong link.')
            return ConversationHandler.END
        if not len(ans):
            context.bot.send_message(chat_id=update.effective_chat.id, text='Wrong link.')
            return ConversationHandler.END

        if ans['type'] == 'user':
            name = ''.join(['id', str(ans['object_id'])])
        else:
            name = ''.join(['public', str(ans['object_id'])])
        result = self.vk.get_sub(name)
        result_rm = self.db.user_rm_sub(update.effective_chat.id, name)
        if result_rm == 'done':
            context.bot.send_message(chat_id=update.effective_chat.id,text=''.join(['[', result['name'], '](https://vk.com/', result['id'], ') is removed.']),parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
            self.db.savedb(self.path)
        elif result_rm == 'already':
            context.bot.send_message(chat_id=update.effective_chat.id,text=''.join(['[', result['name'], '](https://vk.com/', result['id'], ') is not in your list.']),parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='You are not registered.')
        return ConversationHandler.END


    def addsub0(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Send me link to add.')
        return 0
    
    def addsub1(self, update, context):
        if len(self.db.userlist[update.effective_user.id].subs) > self.subs_max:
            context.bot.send_message(chat_id=update.effective_chat.id, text='You\'ve reached maximum of subs.')
        else:
            try:
                ans = self.vk.resolve_link(self.makelink(update.effective_message.text))
            except Exception as e:
                log(''.join(['fail: ', e]))
                context.bot.send_message(chat_id=update.effective_chat.id, text='Wrong link.')
                return ConversationHandler.END
            if not len(ans):
                context.bot.send_message(chat_id=update.effective_chat.id, text='Wrong link.')
                return ConversationHandler.END

            if ans['type'] == 'user':
                name = ''.join(['id', str(ans['object_id'])])
            else:
                name = ''.join(['public', str(ans['object_id'])])
            result = self.vk.get_sub(name)
            result_rm = self.db.user_add_sub(update.effective_chat.id, name)
            if result_rm == 'done':
                context.bot.send_message(chat_id=update.effective_chat.id,text=''.join(['[', result['name'], '](https://vk.com/', result['id'], ') is added.']),parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
                self.db.savedb(self.path)
            elif result_rm == 'already':
                context.bot.send_message(chat_id=update.effective_chat.id,text=''.join(['[', result['name'], '](https://vk.com/', result['id'], ') is already in your list.']),parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='You are not registered.')
        return ConversationHandler.END



    def help(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text='''Hi! I'm @vkfeedsbot, and I can send you news from VK.\n
To add sub from page use /addsub and send me link you want to follow.
To copy subs from page use /copysubs and send me link you want to copy subs from.
To remove sub use /rmsub and send me link you want to remove.
To set max text length to send sub use /setmaxtext and send me value (integer). If 0, limit is off.
To show all your subs use /showsubs.
To empty your subs list use /emptysubs.\n
If you have any questions, suggestions or you've found bugs, please write me @vasilyan.''')


    def emptysubs(self, update, context):
        if self.db.emptysubs(int(update.effective_user.id)) == 'done':
            self.db.savedb(self.path)
            context.bot.send_message(chat_id=update.effective_chat.id, text='Your subs list is empty.')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='You are not registered. Please send /start.') 


    def showsubs(self, update, context):
        if update.effective_chat.id in self.db.userlist:
            text = 'Your subs:\n'
            subs = self.vk.get_subs(self.db.userlist[update.effective_chat.id].get_subs())
            if len(subs):
                for sub in subs:
                    text = ''.join([text, '[', sub['name'], '](https://vk.com/', str(sub['id']), ')\n'])
                context.bot.send_message(chat_id=update.effective_chat.id, text=text,parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='You have no subs.')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='You are not registered. Please send /start.')
    


    def start(self, update, context):
        log(''.join(['new start: ',str(update.effective_user.id), ', ', str(update.effective_user.first_name)]))
        if self.db.add_user(int(update.effective_user.id)) == 'done':
            self.db.savedb(self.path)
            context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(["Hi, ", str(update.effective_user.first_name), '''Hi! I'm @vkfeedsbot, and I can send you news from VK.\n
To add sub from page use /addsub and send me link you want to follow.
To copy subs from page use /copysubs and send me link you want to copy subs from.
To remove sub use /rmsub and send me link you want to remove.
To set max text length to send sub use /setmaxtext and send me value (integer). If 0, limit is off.
To show all your subs use /showsubs.
To empty your subs list use /emptysubs.\n
If you have any questions, suggestions or you've found bugs, please write me @vasilyan.''']))
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(["Nice to see you again, ", str(update.effective_user.first_name), '!']))


    def makelink(self, link):
        pos = link.rfind('/')
        if pos != -1:
            return link[pos + 1:]
        else:
            return link


    def posts_send(self, uid, post, sub, sub_data):
        text = ''.join([sub_data, '\n[',
                        str(datetime.fromtimestamp(post['date'])), '](https://vk.com/wall',
                        str(self.vk.makemlink(sub.id)), '_', str(post['id']), ')\n\n'])
        if 'attachments' in post.keys():
            attachments = self.parser.attachments(post)
            att_added = False
            for key in attachments.keys():
                if key != 'photo' and key != 'video' and key != 'album':
                    if not att_added:
                        text = ''.join([text, 'Attachments:\n\n'])
                        att_added = True
                    for att in attachments[key]:
                        text = ''.join([text, att['text'], '\n'])
            self.send_text(uid, text)
            self.send_text_noparse(uid, post['text'])


            if 'photo' in attachments.keys():
                if len(attachments['photo']) == 1:
                    self.bot.send_photo(chat_id=uid, photo=attachments['photo'][0]['preview'])
                else:
                    media = []
                    for att in attachments['photo']:
                        media.append(telegram.InputMediaPhoto(att['preview']))
                    self.bot.send_media_group(chat_id=uid, media=media)

            if 'video' in attachments.keys():
                if len(attachments['video']) == 1:
                    self.bot.send_message(chat_id=uid, text=''.join(['Video:\n',attachments['video'][0]['text']]),parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
                    self.bot.send_photo(chat_id=uid, photo=attachments['video'][0]['preview'])
                else:
                    text = 'Videos:\n'
                    media = []
                    for att in attachments['video']:
                        text = ''.join([text, att['text'], '\n'])
                        media.append(telegram.InputMediaPhoto(att['preview']))
                    self.bot.send_message(chat_id=uid, text=text,parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
                    self.bot.send_media_group(chat_id=uid, media=media)

        else:
            if self.db.userlist[uid].maxtext:
                text = ''.join([text, post['text'][:self.db.userlist[uid].maxtext], '…'])
            else:
                text = ''.join([text, post['text']])
            self.send_text(uid, text)
        if 'copy_history' in post.keys():
            if len(post['copy_history']):
                self.bot.send_message(chat_id=uid, text='This post contains repost:')
                self.posts_send(uid, post['copy_history'][0], sub, sub_data)
                    

    def send_text(self, uid, rawtext):
        if len(rawtext):
            if len(rawtext) < 4097:
                self.bot.send_message(chat_id=uid, text=rawtext,parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)
            else:
                data = []
                while len(rawtext) > 4096:
                    data.append(rawtext[:4096])
                    rawtext = rawtext[4096:]
                data.append(rawtext)
                for text in data:
                    self.bot.send_message(chat_id=uid, text=text,parse_mode=telegram.ParseMode.MARKDOWN,disable_web_page_preview=True)

    def send_text_noparse(self, uid, rawtext):
        if len(rawtext):
            if self.db.userlist[uid].maxtext:
                rawtext = ''.join([rawtext[:self.db.userlist[uid].maxtext], '…'])
            if len(rawtext) < 4097:
                self.bot.send_message(chat_id=uid, text=rawtext,disable_web_page_preview=True)
            else:
                data = []
                while len(rawtext) > 4096:
                    data.append(rawtext[:4096])
                    rawtext = rawtext[4096:]
                data.append(rawtext)
                for text in data:
                    self.bot.send_message(chat_id=uid, text=text,disable_web_page_preview=True)
