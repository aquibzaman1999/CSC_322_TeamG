from Message import Message
from flask import g

class MessageJobAd(Message):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ad = 1
        self.job_ad = 1
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()

    def delete(self):
        super().delete()
        g.database.delete_rows('job_applications', where=" message_id = ? ", values=(self.id,))

    def get_applications(self):
        from JobApplication import JobApplication
        return JobApplication.get_applications_by_message(self)

    @staticmethod
    def get_job_ads():
        rows = g.database.get_rows('messages', where=" job_ad = 1 ")
        return [Message.get_message_obj(row) for row in rows]
    
    @staticmethod
    def get_job_ads_by_author(user):
        rows = g.database.get_rows('messages', where=" author_id = ? AND job_ad = 1 ", values=(user.id,))
        return [Message.get_message_obj(row) for row in rows]