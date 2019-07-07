from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

from passlib import pwd, hash
import random, string, time

app = Flask(__name__)
app.secret_key = 'Kw4zL8StOmb2DxyeoickGyclkaGA2eYbBEQ6'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/gordonwedding/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_USE_SSL']  = True
app.config['MAIL_PORT']     = 465
app.config['MAIL_USERNAME'] = 'brydevmail@gmail.com'
app.config['MAIL_PASSWORD'] = '&gZB4@jQ8UFa'
mail = Mail(app)

addresses = { 'dev': ['bryches@gmail.com'], 'admin': ['bryches@gmail.com', 'Jaysinlayne.gordon@gmail.com'] }

app.debug = True



class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    type     = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100))
    code     = db.Column(db.String(100))



class Memory(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    text     = db.Column(db.String(50),  nullable=False)
    sig      = db.Column(db.String(100), nullable=False)
    public   = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)
    skipped  = db.Column(db.Boolean, default=False)
    created  = db.Column(db.Integer)



class Page(db.Model):
    id     = db.Column(db.Integer, primary_key=True)
    name   = db.Column(db.String(50))
    visits = db.Column(db.Integer, default=0)
    last   = db.Column(db.Integer)



@app.route('/')
def home():
    add_page_visit('Home')
    return render_template('home.html', home=True)



@app.route('/details')
def details():
    add_page_visit('Details')
    return render_template('details.html')



@app.route('/gifts')
def gifts():
    add_page_visit('Gifts')
    return render_template('gifts.html')



@app.route('/feedback')
def feedback():
    return render_template('feedback.html')



@app.route('/memories')
def memories():
    add_page_visit('Memories')

    if 'type' in session:
        count    = Memory.query.filter_by(approved=False, rejected=False, public=True).count()
        memories = Memory.query.filter_by(approved=True).order_by(Memory.created.desc()).all()

    else:
        count    = 0
        memories = Memory.query.filter_by(approved=True, public=True).order_by(Memory.created.desc()).all()

    return render_template('memories.html', memories=memories, count=count)



@app.route('/share', methods=['GET', 'POST'])
def share():
    add_page_visit('Share')

    if 'submit' in request.form:
        text     = request.form['text'] if 'text' in request.form else None
        sig      = request.form['from'] if 'from' in request.form else None
        public   = True if request.form['submit'] == 'Everyone' else False
        approved = not public 
        created  = int(time.time())

        if text and sig:
            memory = Memory(text=text, sig=sig, approved=approved, public=public, created=created)
            db.session.add(memory)
            db.session.commit()

            send_mail('New Memory from ' + memory.sig, addresses['admin'], memory.text)
            return redirect('/thanks')

    return render_template('share.html')



@app.route('/thanks')
def thanks():
    return render_template('thanks.html')



@app.route('/review')
def review():
    if 'id' not in session: return redirect('/login')
    count  = Memory.query.filter_by(approved=False, rejected=False, public=True).count()
    memory = Memory.query.filter_by(approved=False, rejected=False, public=True, skipped=False).order_by(Memory.created).first()

    if not memory:
        skipped = Memory.query.filter_by(approved=False, rejected=False, public=True, skipped=True).all()
        if skipped: return redirect('/review/clear')

    return render_template('review.html', memory=memory, count=count)



@app.route('/review/skip/<int:id>')
def skip(id):
    if 'id' not in session: return redirect('/login')
    memory = Memory.query.get(id)

    memory.skipped = True
    db.session.commit()
    return redirect('/review')



@app.route('/review/clear')
def clear():
    if 'id' not in session: return redirect('/login')
    memories = Memory.query.filter_by(approved=False, rejected=False, skipped=True).all()

    for memory in memories:
        memory.skipped = False

    db.session.commit()
    return redirect('/review')



