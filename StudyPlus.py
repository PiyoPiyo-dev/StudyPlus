import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
import time


class StudyPlus:
    def __init__(self, username, password):
        r = requests.get("https://www.studyplus.jp/")
        self.ID = ""
        self.next = ""
        web_session = r.cookies.get("_studyplus-web_session")
        self.csrf_token = BeautifulSoup(r.content, "html.parser").find(
            'meta', attrs={'name': 'csrf-token'}).get("content")
        self.cookies = {
            '_studyplus-web_session': web_session
        }
        self.headers = {
            'authority': 'www.studyplus.jp',
            'accept': 'application/json, text/html, */*',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'cache': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://www.studyplus.jp',
            'referer': 'https://www.studyplus.jp',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1 Edg/112.0.0.0',
            'x-csrf-token': self.csrf_token
        }

        json_data = {
            'username': username,
            'password': password,
            'remember_me': False,
        }
        r = requests.post('https://www.studyplus.jp/api/auth',
                          cookies=self.cookies, headers=self.headers, json=json_data)
        if(r.status_code == 200):
            self.username = json.loads(urllib.parse.unquote(
                r.cookies.get("auth")))["username"]
            self.access_token = json.loads(urllib.parse.unquote(
                r.cookies.get("auth")))["access_token"]
            self.headers["Authorization"] = "OAuth "+self.access_token
            r = requests.get(f"https://api.studyplus.jp/2/users/{self.username}",
                             cookies=self.cookies, headers=self.headers)
            _study_goals_label = [i["label"]
                                  for i in r.json()["study_goals"]]
            _study_goals_key = [i["key"] for i in r.json()["study_goals"]]
            self._study_goals = dict(
                zip(_study_goals_label, _study_goals_key))
        else:
            raise StudyPlusLoginError from None

    def followee(self):
        data = {
            'followee': self.username,
            'page': 1,
            'per_page': 100,
            'include_recent_record_seconds': 't'
        }
        r = requests.get("https://api.studyplus.jp/2/users", data=data)
        _followees = json.loads(r.text)["users"]
        if json.loads(r.text)["page"] < json.loads(r.text)["total_page"]:
            for i in range(2, json.loads(r.text)["total_page"]+1):
                data = {
                    'followee': self.username,
                    'page': i,
                    'per_page': 100,
                    'include_recent_record_seconds': 't'
                }
                _followees += json.loads(requests.get("https://api.studyplus.jp/2/users",
                                                      data=data).json().text)["users"]
        followees_name = [i["nickname"] for i in _followees]
        followees_id = [i["username"] for i in _followees]
        self.followees = dict(zip(followees_name, followees_id))
        return followees_name

    def follower(self):
        data = {
            'follower': self.username,
            'page': 1,
            'per_page': 100,
            'include_recent_record_seconds': 't'
        }
        r = requests.get("https://api.studyplus.jp/2/users", data=data)
        _followers = json.loads(r.text)["users"]
        if json.loads(r.text)["page"] < json.loads(r.text)["total_page"]:
            for i in range(2, json.loads(r.text)["total_page"]+1):
                data = {
                    'follower': self.username,
                    'page': i,
                    'per_page': 100,
                    'include_recent_record_seconds': 't'
                }
                _followers += json.loads(requests.get("https://api.studyplus.jp/2/users",
                                                      data=data).json().text)["users"]
        followers_name = [i["nickname"] for i in _followers]
        followers_id = [i["username"] for i in _followers]
        self.followers = dict(zip(followers_name, followers_id))
        return followers_name

    def study_goals(self):
        return self._study_goals

    def GetTimeLineByUserID(self, ID):
        r = requests.get(
            f"https://api.studyplus.jp/2/timeline_feeds/user/{ID}", cookies=self.cookies, headers=self.headers)
        if r.status_code == 200:
            return_list = [list(i.values())[1]["event_id"] if "feed_type" in i else (lambda: None)()
                           for i in r.json()["feeds"]]
        else:
            raise StudyPlusUserNotFoundError from None
        next = r.json()["next"]
        while True:
            time.sleep(1)
            r = requests.get(
                f"https://api.studyplus.jp/2/timeline_feeds/user/{ID}?until={next}", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return_list += [list(i.values())[1]["event_id"] if "feed_type" in i else (lambda: None)()
                                for i in r.json()["feeds"]]
            else:
                raise StudyPlusUserNotFoundError from None
            try:
                next = r.json()["next"]
            except KeyError:
                break
        return return_list

    def GetTimeLineByUserName(self, Name):
        self.followee()
        self.follower()
        try:
            ID = self.followers[Name]
        except (KeyError, AttributeError):
            try:
                ID = self.followees[Name]
            except (KeyError, AttributeError):
                raise StudyPlusUserNotFoundError from None
        r = requests.get(
            f"https://api.studyplus.jp/2/timeline_feeds/user/{ID}", cookies=self.cookies, headers=self.headers)

        if r.status_code == 200:
            return_list = [l for l in [list(i.values())[1]["event_id"] if "feed_type" in i else (lambda: None)()
                           for i in r.json()["feeds"]] if l != None]
        else:
            raise StudyPlusUserNotFoundError from None
        next = r.json()["next"]
        while True:
            time.sleep(0.1)
            r = requests.get(
                f"https://api.studyplus.jp/2/timeline_feeds/user/{ID}?until={next}", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return_list += [l for l in [list(i.values())[1]["event_id"] if "feed_type" in i else (lambda: None)()
                                            for i in r.json()["feeds"]] if l != None]
            else:
                raise StudyPlusUserNotFoundError from None
            try:
                next = r.json()["next"]
            except KeyError:
                break
        return return_list

    def GetTimeLineByGoalID(self, ID, limit=0):
        mode = not(limit == 0)
        return_list = []
        if self.ID != ID or self.next == "":
            self.ID = ID
            r = requests.get(
                f"https://api.studyplus.jp/2/timeline_feeds/study_goal/{ID}", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return_list = [l for l in [list(i.values())[1]["event_id"] if "feed_type" in i and i["feed_type"] != "ads" else (lambda: None)()
                                           for i in r.json()["feeds"]] if l != None]
            else:
                raise StudyPlusUserNotFoundError from None
            self.next = r.json()["next"]
        while True:
            if mode:
                if len(return_list) >= limit:
                    break
            time.sleep(1)
            r = requests.get(
                f"https://api.studyplus.jp/2/timeline_feeds/study_goal/{ID}?until={self.next}", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return_list += [l for l in [list(i.values())[1]["event_id"] if "feed_type" in i and i["feed_type"] != "ads" else (lambda: None)()
                                            for i in r.json()["feeds"]] if l != None]
            else:
                raise StudyPlusGoalNotFoundError from None
            try:
                self.next = r.json()["next"]
            except KeyError:
                self.next == ""
                break
        if mode:
            return return_list[0: limit]
        return return_list

    def GetTimeLineByGoalName(self, Name, limit=0):
        mode = not(limit == 0)
        try:
            ID = self._study_goals[Name]
        except (KeyError, AttributeError):
            raise StudyPlusUserNotFoundError from None
        return_list = []
        if self.ID != ID or self.next == "":
            self.ID = ID
            r = requests.get(
                f"https://api.studyplus.jp/2/timeline_feeds/study_goal/{ID}", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return_list = [l for l in [list(i.values())[1]["event_id"] if "feed_type" in i and i["feed_type"] != "ads" else (lambda: None)()
                                           for i in r.json()["feeds"]] if l != None]
            else:
                raise StudyPlusGoalNotFoundError from None
            self.next = r.json()["next"]
        while True:
            if mode:
                if len(return_list) >= limit:
                    break
            time.sleep(1)
            r = requests.get(
                f"https://api.studyplus.jp/2/timeline_feeds/study_goal/{ID}?until={self.next}", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return_list += [l for l in [list(i.values())[1]["event_id"] if "feed_type" in i and i["feed_type"] != "ads" else (lambda: None)()
                                            for i in r.json()["feeds"]] if l != None]
            else:
                raise StudyPlusGoalNotFoundError from None
            try:
                self.next = r.json()["next"]
            except KeyError:
                self.next == ""
                break
        if mode:
            return return_list[0: limit]
        return return_list

    def like(self, event_id):
        if isinstance(event_id, str):
            r = requests.post(
                f"https://api.studyplus.jp/2/timeline_events/{event_id}/likes/like", cookies=self.cookies, headers=self.headers)
            if r.status_code == 200:
                return True
            else:
                raise StudyPlusLikeError from None
        elif isinstance(event_id, list):
            for i in event_id:
                r = requests.post(
                    f"https://api.studyplus.jp/2/timeline_events/{i}/likes/like", cookies=self.cookies, headers=self.headers)
                if r.status_code == 200:
                    time.sleep(1)
                else:
                    raise StudyPlusLikeError from None


class StudyPlusException(Exception):
    def __init__(self, arg=""):
        self.arg = arg


class StudyPlusLoginError(StudyPlusException):
    def __str__(self):
        return "ログインに失敗しました。"


class StudyPlusUserNotFoundError(StudyPlusException):
    def __str__(self):
        return "ユーザーが見つかりませんでした。"


class StudyPlusGoalNotFoundError(StudyPlusException):
    def __str__(self):
        return "達成目標が見つかりませんでした。"


class StudyPlusLikeError(StudyPlusException):
    def __str__(self):
        return "いいねに失敗しました。"


if __name__ == "__main__":
    # ログイン
    Email = ""
    Password = ""
    studyplus = StudyPlus(Email, Password)
    # フォロー中を取得
    studyplus.followee()
    # フォロワーを取得
    studyplus.follower()
    # 達成目標を取得
    studyplus.study_goals()
    # ユーザーIDからタイムラインを取得
    UserID = ""
    studyplus.GetTimeLineByUserID(UserID)
    # ユーザー名からタイムラインを取得
    UserName = ""
    studyplus.GetTimeLineByUserName(UserName)
    # 達成目標IDからタイムラインを取得(limitで取得数を指定)
    GoalID = ""
    limit = 50
    studyplus.GetTimeLineByGoalID(GoalID, limit=limit)
    # 達成目標からタイムラインを取得(limitで取得数を指定)
    GoalName = ""
    limit = 50
    studyplus.GetTimeLineByGoalName(GoalName, limit=limit)
    # タイムラインIDからいいねを実行
    TimeLineID = ""
    studyplus.like(TimeLineID)

