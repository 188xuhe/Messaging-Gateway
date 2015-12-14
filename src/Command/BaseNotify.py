'''
Created on Jun 3, 2014

@author: E525649
'''

from BaseCommand import CBaseCommand


class CBaseNotify(CBaseCommand):
    '''
    classdocs
    '''


    def __init__(self,data=None,protocol=None,client_id=0):
        '''
        Constructor
        '''
        CBaseCommand.__init__(self, data, protocol)
        self.client_id=client_id
        
    def Notify(self,internalMessage=None):
        
        if internalMessage:
            print "notify :aaaaaaaaaaaaaaaaaa",internalMessage
            self.Send(internalMessage)
            return
        if self.superbox_id ==0 :  return
        with self.protocol.factory.lockDict:
            dictAccount=self.protocol.factory.dictAccounts
            if dictAccount.has_key(self.superbox_id):
                self.command_seq=self.GetNextSeq()
                for clientProtocol in dictAccount[self.superbox_id]:
#                     if clientProtocol.rcv_alarm=="True" and clientProtocol.client_id==self.client_id:
                    if clientProtocol.client_id==self.client_id:
                        self.protocol=clientProtocol
                        self.Send()
                        break
            