@app.route('/review/approve/<int:id>')
def approve(id):
    if 'id' not in session: return redirect('/login')
    memory = Memory.query.get(id)

    memory.approved = True
    db.session.commit()
    return redirect('/review')



@app.route('/review/reject/<int:id>')
def reject(id):
    if 'id' not in session: return redirect('/login')
    memory = Memory.query.get(id)

    memory.rejected = True
    db.session.commit()
    return redirect('/review')



@app.route('/login', methods=['GET', 'POST'])
def login():
    users = User.query.all()
    auth  = False

    if 'submit' in request.form: 
        password = request.form['8aW4GAk6Q5yz'] if request.form['8aW4GAk6Q5yz'] else None

        if password:
            for user in users:
                if user.password:
                    if hash.pbkdf2_sha256.verify(password, user.password):
                        auth = True
                        break

    if auth:
        session['type'] = user.type
        session['id']   = user.id
        return redirect('/memories')

    if 'user' in session:
        session.clear()

    return render_template('login.html')



@app.route('/login/<string:code>')
def login_with_link(code):
    users = User.query.all()
    auth  = False

    for user in users:
        if user.code:
            if user.code == code:
                auth = True
                break

    if auth:
        session['type'] = user.type
        session['id']   = user.id

        if 'link' in session:
            session.pop('link')
            return render_template('link.html', code=user.code)

        else: return redirect('/memories')

    if 'user' in session:
        session.clear()

    return redirect('/login')



@app.route('/settings')
def settings():
    return render_template('settings.html')



@app.route('/stats')
def stats():
    pending = Memory.query.filter_by(approved=False, rejected=False, public=True).count()
    private = Memory.query.filter_by(public=False).count()
    public  = Memory.query.filter_by(approved=False, public=True).count()

    memories = {
        'Pending': pending,
        'Private': private,
        'Public':  public,
        'Total':   pending + private + public
    }

    pages = Page.query.all()

    return render_template('stats.html', memories=memories, pages=pages)



@app.route('/settings/password', methods=['GET', 'POST'])
def change_password():
    if 'id' not in session:
        return redirect('/login')

    if 'submit' in request.form:
        old = request.form['3DMcpgW1TE20'].strip() if request.form['3DMcpgW1TE20'] else None
        new = request.form['jeexVIObu6vo'].strip() if request.form['jeexVIObu6vo'] else None

        user = User.query.get(int(session['id']))

        if hash.pbkdf2_sha256.verify(old, user.password):
            if valid_password(new):
                user.password = hash.pbkdf2_sha256.encrypt(new)

                db.session.commit()
                return redirect('/settings')

    return render_template('password.html')



def valid_password(pw):
    allowed = 'abcdefghijklmnopqrstuvwxyz01234656789!-@#$%^&*(=)?+'

    if len(pw) < 6 or len(pw) > 20:
        return False

    for char in pw.lower():
        if char not in allowed: return False

    if len(set(pw)) < 3: return False

    return True



@app.route('/settings/link')
def login_link():
    if 'id' not in session:
        return redirect('/login')

    user = User.query.get(int(session['id']))

    if not user.code:
        return redirect('/settings/link/new')

    session['link'] = True
    return redirect('/login/' + user.code)



@app.route('/settings/link/new')
def new_link():
    if 'id' not in session:
        return redirect('/login')

    user = User.query.get(int(session['id']))

    chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    code  = ''.join(random.choice(chars) for x in range(24))
    print(code)

    user.code = code
    db.session.commit()
    return redirect('/settings/link')



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



def send_mail(subject, recipients, body):
    msg = Message(subject, sender='brydevmail@gmail.com', recipients=recipients, body=body)
    mail.send(msg)



def add_page_visit(name):
    page = Page.query.filter_by(name=name).first()

    if not page:
        page = Page(name=name, visits=0)
        db.session.add(page)

    page.visits = page.visits + 1
    page.last   = int(time.time())
    db.session.commit()



if __name__ == '__main__':
    app.run()
