class status:
    def __init__(self):
        self.name = 'regular'
        self.subs_max = 7
        self.audio = False
        self.video = False


statuses = {}

statuses.update({'regular': status()})
statuses['regular'].name = 'regular'
statuses['regular'].subs_max = 10
statuses['regular'].audio = False
statuses['regular'].video = False


statuses.update({'admin': status()})
statuses['admin'].name = 'admin'
statuses['admin'].subs_max = 100
statuses['admin'].audio = True
statuses['admin'].video = True

