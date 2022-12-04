from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

# needed for BERT Similarity Score
from sentence_transformers import SentenceTransformer, util

# needed for API requests
import requests

app = Flask(__name__)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
app.config['SECRET_KEY'] = 'thisisasecretkey' 
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    def get(id):
        return User.query.filter_by(id=id).first()


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("The username already exists. Please choose a different one.")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


class TextSum(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(10000), nullable=False)
    predicted_summary = db.Column(db.String(1000), nullable=False)
    actual_summary = db.Column(db.String(1000), nullable=False)
    cos_sim_score = db.Column(db.Float, nullable=True)
    human_score = db.Column(db.Integer, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self) -> str:
        return f"{self.sno} - {self.text}"


class QuickSummary(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(10000), nullable=False)
    predicted_summary = db.Column(db.String(1000), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self) -> str:
        return f"{self.sno} - {self.text}"



# for getting BERT score 
st_model = SentenceTransformer('all-MiniLM-L6-v2')
def get_score(predicted_summary, actual_summary):
    pred_embedding = st_model.encode([predicted_summary])
    gt_embedding = st_model.encode([actual_summary])
    sim = util.cos_sim(pred_embedding, gt_embedding)
    sc = format(sim[0][0], '.4')
    return sc


# for predicting summary
error_message = "Couldn't get the summary! Please try again after a minute!"
API_TOKEN = "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" 
API_URL = "https://api-inference.huggingface.co/models/csebuetnlp/mT5_m2o_english_crossSum"
headers = {"Authorization": f"Bearer {API_TOKEN}"}
def get_predicted_summary(text):
    try: 
        response = requests.post(API_URL, headers=headers, json=text) # may get timeout error
        output = response.json()
        return output[0]['summary_text']
    except:
        return error_message


@app.route('/')
def home(): 
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required 
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    allTextSum = TextSum.query.all()
    return render_template('dashboard.html', allTextSum=allTextSum)


@app.route('/evaluate', methods=['GET', 'POST'])
@login_required
def evaluate():
    allTextSum = TextSum.query.all()
    return render_template('evaluate.html', allTextSum=allTextSum)


@app.route('/evaluate/update/<int:sno>', methods=['GET', 'POST'])
@login_required
def evaluate_update(sno):
    textSum = TextSum.query.filter_by(sno=sno).first()
    textSum.human_score = request.form['human_score']
    db.session.add(textsum)
    db.session.commit()
    allTextSum = TextSum.query.all()
    return render_template('evaluate.html', allTextSum=allTextSum)


@app.route('/quick_summary', methods=['GET', 'POST'])
@login_required
def quick_summary():    
    if request.method == "POST":
        text = request.form['text']
        if len(text) <= 10:
            predicted_summary = text
        else:
            predicted_summary = get_predicted_summary(text)
        
        allQuickSummary = QuickSummary.query.filter_by(user_id=current_user.id).all()
        return render_template('quick_summary.html', text=text, predicted_summary=predicted_summary, allQuickSummary=allQuickSummary)

    allQuickSummary = QuickSummary.query.filter_by(user_id=current_user.id).all()
    return render_template('quick_summary.html', allQuickSummary=allQuickSummary)


@app.route('/quick_summary/save', methods=['GET', 'POST'])
@login_required
def save_quick_summary():
    text = request.form['text']
    if len(text) <= 10:
        predicted_summary = text
    else:
        predicted_summary = get_predicted_summary(text)
    
    quick_summary = QuickSummary(text=text, predicted_summary=predicted_summary, user_id=current_user.id)
    db.session.add(quick_summary)
    db.session.commit()
    return redirect("/quick_summary")


@app.route('/quick_summary/delete/<int:sno>')
@login_required
def delete_quick_summary(sno):
    quick_summary = QuickSummary.query.filter_by(sno=sno).first()
    db.session.delete(quick_summary)
    db.session.commit()
    return redirect("/quick_summary")


@app.route('/textsum', methods=['GET', 'POST'])
@login_required
def textsum():  
    if request.method == "POST":
        text = request.form['text']
        actual_summary = request.form['actual_summary']
        if len(text) <= 10:
            predicted_summary = text
        else:
            predicted_summary = get_predicted_summary(text)

        # request from get predicted summary button
        if request.form['predicted_summary'] == '' or request.form['predicted_summary'] == error_message:
            return render_template('add.html', text=text, predicted_summary=predicted_summary)

        # request from get bert similarity score button
        elif request.form['actual_summary'] != '' and not request.form['human_score']:
            cos_sim_score = get_score(predicted_summary, actual_summary)
            return render_template('add.html', text=text, predicted_summary=predicted_summary, actual_summary=actual_summary, cos_sim_score=cos_sim_score)
    
        # request from submit button
        else:
            cos_sim_score = get_score(predicted_summary, actual_summary)
            human_score = request.form['human_score']
            textsum = TextSum(text=text, predicted_summary=predicted_summary, actual_summary=actual_summary, cos_sim_score=cos_sim_score, human_score=human_score)
            db.session.add(textsum)
            db.session.commit()
            return redirect("/dashboard")   

    return render_template('add.html')


@app.route('/textsum/update/<int:sno>',  methods=['GET', 'POST'])
@login_required
def update(sno):
    if request.method == "POST":
        textsum = TextSum.query.filter_by(sno=sno).first()
        text = request.form['text']
        actual_summary = request.form['actual_summary']
        predicted_summary = get_predicted_summary(text)
        textsum.text = text
        textsum.actual_summary = actual_summary
        textsum.predicted_summary = predicted_summary
        textsum.cos_sim_score = get_score(predicted_summary, actual_summary)
        textsum.human_score = request.form['human_score']
        db.session.add(textsum)
        db.session.commit()
        return redirect("/dashboard")   
    
    textsum = TextSum.query.filter_by(sno=sno).first()
    return render_template('update.html', textsum=textsum)


@app.route('/textsum/delete/<int:sno>')
@login_required
def delete(sno):
    textsum = TextSum.query.filter_by(sno=sno).first()
    db.session.delete(textsum)
    db.session.commit()
    return redirect("/dashboard")


if __name__ == "__main__": 
    app.run(debug=True, host='192.168.208.33', port=8000)

