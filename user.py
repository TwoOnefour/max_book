# @Time    : 2025/10/15 19:24
# @Author  : TwoOnefour
# @blog    : https://www.voidval.com
# @Email   : twoonefour@voidval.com
# @File    : user.py
import requests



class User:
    def __init__(self, username, password, session):
        self.username = username
        self.password = password
        self.session : requests.Session = session
        self.loginStatus = False

    def login(self):
        """
        {
            "status": 200,
            "msg": "登录成功",
            "datas": {
                "token": "xxx",
                "callback": "https:\/\/max.book118.com\/index.php?g=User&m=Index&a=login&token=xxx"
            }
        }
        :param session:
        :return:
        """
        API = "https://max.book118.com/open/login/login/passwordlogin.html"
        res = self.session.post(API, data={"username": self.username, "password": self.password})
        if res.status_code != 200:
            return False
        json = res.json()
        if json["status"] != 200 or json.get("datas") is None:
            return False

        max_u_token = json["datas"]["token"]
        callback = json["datas"]["callback"]
        res = self.session.get(callback)
        # self.session.cookies.set("max_u_token", max_u_token)
        return True

    def getUserInfo(self):
        """
        {
            "code": "200",
            "data": {
                "userid": "qaqqaxx",
                "money": "0.000",
                "messageNums": 0,
                "isAuthCard": 0,
                "legal_all_divide_money": "0.000",
                "is_company_vip": 0,
                "is_vip": 0,
                "vip_status": 0,
                "is_buy_vip": 0,
                "expire_time": ""
            },
            "message": "获取成功"
        }
        :param session:
        :return:
        """
        API = "https://max.book118.com/user_center_v1/user/Api/getUserInfo.html"
        res = self.session.get(API)
        if res.status_code != 200:
            return False
        json = res.json()
        if json["code"] != "200":
            return False
        return json["data"]["userid"]