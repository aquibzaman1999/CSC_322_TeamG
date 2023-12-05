from CorporateUser import CorporateUser
from flask import g

class SuperUser(CorporateUser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.super = 1

    def charge_money(self, *args, **kwargs):
        return True

    def add_taboo_word(self, word):
        if word == '':
            raise Exception('Word cannot be empty')
        g.database.insert_row('taboo_words', {
            'word': word,
        })
        return word

    def remove_taboo_word(self, taboo_word_id):
        g.database.delete_rows('taboo_words', where=" id = ? ", values=(taboo_word_id,))
        return True

    def accept_user(self, user):
        if user.reviewed == 1:
            raise Exception('User already reviewed')
        user.reviewed = 1
        user.save()
        return user 

    def reject_user(self, user, reason):
        if user.reviewed == 1:
            raise Exception('User already reviewed')
        user.reviewed = 1
        user.denied = 1
        user.reason = reason
        user.save()
        return user
    
    def delete_user(self, user):
        if user.super == 1:
            raise Exception('Cannot delete super user')
        user.delete()
        return True

    def forgive_warning(self, warning):
        if warning.dispute_closed == 1:
            raise Exception('Warning already forgiven')
        if warning.disputed == 0:
            raise Exception('Warning not disputed')
        warning.forgive()
        return warning

    def close_dispute(self, warning):
        if warning.dispute_closed == 1:
            raise Exception('Warning already forgiven')
        if warning.disputed == 0:
            raise Exception('Warning not disputed')
        warning.close_dispute()
        return warning
