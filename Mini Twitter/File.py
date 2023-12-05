import os
import random
import string
from Config import FILES_FOLDER, FILE_TYPES
from werkzeug.utils import secure_filename

class File:
    def __init__(self, filename="", type="", external_file = None):
        if external_file is not None:
            self.external_file = external_file
            self.filename = File.get_random_filename(self.external_file.filename)
            self.type = File.get_type(self.filename)
            if self.type == "" or (type != "" and self.type != type):
                raise Exception(f"Invalid file type.")
            self.save()
        else:
            if not os.path.exists(os.path.join(FILES_FOLDER, filename)):
                raise Exception(f"File {filename} does not exist.")
            self.filename = filename
            self.type = File.get_type(self.filename)
    
    def save(self):
        self.external_file.save(os.path.join(FILES_FOLDER, self.filename))

    def delete(self):
        os.remove(os.path.join(FILES_FOLDER, self.filename))

    def get_file_path(self):
        return os.path.join(FILES_FOLDER, self.filename)
    
    @staticmethod
    def get_random_filename(filename):
        random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(20)) + filename
        random_name = secure_filename(random_name)
        if os.path.exists(os.path.join(FILES_FOLDER, random_name)):
            return File.get_random_filename(filename)
        return random_name

    @staticmethod
    def get_type(filename):
        extension = filename.split('.')[-1]
        for type, extensions in FILE_TYPES.items():
            if extension in extensions:
                return type
        return ""