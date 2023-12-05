from flask import g, session
from Config import MAX_COMMENT_LENGTH

class Comment:
    def __init__(self,**kwargs):
        self.id = kwargs.get('id', 0)
        self.user_id = kwargs.get('user_id', g.user.id)
        self.comment = kwargs.get('comment', '')
        self.message_id = kwargs.get('message_id', 0)
        self.reported = kwargs.get('reported', 0)
        if not self.id:
            self.validate()

    def validate(self):
        if len(self.comment) < 1:
            raise Exception('Comment cannot be empty')
        if len(self.comment) > MAX_COMMENT_LENGTH:
            raise Exception(f'Comment cannot be longer than {MAX_COMMENT_LENGTH} characters')
        if not self.message_id:
            raise Exception('Message ID cannot be empty')

    def to_dict(self):
        data = {
            'user_id': self.user_id,
            'message_id': self.message_id,
            'comment': self.comment,
            'reported': self.reported,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def save(self):
        if self.id == 0:
            self.id = g.database.insert_row('comments', self.to_dict())
        else:
            g.database.update_row('comments', self.to_dict(), where=" id = ? ", values=(self.id,))

    def delete(self):
        if not self.can_be_deleted():
            raise Exception('Message cannot be deleted')
        g.database.delete_rows('comments', where=" id = ? ", values=(self.id,))

    def get_author(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.user_id)
    
    def get_message(self):
        from Message import Message
        return Message.get_message(self.message_id)
    
    def get_warnings(self):
        from CommentWarning import CommentWarning
        return CommentWarning.get_warnings_by_comment(self)
    
    def can_be_deleted(self):
        if not g.auth or not (g.user.super == 1 or g.user.id == self.user_id):
            return False
        for warning in self.get_warnings():
            if warning.disputed == 1 and warning.dispute_closed == 0:
                return False
        return False
    
    def can_be_reported(self):
        if self.get_author().super == 1:
            return False
        if not g.auth:
            temp = session['reports']
            for report in temp:
                if report['type'] == 'comment' and report['id'] == self.id:
                    return False
            return True 
        if g.user.id == self.user_id:
            return False
        for warning in self.get_warnings():
            if warning.reported_by_user_id == g.user.id:
                return False
        return True
    
    def mark_reported(self):
        self.reported = 1
        self.save()

    def mark_forgiven(self):
        self.reported = 0
        self.save()

    @staticmethod
    def get_comment(id):
        row = g.database.get_row('comments', where=" id = ? ", values=(id,))
        if row is None:
            return None
        return Comment.get_comment_obj(row)
    
    @staticmethod
    def get_comments():
        rows = g.database.get_rows('comments')
        return [Comment.get_comment_obj(row) for row in rows]
    
    @staticmethod
    def get_comments_by_message(message):
        rows = g.database.get_rows('comments', where=" message_id = ? ", values=(message.id,))
        return [Comment.get_comment_obj(row) for row in rows]

    @staticmethod
    def get_comments_by_user(user):
        rows = g.database.get_rows('comments', where=" user_id = ? ", values=(user.id,))
        return [Comment.get_comment_obj(row) for row in rows]
    
    @staticmethod
    def get_comment_obj(row):
        return Comment(**row)
    