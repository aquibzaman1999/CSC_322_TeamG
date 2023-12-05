from datetime import datetime
from Warning import Warning
from Message import Message
from flask import g

class MessageWarning(Warning):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "message_warning"
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()
        if self.message_id == 0:
            raise Exception('Message ID cannot be empty')

    def save(self):
        if self.id == 0:
            message = Message.get_message(self.message_id)
            message.mark_reported()
        super().save()

    def forgive(self):
        super().forgive()
        message = Message.get_message(self.message_id)
        message.mark_forgiven()

    def get_message(self):
        return Message.get_message(self.message_id)
    
    @staticmethod
    def get_warnings_by_message(message):
        warnings = []
        for warning in g.database.get_rows('warnings', where=" message_id = ? ", values=(message.id,)):
            warnings.append(MessageWarning(**warning))
        return warnings 
