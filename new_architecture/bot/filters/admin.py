import os
from telebot import SimpleCustomFilter
from telebot.types import Message
from new_architecture.bot.exec import bot


class IsAdminSimpleFilter(SimpleCustomFilter):
    key = "IsAdmin"

    def check(self, update: Message) -> bool:
        return str(update.chat.id) in os.getenv("ADMINS").split(sep=",")


bot.add_custom_filter(IsAdminSimpleFilter())