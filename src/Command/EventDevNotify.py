'''
Created on Jun 3, 2014

@author: E525649
'''
from BaseNotify import CBaseNotify
import BaseCommand
from DB import SBDB,SBDB_ORM
from sqlalchemy import and_

class CEventDevNotify(CBaseNotify):
    '''
    classdocs
    '''


    def __init__(self,data=None,protocol=None,client_id=0):
        '''
        Constructor
        '''
        CBaseNotify.__init__(self, data, protocol,client_id)        
        
        if protocol is not None:

#             self.superbox_id=protocol.superbox_id
#             print "superbox_id is ", self.superbox_id, "xxxxxxxxxxxxxxxxxxxxx"
            with SBDB.session_scope() as session :
                self.body[BaseCommand.PN_DEVCODE]=self.body[BaseCommand.PN_DEVCODE].upper()
                print "-----",self.body[BaseCommand.PN_DEVCODE],"----",client_id,"---",self.body[BaseCommand.PN_DEVSEQ]
                self.body[BaseCommand.PN_DEVNAME],=session.query(SBDB_ORM.ApartmentDeviceKey.name).join(SBDB_ORM.DeviceKeyCode).join(SBDB_ORM.DeviceKey).join(SBDB_ORM.Device,SBDB_ORM.Device.id==SBDB_ORM.DeviceKeyCode.device_id).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).join(SBDB_ORM.Client).filter(and_(SBDB_ORM.Client.id==client_id,SBDB_ORM.Device.uni_code==self.body[BaseCommand.PN_DEVCODE],SBDB_ORM.DeviceKey.seq==self.body[BaseCommand.PN_DEVSEQ])).first()
                self.body[BaseCommand.PN_DEVMODEL],=session.query(SBDB_ORM.DeviceModel.name).join(SBDB_ORM.Device).filter(SBDB_ORM.Device.uni_code==self.body[BaseCommand.PN_DEVCODE]).first()
                self.body[BaseCommand.PN_ISALARM]="True"
            
        
    