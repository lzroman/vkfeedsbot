import datetime
import humanize
from logger import log

class Parser:

    def __init__(self):
        pass



    def attachments_count(self, post):
        attachments = {}
        for att in post['attachments']:
            att_type = att['type']
            if att_type in attachments.keys():
                attachments[att_type] += 1
            else:
                attachments.update({'photo': 1})
        return attachments

    def photos(self, post):
        photos = []
        for att in post['attachments']:
            if att['type'] == 'photo':
                photos.append(self.photo_best(att['photo']))
            elif att['type'] == 'graffiti':
                photos.append(att['graffiti']['photo_604'])
        return photos

    def photo_best(self, photo):
        link = ''
        size = 0
        for ph in photo['sizes']:
            if ph['height'] > size:
                size = ph['height']
                link = ph['url']
        return link


    def attachments(self, post):
        attachments = {}
        for att in post['attachments']:
            att_type = att['type']
            if not att_type in attachments.keys():
                attachments.update({att_type: []})

            if att_type == 'photo': # preview
                attachments['photo'].append({'preview': self.photo_best(att['photo'])})
            elif att['type'] == 'graffiti':
                attachments['photo'].append({'preview': att['graffiti']['photo_604']})

            elif att['type'] == 'video': # text, preview
                video = {}
                text = ''
                if 'title' in att['video'].keys():
                    if len(att['video']['title']):
                        text = ''.join(['[', att['video']['title'], ']'])
                    else:
                        text = '[Unnamed]'
                else:
                    text = '[Unnamed]'
                text = ''.join([text, '(https://vk.com/video', str(att['video']['owner_id']), '_', str(att['video']['id']), ') ', humanize.naturaldelta(datetime.timedelta(seconds=att['video']['duration']))])
                video.update({'text': text})
                if 'photo_1280' in att['video'].keys():
                    video.update({'preview': att['video']['photo_1280']})
                elif 'photo_800' in att['video'].keys():
                    video.update({'preview': att['video']['photo_800']})
                elif 'photo_640' in att['video'].keys():
                    video.update({'preview': att['video']['photo_640']})
                else:
                    video.update({'preview': att['video']['photo_320']})
                attachments['video'].append(video)
            
            elif att['type'] == 'audio': # text
                audio = {}
                text = ''.join([att['audio']['artist'], ' - ', att['audio']['title']])
                audio.update({'text': text})
                attachments['audio'].append(audio)

            elif att['type'] == 'doc': # text
                doc = {}
                doc.update({'text': ''.join(['[', att['doc']['title'], '](', att['doc']['url'], ') ', humanize.naturalsize(att['doc']['size'])])})
                attachments['doc'].append(doc)

            elif att['type'] == 'link': # text
                link = {}
                link.update({'text': ''.join(['[', att['link']['title'], '](', att['link']['url'], ')'])})
                attachments['link'].append(link)
            
            elif att['type'] == 'note': # text
                note = {}
                note.update({'text': ''.join(['[', att['note']['title'], '](', att['note']['url'], ')'])})
                attachments['note'].append(note)
            
            elif att['type'] == 'page': # text
                page = {}
                page.update({'text': ''.join(['[', att['page']['title'], '](', att['page']['url'], ')'])})
                attachments['page'].append(page)
            
            elif att['type'] == 'album': # text, preview
                album = {}
                album.update({'text': ''.join(['[', att['album']['title'], '](https://vk.com/album', str(att['album']['owner_id']), '_', str(att['album']['id']), ')'])})
                album.update({'preview': self.photo_best(att['album']['thumb'])})
                attachments['album'].append(album)


        return attachments
