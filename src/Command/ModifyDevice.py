'''
Created on 2013-8-12

@author: E525649
'''
from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
from sqlalchemy import and_
import logging

class CModifyDevice(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00040001
    def __init__(self,data=None,protocol=None):
        '''
        Constructor
        '''
        CBaseCommand.__init__(self, data, protocol)
    
    def Run(self):
        with self.protocol.lockCmd:
            if not self.Authorized(): 
                self.SendUnauthorizedResp()
                return
            CBaseCommand.Run(self)
            with SBDB.session_scope() as session :
                apartment_id=self.body[BaseCommand.PN_APARTMENTID]
                dev_id=self.body[BaseCommand.PN_DEVICEID]
                dev_code=self.body.get(BaseCommand.PN_DEVCODE,None)
                name=self.body.get(BaseCommand.PN_DEVNAME,None)
                flag_notification=self.body.get(BaseCommand.PN_FLAGNOTIFICATION,None)
                dev_keys=self.body.get(BaseCommand.PN_DEVKEYS,None)
                respond=self.GetResp()
                if dev_id is None:
                    respond.SetErrorCode(BaseCommand.CS_PARAMLACK)
                else:
                    try:
                        #SBDB.IncreaseVersion(session, self.protocol.account)
                        #superbox=session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Device).filter(SBDB_ORM.Device.id==dev_id).first()
                        #apartment=SBDB.IncreaseVersions(session, superbox.id,apartment_id)
                        apartment=SBDB.IncreaseVersions(session, 0,apartment_id)
                        apartment_device=session.query(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).join(SBDB_ORM.Apartment).filter(and_(SBDB_ORM.Device.id==dev_id,SBDB_ORM.Apartment.id==apartment_id)).first()
                        if dev_code is not None: apartment_device.device.uni_code=dev_code 
                        if name is not None: apartment_device.name=name
                        if flag_notification is not None: apartment_device.flag_notification=flag_notification
                        if dev_keys is not None:
                            for dev_key in dev_keys:
                                for apartment_dev_key in apartment_device.apartment_device_keys:
                                    if apartment_dev_key.device_key_code.device_key.seq==dev_key[BaseCommand.PN_DEVSEQ]:
                                        if dev_key.has_key(BaseCommand.PN_NAME): apartment_dev_key.name=dev_key[BaseCommand.PN_NAME]
                                        if dev_key.has_key(BaseCommand.PN_DEVCODE): apartment_dev_key.device_key_code.uni_code=dev_key[BaseCommand.PN_DEVCODE]
                                #obj_device_key_code=session.query(SBDB_ORM.DeviceKeyCode).filter(and_(SBDB_ORM.DeviceKeyCode.device_id==device.id,SBDB_ORM.DeviceKeyCode.device_key_id==SBDB.GetDeviceKeyByModelAndSeq(device.device_model,dev_key[BaseCommand.PN_DEVSEQ]).id))
                                #if dev_key.has_key(BaseCommand.PN_NAME): obj_device_key_code.name=dev_key[BaseCommand.PN_NAME]
                                #if dev_key.has_key(BaseCommand.PN_DEVCODE): obj_device_key_code.uni_code=dev_key[BaseCommand.PN_DEVCODE]
                        respond.body[BaseCommand.PN_VERSION]=apartment.version
                        session.commit()
                    except SQLAlchemyError,e:
                        respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                        logging.error("transport %d:%s",id(self.protocol.transport),e)
                        session.rollback()
            respond.Send()


