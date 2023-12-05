from Like import Like
from flask import g

class Dislike(Like):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.positive = 0
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()

    @staticmethod
    def get_dislike(id):
        row = g.database.get_row('likes', where=" id = ? ", values=(id,))
        if row is None:
            return None
        return Dislike.get_dislike_obj(row)
    
    @staticmethod
    def get_dislikes():
        return g.database.get_rows('likes', where=" positive = 0 ")
    
    @staticmethod
    def get_dislikes_by_user(user):
        rows = g.database.get_rows('likes', where=" user_id = ? and positive = 0 ", values=(user.id,))
        return [Dislike.get_like_obj(row) for row in rows]
    
    @staticmethod
    def get_dislikes_by_message(message):
        rows = g.database.get_rows('likes', where=" message_id = ? and positive = 0 ", values=(message.id,))
        return [Dislike.get_like_obj(row) for row in rows]
    
    @staticmethod
    def get_dislike_by_message_and_user(message, user):
        row = g.database.get_row('likes', where=" message_id = ? and user_id = ? and positive = 0 ", values=(message.id, user.id))
        return Dislike.get_dislike_obj(row)
    
    @staticmethod
    def get_dislike_obj(row):
        if row is None:
            return None
        return Dislike(**row)