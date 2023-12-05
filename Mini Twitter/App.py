import sqlite3
from Comment import Comment
from Config import FILES_FOLDER, STATIC_FOLDER, SECRET_KEY, DATABASE_NAME
from flask import Flask, g, render_template, request, redirect, send_from_directory, url_for, session, jsonify
from Database import Database
from JobApplication import JobApplication
from Message import Message
from MessageJobAd import MessageJobAd
from User import User
from Warning import Warning 
from Payment import Payment 
from OrdinaryUser import OrdinaryUser
from File import File

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = FILES_FOLDER

def get_db():
    db = getattr(g, 'database', None)
    if db is None:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        g.database = Database(conn)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'database', None)
    if db is not None:
        db.conn.close()

@app.route('/static/<path:path>')
def static_file(path):
    return send_from_directory(STATIC_FOLDER, path)

@app.route('/files/<path:path>')
def files(path):
    return send_from_directory(FILES_FOLDER, path)

@app.before_request
def before_request():
    get_db()
    g.session = session
    g.user = User() if session.get('user_id') is None else OrdinaryUser.get_user(session.get('user_id'))
    if g.user is None:
        session.pop('user_id', None)
        session.pop('reports', None)
        g.user = User()
    g.auth = g.user.auth if g.user is not None else False
    if not g.auth and 'reports' not in session:
        session['reports'] = []
    pass_exception_routes = ['/logout', '/update_password', '/delete_user']
    if g.auth and not g.user.first_password_changed and request.path not in pass_exception_routes:
        return redirect(url_for('update_password'))
    payment_exception_routes = ['/add_payment', '/payments', '/my_payments', '/logout', '/update_password', '/delete_user']
    if g.auth and (g.user.first_payment_done == 0 or g.user.balance < 0) and request.path not in payment_exception_routes:
        return redirect(url_for('add_payment'))
    if g.auth:
        was_demoted = g.user.demoted 
        warning_penalty = g.user.check_warning_limit()
        if warning_penalty and request.path not in payment_exception_routes:
            if was_demoted:
                return redirect(url_for('my_payments'))
            else:
                return redirect(url_for('my_warnings'))

@app.route('/')
def home_page():
    posts = g.user.get_news_feed()
    return render_template('index.jinja', posts=posts)

@app.route('/trending')
def trending():
    posts = g.user.get_trending_messages()
    return render_template('index.jinja', posts=posts)

@app.route('/search')
def search():
    author = request.args.get('author')
    keywords = request.args.get('keywords')
    min_likes = request.args.get('min_likes')
    max_likes = request.args.get('max_likes')
    min_dislikes = request.args.get('min_dislikes')
    max_dislikes = request.args.get('max_dislikes')
    posts = g.user.search_messages(
        author = author,
        keywords = keywords,
        min_likes = min_likes,
        max_likes = max_likes,
        min_dislikes = min_dislikes,
        max_dislikes = max_dislikes,
    )
    return render_template('index.jinja', posts=posts)

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if not g.user.auth:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('add_post.jinja')
    message = request.form['message']
    type = request.form['type']
    keywords = request.form['keywords']
    file = request.files['attachment'] if 'attachment' in request.files else None
    try:
        if file is not None and file.filename != '':
            file = File(external_file = file)
        post = g.user.post_message(message, type, keywords, file.filename if file is not None else '')
        return redirect(url_for('post', id=post.id))
    except Exception as e:
        return render_template('add_post.jinja', error=e)
    
@app.route('/repost/<id>')
def repost(id):
    if not g.user.auth:
        return redirect(url_for('login'))
    message = Message.get_message(id)
    if message is None:
        return render_template('index.jinja', error='Message not found.')
    try:
        post = g.user.repost(message)
        return redirect(url_for('post', id=post.id))
    except Exception as e:
        return render_template('post.jinja', post=message, error=e)
    
@app.route('/post/<id>')
def post(id):
    post = Message.get_message(id)
    if post is None:
        return render_template('index.jinja', error='Message not found.')
    return render_template('post.jinja', post=post, showcomments=True)

