# -*- coding: utf-8 -*-

import os
import sys
from flask import Flask, render_template, redirect, url_for, session, flash, request

from models import db, User, TestOneResult, TestOne, db_init
from config import SECRET_KEY, SQLITE_DATABASE_NAME

app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')


# SQLAlchimy config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + SQLITE_DATABASE_NAME
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = "se_session"


# Init Database
db.app = app
db.init_app(app)


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route("/")
def index():

    if "username" not in session:
        username = os.urandom(16).hex()

        # Create new user
        u = User(name=username)

        try:
            db.session.add(u)
            db.session.commit()
            session["username"] = username
        except:
            print("Error while add user to the database")
            print(u)

        return render_template("index.html")

    username = session["username"]
    user = User.query.filter_by(name=username).first()

    if not user:
        u = User(name=username)

        try:
            db.session.add(u)
            db.session.commit()
            session["username"] = username
        except:
            print("Error while add user to the database")
            print(u)
            return render_template("error.html", msg="User not found")

        user = User.query.filter_by(name=username).first()

    # Do we have answers?
    last_question_id = TestOneResult.query.filter_by(author_id=user.id).count()

    return render_template("index.html", last_question_id=last_question_id)


@app.route('/index.html')
def index_html():
    return redirect(url_for('index'))


@app.route('/calculate_result.html')
def calculate_result():

    if "username" not in session:
        return redirect(url_for('index'))

    username = session["username"]
    user = User.query.filter_by(name=username).first()

    if not user:
        return redirect(url_for('index'))

    answers = TestOneResult.query.filter_by(author_id=user.id)

    a_count = answers.count()

    if a_count < 74:
        flash("Вы ответили не на все вопросы", category='error')
        return redirect(url_for('index'))

    groups_count_no = []
    groups_count_yes = []
    for x in [0, 1, 2, 3]:
        group_no = db.session.query(TestOneResult).join(TestOne).filter(TestOne.type == x)\
        .filter(TestOneResult.author_id == user.id).filter(TestOneResult.answer < 4)

        group_yes = db.session.query(TestOneResult).join(TestOne).filter(TestOne.type == x)\
        .filter(TestOneResult.author_id == user.id).filter(TestOneResult.answer > 4)

        groups_count_no.append(group_no.count())
        groups_count_yes.append(group_yes.count())

    return render_template('result.html', groups_count_no=groups_count_no, groups_count_yes=groups_count_yes)


@app.route('/question.html', methods=['GET', 'POST'])
def get_question():

    if "username" not in session:
        return redirect(url_for('index'))

    username = session["username"]
    user = User.query.filter_by(name=username).first()

    if not user:
        return redirect(url_for('index'))

    if request.method == "POST":
        question_id = request.args.get('question', default=0, type=int)
        answer = request.form.get('q_answer', type=int, default=0)

        if (not question_id) or (question_id > 74) or (question_id < 0):
            flash("Не указан номер вопроса", category='error')
            return redirect(url_for('index'))

        if (answer <= 0) or (answer > 7):
            flash("Указанный ответ неверный", category='error')
            return redirect(request.url)

        # Check if question_id in database
        q = TestOne.query.get(question_id)

        if not q:
            flash("Такого вопроса нет в базе", category='error')
            return redirect(url_for('index'))

        res = TestOneResult(author_id=user.id, test_one_id=question_id, answer=answer)
        db.session.add(res)
        db.session.commit()

        next_q = q.id + 1
        return redirect(url_for("get_question", question=next_q))

    # If it's GET
    question_id = request.args.get('question', default=0, type=int)

    if question_id:

        if question_id > 74:
            return redirect(url_for('calculate_result'))

        question = TestOne.query.get(question_id)

        if not question:
            flash("Такого вопроса нет", category='error')
            return redirect(url_for('index'))

        return render_template("question.html", user=user, question=question)

    # Well, no question_id
    # Try to get last user question.

    last_question = TestOneResult.query.filter_by(author_id=user.id).order_by(TestOneResult.id.desc()).first()

    # First time, get the first question and go
    if not last_question:
        first_question = TestOne.query.get(1)

        if not first_question:
            print("Database nas no questions")
            return redirect(url_for('index'))

        return render_template("question.html", user=user, question=first_question)

    if last_question.test_one_id >= 74:
        return redirect(url_for('calculate_result'))

    current_question = TestOne.query.get(last_question.test_one_id+1)
    return render_template("question.html", user=user, question=current_question)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1] == "init":
            db_init()

    app.run(port=5000)
