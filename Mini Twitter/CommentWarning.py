from datetime import datetime
from Comment import Comment
from Warning import Warning
from flask import g

class CommentWarning(Warning):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = "comment_warning"
        if self.id == 0:
            self.validate()

    def validate(self):
        super().validate()
        if self.comment_id == 0:
            raise Exception('Comment ID cannot be empty')

    def save(self):
        if self.id == 0:
            comment = Comment.get_comment(self.comment_id)
            comment.mark_reported()
        super().save()

    def forgive(self):
        super().forgive()
        comment = Comment.get_comment(self.comment_id)
        comment.mark_forgiven()

    def get_comment(self):
        return Comment.get_comment(self.comment_id)
    
    @staticmethod
    def get_warnings_by_comment(comment):
        warnings = []
        for warning in g.database.get_rows('warnings', where=" comment_id = ? ", values=(comment.id,)):
            warnings.append(CommentWarning(**warning))
        return warnings 
