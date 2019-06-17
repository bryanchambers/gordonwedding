from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from passlib  import pwd, hash

app = Flask(__name__)
app.secret_key = 'Kw4zL8StOmb2DxyeoickGyclkaGA2eYbBEQ6'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/gordonwedding/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.debug = True



class User(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    type     = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100))



class Memory(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    text     = db.Column(db.String(50), nullable=False)
    sig      = db.Column(db.String(100), nullable=False)
    public   = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)
    skipped  = db.Column(db.Boolean, default=False)
    created  = db.Column(db.DateTime)



@app.route('/')
def home():
    return render_template('home.html', home=True)



@app.route('/gifts')
def gifts():
    return render_template('gifts.html')



@app.route('/details')
def details():
    return render_template('details.html')



@app.route('/memories')
def memories():
    if 'type' in session:
        count  = Memory.query.filter_by(approved=False, rejected=False, public=True).count()
        memories = Memory.query.filter_by(approved=True).order_by(Memory.created).all()
    
    else:
        count = 0
        memories = Memory.query.filter_by(approved=True, public=True).order_by(Memory.created).all()

    return render_template('memories.html', memories=memories, count=count)



@app.route('/share', methods=['GET', 'POST'])
def share():
    if 'submit' in request.form:
        text     = request.form['text'] if 'text' in request.form else None
        sig      = request.form['from'] if 'from' in request.form else None
        public   = True if request.form['submit'] == 'Everyone' else False
        approved = not public 

        if text and sig:
            memory = Memory(text=text, sig=sig, approved=approved, public=public)
            db.session.add(memory)
            db.session.commit()
            return redirect('/thanks')

    return render_template('share.html')



@app.route('/thanks')
def thanks():
    return render_template('thanks.html')



@app.route('/review')
def review():
    count  = Memory.query.filter_by(approved=False, rejected=False, public=True).count()
    memory = Memory.query.filter_by(approved=False, rejected=False, public=True, skipped=False).order_by(Memory.created).first()
    
    if not memory:
        skipped = Memory.query.filter_by(approved=False, rejected=False, public=True, skipped=True).all()
        if skipped: return redirect('/review/clear')

    return render_template('review.html', memory=memory, count=count)



@app.route('/review/skip/<int:id>')
def skip(id):
    memory = Memory.query.get(id)
    
    memory.skipped = True
    db.session.commit()
    return redirect('/review')



@app.route('/review/clear')
def clear():
    memories = Memory.query.filter_by(approved=False, rejected=False, skipped=True).all()
    
    for memory in memories:
        memory.skipped = False

    db.session.commit()
    return redirect('/review')



@app.route('/review/approve/<int:id>')
def approve(id):
    memory = Memory.query.get(id)

    memory.approved = True
    db.session.commit()
    return redirect('/review')



@app.route('/review/reject/<int:id>')
def reject(id):
    memory = Memory.query.get(id)
    
    memory.rejected = True
    db.session.commit()
    return redirect('/review')



@app.route('/login', methods=['GET', 'POST'])
def login():
    password = None
    skip_bookmark = False

    if '3fQ3C2P2v8z2' in request.args:
        password = request.args['3fQ3C2P2v8z2'] if request.args['3fQ3C2P2v8z2'] else None
        skip_bookmark = True

    elif 'submit' in request.form: 
        password = request.form['8aW4GAk6Q5yz'] if request.form['8aW4GAk6Q5yz'] else None

    if password:
        users = User.query.all()
        auth  = False

        for user in users:
            if user.password:
                if hash.pbkdf2_sha256.verify(password, user.password): auth = True

        if auth:
            session['type'] = user.type
            
            if skip_bookmark:
                return redirect('/memories')

            else:
                return render_template('bookmark.html')

    if 'user' in session: session.pop('type')
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/memories')


if __name__ == '__main__':
	app.run()