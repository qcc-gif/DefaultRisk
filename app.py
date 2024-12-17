from flask import Flask, render_template, request, redirect, url_for, flash,session,send_file
import os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import sqlite3 
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from data_analysis import generate_analysis_plots
matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
IMAGE_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
DB_NAME='users.db'


# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# 加载模型
# MODEL_PATH = 'model.pkl'
# model = joblib.load(MODEL_PATH)

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
    conn.commit()
    conn.close()

@app.route('/register',methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        password = request.form.get('password','').strip()
        if not email or not password:
            flash('Email and password are required.','danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)

        try:
            conn=sqlite3.connect(DB_NAME)
            cursor=conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.','scuess')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered. Please use another email.','danger')
    return render_template('register.html')

@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print(request.form)# 打印表单数据
        email = request.form.get('email','').strip()
        password = request.form.get('password','').strip()
        #如果没有输入邮箱或密码，显示错误提示
        if not email or not password:
            flash('Email and password are required.','danger')
            return render_template('login.html')
        #查询用户数据
        conn=sqlite3.connect(DB_NAME)
        cursor=conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=?', (email,))
        user=cursor.fetchone()
        conn.close()
        #如果用户存在并且密码正确
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['email'] = user[1]
            flash('Logged in successfully!','success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.','danger')
    #如果是GET请求，或者表单验证失败，显示登录页面
    return render_template('login.html')

@app.route('/')
def home():
    """欢迎主页"""
    return render_template('home.html')

@app.route('/index')
def index():
    """主页面"""
    if 'user_id' not in session:
        flash('Please log in first.','warning')
        return redirect(url_for('login'))
    return render_template('index.html',email=session.get('email'))

@app.route('/logout')
def logout():
    """注销用户"""
    session.clear()
    flash('Logged out successfully.','info')
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """上传文件并使用模型预测"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('upload'))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                #读取文件
                data = pd.read_csv(filepath)

                #执行预测
                # predictions = model.predict(data)
                # data['Prediction'] = predictions

                #将预测结果保存到新的csv文件
                result_filename = f'predicted_{filename}'
                result_filepath = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
                data.to_csv(result_filepath, index=False)
                return render_template('upload.html', download_link=url_for('download_file', filename=result_filename),result_filename=result_filename )
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                return redirect(request.url)

    return render_template('upload.html')

@app.route('/download/<filename>')
def download_file(filename):
    """提供下载功能"""
    return send_file(os.path.join(app.config['RESULTS_FOLDER'], filename), as_attachment=True)

@app.route('/charts')
def charts():
    """展示现有统计图表"""
    # 图表文件路径
    charts = [
        {'title': 'Loan Amount Distribution', 'path': url_for('static', filename='images/Pasted image 20241217122814.png')},
        {'title':'Missing Percent','path':url_for('static',filename='images/Pasted image 20241217122823.png')},
        {'title':'Loan Status Per Year','path':url_for('static',filename='images/Pasted image 20241217122834.png')},
        {'title':'Top 30 States','path':url_for('static',filename='images/Pasted image 20241217122841.png')},
        {'title':'Loan Time Per Title','path':url_for('static',filename='images/Pasted image 20241217122847.png')},
        {'title':'Loan Time Per Length','path':url_for('static',filename='images/Pasted image 20241217122852.png')},
        {'title':'Loan Time Per Time','path':url_for('static',filename='images/Pasted image 20241217122857.png')},
        
        {'title':'Good loans and bad loans percent','path':url_for('static',filename='images/Pasted image 20241217122903.png')},
        {'title':'Int Rate Distribution','path':url_for('static',filename='images/Pasted image 20241217122931.png')},
        # {'title':'Loan Time Per Time','path':url_for('static',filename='images/Pasted image 20241217122857.png')},
        # {'title':'Loan Time Per Time','path':url_for('static',filename='images/Pasted image 20241217122857.png')},
    ]
    return render_template('charts.html', charts=charts)


@app.route('/generate',methods=['POST','GET'])
def generate():
    if request.method=='POST':
        #上传数据文件
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file=request.files['file']
        if file.filename=='':
            flash('No file selected')
            return redirect(request.url)
        if file:
            filename=secure_filename(file.filename)
            filepath=os.path.join(app.config['UPLOAD_FOLDER'],filename)
            file.save(filepath)
            print(f'File uploaded successfully:{filename}')

            #加载数据
            try:
                analysis_results = generate_analysis_plots(filepath, app.config['RESULTS_FOLDER'])
                if analysis_results:
                    return render_template('charts.html', charts=analysis_results)
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                return redirect(request.url)

    return render_template('generate.html')

@app.route('/profile',methods=['GET','POST'])
def profile():
    #如果用户已经登录，显示用户个人信息详情
    if 'user_id' in session:
        user_id=session.get('user_id')
        email=session.get('email')
        return render_template('profile.html',email=email)
       
    #如果用户没有登录，显示默认信息，提示点击登录按钮跳转登录页面
    else:
        flash('Please log in first.','danger')
        return redirect(url_for('login'))


    

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
