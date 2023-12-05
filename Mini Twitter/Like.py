from flask import g

class Like:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.user_id = kwargs.get('user_id', g.user.id)
        self.message_id = kwargs.get('message_id', 0)
        self.positive = 1
        if self.id == 0:
            self.validate()

    def validate(self):
        if self.user_id == 0:
            raise Exception('User ID cannot be empty')
        if self.message_id == 0:
            raise Exception('Message ID cannot be empty')

    def to_dict(self):
        data = {
            'user_id': self.user_id,
            'message_id': self.message_id,
            'positive': self.positive,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def save(self):
        if self.id == 0:
            self.id = g.database.insert_row('likes', self.to_dict())
        else:
            g.database.update_row('likes', self.to_dict(), where=" id = ? ", values=(self.id,))

    def delete(self):
        g.database.delete_rows('likes', where=" id = ? ", values=(self.id,))

    def get_user(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.user_id)

    def get_message(self):
        from Message import Message
        return Message.get_message(self.message_id)

    @staticmethod
    def get_like(id):
        row = g.database.get_row('likes', where=" id = ? ", values=(id,))
        if row is None:
            return None
        return Like.get_like_obj(row)
    
    @staticmethod
    def get_likes():
        return g.database.get_rows('likes', where=" positive = 1 ")
    
    @staticmethod
    def get_likes_by_user(user):
        rows = g.database.get_rows('likes', where=" user_id = ? and positive = 1 ", values=(user.id,))
        return [Like.get_like_obj(row) for row in rows]
    
    @staticmethod
    def get_likes_by_message(message):
        rows = g.database.get_rows('likes', where=" message_id = ? and positive = 1 ", values=(message.id,))
        return [Like.get_like_obj(row) for row in rows]
    
    @staticmethod
    def get_like_by_message_and_user(message, user):
        row = g.database.get_row('likes', where=" message_id = ? and user_id = ? and positive = 1 ", values=(message.id, user.id))
        return Like.get_like_obj(row)
    
    @staticmethod
    def get_like_obj(row):
        if row is None:
            return None
        return Like(**row)