@app.route('/like_post/<id>', methods=['POST'])
def like_post(id):
    message = Message.get_message(id)
    if message is None:
        raise Exception('Message not found.')
    if g.user.likes_message(message):
        g.user.unlike_message(message)
    else:
        if g.user.dislikes_message(message):
            g.user.undislike_message(message)
        g.user.like_message(message)
    dict = message.to_dict()
    dict['likes'] = len(message.get_likes())
    dict['dislikes'] = len(message.get_dislikes())
    dict['liked'] = g.user.likes_message(message)
    dict['disliked'] = g.user.dislikes_message(message)
    return jsonify(dict)

@app.route('/dislike_post/<id>', methods=['POST'])
def dislike_post(id):
    message = Message.get_message(id)
    if message is None:
        raise Exception('Message not found.')
    if g.user.dislikes_message(message):
        g.user.undislike_message(message)
    else:
        if g.user.likes_message(message):
            g.user.unlike_message(message)
        g.user.dislike_message(message)
    dict = message.to_dict()
    dict['likes'] = len(message.get_likes())
    dict['dislikes'] = len(message.get_dislikes())
    dict['liked'] = g.user.likes_message(message)
    dict['disliked'] = g.user.dislikes_message(message)
    return jsonify(dict)

@app.route('/report_post/<id>', methods=['POST'])
def report_post(id):
    message = Message.get_message(id)
    if message is None:
        raise Exception('Message not found.')
    warning = g.user.report_message(message)
    return jsonify(warning.to_dict())

@app.route('/report_ad/<id>', methods=['POST'])
def report_ad(id):
    message = Message.get_message(id)
    if message is None:
        raise Exception('Message not found.')
    warning = g.user.report_ad(message)
    return jsonify(warning.to_dict())

@app.route('/delete_post/<id>', methods=['POST'])
def delete_post(id):
    if not g.auth:
        raise Exception('You are not authorized to perform this action.')
    message = Message.get_message(id)
    if message is None:
        raise Exception('Message not found.')
    if message.author_id != g.user.id and g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    message.delete()
    return jsonify(True)

@app.route('/add_comment/<id>', methods=['POST'])
def add_comment(id):
    try:
        message = Message.get_message(id)
        if message is None:
            raise Exception('Message not found.')
        comment = request.form['comment']
        comment = g.user.add_comment(message, comment)
        return redirect(url_for('post', id=message.id))
    except Exception as e:
        return render_template('post.jinja', post=message, comment_error=e, showcomments=True)

@app.route('/delete_comment/<id>', methods=['POST'])
def delete_comment(id):
    comment = Comment.get_comment(id)
    if comment is None:
        raise Exception('Comment not found.')
    if comment.author_id != g.user.id and g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    comment.delete()
    return jsonify(True)

@app.route('/report_comment/<id>', methods=['POST'])
def report_comment(id):
    comment = Comment.get_comment(id)
    if comment is None:
        raise Exception('Comment not found.')
    warning = g.user.report_comment(comment)
    return jsonify(warning.to_dict())

@app.route('/apply_to_job/<id>', methods=['POST'])
def apply_to_job(id):
    message = Message.get_message(id)
    if message is None:
        raise Exception('Message not found.')
    application = g.user.apply_to_job(message)
    return jsonify(application.to_dict())

@app.route('/accept_application/<id>', methods=['POST'])
def accept_application(id):
    application = JobApplication.get_job_application(id)
    if application is None:
        raise Exception('Application not found.')
    if application.answered == 1:
        raise Exception('Application already answered.')
    application = g.user.accept_application(application)
    return jsonify(application.to_dict())

@app.route('/reject_application/<id>', methods=['POST'])
def reject_application(id):
    application = JobApplication.get_job_application(id)
    if application is None:
        raise Exception('Application not found.')
    if application.answered == 1:
        raise Exception('Application already answered.')
    application = g.user.reject_application(application)
    return jsonify(application.to_dict())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user.auth:
        return redirect(url_for('home_page'))
    if request.method == 'GET':
        return render_template('register.jinja')
    username = request.form['username']
    fullname = request.form['fullname']
    bio = request.form['bio']
    type = request.form['type']
    image = request.files['profile_picture'] if 'profile_picture' in request.files else ""
    try:
        if image is not None and image.filename != '':
            image = File(external_file = image, type='image').filename
        else:
            image = ""
        user, password = g.user.register(username, fullname, bio, type, image)
        return render_template('registered.jinja', password=password)
    except Exception as e:
        return render_template('register.jinja', error=e)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user.auth:
        return redirect(url_for('home_page'))
    if request.method == 'GET':
        return render_template('login.jinja')
    username = request.form['username']
    password = request.form['password']
    try:
        user = g.user.login(username, password)
        session['user_id'] = user.id
        return redirect(url_for('home_page'))
    except Exception as e:
        return render_template('login.jinja', error=e)
    
