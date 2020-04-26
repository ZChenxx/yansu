"""
文件名: views.py
日期: 2019-03-17  
作者: lvah
联系: xc_guofan@qq.com
代码描述: 



"""
# 导入home的蓝图对象
import json
import os
from random import randrange
import pandas as pd

from example.commons import Faker
from pyecharts.charts import Bar, Line, Scatter, Pie
from pyecharts import options as opts

from app import db, app
from app.home.forms import LoginForm, RegisterForm, PwdForm, UploadForm
from app.home.utils import is_login, change_filename
from app.models import User

from . import home
from flask import render_template, flash, session, redirect, url_for, request, jsonify, send_from_directory, \
    make_response
from werkzeug.security import generate_password_hash


@home.route('/')
def index():
    if session.get('user'):
        file_save_path = app.config.get('UPLOAD_FILE_DIR')
        old_grades = os.listdir(file_save_path)

        grades = []
        for grade in old_grades:
            filename = os.path.join(file_save_path, grade)
            grade_name = grade.split('.')[0]
            count = pd.read_excel(filename, skiprows=2).shape[0]
            grades.append((grade_name, count, grade))
        return render_template('home/index.html', grades=grades)
    else:
        return redirect(url_for('home.login'))


# 注册页面
@home.route('/register/', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # 1. 从前端获取用户输入的值;
        email = form.email.data
        username = form.username.data
        password = form.password.data

        # 2. 判断用户是否已经存在? 如果返回位None，说明可以注册;
        u = User.query.filter_by(name=username).first()
        if u:
            flash("用户%s已经存在" % (u.name))
            return redirect(url_for('home.register'))
        else:
            u = User(name=username, email=email)
            u.password = generate_password_hash(password)  # 对于密码进行加密
            db.session.add(u)
            db.session.commit()
            flash("注册用户%s成功" % (u.name))
            return redirect(url_for('home.login'))
    return render_template('home/register.html',
                           form=form)


@home.route('/login/', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    # print(form.password.data)
    # print(form.username.data)
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(name=username).first()
        if user and user.verify_password(password):
            # session信息的保存
            session['user_id'] = user.id
            session['user'] = user.name
            flash("用户%s登录成功" % (user.name))

            # 从index蓝图里面寻找index函数;
            return redirect(url_for('home.index'))
        else:
            flash("用户登录失败")
            return redirect(url_for('home.login'))
    return render_template('home/login.html',
                           form=form)


@home.route('/logout/')
@is_login
def logout():
    session.pop('user_id', None)
    session.pop('user', None)

    return redirect(url_for('home.login'))


# 修改密码
@home.route('/pwd/', methods=['GET', 'POST'])
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        # 获取当前登录用户的密码
        user = User.query.filter_by(name=session.get('user')).first()
        # print(session.get('name'))
        # 判断用户的旧密码是否正确
        if user.verify_password(form.old_pwd.data):
            # ********数据库里面的是password
            user.password = generate_password_hash(form.new_pwd.data)
            db.session.add(user)
            db.session.commit()
            flash("密码更新成功")
        else:
            flash("旧密码错误, 请重新输入")
        return redirect(url_for('home.pwd'))
    return render_template('home/pwd.html', form=form)


@home.route('/upload/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # 获取上传文件的文件名;
        filename = form.file.data.filename
        # 文件名称-将来用作图片标题
        global title
        title = filename.split('.')[0]
        # 将上传的文件保存到服务器;
        file_save_path = app.config.get('UPLOAD_FILE_DIR')
        if not os.path.exists(file_save_path):
            os.makedirs(file_save_path)
        filename = os.path.join(file_save_path, filename)
        form.file.data.save(filename)

        import pandas as pd
        global df
        # df = pd.read_excel(filename, skiprows=2)  #略去2行的数据，自上而下的开始略去数据的行
        df = pd.read_excel(filename)

        # 折线图(排名连续)
        # df = df.sort_values(by="名次", ascending=True)  #通过列名 正序

        # 获取类型和分析维度
        # kind = form.kind.data
        element = form.element.data
        dict_elements = dict([(1, "是否为国企"), (2, "是否与专业相关"), (3, '是否已跳槽'),(4,'就业满意度（十分满意、满意、一般满意、不满意）'),(5,'毕业年级')
                              ,(6,'薪资（月）')])
        # dict_kinds = dict([(1, "折线图"), (2, "散点图"), (3, '饼状图'), (4, '柱状图')])
        global str_element
        str_element = dict_elements.get(element)
        flash("上传成功", 'ok')
        # if == 1:
        #     return render_template('home/line.html')
        # elif == 2:
        #     return render_template('home/scatter.html')
        if element in [1,2,3,4]:
            return render_template('home/pie.html')
        elif element in [5,6]:
            return render_template('home/bar.html')

        # return redirect(url_for('home.upload'))
        return render_template('home/upload.html', form=form)
    return render_template('home/upload.html', form=form)


# @home.route('/line/')
# def get_line_chart():
#     from pyecharts import options as opts
#     df1 = df.sort_values(by=str_element).head(10)
#
#     # print(df1)
#     x = df1['姓名']
#     y1 = df1[str_element]
#     c = (
#         Line()
#             .add_xaxis(list(x))
#             .add_yaxis("后10名", list(y1),
#                        is_smooth=True,
#                        markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="max")]),
#
#                        )
#             .set_global_opts(title_opts=opts.TitleOpts(title="%s-%s-%s" % (title, str_element)))
#     )
#     return c.dump_options()


# def get_all_grade():
#     """获取所有已上传班级的信息"""
#     file_save_path = app.config.get('UPLOAD_FILE_DIR')
#     if not os.path.exists(file_save_path):
#         os.makedirs(file_save_path)
#
#     # 读取所有已经上传班级的信息;
#     grades = os.listdir(file_save_path)
#
#     # 添加信息到列表中
#     dfs = []
#     for grade in grades:
#         grade_name = grade.split('.')[0]
#         filename = os.path.join(file_save_path, grade)
#         df1 = pd.read_excel(filename, skiprows=2)[str_element]
#         df2 = df1.sum()
#         df3 = df1.mean()
#         dfs.append((grade_name, df2, df3))
#     return dfs


@home.route('/bar/')
def get_bar_chart():
    if str_element != '薪资（月）':
        x_grade_name = list(set(df[str_element].astype(int)))
        y = []
        # a = len(df.loc[(df[str_element] == '是')])
        print(x_grade_name)
        for a in x_grade_name:
            print(a)
            x = len(df.loc[(df[str_element] == a ) & (df['是否就业'] == '是')]) / len(df.loc[(df[str_element] == a )]) * 100
            y.append(x)
        y_grade_score_sum = [_ for _ in y ]


        c = (
            Bar()
                .add_xaxis(x_grade_name)
                .add_yaxis("就业率", y_grade_score_sum
                           )

                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title="%s就业率-信息柱状图对比分析" % (str_element)),
                toolbox_opts=opts.ToolboxOpts(),
                yaxis_opts=opts.AxisOpts(name="就业率"),
                xaxis_opts=opts.AxisOpts(name="毕业年级"),
            ))
        return c.dump_options()
    else:
        x_grade_name = {'5000以下':0,'5000-100000':0,'100000-15000':0,'15000-20000':0,'20000以上':0}
        y = []
        print(x_grade_name)
        x_grade_name['5000以下'] = len(df.loc[df[str_element] < 5000])
        x_grade_name['5000-100000'] = len(df.loc[(df[str_element] >= 5000) & (df[str_element] < 10000) ])
        x_grade_name['100000-15000'] = len(df.loc[(df[str_element] >= 10000) & (df[str_element] < 15000) ])
        x_grade_name['15000-20000'] = len(df.loc[(df[str_element] >= 15000) & (df[str_element] < 20000) ])
        x_grade_name['20000以上'] = len(df.loc[(df[str_element] >= 20000)])
        x = [_ for _ in x_grade_name.keys()]
        y_grade_score_sum = [_ for _ in x_grade_name.values()]
        print(x)
        print(y_grade_score_sum)
        c = (
            Bar()
                .add_xaxis(x)
                .add_yaxis("人数", y_grade_score_sum
                           )

                .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                .set_global_opts(
                title_opts=opts.TitleOpts(title="%s-信息柱状图对比分析" % (str_element)),
                toolbox_opts=opts.ToolboxOpts(),
                yaxis_opts=opts.AxisOpts(name="人数"),
                xaxis_opts=opts.AxisOpts(name="薪资范围"),
            ))
        return c.dump_options()


# def get_data(element):
#     global str_element
#     str_element = element
#     # 获取所有上传的班级信息， 并将新上传的班级信息添加到里面去
#     dfs = get_all_grade()
#     mydf = dfs[0]
#     # 获取所有的班级名称
#     x_grade_name = [_[0] for _ in dfs]
#
#     y_grade_score_sum = [_[1] for _ in dfs]
#     y_grade_score_avg = [_[2] for _ in dfs]
#
#     c = (
#         Bar()
#             .add_xaxis(x_grade_name)
#             .add_yaxis("总和", y_grade_score_sum
#                        )
#             .add_yaxis("平均值", y_grade_score_avg,
#                        )
#             .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
#             .set_global_opts(
#             title_opts=opts.TitleOpts(title="%s-信息柱状图对比分析" % (element)),
#             toolbox_opts=opts.ToolboxOpts(),
#             yaxis_opts=opts.AxisOpts(name="班级名称"),
#             xaxis_opts=opts.AxisOpts(name="分数"),
#         ))
#     return c.dump_options()


# @home.route('/bar/avg/')
# def get_bar_avg():
#     return get_data("平均学分绩点")
#
#
# @home.route('/bar/sum/')
# def get_bar_sum():
#     return get_data("学分绩点总和")
#
#
# @home.route('/bar/wsum/')
# def get_bar_wsum():
#     return get_data("▼学分加权平均分")


@home.route('/analyze/<string:element>')
def analyze(element):
    if element == 'avg':
        return render_template('home/avg_bar.html')
    elif element == 'sum':
        return render_template('home/sum_bar.html')
    elif element == 'wsum':
        return render_template('home/wsum_bar.html')


@app.route('/scatter/')
def get_scatter_chart():
    y = df[str_element]
    x = list(range(df.shape[0]))
    c = (
        Scatter()
            .add_xaxis(x)
            .add_yaxis("", y
                       )
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(title_opts=opts.TitleOpts(title="%s-%s散点图可视化分析" % (title, str_element)),
                             toolbox_opts=opts.ToolboxOpts(),
                             yaxis_opts=opts.AxisOpts(name="班级名称"),
                             xaxis_opts=opts.AxisOpts(name="分数"),
                             ))
    return c.dump_options()


@app.route('/pie/')
def get_pie_chart():
    if str_element != '就业满意度（十分满意、满意、一般满意、不满意）':
        a = len(df.loc[(df[str_element] == '是')])
        b = len(df.loc[(df[str_element] == '否')])

        attr = ['是', '否']
        v1 = [a, b]

        data = list(zip(attr, v1))

        c = (
            Pie()
                .add(
                "",
                data,
                radius=["40%", "75%"],
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title="%s-%s分布图" % (title, str_element)),
                toolbox_opts=opts.ToolboxOpts(),
                legend_opts=opts.LegendOpts(
                    orient="vertical", pos_top="15%", pos_left="2%"
                ),
            )
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )

        return c.dump_options()

    else:
        a = len(df.loc[(df[str_element] == '满意')])
        b = len(df.loc[(df[str_element] == '十分满意')])
        c = len(df.loc[(df[str_element] == '不满意')])

        attr = ['满意', '十分满意', '不满意']
        v1 = [a, b, c]

        data = list(zip(attr, v1))

        c = (
            Pie()
                .add(
                "",
                data,
                radius=["40%", "75%"],
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title="%s-%s分布图" % (title, str_element)),
                toolbox_opts=opts.ToolboxOpts(),
                legend_opts=opts.LegendOpts(
                    orient="vertical", pos_top="15%", pos_left="2%"
                ),
            )
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        )

        return c.dump_options()





@app.route("/download/<filename>/", methods=['GET'])
def download_file(filename):
    # 需要知道2个参数, 第1个参数是本地目录的path, 第2个参数是文件名(带扩展名)
    file_save_path = app.config.get('UPLOAD_FILE_DIR')
    if not os.path.exists(file_save_path):
        os.makedirs(file_save_path)
    response = make_response(send_from_directory(file_save_path, filename, as_attachment=True))
    return response
