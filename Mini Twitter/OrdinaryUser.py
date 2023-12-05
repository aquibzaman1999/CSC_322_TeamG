from flask import g, session
from User import User
from File import File
import random

class OrdinaryUser(User):
    def __init__(self, **kwargs):
        super().__init__()
        self.auth = True
        self.username = kwargs.get('username', "")
        self.fullname = kwargs.get('fullname', "")
        self.bio = kwargs.get('bio', "")
        profile_picture = kwargs.get('profile_picture', "")
        self.profile_picture = File(filename=profile_picture) if profile_picture != "" else None
        self.id = kwargs.get('id', 0)
        self.password = kwargs.get('password', "")
        self.salt = kwargs.get('salt', "")
        self.reviewed = kwargs.get('reviewed', 0)
        self.denied = kwargs.get('denied', 0)
        self.reason = kwargs.get('reason', "")
        self.balance = kwargs.get('balance', 0)
        self.first_password_changed = kwargs.get('first_password_changed', 0)
        self.first_payment_done = kwargs.get('first_payment_done', 0)
        self.reported = kwargs.get('reported', 0)
        self.demoted = kwargs.get('demoted', 0)
        self.super = 0
        self.corporate = 0
        if self.id == 0:
            self.validate()

    def validate(self):
        if self.username == '':
            raise Exception('Username cannot be empty')
        if OrdinaryUser.get_user_by_username(self.username) is not None:
            raise Exception('Username already exists')
        if self.fullname == '':
            raise Exception('Full name cannot be empty')
        if self.password == '':
            raise Exception('Password cannot be empty')
        if self.salt == '':
            raise Exception('Salt cannot be empty')
        if self.balance < 0:
            raise Exception('Balance cannot be negative')

    def to_dict(self):
        data = {
            'username': self.username,
            'fullname': self.fullname,
            'bio': self.bio,
            'password': self.password,
            'salt': self.salt,
            'reviewed': self.reviewed,
            'denied': self.denied,
            'reason': self.reason,
            'balance': self.balance,
            'profile_picture': self.profile_picture.filename if self.profile_picture is not None else "",
            'first_password_changed': self.first_password_changed,
            'first_payment_done': self.first_payment_done,
            'reported': self.reported,
            'demoted': self.demoted,
            'super': self.super,
            'corporate': self.corporate,
        }
        if self.id > 0:
            data['id'] = self.id
        return data

    def get_news_feed(self):
        from Message import Message
        messages = Message.get_messages()
        messages = [message for message in messages if message.author_id != self.id]
        following = [user.id for user in self.get_following()]
        # add messages from followed users
        feed = [message for message in messages if message.author_id in following]
        # add trending messages
        feed += [messages for message in messages if message.is_trending() and message not in feed]
        # sort the current feed in random order
        random.shuffle(feed)
        # all the other messages
        feed += [message for message in messages if message not in feed]
        return feed


    
    def update_password(self, password):
        if self.super != 1:
            if len(password) < 8:
                raise Exception('Password must be at least 8 characters long.')
            if len(password) > 64:
                raise Exception('Password cannot be longer than 64 characters.')
            if not any(c.isupper() for c in password):
                raise Exception('Password must contain at least one uppercase letter.')
            if not any(c.islower() for c in password):
                raise Exception('Password must contain at least one lowercase letter.')
            if not any(c.isdigit() for c in password):
                raise Exception('Password must contain at least one number.')
        self.password = User.get_hashed_password(password, self.salt)
        self.first_password_changed = 1
        self.save()

    def update_information(self, fullname, bio, profile_picture = None):
        if len(fullname) < 1:
            raise Exception('Full name cannot be empty.')
        self.fullname = fullname
        self.bio = bio
        if profile_picture != '':
            self.profile_picture = File(filename=profile_picture)
        self.save()

    def deposit_money(self, amount, explanation = 'Deposit'):
        if amount <= 0:
            raise Exception('Deposit amount must be positive.')
        from Payment import Payment
        payment = Payment(payment_amount=amount, explanation=explanation, user_id=self.id)
        payment.save()
        self.balance += amount
        self.balance = round(self.balance, 2)
        self.first_payment_done = 1
        self.save()
        return payment

    def charge_money(self, amount, explanation = 'Charge', force_charge = False):
        if amount <= 0:
            raise Exception('Charge amount must be positive.')
        if self.balance < amount and not force_charge:
            raise Exception('Insufficient funds.')
        from Payment import Payment
        payment = Payment(payment_amount=-amount, explanation=explanation, user_id=self.id)
        payment.save()
        self.balance -= amount
        self.balance = round(self.balance, 2)
        self.save()
        return payment

    def post_message(self, message, type, keywords, attachment):
        if len(message) < 1:
            raise Exception('Message cannot be empty.')
        if not self.corporate and type == 'job_ad':
            from Warning import Warning
            warning = Warning(
                user_id = self.id,
                reason = "Posted job ad as ordinary user",
                fine = 10,
                disputable = 0,
            )
            warning.save()
            raise Exception('You cannot post job ads as an ordinary user. You have been fined 10$ for this action.')
        from Message import Message
        obj_type = Message
        if type == 'job_ad':
            from MessageJobAd import MessageJobAd
            obj_type = MessageJobAd
        elif type == 'ad':
            from MessageAd import MessageAd
            obj_type = MessageAd
        message = obj_type(
            message = message, 
            keywords = keywords, 
            attachment = attachment,
            author_id = self.id,
        )
        message.save()
        return message
    
    def add_comment(self, message, comment):
        if len(comment) < 1:
            raise Exception('Comment cannot be empty.')
        from Comment import Comment
        comment = Comment(
            comment = comment,
            message_id = message.id,
        )
        comment.save()
        return comment
        
    def likes_message(self, message):
        from Like import Like
        like = Like.get_like_by_message_and_user(message, self)
        return like is not None

    def like_message(self, message):
        if message.author_id == self.id:
            raise Exception('You cannot like your own messages.')
        if self.likes_message(message):
            raise Exception('You cannot like a message twice.')
        from Like import Like
        like = Like(message_id = message.id)
        like.save()
        return like

    def unlike_message(self, message):
        from Like import Like
        like = Like.get_like_by_message_and_user(message, self)
        if like is None:
            raise Exception('You cannot unlike a message you have not liked.')
        like.delete()

    def dislikes_message(self, message):
        from Dislike import Dislike
        dislike = Dislike.get_dislike_by_message_and_user(message, self)
        return dislike is not None

    def dislike_message(self, message):
        if message.author_id == self.id:
            raise Exception('You cannot dislike your own messages.')
        if self.dislikes_message(message):
            raise Exception('You cannot dislike a message twice.')
        from Dislike import Dislike
        dislike = Dislike(message_id = message.id)
        dislike.save()
        return dislike

    def undislike_message(self, message):
        from Dislike import Dislike
        dislike = Dislike.get_dislike_by_message_and_user(message, self)
        if dislike is None:
            raise Exception('You cannot undislike a message you have not disliked.')
        dislike.delete()

    def is_following(self, user):
        follow = g.database.get_row('follows', where=" followed_id = ? and follower_id = ? ", values=(user.id, self.id))
        return follow is not None

    def follow_user(self, user):
        if user.id == self.id:
            raise Exception('You cannot follow yourself.')
        if self.is_following(user):
            raise Exception('You are already following this user.')
        g.database.insert_row('follows', {
            'followed_id': user.id,
            'follower_id': self.id,
        })
        return True

    def unfollow_user(self, user):
        if not self.is_following(user):
            raise Exception('You are not following this user.')
        g.database.delete_rows('follows', where=" followed_id = ? and follower_id = ? ", values=(user.id, self.id))
        return True

    def tip_user(self, user, amount):
        if user.id == self.id:
            raise Exception('You cannot tip yourself.')
        if amount <= 0:
            raise Exception('Tip amount must be positive.')
        if self.balance < amount and self.super == 0:
            raise Exception('Insufficient funds.')
        self.charge_money(amount, 'Tip to user ' + user.username, True)
        user.deposit_money(amount, 'Tip from user ' + self.username)
        from Tip import Tip
        tip = Tip(
            user_id = self.id,
            author_id = user.id,
            amount = amount,
        )
        return tip

    def dispute_warning(self, warning):
        if warning.user_id != self.id:
            raise Exception('You cannot dispute a warning that is not yours.')
        if warning.disputable == 0:
            raise Exception('You cannot dispute a warning that is not disputable.')
        if warning.disputed == 1:
            raise Exception('You cannot dispute a warning that is already disputed.')
        warning.disputed = 1
        warning.save()
        return warning
    
    def get_job_application(self, post):
        application = g.database.get_row('job_applications', where=" user_id = ? and message_id = ? ", values=(self.id, post.id))
        return application

    def apply_to_job(self, post):
        if post.author_id == self.id:
            raise Exception('You cannot apply to your own job ads.')
        if self.get_job_application(post) is not None:
            raise Exception('You cannot apply to the same job twice.')
        from JobApplication import JobApplication
        application = JobApplication(
            user_id = self.id,
            message_id = post.id,
        )
        application.save()
        return application

    def get_warnings(self):
        from Warning import Warning
        return Warning.get_warnings_by_user(self)

    def get_messages(self):
        from Message import Message
        return Message.get_messages_by_author(self)

    def get_followers(self):
        followers = g.database.get_rows('follows', where=" followed_id = ? ", values=(self.id,))
        return [OrdinaryUser.get_user(follower['follower_id']) for follower in followers]

    def get_following(self):
        following = g.database.get_rows('follows', where=" follower_id = ? ", values=(self.id,))
        return [OrdinaryUser.get_user(followed['followed_id']) for followed in following]

    def get_likes(self):
        from Like import Like
        return Like.get_likes_by_user(self)

    def get_dislikes(self):
        from Dislike import Dislike
        return Dislike.get_dislikes_by_user(self)

    def get_tips(self):
        from Tip import Tip
        return Tip.get_tips_by_user(self)

    def get_job_applications(self):
        from JobApplication import JobApplication
        return JobApplication.get_job_applications_by_user(self)

    def get_payments(self):
        from Payment import Payment
        return Payment.get_payments_by_user(self)

    def get_comments(self):
        from Comment import Comment
        return Comment.get_comments_by_user(self)
    
    def did_repost(self, message):
        repost = g.database.get_row('messages', where=" original_id = ? and author_id = ? ", values=(message.id, self.id))
        return repost is not None
    
    def get_repost(self, message):
        from Message import Message
        repost = Message.get_user_repost(message, self)
        return repost

    def repost(self, message):
        if message.author_id == self.id:
            raise Exception('You cannot repost your own messages.')
        if message.ad == 1:
            raise Exception('You cannot repost ads.')
        from Message import Message
        repost = Message(
            message = message.message, 
            keywords = message.keywords, 
            attachment = message.attachment.filename if message.attachment is not None else "",
            original_id = message.original_id if message.is_repost() else message.id,
        )
        repost.save()
        return repost
        
    def save(self):
        if not self.auth:
            raise Exception("User is not authenticated")
        if self.id == 0:
            self.id = g.database.insert_row('users', self.to_dict())
        else:
            g.database.update_row('users', self.to_dict(), where=" id = ? ", values=(self.id,))

    def delete(self):
        if self.super == 1:
            raise Exception('Cannot delete super user')
        g.database.delete_rows('users', where=" id = ? ", values=(self.id,))
        g.database.delete_rows('follows', where=" followed_id = ? or follower_id = ? ", values=(self.id, self.id))
        g.database.delete_rows('messages', where=" author_id = ? ", values=(self.id,))
        g.database.delete_rows('warnings', where=" user_id = ? ", values=(self.id,))
        g.database.delete_rows('likes', where=" user_id = ? ", values=(self.id,))
        g.database.delete_rows('tips', where=" user_id = ? or author_id = ? ", values=(self.id, self.id))
        g.database.delete_rows('job_applications', where=" user_id = ? ", values=(self.id,))
        g.database.delete_rows('payments', where=" user_id = ? ", values=(self.id,))
        g.database.delete_rows('comments', where=" user_id = ? ", values=(self.id,))

    def can_be_reported(self):
        if self.super == 1:
            return False
        if not g.auth:
            temp = session['reports']
            for report in temp:
                if report['type'] == 'profile' and report['id'] == self.id:
                    return False
        if g.user.id == self.id:
            return False
        for warning in self.get_warnings():
            if warning.reported_by_user_id == g.user.id and warning.type == "profile_warning":
                return False
        return True
    
    def mark_reported(self):
        self.reported = 1
        self.save()

    def mark_forgiven(self):
        self.reported = 0
        self.save()

    def mark_demoted(self):
        self.demoted = 1
        self.save()

    def check_warning_limit(self):
        if self.super == 1:
            return False
        warnings = self.get_warnings()
        problematic_warnings = []
        for warning in warnings:
            if warning.account_for_penalty():
                problematic_warnings.append(warning)
        if len(problematic_warnings) >= 3:
            self.issue_warning_penalty(problematic_warnings)
            return True
        return False
        
    def issue_warning_penalty(self, problematic_warnings):
        if self.is_trending():
            self.mark_demoted()
        else:
            self.charge_money(len(problematic_warnings) * 50, f"Penalty for getting to {len(problematic_warnings)} warnings. All of your warnings were forgiven.", True)
        # we forgive all of the user's warnings, problematic or not, so that they can start fresh
        for warning in self.get_warnings():
            warning.forgive()

    def is_trending(self):
        if self.demoted == 1 or self.corporate == 1:
            return False
        followers = self.get_followers()
        if len(followers) < 10:
            return False
        tips = self.get_tips()
        messages = self.get_messages()
        likes = 0
        dislikes = 0
        trending = 0
        tip_amount = 0
        for message in messages:
            likes += len(message.get_likes())
            dislikes += len(message.get_dislikes())
            if message.is_trending():
                trending += 1
        for tip in tips:
            tip_amount += tip.amount
        if tip_amount < 100 and likes - dislikes <= 10:
            return False
        if trending < 3:
            return False
        return True
        
        
        
    @staticmethod
    def get_user(id):
        row = g.database.get_row('users', where=" id = ? ", values=(id,))
        return OrdinaryUser.get_user_obj(row)
    
    @staticmethod
    def get_user_by_username(username):
        row = g.database.get_row('users', where=" username = ? ", values=(username,))
        return OrdinaryUser.get_user_obj(row)
    
    @staticmethod
    def get_users():
        rows = g.database.get_rows('users')
        return [OrdinaryUser.get_user_obj(row) for row in rows]

    @staticmethod
    def get_user_obj(row):
        if row is None:
            return None
        if row['super'] == 1:
            from SuperUser import SuperUser
            return SuperUser(**row)
        elif row['corporate'] == 1:
            from CorporateUser import CorporateUser
            return CorporateUser(**row)
        else:
            return OrdinaryUser(**row)