from datetime import datetime
from flask import g, session
from File import File
from Config import MAX_MESSAGE_LENGTH, MAX_KEYWORDS

class Message:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 0)
        self.message = kwargs.get('message', '')
        keywords = kwargs.get('keywords', '')
        self.keywords = [keyword.strip() for keyword in keywords.split(',') if keyword.strip() != ''] if type(keywords) == str else keywords
        attachment = kwargs.get('attachment', '')
        self.attachment = File(filename=attachment) if attachment != '' else None
        self.author_id = kwargs.get('author_id', g.user.id)
        self.price = kwargs.get('price', self.compute_price())
        self.reads = kwargs.get('reads', 0)
        self.reported = kwargs.get('reported', 0)
        self.original_id = kwargs.get('original_id', 0)
        self.date = kwargs.get('date', datetime.now().strftime("%Y-%m-%d"))
        self.time = kwargs.get('time', datetime.now().strftime("%H:%M:%S"))
        self.ad = 0
        self.job_ad = 0
        if self.id == 0:
            self.validate()

    def validate(self):
        if len(self.message) < 1:
            raise Exception('Message cannot be empty')
        if len(self.message) > MAX_MESSAGE_LENGTH:
            raise Exception(f'Message cannot be longer than {MAX_MESSAGE_LENGTH} characters')
        if self.author_id == 0:
            raise Exception('Author ID cannot be empty')
        if len(self.keywords) > MAX_KEYWORDS:
            raise Exception('Message cannot have more than 10 keywords')
        if not g.user.super == 1:
            taboo_words = self.get_taboo_words()
            if len(taboo_words) > 2:
                from Warning import Warning
                warning = Warning(
                    user_id=self.author_id,
                    reason=f'Trying to post a message with more than 2 taboo words: {",".join(taboo_words)}.',
                    disputable=0,
                )
                warning.save()
                raise Exception(f'Your message had more than two taboo words: {",".join(taboo_words)}. You have been issued 1 warning.')
        self.replace_taboo_words()


    def to_dict(self):
        data = {
            'author_id': self.author_id,
            'message': self.message,
            'keywords': ','.join(self.keywords),
            'attachment': self.attachment.filename if self.attachment is not None else "",
            'price': self.price,
            'reads': self.reads,
            'reported': self.reported,
            'original_id': self.original_id,
            'ad': self.ad,
            'job_ad': self.job_ad,
            'date': self.date,
            'time': self.time,
        }
        if self.id > 0:
            data['id'] = self.id
        return data
        
    def save(self):
        if self.id == 0:
            if self.price > 0:
                self.get_author().charge_money(self.price, explanation = "Message cost")
            self.id = g.database.insert_row('messages', self.to_dict())
        else:
            g.database.update_row('messages', self.to_dict(), where=" id = ? ", values=(self.id,))

    def delete(self):
        if not self.can_be_deleted():
            raise Exception('Message cannot be deleted')
        g.database.delete_rows('messages', where=" id = ? ", values=(self.id,))
        g.database.delete_rows('likes', where=" message_id = ? ", values=(self.id,))
        g.database.delete_rows('comments', where=" message_id = ? ", values=(self.id,))

    def compute_price(self):
        from Config import CORPORATE_PRICE_PER_WORD, FREE_WORDS, IMAGE_WORDS, PRICE_PER_WORD, VIDEO_WORDS
        author = self.get_author()
        if author.super == 1:
            return 0
        attachment_words = 0
        if self.attachment is not None:
            if self.attachment.type == 'image':
                attachment_words = IMAGE_WORDS
            elif self.attachment.type == 'video':
                attachment_words = VIDEO_WORDS
        words = len(self.message.split()) + attachment_words
        if author.corporate == 1:
            return words * CORPORATE_PRICE_PER_WORD
        else:
            return (words - FREE_WORDS) * PRICE_PER_WORD if words > FREE_WORDS else 0
        
    def get_author(self):
        from OrdinaryUser import OrdinaryUser
        return OrdinaryUser.get_user(self.author_id)

    def get_likes(self):
        from Like import Like
        return Like.get_likes_by_message(self)
    
    def get_dislikes(self):
        from Dislike import Dislike
        return Dislike.get_dislikes_by_message(self)
    
    def get_comments(self):
        from Comment import Comment
        return Comment.get_comments_by_message(self)
    
    def get_reposts(self):
        return Message.get_messages_by_original(self)
    
    def get_warnings(self):
        from MessageWarning import MessageWarning
        return MessageWarning.get_warnings_by_message(self)
    
    def get_original_message(self):
        return Message.get_message(self.original_id) if self.is_repost() else None

    def get_attachment(self):
        return self.attachment
        
    def is_repost(self):
        return self.original_id > 0
    
    def is_trending(self):
        return self.reads > 10 and len(self.get_likes()) - len(self.get_dislikes()) > 3
    
    def mark_reported(self):
        self.reported = 1
        self.save()

    def mark_forgiven(self):
        self.reported = 0
        self.save()

    def add_read(self):
        if self.author_id != g.user.id:
            self.reads += 1
            self.save()

    def get_taboo_words(self):
        taboo_words = Message.get_taboo_words_all()
        words = [word for word in self.message.split() if word in taboo_words]
        return words
    
    def replace_taboo_words(self):
        taboo_words = self.get_taboo_words()
        if len(taboo_words) == 0:
            return
        message_words = self.message.split()
        new_words = []
        for word in message_words:
            if word in taboo_words:
                new_words.append('*' * len(word))
            else:
                new_words.append(word)
        self.message = ' '.join(new_words)
            

    def can_be_deleted(self):
        if not g.auth or not (g.user.super == 1 or g.user.id == self.author_id):
            return False
        comments = self.get_comments()
        for comment in comments:
            if not comment.can_be_deleted():
                return False
        for warning in self.get_warnings():
            if warning.disputed == 1 and warning.dispute_closed == 0:
                return False
        return True
    
    def can_be_reported(self):
        if self.get_author().super == 1:
            return False
        if not g.auth:
            temp = session['reports']
            for report in temp:
                if report['type'] == 'message' and report['id'] == self.id:
                    return False
            return True 
        if g.user.id == self.author_id:
            return False
        for warning in self.get_warnings():
            if warning.reported_by_user_id == g.user.id:
                return False
        return True
    
    def can_be_reposted(self):
        if self.author_id == g.user.id:
            return False
        if self.ad == 1:
            return False
        for warning in self.get_warnings():
            if warning.forgiven != 1:
                return False
        return True

    @staticmethod
    def get_message(id):
        row = g.database.get_row('messages', where=" id = ? ", values=(id,))
        return Message.get_message_obj(row)
    
    @staticmethod
    def get_messages():
        rows = g.database.get_rows('messages')
        return [Message.get_message_obj(row) for row in rows]
    
    @staticmethod
    def get_message_obj(row):
        if row is None:
            return None
        obj_type = Message
        if row['job_ad'] == 1:
            from MessageJobAd import MessageJobAd
            return MessageJobAd(**row)
        elif row['ad'] == 1:
            from MessageAd import MessageAd
            return MessageAd(**row)
        return Message(**row)
    
    @staticmethod
    def get_messages_by_author(user):
        rows = g.database.get_rows('messages', where=" author_id = ? ", values=(user.id,))
        return [Message.get_message_obj(row) for row in rows]
    
    @staticmethod
    def get_messages_by_original(original):
        rows = g.database.get_rows('messages', where=" original_id = ? ", values=(original.id,))
        return [Message.get_message_obj(row) for row in rows]
    
    @staticmethod
    def get_user_repost(message, user):
        row = g.database.get_row('messages', where=" original_id = ? AND author_id = ? ", values=(message.id, user.id))
        return Message.get_message_obj(row)
    
    @staticmethod
    def search_messages(author="", keywords="", likes=None, dislikes=None):
        messages = Message.get_messages()
        if author != "":
            messages = [message for message in messages if message.get_author().username == author]
        if keywords != "":
            messages = [message for message in messages if any(keyword.strip() in message.keywords for keyword in keywords.split(","))]
        if likes is not None:
            min_likes = likes[0] if likes[0].isnumeric() else 0
            max_likes = likes[1] if likes[1].isnumeric() else 999999999
            messages = [message for message in messages if min_likes <= len(message.get_likes()) <= max_likes]
        if dislikes is not None:
            min_dislikes = dislikes[0] if dislikes[0].isnumeric() else 0
            max_dislikes = dislikes[1] if dislikes[1].isnumeric() else 999999999
            messages = [message for message in messages if min_dislikes <= len(message.get_dislikes()) <= max_dislikes]
        return messages

    @staticmethod
    def get_taboo_words_all():
        rows = g.database.get_rows('taboo_words')
        return [row['word'] for row in rows]

    @staticmethod
    def get_taboo_words_list():
        rows = g.database.get_rows('taboo_words')
        return rows

