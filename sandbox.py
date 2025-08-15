import datetime

from apscheduler.triggers.cron import CronTrigger

if __name__ == "__main__":
    now = datetime.datetime.now()
    cron = CronTrigger.from_crontab('0 8-23 * * *')
    print(f'Now is: {now}')
    print(f'Next:   {cron.get_next_fire_time(None, now)}')