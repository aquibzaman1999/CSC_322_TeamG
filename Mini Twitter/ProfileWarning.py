from datetime import datetime
from OrdinaryUser import OrdinaryUser
from Warning import Warning
from Comment import Comment
from flask import g

class ProfileWarning(Warning):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "profile_warning"
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()

    def save(self):
        if self.id == 0:
            user = OrdinaryUser.get_user(self.user_id)
            user.mark_reported()
        super().save()

    def forgive(self):
        super().forgive()
        user = OrdinaryUser.get_user(self.user_id)
        user.mark_forgiven()

    def get_profile(self):
        return OrdinaryUser.get_user(self.user_id)
    
    @staticmethod
    def get_warnings_by_profile(profile):
        warnings = []
        for warning in g.database.get_rows('warnings', where=" user_id = ? ", values=(profile.id,)):
            warnings.append(ProfileWarning(**warning))
        return warnings 
