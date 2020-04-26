# 部署

- 修改config.py

```
# 修改用户名和密码， 数据库名
SQLALCHEMY_DATABASE_URI = "mysql://root:redhat@localhost/student"
```


- 初始化数据库

```
python3 manage.py initdb
```


- 开启服务
```
python3 manage.py runserver
```



# 运行效果图











