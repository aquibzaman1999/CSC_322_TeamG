from OrdinaryUser import OrdinaryUser
from flask import g

class CorporateUser(OrdinaryUser):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.corporate = 1
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()

    def accept_application(self, application):
        if application.answered == 1:
            raise Exception('Application already answered')
        application.accept()
        for other_application in application.get_message().get_applications():
            if other_application.id != application.id:
                other_application.deny()
        return application

    def reject_application(self, application):
        if application.answered == 1:
            raise Exception('Application already answered')
        application.deny()
        return application

    def get_applications(self, message_ad = None):
        if message_ad is None:
            from MessageJobAd import MessageJobAd
            return MessageJobAd.get_applications(self)
        job_ads = self.get_job_ads()
        applications = []
        for job_ad in job_ads:
            applications += job_ad.get_applications()
        return applications

    def get_ads(self):
        from MessageAd import MessageAd
        return MessageAd.get_ads_by_author(self)

    def get_job_ads(self):
        from MessageJobAd import MessageJobAd
        return MessageJobAd.get_job_ads_by_author(self)