@app.route('/update_information', methods=['GET', 'POST'])
def update_information():
    if not g.user.auth:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('update_user.jinja')
    fullname = request.form['fullname']
    bio = request.form['bio']
    image = request.files['profile_picture'] if 'profile_picture' in request.files else ""
    try:
        if image is not None and image.filename != '':
            image = File(external_file = image, type='image').filename
        else:
            image = ""
        g.user.update_information(fullname, bio, image)
        return redirect(url_for('profile', id=g.user.id))
    except Exception as e:
        return render_template('update_user.jinja', error=e)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('reports', None)
    return redirect(url_for('home_page'))

@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if not g.user.auth:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('update_password.jinja')
    password = request.form['password']
    try:
        g.user.update_password(password)
        return redirect(url_for('home_page'))
    except Exception as e:
        return render_template('update_password.jinja', error=e)
    
@app.route('/profile/<id>')
def profile(id=None):
    if not g.user.auth and id is None:
        return redirect(url_for('login'))
    profile_id = id
    if id is None:
        profile_id = g.user.id
    profile = OrdinaryUser.get_user(profile_id)
    messages = profile.get_messages()
    return render_template('profile.jinja', profile=profile, posts=messages)

@app.route('/report_user/<id>', methods=['POST'])
def report_user(id):
    if id is None or not g.user.auth:
        raise Exception('Invalid request.')
    profile = OrdinaryUser.get_user(id)
    warning = g.user.report_user(profile)
    return jsonify(warning.to_dict())

@app.route('/follow_user/<id>', methods=['POST'])
def follow_user(id):
    if id is None or not g.user.auth:
        raise Exception('Invalid request.')
    profile = OrdinaryUser.get_user(id)
    g.user.follow_user(profile)
    return jsonify(True)

@app.route('/unfollow_user/<id>', methods=['POST'])
def unfollow_user(id):
    if id is None or not g.user.auth:
        raise Exception('Invalid request.')
    profile = OrdinaryUser.get_user(id)
    g.user.unfollow_user(profile)
    return jsonify(True)

@app.route('/add_tip/<id>', methods=['POST'])
def add_tip(id):
    if id is None or not g.user.auth:
        raise Exception('Invalid request.')
    profile = OrdinaryUser.get_user(id)
    amount = float(request.form['amount'])
    g.user.tip_user(profile, amount)
    return redirect(url_for('profile', id=profile.id))

@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    if not g.user.auth:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('add_payment.jinja')
    card_number = request.form['card_number']
    expiration_month = request.form['expiration_month']
    expiration_year = request.form['expiration_year']
    cvv = request.form['cvv']
    amount = request.form['amount']
    try:
        Payment.validate_card_information(card_number, expiration_month, expiration_year, cvv)
        g.user.deposit_money(round(float(amount), 2))
    except Exception as e:
        return render_template('add_payment.jinja', error=e)
    return redirect(url_for('home_page'))

@app.route('/dispute_warning/<id>', methods=['POST'])
def dispute_warning(id):
    warning = Warning.get_warning(id)
    warning = g.user.dispute_warning(warning)
    return jsonify(warning.to_dict())

@app.route('/forgive_warning/<id>', methods=['POST'])
def forgive_warning(id):
    if not g.auth or g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    warning = Warning.get_warning(id)
    warning = g.user.forgive_warning(warning)
    return jsonify(warning.to_dict())

@app.route('/close_dispute/<id>', methods=['POST'])
def close_dispute(id):
    if not g.auth or g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    warning = Warning.get_warning(id)
    warning = g.user.close_dispute(warning)
    return jsonify(warning.to_dict())

@app.route('/add_taboo_word', methods=['POST'])
def add_taboo_word():
    if not g.auth or g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    word = request.form['word']
    g.user.add_taboo_word(word)
    return redirect(url_for('taboo_words'))

