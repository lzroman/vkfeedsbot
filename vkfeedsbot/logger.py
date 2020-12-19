import datetime

def log(msg):
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(''.join([time, ':\t', str(msg)]), flush=True)