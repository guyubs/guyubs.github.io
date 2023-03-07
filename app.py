# app.py
"""
flask框架，

"""

from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # 创建一个Flask应用程序

############################################
# 数据库
############################################
# 配置应用程序的数据库URI为SQLite，默认情况下，Flask-SQLAlchemy会将应用程序与本地SQLite数据库进行连接。如果你想使用其他的数据库，可以修改这个配置项。
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # 开启了 SQLAlchemy track modifications 追踪修改功能，用于在开发时自动更改数据库模型。
app.secret_key = '\xc9ixnRb\xe40\xd4\xa5\x7f\x03\xd0y6\x01\x1f\x96\xeao+\x8a\x9f\xe4'  # 设置Flask应用程序的密钥，用于保护用户会话数据。
db = SQLAlchemy(app)  # 使用SQLAlchemy扩展创建了一个SQLAlchemy数据库实例，可以通过这个实例来管理应用程序的数据库。

# 定义ORM
'''
定义了一个User类，该类继承自db.Model类，代表了一个数据库表。
在User类中定义了id、username、password、email等属性，这些属性对应了表中的字段。
通过ORM，我们可以通过操作User类来进行对数据库表的增删改查等操作。
'''


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return '<User %r>' % self.username


# 创建表格、插入数据
@app.before_first_request
def create_db():
    db.drop_all()  # 每次运行，先删除再创建
    db.create_all()

    admin = User(username='admin', password='root', email='admin@example.com')
    db.session.add(admin)

    guests = [User(username='guest1', password='guest1', email='guest1@example.com'),
              User(username='guest2', password='guest2', email='guest2@example.com'),
              User(username='guest3', password='guest3', email='guest3@example.com'),
              User(username='guest4', password='guest4', email='guest4@example.com')]
    db.session.add_all(guests)
    db.session.commit()


############################################
# 辅助函数、装饰器
############################################

# 登录检验（用户名、密码验证）

def valid_login(username, password):
    # user = User.query.filter(and_(User.username == username, User.password == password)).first()
    user = User.query.filter_by(username=username, password=password).first()  # 避免使用SQL query

    if user:
        return True
    else:
        return False


# 注册检验（用户名、邮箱验证）
'''
检查数据库中是否已经存在一个具有相同用户名或电子邮件的用户。
User.query：假设有一个SQLAlchemy User模型来表示数据库中的用户。
User.query 创建一个查询对象，用于与 User表进行交互。
filter(or_(User.username == username, User.email == email))：这将查询过滤为仅包括用户名或电子邮件与输入值匹配的用户。
or_是一个函数，将两个或多个过滤条件与 OR 运算符结合起来。
first()：这从过滤的查询中检索第一个结果，如果没有结果，则返回 None。
if user:：这检查 user 变量是否不是 None，这意味着系统中已经存在具有相同用户名或电子邮件的用户。
return False：如果已经存在用户，则函数返回 False。
else: return True：如果不存在用户，则函数返回 True。
'''


def valid_register(username, email):
    # user = User.query.filter(or_(User.username == username, User.email == email)).first()
    user = User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first()  # 不用SQL query

    if user:
        return False
    else:
        return True


# 防止直接访问panel页面
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # if g.user:
        if session.get('username'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login', next=request.url))  #

    return wrapper


############################################
# 路由
############################################

# 1.主页
@app.route('/')
def index():
    return render_template('index.html')


# 2.登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            session['username'] = request.form.get('username')
            return redirect(url_for('panel'))
        else:
            error = '错误的用户名或密码！'

    return render_template('login.html', error=error)


# 3.退出
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('您已成功退出', 'success')
    return redirect(url_for('index'))


# 4.注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if request.form['username'] == '' or request.form['email'] == '' or request.form['password1'] == '':
            error = '用户名、密码、邮箱不能为空！'

        elif request.form['password1'] != request.form['password2']:
            error = '两次密码不相同！'

        elif valid_register(request.form['username'], request.form['email']):
            user = User(username=request.form['username'], password=request.form['password1'],
                        email=request.form['email'])
            db.session.add(user)  # 添加用户注册信息到数据库
            db.session.commit()  # 确认更改并将其保存到数据库中。

            flash("注册成功！")
            return redirect(url_for('login'))
        else:
            error = '该用户名或邮箱已被注册！'

    return render_template('register.html', error=error)


# 5.操作页面
@app.route('/panel')
@login_required  # 满足login_required 才能显示panel页面
def panel():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    return render_template("panel.html", user=user, username=session.get('username'))


if __name__ == '__main__':
    app.run(debug=True)
