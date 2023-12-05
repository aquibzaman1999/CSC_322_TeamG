from datetime import datetime
from flask import g

class Payment:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.payment_amount = kwargs.get('payment_amount', 0)
        self.user_id = kwargs.get('user_id', g.user.id)
        self.explanation = kwargs.get('explanation', 'No explanation provided.')
        self.date = kwargs.get('date', datetime.now().strftime("%Y-%m-%d"))
        if self.id == 0:
            self.validate()

    def validate(self):
        if self.user_id == 0:
            raise Exception('User ID cannot be empty')
        if self.payment_amount == 0:
            raise Exception('Payment amount cannot be empty')
    
    def to_dict(self):
        data = {
            'user_id': self.user_id,
            'payment_amount': self.payment_amount,
            'explanation': self.explanation,
            'date': self.date,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def save(self):
        if self.id == 0:
            self.id = g.database.insert_row('payments', self.to_dict())
        else:
            g.database.update_row('payments', self.to_dict(), where=" id = ? ", values=(self.id,))


    def get_user(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.user_id)
    
    @staticmethod
    def validate_card_information(card_number, expiration_month, expiration_year, cvv):
        if len(card_number) != 16:
            raise Exception('Invalid card number.')
        if len(expiration_month) != 2:
            raise Exception('Invalid expiration month.')
        if len(expiration_year) != 2:
            raise Exception('Invalid expiration year.')
        if len(cvv) != 3:
            raise Exception('Invalid CVV.')
        month = int(expiration_month)
        year = int(expiration_year)
        if month < 1 or month > 12:
            raise Exception('Invalid expiration month.')
        if year < 0 or year > 99:
            raise Exception('Invalid expiration year.')
        today = datetime.now()
        if year < today.year % 100 or (year == today.year % 100 and month < today.month):
            raise Exception('Card is expired.')
        return True

    @staticmethod
    def get_payment(id):
        row = g.database.get_row('payments', where=" id = ? ", values=(id,))
        return Payment.get_payment_obj(row)
    
    @staticmethod
    def get_payments():
        rows = g.database.get_rows('payments')
        return [Payment.get_payment_obj(row) for row in rows]
    
    @staticmethod
    def get_payments_by_user(user):
        rows = g.database.get_rows('payments', where=" user_id = ? ", values=(user.id,))
        return [Payment.get_payment_obj(row) for row in rows]
    
    @staticmethod
    def get_payment_obj(row):
        if row is None:
            return None
        return Payment(**row)

        