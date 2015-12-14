'''
Created on 2013-8-12

@author: E525649
'''
from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
import logging
from sqlalchemy import and_

class CRemoveDevice(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00030001
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
                dev_id=self.body[BaseCommand.PN_DEVICEID]
                apartment_id=self.body[BaseCommand.PN_APARTMENTID]
                dev_keys=self.body.get(BaseCommand.PN_DEVKEYS,None)
                respond=self.GetResp()
                if dev_id is None:
                    respond.SetErrorCode(BaseCommand.CS_PARAMLACK)
                else:
                    try:
                        #SBDB.IncreaseVersion(session, self.protocol.account)
                        #superbox=session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Device).filter(SBDB_ORM.Device.id==dev_id).first()
                        apartment=SBDB.IncreaseVersions(session, 0,apartment_id)
                        if dev_keys is None:
                            session.query(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).join(SBDB_ORM.Device).filter(and_(SBDB_ORM.Apartment.id==apartment_id,SBDB_ORM.Device.id==dev_id)).delete()
                        else:
                            for dev_key in dev_keys:
                                session.delete(session.query(SBDB_ORM.ApartmentDeviceKey).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).join(SBDB_ORM.DeviceKeyCode).join(SBDB_ORM.DeviceKey).filter(and_(SBDB_ORM.Apartment.id==apartment_id,SBDB_ORM.DeviceKeyCode.device_id==dev_id,SBDB_ORM.DeviceKey.seq==dev_key[BaseCommand.PN_DEVSEQ])).first())                            
                            if session.query(SBDB_ORM.ApartmentDeviceKey).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).join(SBDB_ORM.DeviceKeyCode).filter(and_(SBDB_ORM.Apartment.id==apartment_id,SBDB_ORM.DeviceKeyCode.device_id==dev_id)).first() is None:
                                session.query(SBDB_ORM.ApartmentDevice).filter(and_(SBDB_ORM.ApartmentDevice.apartment_id==apartment_id,SBDB_ORM.ApartmentDevice.device_id==dev_id)).delete()
                                pass
                        respond.body[BaseCommand.PN_VERSION]=apartment.version
                        session.commit()
                        '''
                        SBDB.IncreaseVersion(session, self.protocol.account)
                        device=session.query(SBDB_ORM.Device).filter(SBDB_ORM.Device.id==dev_id).first()
                        device.deleted=True
                        respond.body[BaseCommand.PN_VERSION]=self.protocol.account.version
                        session.commit()
                        '''
                    except SQLAlchemyError,e:
                        respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                        logging.error("transport %d:%s",id(self.protocol.transport),e)
                        session.rollback()
            respond.Send()


