'''
Created on Jun 3, 2014

@author: E525649
'''

from BaseSimpleControl import CBaseSimpleControl,CBaseRespSimpleControl


class CQuerySuperboxStatus(CBaseSimpleControl):
    '''
    classdocs
    '''

    command_id=0x00010008
    def __init__(self,data=None,protocol=None):
        '''
        Constructor
        '''
        CBaseSimpleControl.__init__(self, data, protocol)
        
        
        
    
class CQuerySuperboxStatusResp(CBaseRespSimpleControl):
    '''
    classdocs
    '''

    command_id=0x80010008
    
    def __init__(self,data=None,protocol=None):
        '''
        Constructor
        '''
        CBaseRespSimpleControl.__init__(self, data, protocol)
        
CQuerySuperboxStatus.TypeResp=CQuerySuperboxStatusResp
