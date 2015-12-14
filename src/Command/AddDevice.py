'''
Created on 2013-8-12

@author: E525649
'''
from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from sqlalchemy import and_
from Command import BaseCommand
import logging
import string



class CAddDevice(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00020001
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
            
            apartment_id=self.body[BaseCommand.PN_APARTMENTID]
            superbox_id=self.body.get(BaseCommand.PN_SUPERBOXID)
            dev_model=self.body[BaseCommand.PN_DEVMODEL]
            dev_code=self.body[BaseCommand.PN_DEVCODE]
            dev_keys=self.body.get(BaseCommand.PN_DEVKEYS)
            respond=self.GetResp()
            with SBDB.session_scope() as session :
                model=SBDB.GetDeviceModelByName(session,dev_model)
                try:
                    if superbox_id is None:
                        superbox_id,=session.query(SBDB_ORM.Superbox.id).join(SBDB_ORM.Apartment_Superbox).filter(SBDB_ORM.Apartment_Superbox.apartment_id==apartment_id).order_by(SBDB_ORM.Superbox.id).first()
                    else:
                        superbox_id=int(superbox_id)
                    if model is None:
                        respond.SetErrorCode(BaseCommand.CS_DEVICEMODEL)
                    elif superbox_id is None:
                        respond.SetErrorCode(BaseCommand.CS_NOSUPERBOX)
                    elif session.query(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).filter(and_(SBDB_ORM.Device.uni_code==dev_code,SBDB_ORM.ApartmentDevice.apartment_id==apartment_id)).first() is not None:
                        respond.SetErrorCode(BaseCommand.CS_DEVICEEXIST)
                    else:
                        apartment=SBDB.IncreaseVersions(session, 0,apartment_id)
                        device=SBDB.GetDeviceForcely(session, dev_code, dev_model)
                        if device is None:
                            device=SBDB_ORM.Device()
                            device.device_model_id=model.id
                            device.uni_code=dev_code
                            
                            obj_dev_model=model#SBDB.GetDeviceModelByName(dev_model)
                            for obj_dev_key in obj_dev_model.device_keys:
                                obj_dev_key_code=SBDB_ORM.DeviceKeyCode()
                                obj_dev_key_code.device_key_id=obj_dev_key.id
                                obj_dev_key_code.key_code=hex(string.atoi(dev_code,16)+obj_dev_key.seq)[2:]
                                device.device_key_codes.append(obj_dev_key_code)
                            session.add(device)
    
                        else:
                            apartment_device=SBDB_ORM.ApartmentDevice()
                            apartment_device.apartment_id=apartment_id
                            apartment_device.name=model.device_type.name
                            apartment_device.superbox_id=superbox_id
                            apartment_device.device_id=device.id
                            
                            for obj_dev_key in device.device_key_codes:
                                obj_apartment_device_key=SBDB_ORM.ApartmentDeviceKey()
                                obj_apartment_device_key.apartment_device_id=apartment_device.id
                                obj_apartment_device_key.device_key_code_id=obj_dev_key.id
                                obj_apartment_device_key.name=model.device_type.name
                                if dev_keys is not None:
                                    for dev_key in dev_keys:
                                        if dev_key[BaseCommand.PN_DEVSEQ]==obj_dev_key.device_key.seq:
                                            obj_apartment_device_key.name=dev_key[BaseCommand.PN_NAME]
                                            break
                                apartment_device.apartment_device_keys.append(obj_apartment_device_key)
                            respond.body[BaseCommand.PN_VERSION]=apartment.version
                            session.add(apartment_device)
                            session.commit()
                            respond.body[BaseCommand.PN_DEVICEID]=device.id
                            #SBDB.setDeviceCodes.update((dev_code,))
                except SQLAlchemyError,e:
                    respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                    logging.error("transport %d:%s",id(self.protocol.transport),e)
                    session.rollback()
            respond.Send()
