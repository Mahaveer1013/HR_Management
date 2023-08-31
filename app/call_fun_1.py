import schedule
from call_fun import fun
import time

def schedule_function(a):
    schedule.every(3).seconds.do(fun,a)

schedule_function(111)

while schedule.get_jobs():
    schedule.run_pending()
    time.sleep(1)