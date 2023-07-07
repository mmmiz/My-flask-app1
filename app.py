from flask import Flask, render_template, request, redirect, flash, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
import os, pytz
from flask_login import login_user, logout_user, LoginManager, login_required, current_user, UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError


# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config["SECRET_KEY"] = os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)

# initialize the app with the extension
db.init_app(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.timezone("US/central")))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(12), nullable=False)

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=["POST", "GET"])
# @login_required
def index():
    if current_user.is_authenticated:
        if request.method == "GET":
            posts = Post.query.all()
        return render_template("index.html", posts=posts, current_user=current_user )
    else:
        flash("you need to log in to access! this page", "warning")
        return redirect(url_for("login"))

@app.route("/create", methods=["GET", "POST"])
# @login_required
def create():
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        post = Post(title=title, body=body)

        db.session.add(post)
        db.session.commit()
        return redirect("/")
    else:
        return render_template("create.html")

@app.route("/post/<int:id>", methods=["GET", "POST"])
# @login_required
def post(id):
    post = Post.query.get(id)
    return render_template('post.html', post=post)

@app.route("/post/edit/<int:id>", methods=["GET", "POST"])
# @login_required
def edit(id):
    post = Post.query.get(id)
    if request.method == "GET":
        return render_template("edit.html", post=post)
    else:
        post.title = request.form.get("title")
        post.body = request.form.get('body')
        db.session.commit()
        return redirect("/")

@app.route("/post/delete/<int:id>", methods=["GET"])
# @login_required
def delete(id):
    post = Post.query.get(id)
    db.session.delete(post)
    db.session.commit()
    return redirect("/")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User(username=username, password=generate_password_hash(password, method="sha256"))

        try:
            db.session.add(user)
            db.session.commit()
            return redirect("/")
        except IntegrityError:
            db.session.rollback()
            error_message = "Username already exists. Please choose a different username."
            return render_template("signup.html", error_message=error_message)
    else:
        # Handle GET request
        return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")
        else:
            return render_template("login.html")

    # Return a response for the case when the request method is not "POST"
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    login_user()
    return redirect("/login")



if __name__ == "__main__":
    app.run(debug=True)

