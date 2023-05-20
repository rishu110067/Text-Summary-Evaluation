from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

# needed for summary model
from transformers import pipeline

# needed for BERT Similarity Score
from sentence_transformers import SentenceTransformer, util

# needed for TER score
from torchmetrics import TranslationEditRate

# needed for METEOR Score
import nltk
nltk.download('omw-1.4')
nltk.download('punkt')
nltk.download('wordnet')
from nltk.translate import meteor
from nltk import word_tokenize


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



# DATABASE CLASSES / MODELS

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
    ter_score = db.Column(db.Float, nullable=True)
    meteor_score = db.Column(db.Float, nullable=True)
    human_score = db.Column(db.Float, nullable=True)
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


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    textsum_sno = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)



# FUNCTIONS

# for predicting summary
hub_model_id = "darshkk/t5-small-finetuned-xsum"
summarizer = pipeline("summarization", model=hub_model_id)
def get_predicted_summary(text):
    output = summarizer(text)
    summary = output[0]['summary_text']
    return summary


# for getting BERT score 
st_model = SentenceTransformer('all-MiniLM-L6-v2')
def get_score(predicted_summary, gold_summary):
    pred_embedding = st_model.encode([predicted_summary])
    gt_embedding = st_model.encode([gold_summary])
    sim = util.cos_sim(pred_embedding, gt_embedding)
    sc = format(sim[0][0], '.4')
    return sc


# for getting TER score
ter = TranslationEditRate()
def get_ter_score(predicted_summary, gold_summary):
    ter_score = (float)(ter(predicted_summary, gold_summary))
    ter_score = format(ter_score, '.4')
    return ter_score


# for getting METEOR score
def get_meteor_score(predicted_summary, gold_summary):
    meteor_score = meteor([word_tokenize(gold_summary)], word_tokenize(predicted_summary))
    meteor_score = format(meteor_score, '.4')
    return meteor_score


# for getting Average Human Evaluation Score
def get_avg_score(textsum_sno):
    scores = Score.query.filter_by(textsum_sno=textsum_sno).all()
    num = 0
    den = 0
    for score in scores:
        num += score.score
        den += 1
    avg_score = int(num*100 / den) / 100
    return avg_score



# ROUTES / APIS

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
    for textsum in allTextSum:
        score = Score.query.filter_by(textsum_sno=textsum.sno, user_id=current_user.id).first()
        textsum.human_score = None
        if score:
            textsum.human_score = int(score.score)
    return render_template('evaluate.html', allTextSum=allTextSum)


@app.route('/evaluate/update_score/<int:sno>/<int:human_score>', methods=['GET', 'POST'])
@login_required
def evaluate_update_score(sno, human_score):
    # update score
    score = Score.query.filter_by(user_id=current_user.id, textsum_sno=sno).first()
    if score:
        score.score = human_score
    else:
        score = Score(textsum_sno=sno, user_id=current_user.id, score=human_score)
    db.session.add(score)
    # updating textsum
    textsum = TextSum.query.filter_by(sno=sno).first()
    textsum.human_score = get_avg_score(sno)
    db.session.add(textsum)
    db.session.commit()
    return redirect('/evaluate')


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
        if request.form['predicted_summary'] == '':
            return render_template('add.html', text=text, predicted_summary=predicted_summary)

        # request from get bert similarity score button
        elif request.form['actual_summary'] != '' and not request.form['user_score']:
            cos_sim_score = get_score(predicted_summary, actual_summary)
            ter_score = get_ter_score(predicted_summary, actual_summary)
            meteor_score = get_meteor_score(predicted_summary, actual_summary)
            return render_template('add.html', text=text, predicted_summary=predicted_summary, actual_summary=actual_summary, cos_sim_score=cos_sim_score, ter_score=ter_score, meteor_score=meteor_score)
    
        # request from submit button
        else:
            # saving textsum
            cos_sim_score = get_score(predicted_summary, actual_summary)
            ter_score = get_ter_score(predicted_summary, actual_summary)
            meteor_score = get_meteor_score(predicted_summary, actual_summary)
            user_score = request.form['user_score']
            textsum = TextSum(text=text, predicted_summary=predicted_summary, actual_summary=actual_summary, cos_sim_score=cos_sim_score, human_score=user_score, ter_score=ter_score, meteor_score=meteor_score)
            db.session.add(textsum)
            db.session.commit()
            # saving score
            score = Score(user_id=current_user.id, textsum_sno=textsum.sno, score=user_score)
            db.session.add(score)
            db.session.commit()
            return redirect("/dashboard")   

    return render_template('add.html')


@app.route('/textsum/update/<int:sno>',  methods=['GET', 'POST'])
@login_required
def update(sno):
    if request.method == "POST":
        text = request.form['text']
        actual_summary = request.form['actual_summary']
        predicted_summary = get_predicted_summary(text)
        user_score = request.form['user_score']

        # if user hasn't given the score then don't save it
        if user_score == 'None':
            return redirect("/dashboard")

        # updating score
        user_score = int(user_score)
        score = Score.query.filter_by(user_id=current_user.id, textsum_sno=sno).first()
        if score:
            score.score = user_score
        else:
            score = Score(user_id=current_user.id, textsum_sno=sno, score=user_score)
        db.session.add(score)

        # updating textsum
        textsum = TextSum.query.filter_by(sno=sno).first()
        textsum.text = text
        textsum.actual_summary = actual_summary
        textsum.predicted_summary = predicted_summary
        textsum.cos_sim_score = get_score(predicted_summary, actual_summary)
        textsum.ter_score = get_ter_score(predicted_summary, actual_summary)
        textsum.meteor_score = get_meteor_score(predicted_summary, actual_summary)
        textsum.human_score = get_avg_score(sno)
        db.session.add(textsum)
        db.session.commit()
        return redirect("/dashboard")
    
    textsum = TextSum.query.filter_by(sno=sno).first()
    score = Score.query.filter_by(textsum_sno=sno, user_id=current_user.id).first()
    user_score = None
    if score:
        user_score = int(score.score)
    return render_template('update.html', textsum=textsum, user_score=user_score)


@app.route('/textsum/delete/<int:sno>')
@login_required
def delete(sno):
    # delete textsum
    textsum = TextSum.query.filter_by(sno=sno).first()
    db.session.delete(textsum)
    # delete score
    Score.query.filter_by(textsum_sno=sno).delete()
    db.session.commit()
    return redirect("/dashboard")


if __name__ == "__main__": 
    app.run(debug=True, port=8000) # host='192.168.208.33'
