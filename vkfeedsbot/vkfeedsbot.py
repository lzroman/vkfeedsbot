import vk_api
from telegram.ext import Updater, CommandHandler, ConversationHandler, Filters, MessageHandler
import json, time, datetime
from tghandlers import TGHandlers
from logger import log

class vkfeedsbot:
    def __init__(self, path):
        log('Read config')
        with open(path, 'r') as f:
                self.conf = json.load(f)

        self.connect_vk()
        self.connect_tg()
        self.handlers()



    def connect_vk(self):
        #self._app_id = "2685278"
        #self._vk_client_secret = "hHbJug59sKJie78wjrH8"
        self._app_id = "7509973"
        self._vk_client_secret = "UQd8ulQ1AsOIo0Rw0KWN"
        log('Connecting VK…')
        self.vk_session = vk_api.VkApi(token=self.conf['token_vk'], app_id=self._app_id, client_secret=self._vk_client_secret)
        log('…Done!')

    def connect_tg(self):
        log('Connecting Telegram…')
        self.handlers_o = TGHandlers(self.conf, self.vk_session)
        log('…Done!')

    def handlers(self):
        self.handlers_o.handlers()

bot = vkfeedsbot('config.json')