@app.route('/remove_taboo_word/<id>', methods=['POST'])
def remove_taboo_word(id):
    if not g.auth or g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    g.user.remove_taboo_word(id)
    return jsonify(True)

@app.route('/accept_user/<id>', methods=['POST'])
def accept_user(id):
    if not g.auth or g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    user = OrdinaryUser.get_user(id)
    user = g.user.accept_user(user)
    return jsonify(user.to_dict())

@app.route('/reject_user/<id>', methods=['POST'])
def reject_user(id):
    if not g.auth or g.user.super != 1:
        raise Exception('You are not authorized to perform this action.')
    user = OrdinaryUser.get_user(id)
    reason = request.get_json()['reason']
    user = g.user.reject_user(user, reason)
    return jsonify(user.to_dict())

@app.route('/delete_user/<id>', methods=['POST'])
def delete_user(id):
    if not g.auth:
        raise Exception('You are not authorized to perform this action.')
    if not g.user.super:
        raise Exception('You are not authorized to perform this action.')
    user = OrdinaryUser.get_user(id)
    g.user.delete_user(user)
    return jsonify(True)

@app.route('/delete_account')
def delete_account():
    if not g.auth:
        return redirect(url_for('login'))
    if g.user.super == 1:
        return redirect(url_for('home_page'))
    g.user.delete()
    session.pop('user_id', None)
    session.pop('reports', None)
    return redirect(url_for('home_page'))

@app.route('/my_payments')
def my_payments():
    if not g.user.auth:
        return redirect(url_for('login'))
    payments = g.user.get_payments()
    return render_template('user_dashboard.jinja', page='payments', payments=payments)

@app.route('/payments')
def payments():
    if not g.user.auth :
        return redirect(url_for('login'))
    if g.user.super != 1:
        return redirect(url_for('my_payments'))
    payments = Payment.get_payments()
    return render_template('dashboard.jinja', page='payments', payments=payments)

@app.route('/my_warnings')
def my_warnings():
    if not g.user.auth:
        return redirect(url_for('login'))
    warnings = g.user.get_warnings()
    return render_template('user_dashboard.jinja', page='warnings', warnings=warnings)

@app.route('/warnings')
def warnings():
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.super != 1:
        return redirect(url_for('my_warnings'))
    warnings = Warning.get_warnings()
    return render_template('dashboard.jinja', page='warnings', warnings=warnings)

@app.route('/applications')
def applications():
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.super != 1:
        return redirect(url_for('my_applications'))
    applications = JobApplication.get_job_applications()
    return render_template('dashboard.jinja', page='applications', applications=applications)

@app.route('/my_applications')
def my_applications():
    if not g.user.auth:
        return redirect(url_for('login'))
    applications = g.user.get_job_applications()
    return render_template('user_dashboard.jinja', page="applications", applications=applications)

@app.route('/my_applicants')
def my_applicants():
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.corporate != 1:
        return redirect(url_for('home_page'))
    applications = []
    messages = MessageJobAd.get_job_ads_by_author(g.user)
    for message in messages:
        applications += message.get_applications()
    return render_template('user_dashboard.jinja', page="applicants", applications=applications)

@app.route('/message_applications/<id>')
def message_applications(id):
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.corporate != 1:
        return redirect(url_for('home_page'))
    message = Message.get_message(id)
    applications = message.get_applications()
    return render_template('message_applications.jinja', post=message, applications=applications)

@app.route('/users')
def users():
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.super != 1:
        return redirect(url_for('home_page'))
    users = OrdinaryUser.get_users()
    return render_template('dashboard.jinja', page='users', users=users)

@app.route('/taboo_words')
def taboo_words():
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.super != 1:
        return redirect(url_for('home_page'))
    taboo_words = Message.get_taboo_words_list()
    return render_template('dashboard.jinja', page='taboo', words=taboo_words)

@app.route('/reset_application')
def reset_application():
    if not g.user.auth:
        return redirect(url_for('login'))
    if g.user.super != 1:
        return redirect(url_for('home_page'))
    g.database.drop_tables()
    g.database.create_tables()
    g.database.create_admin_user()
    return redirect(url_for('home_page'))


if __name__ == '__main__':
    conn = sqlite3.connect(DATABASE_NAME)
    db = Database(conn)
    db.create_tables()
    db.create_admin_user()
    conn.close()
    app.run(debug=True)