'''
Created on Jul 28, 2014

@author: E525649
'''
import sys,os 

#sys.path.append("..")
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),os.path.pardir,os.path.pardir))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),os.path.pardir,os.path.pardir,"src"))

activate_this = os.path.join(os.path.dirname(os.path.abspath(__file__)),os.path.pardir,'venv/Scripts/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))


from src.Utils import Config
class CwebUtil(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
g_listLangs=[]
def GetValidLangs():
    listLangs=[]
    for lists in os.listdir(Config.dir_local_templates): 
        path = os.path.join(Config.dir_local_templates, lists) 
        print path 
        if os.path.isdir(path): 
            listLangs.append(lists)
    return listLangs

g_listLangs=GetValidLangs()
dir_local_root=Config.dir_local_root
dir_local_webserver=Config.dir_local_webserver

LANGUAGES = {
    'en-us': 'en',
    'zh-cn': 'zh_Hans'
}
    
def GetLangDirFromRequest(request):
    header = request.headers.get('Accept-Language', 'en-us')
    locales = [locale.split(';')[0] for locale in header.split(',')]
    for locale in locales:
        for validLang in g_listLangs:
            if locale.lower().find(validLang)>=0:
                return validLang
    return 'en-us'
    
def CheckResetPasswordCode(code_uuid):
    return False    