from flask import g

class Tip:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.author_id = kwargs.get('author_id', 0)
        self.amount = kwargs.get('amount', 0)
        self.user_id = kwargs.get('user_id', g.user.id)
        if self.id == 0:
            self.validate()

    def validate(self):
        if self.author_id == 0:
            raise Exception('Author ID cannot be empty')
        if self.amount <= 0:
            raise Exception('Amount has to be greater than 0')
        if self.user_id == 0:
            raise Exception('User ID cannot be empty')

    def to_dict(self):
        data = {
            'user_id': self.user_id,
            'author_id': self.author_id,
            'amount': self.amount,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def save(self):
        if self.id == 0:
            self.id = g.database.insert_row('tips', self.to_dict())
        else:
            g.database.update_row('tips', self.to_dict(), where=" id = ? ", values=(self.id,))
    
    def delete(self):
        g.database.delete_rows('tips', where=" id = ? ", values=(self.id,))

    def get_user(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.user_id)
    
    def get_author(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.author_id)

    @staticmethod
    def get_tip(id):
        row = g.database.get_row('tips', where=" id = ? ", values=(id,))
        if row is None:
            return None
        return Tip.get_tip_obj(row)
    
    @staticmethod
    def get_tips():
        return g.database.get_rows('tips')
    
    @staticmethod
    def get_tips_by_user(user):
        rows = g.database.get_rows('tips', where=" user_id = ? ", values=(user.id,))
        return [Tip.get_tip_obj(row) for row in rows]
    
    @staticmethod
    def get_tips_by_author(author):
        rows = g.database.get_rows('tips', where=" author_id = ? ", values=(author.id,))
        return [Tip.get_tip_obj(row) for row in rows]

    @staticmethod
    def get_tip_obj(row):
        if row is None:
            return None
        return Tip(
            row['author_id'],
            row['amount'],
            **row
        )