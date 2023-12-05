from Message import Message
from flask import g

class MessageAd(Message):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ad = 1
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()

    @staticmethod
    def get_ads():
        rows = g.database.get_rows('messages', where=" ad = 1 AND job_ad = 0 ")
        return [Message.get_message_obj(row) for row in rows]
    
    @staticmethod
    def get_ads_by_author(user):
        rows = g.database.get_rows('messages', where=" author_id = ? AND ad = 1 AND job_ad = 0 ", values=(user.id,))
        return [Message.get_message_obj(row) for row in rows]