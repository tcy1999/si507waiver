#################################
##### Name: 
##### Uniqname: 
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key


class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, name='', category='', address='', zip='', phone=''):
        self.name = name
        self.category = category
        self.address = address
        self.zipcode = zip
        self.phone = phone

    def info(self):
        return self.name + ' (' + self.category + '): ' + self.address + ' ' + self.zipcode


class Cache:
    def __init__(self, filename):
        self.filename = filename
        try:
            with open(self.filename, 'r') as file:
                self.cacheDict = json.load(file)
        except:
            self.cacheDict = {}

    def read(self, url):
        if url in self.cacheDict.keys():
            print('Using cache')
            data = self.cacheDict[url]
        else:
            print('Fetching')
            data = requests.get(url).text
            self.write(url, data)
        return data

    def write(self, url, data):
        self.cacheDict[url] = data
        with open(self.filename, 'w') as file:
            json.dump(self.cacheDict, file)


cache = Cache('temp.json')


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    baseUrl = 'https://www.nps.gov'
    res = cache.read(baseUrl)
    soup = BeautifulSoup(res, 'html.parser')
    stateList = soup.find('ul', class_="dropdown-menu SearchBar-keywordSearch").find_all('a')
    dict = {}
    for state in stateList:
        dict[state.get_text().strip().lower()] = baseUrl + state.attrs['href']
    return dict


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    res = cache.read(site_url)
    soup = BeautifulSoup(res, 'html.parser')
    title = soup.find('div', class_='Hero-titleContainer')
    name = title.a.get_text().strip()
    category = title.find('span', class_='Hero-designation').get_text().strip()
    contactInfo = soup.find('div', class_='vcard')
    adr = contactInfo.find('p', class_='adr')
    address = zip = ''
    if adr:
        address = adr.find('span', itemprop='addressLocality').get_text().strip() + ', ' + adr.find('span', itemprop='addressRegion').get_text().strip()
        zip = adr.find('span', class_='postal-code').get_text().strip()
    phone = contactInfo.find('span', class_='tel').get_text().strip()
    nationalSite = NationalSite(name, category, address, zip, phone)
    return nationalSite


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    res = cache.read(state_url)
    soup = BeautifulSoup(res, 'html.parser')
    list_parks = soup.find('ul', id='list_parks').find_all('li', class_='clearfix')
    nationalSites = []
    for park in list_parks:
        nationalSites.append(get_site_instance('https://www.nps.gov' + park.find('div', class_='list_left').find('a').attrs['href']))
    return nationalSites


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    if site_object.zipcode == '':
        print('No zip code')
        return None
    url = 'http://www.mapquestapi.com/search/v2/radius?key=' + secrets.API_KEY + '&origin=' + site_object.zipcode + '&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json'
    res = cache.read(url)
    return json.loads(s=res)
    

if __name__ == "__main__":
    urlDict = build_state_url_dict()
    while True:
        print('Enter a state name (e.g. Michigan, michigan) or "exit"')
        state = input(': ')
        if state == 'exit':
            exit()
        if state.lower() not in urlDict.keys():
            print('[Error] Enter proper state name\n')
            continue

        nationalSites = get_sites_for_state(urlDict[state.lower()])
        listTitle = 'List of national sites in ' + state
        line = '-' * len(listTitle)
        print(line + '\n' + listTitle + '\n' + line)
        for i in range(0, len(nationalSites)):
            print('[' + str(i + 1) + '] ' + nationalSites[i].info())

        while True:
            print('Choose the number for detail search or "exit" or "back"')
            option = input(': ')
            if option == 'exit':
                exit()
            elif option == 'back':
                break
            elif option.isdecimal() and int(option) in range(1, len(nationalSites)+1):
                print(line + '\n' + 'Places near ' + nationalSites[int(option)-1].name + '\n' + line)
                nearbyPlaces = get_nearby_places(nationalSites[int(option)-1])
                for i in range(0, nearbyPlaces['resultsCount']):
                    placeStr = '- ' + nearbyPlaces['searchResults'][i]['name'] + ' ('
                    if nearbyPlaces['searchResults'][i]['fields']['group_sic_code_name']:
                        placeStr += nearbyPlaces['searchResults'][i]['fields']['group_sic_code_name'] + '): '
                    else:
                        placeStr += 'no category): '
                    if nearbyPlaces['searchResults'][i]['fields']['address']:
                        placeStr += nearbyPlaces['searchResults'][i]['fields']['address'] + ', '
                    else:
                        placeStr += 'no address, '
                    if nearbyPlaces['searchResults'][i]['fields']['city']:
                        placeStr += nearbyPlaces['searchResults'][i]['fields']['city']
                    else:
                        placeStr += 'no city'
                    print(placeStr)
            else:
                print('[Error] Invalid input\n' + line)
