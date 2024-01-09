from telebot import TeleBot
from telebot.types import Message
from telebot.handler_backends import BaseMiddleware, CancelUpdate
from new_architecture.bot.exec import bot



class DeleteMessagesMiddleware(BaseMiddleware):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.update_types = ['message']
        # Always specify update types, otherwise middlewares won't work

    def pre_process(self, message: Message):
        pass

    def post_process(self, message: Message):
        bot.delete_message(chat_id= message.chat.id,
                           message_id= message.id)

bot.setup_middleware(DeleteMessagesMiddleware())