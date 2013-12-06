from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import toUnicode, tryUrlencode
from couchpotato.core.helpers.rss import RSS
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.event import fireEvent
from couchpotato.core.providers.base import MultiProvider
from couchpotato.core.providers.info.base import MovieProvider, SeasonProvider, EpisodeProvider
from couchpotato.core.providers.nzb.base import NZBProvider
from couchpotato.environment import Env
from dateutil.parser import parse
import re
import time

log = CPLog(__name__)

class NzbIndex(MultiProvider):

    def getTypes(self):
        return [Movie, Season, Episode]


class Base(NZBProvider, RSS):

    urls = {
        'download': 'https://www.nzbindex.com/download/',
        'search': 'https://www.nzbindex.com/rss/?%s',
    }

    http_time_between_calls = 1 # Seconds

    def _search(self, media, quality, results):

        nzbs = self.getRSSData(self.urls['search'] % self.buildUrl(media, quality))

        for nzb in nzbs:

            enclosure = self.getElement(nzb, 'enclosure').attrib
            nzbindex_id = int(self.getTextElement(nzb, "link").split('/')[4])

            try:
                description = self.getTextElement(nzb, "description")
            except:
                description = ''

            def extra_check(item):
                if '#c20000' in item['description'].lower():
                    log.info('Wrong: Seems to be passworded: %s', item['name'])
                    return False

                return True

            results.append({
                'id': nzbindex_id,
                'name': self.getTextElement(nzb, "title"),
                'age': self.calculateAge(int(time.mktime(parse(self.getTextElement(nzb, "pubDate")).timetuple()))),
                'size': tryInt(enclosure['length']) / 1024 / 1024,
                'url': enclosure['url'],
                'detail_url': enclosure['url'].replace('/download/', '/release/'),
                'description': description,
                'get_more_info': self.getMoreInfo,
                'extra_check': extra_check,
            })

    def getMoreInfo(self, item):
        try:
            if '/nfo/' in item['description'].lower():
                nfo_url = re.search('href=\"(?P<nfo>.+)\" ', item['description']).group('nfo')
                full_description = self.getCache('nzbindex.%s' % item['id'], url = nfo_url, cache_timeout = 25920000)
                html = BeautifulSoup(full_description)
                item['description'] = toUnicode(html.find('pre', attrs = {'id':'nfo0'}).text)
        except:
            pass

class Movie(MovieProvider, Base):

    def buildUrl(self, media):
        title = fireEvent('searcher.get_search_title', media['library'], single = True)
        year =  media['library']['year']

        query = tryUrlencode({
            'q': '"%s %s" | "%s (%s)"' % (title, year, title, year),
            'age': Env.setting('retention', 'nzb'),
            'sort': 'agedesc',
            'minsize': quality.get('size_min'),
            'maxsize': quality.get('size_max'),
            'rating': 1,
            'max': 250,
            'more': 1,
            'complete': 1,
        })
        return query

class Season(SeasonProvider, Base):

    def buildUrl(self, media, quality):
        query = tryUrlencode({
            'q': fireEvent('searcher.get_search_title', media['library'], include_identifier = True, single = True),
            'age': Env.setting('retention', 'nzb'),
            'sort': 'agedesc',
            'minsize': quality.get('size_min'),
            'maxsize': quality.get('size_max'),
            'rating': 1,
            'max': 250,
            'more': 1,
            'complete': 1,
        })
        return query

class Episode(EpisodeProvider, Base):

    def buildUrl(self, media, quality):
        query = tryUrlencode({
            'q': fireEvent('searcher.get_search_title', media['library'], include_identifier = True, single = True),
            'age': Env.setting('retention', 'nzb'),
            'sort': 'agedesc',
            'minsize': quality.get('size_min'),
            'maxsize': quality.get('size_max'),
            'rating': 1,
            'max': 250,
            'more': 1,
            'complete': 1,
        })
        return query
