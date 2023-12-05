from flask import g

class JobApplication():
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.user_id = kwargs.get('user_id', 0)
        self.message_id = kwargs.get('message_id', 0)
        self.answered = kwargs.get('answered', 0)
        self.accepted = kwargs.get('accepted', 0)
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
            'answered': self.answered,
            'accepted': self.accepted,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def save(self):
        if self.id == 0:
            self.id = g.database.insert_row('job_applications', self.to_dict())
        else:
            g.database.update_row('job_applications', self.to_dict(), where=" id = ? ", values=(self.id,))

    def delete(self):
        g.database.delete_rows('job_applications', where=" id = ? ", values=(self.id,))

    def accept(self):
        self.accepted = 1
        self.answered = 1
        self.save()

    def deny(self):
        self.accepted = 0
        self.answered = 1
        self.save()

    def get_user(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.user_id)
    
    def get_message(self):
        from Message import Message
        return Message.get_message(self.message_id)
    
    @staticmethod
    def get_job_application(id):
        row = g.database.get_row('job_applications', where=" id = ? ", values=(id,))
        return JobApplication.get_job_application_obj(row)
    
    @staticmethod
    def get_job_applications():
        rows = g.database.get_rows('job_applications')
        return [JobApplication.get_job_application_obj(row) for row in rows]
    
    @staticmethod
    def get_job_applications_by_user(user):
        rows = g.database.get_rows('job_applications', where=" user_id = ? ", values=(user.id,))
        return [JobApplication.get_job_application_obj(row) for row in rows]
    
    @staticmethod
    def get_applications_by_message(message):
        rows = g.database.get_rows('job_applications', where=" message_id = ? ", values=(message.id,))
        return [JobApplication.get_job_application_obj(row) for row in rows]

    @staticmethod
    def get_job_application_obj(row):
        if row is None:
            return None
        return JobApplication(**row)
    