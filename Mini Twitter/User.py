import binascii
import hashlib
from flask import g, session
import os

class User:
    def __init__(self):
        self.id = 0
        self.auth = False
        
    def get_news_feed(self):
        from Message import Message
        messages = Message.get_messages()
        top = []
        for message in messages:
            top.append([message, len(message.get_likes()) - len(message.get_dislikes())])
        top.sort(key=lambda x: x[1], reverse=True)
        if(len(top) > 3):
            top = top[:3]
        return [message[0] for message in top]
    
    def get_trending_messages(self):
        from Message import Message
        messages = Message.get_messages()
        return [message for message in messages if message.is_trending()]
    
    def search_messages(self, author = None, keywords = None, min_likes = None, max_likes = None, min_dislikes = None, max_dislikes = None):
        from Message import Message
        messages = Message.search_messages(
            author = author,
            keywords = keywords,
            likes = (min_likes, max_likes),
            dislikes = (min_dislikes, max_dislikes),
        )
        return messages
    
    def report_message(self, message):
        from MessageWarning import MessageWarning
        warning = MessageWarning(
            message_id = message.id,
            user_id = message.author_id,
            reason = "Message reported as inappropriate content",
        )
        warning.save()
        if not self.auth:
            temp = session['reports']
            temp.append({
                'type': 'message',
                'id': message.id,
            })
            session['reports'] = temp
        return warning
    
    def report_ad(self, message):
        from MessageWarning import MessageWarning
        warning = MessageWarning(
            message_id = message.id,
            user_id = message.author_id,
            reason = "Message reported as advertisement",
            fine = 10
        )
        warning.save()
        if not self.auth:
            temp = session['reports']
            temp.append({
                'type': 'message',
                'id': message.id,
            })
            session['reports'] = temp
        return warning
    
    def report_comment(self, comment):
        from CommentWarning import CommentWarning
        warning = CommentWarning(
            comment_id = comment.id,
            user_id = comment.user_id,
            reason = "Comment reported as inappropriate content",
        )
        warning.save()
        if not self.auth:
            temp = session['reports']
            temp.append({
                'type': 'comment',
                'id': comment.id,
            })
            session['reports'] = temp
        return warning
    
    def report_user(self, user):
        from ProfileWarning import ProfileWarning
        warning = ProfileWarning(
            user_id = user.id,
            reason = "Profile reported as inappropriate content",
        )
        warning.save()
        if not self.auth:
            temp = session['reports']
            temp.append({
                'type': 'profile',
                'id': user.id,
            })
            session['reports'] = temp
        return warning
    
    def register(self,username, fullname, bio, type, image):
        password = User.get_random_password()
        salt = User.get_random_salt()
        key = User.get_hashed_password(password, salt)
        from CorporateUser import CorporateUser
        from OrdinaryUser import OrdinaryUser
        user_type = CorporateUser if type == 'corporate' else OrdinaryUser
        user = user_type(
                username = username, 
                fullname = fullname, 
                bio = bio, 
                profile_picture = image, 
                password = key, 
                salt = salt.hex()
        )
        user.save()
        return user, password
        
    def login(self, username, password):
        from OrdinaryUser import OrdinaryUser
        user = OrdinaryUser.get_user_by_username(username)
        if user is None:
            raise Exception('User not found')
        key = User.get_hashed_password(password, user.salt)
        if key != user.password:
            raise Exception('Wrong password')
        return user
    
    @staticmethod
    def get_hashed_password(password, salt):
        if type(salt) is str:
            salt = binascii.unhexlify(salt)
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 500000).hex()
    
    @staticmethod
    def get_random_password():
        return os.urandom(32).hex()[0:8]
    
    @staticmethod
    def get_random_salt():
        return os.urandom(32)