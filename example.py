from StudyPlus import *

Email = ""
Password = ""
studyplus = StudyPlus(Email, Password)
# 特定のユーザーを全いいねする
TargetUserName = ""
studyplus.like(studyplus.GetTimeLineByUserName(TargetUserName))
# 特定の達成目標をいいねする
TargetGoalName = ""
Amount = 100
for i in range(Amount//30):
    studyplus.like(studyplus.GetTimeLineByGoalName(TargetGoalName, limit=30))
studyplus.like(studyplus.GetTimeLineByGoalName(
    TargetGoalName, limit=Amount % 30))
