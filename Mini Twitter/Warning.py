from datetime import datetime
from flask import g
from Message import Message
from OrdinaryUser import OrdinaryUser
from Comment import Comment

class Warning:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.user_id = kwargs.get('user_id', 0)
        self.reason = kwargs.get('reason', 'No reason provided.')
        self.fine = kwargs.get('fine', 0)
        self.reported_by_user_id = kwargs.get('reported_by_user_id', g.user.id if g.user.auth else 0)
        self.message_id = kwargs.get('message_id', 0)
        self.comment_id = kwargs.get('comment_id', 0)
        self.disputable = kwargs.get('disputable', 1)
        self.disputed = kwargs.get('disputed', 0)
        self.dispute_closed = kwargs.get('dispute_closed', 0)
        self.forgiven = kwargs.get('forgiven', 0)
        self.date = kwargs.get('date', datetime.now().strftime("%Y-%m-%d"))
        self.time = kwargs.get('time', datetime.now().strftime("%H:%M:%S"))
        self.type = "warning"
        if self.id == 0:
            self.validate()

    def validate(self):
        if self.user_id == 0:
            raise Exception('User ID cannot be empty')
        if self.reason == '':
            raise Exception('Reason cannot be empty')
        if self.fine < 0:
            raise Exception('Fine cannot be negative')
        if self.get_user().super == 1:
            raise Exception('Cannot warn a super user')

    def to_dict(self):
        data = {
            'reason': self.reason,
            'fine': self.fine,
            'type': self.type,
            'reported_by_user_id': self.reported_by_user_id,
            'message_id': self.message_id,
            'comment_id': self.comment_id,
            'user_id': self.user_id,
            'disputable': self.disputable,
            'disputed': self.disputed,
            'dispute_closed': self.dispute_closed,
            'forgiven': self.forgiven,
            'date': self.date,
            'time': self.time,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def save(self):
        if self.id == 0:
            self.id = g.database.insert_row('warnings', self.to_dict())
            if self.fine > 0:
                self.get_user().charge_money(self.fine, explanation = "Fine for warning", force_charge = True)
        else:
            g.database.update_row('warnings', self.to_dict(), where=" id = ? ", values=(self.id,))
        return self.id
    
    def delete(self):
        g.database.delete_rows('warnings', where=" id = ? ", values=(self.id,))

    def forgive(self, refund = True):
        self.forgiven = 1
        self.dispute_closed = 1
        self.save()
        if self.fine > 0 and refund:
            self.get_user().deposit_money(self.fine, explanation = "Refund for forgiven warning")

    def dispute(self):
        self.disputed = 1
        self.save()

    def close_dispute(self):
        self.dispute_closed = 1
        self.save()

    def get_user(self):
        return OrdinaryUser.get_user(self.user_id)
    
    def get_reported_by_user(self):
        if self.reported_by_user_id == 0:
            return None
        return OrdinaryUser.get_user(self.reported_by_user_id)
    
    def account_for_penalty(self):
        '''
        States:
        Forgiven - no
        Undisputable - yes
        Disputed, pending answer - no
        Disputed, not forgiven - yes
        Not disputed and after 24 hours - yes
        Not disputed and in the first 24 hours - no
        '''
        if self.forgiven == 1:
            return False
        if self.disputable == 0:
            return True
        if self.disputed == 1:
            if self.dispute_closed == 0:
                return False
            return True
        if self.disputed == 0:
            if self.older_than_one_hour():
                return True
            return False
        return True
        
    def older_than_one_hour(self):
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        difference_in_hours = (datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S") - datetime.strptime(f"{self.date} {self.time}", "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600
        if difference_in_hours > 1:
            return True
        return False

    @staticmethod
    def get_warning(id):
        row = g.database.get_row('warnings', where=" id = ? ", values=(id,))
        return Warning.get_warning_obj(row)
    
    @staticmethod
    def get_warnings():
        rows = g.database.get_rows('warnings')
        return [Warning.get_warning_obj(row) for row in rows]
    
    @staticmethod
    def get_warning_obj(row):
        if row is None:
            return None
        if row['type'] == 'comment_warning':
            from CommentWarning import CommentWarning
            return CommentWarning(**row)
        if row['type'] == 'message_warning':
            from MessageWarning import MessageWarning
            return MessageWarning(**row)
        if row['type'] == 'profile_warning':
            from ProfileWarning import ProfileWarning
            return ProfileWarning(**row)
        return Warning(**row)
    
    @staticmethod
    def get_warnings_by_user(user):
        rows = g.database.get_rows('warnings', where=" user_id = ? ", values=(user.id,))
        return [Warning.get_warning_obj(row) for row in rows]
    
    @staticmethod
    def get_warnings_by_reported_by_user(user):
        rows = g.database.get_rows('warnings', where=" reported_by_user_id = ? ", values=(user.id,))
        return [Warning.get_warning_obj(row) for row in rows]