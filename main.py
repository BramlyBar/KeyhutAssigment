# !/usr/bin/env python
import gitlab
from apscheduler.schedulers.blocking import BlockingScheduler
import sys
import datetime


# here we use try-except as we are going to try changing mr, which may fail
def comment_and_close_mr(mr, comment_content):
    try:
        mr_note = mr.notes.create({'body': str(comment_content)})
        mr.state_event = 'close'
        mr.save()
        return True
    except:
        return False


# calculates the difference in days between given date in it's format and today's date
def days_diff(given_date_time):
    time_split = given_date_time.split("T")
    date = datetime.date.fromisoformat(time_split[0])
    time = datetime.time.fromisoformat(time_split[1].split(".")[0])
    date_time = datetime.datetime.combine(date, time)
    return (datetime.datetime.now() - date_time).days


# here we use try-except as we are going to try accessing a specific gitlab repo by url and token, which may fail
def main_job(group_id, url_given, token_given):
    try:
        gl = gitlab.Gitlab(url=url_given, private_token=token_given)
        group = gl.groups.get(int(group_id))
        proj_list = group.projects.list(all=True)
        for proj in proj_list:
            project = gl.projects.get(proj.id)
            mr_list = project.mergerequests.list(all=True, state='opened')
            for mr in mr_list:
                changed_files_count = mr.changes()["changes_count"]
                if int(changed_files_count) > 30:
                    comment_and_close_mr(mr, "Closing due to attempt to change too many files")
                    continue
                comment_list=mr.notes.list(all=True)    
                if comment_list:  ## checking if there are any comments at all in the list
                    last_created_comment_datetime = str(comment_list[0].created_at) ## only need to check the first element as the list is sorted by creation date
                    if days_diff(last_created_comment_datetime) >= 10:
                        comment_and_close_mr(mr, "Closing due to no new comment added in the last 10 days")
                        continue
    except:
        return False
    return True


def main():
    given_url = input("Please enter desired gitlab url:\n")
    given_key = input("Please enter private key which we will use here:\n")
    given_group = input("Please enter group id which we will use here:\n")
    if given_group.isdigit():
        try:
            sche = BlockingScheduler()
            sche.add_job(main_job(int(given_group), given_url, given_key), 'interval', hours=12)
            sche.start()
            return True
        except:
            return False
    else:
        return False


if __name__ == "__main__":
    main_ret = main()
    if main_ret:
        sys.exit(0)
    else:
        sys.exit(1)






