'''
Created on 2013-9-3

@author: E525649
'''

from BaseControl import CDeviceCmd
from Command import BaseCommand, ControlDevice
from ControlDevice import CControlDevice
from DB import SBDB,SBDB_ORM
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy import and_
from sqlalchemy.orm import undefer

class CSetScene(CControlDevice):
    '''
    classdocs
    '''

    command_id=0x00060004
    
    def __init__(self,data=None,protocol=None):
        '''
        Constructor
        '''
        CControlDevice.__init__(self, data, protocol)
    
    def initDictSuperboxControls(self):
        special_scene=self.body.get(BaseCommand.PN_SPECIALSCENE,BaseCommand.PV_SCENE_SPECIFIED)
        with SBDB.session_scope() as session :
            try:
                session.expire_on_commit = False
                if special_scene==BaseCommand.PV_SCENE_GASSENSOR:
                    apartment_id=self.body[BaseCommand.PN_APARTMENTID]
                    for superbox in session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Apartment_Superbox).filter(SBDB_ORM.Apartment_Superbox.apartment_id==apartment_id).all():
                        with self.protocol.factory.lockDict:
                            sb_protocol=self.protocol.factory.dictSuperbox.get(superbox.id)
                        if sb_protocol is None:
                            continue
                        request=ControlDevice.CControlDevice(protocol=sb_protocol)
                        request.body[BaseCommand.PN_DEVMODEL]=BaseCommand.gas_actuator_model
                        request.body[BaseCommand.PN_DEVCODE]="00"
                        request.body[BaseCommand.PN_DEVSEQ]=0                    
                        request.body[BaseCommand.PN_DEVVALUE]=1   
                        request.Send()
                if special_scene==BaseCommand.PV_SCENE_ALLLIGHTON:
                    apartment_id=self.body[BaseCommand.PN_APARTMENTID]
                    listDeviceCmd=[]    
                    for device,device_key,device_state, in SBDB.GetLightsByApartmentID(session,apartment_id,"on"):
                    #for device,device_key,device_state, in session.query(SBDB_ORM.Device,SBDB_ORM.DeviceKey,SBDB_ORM.DeviceState).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).join(SBDB_ORM.DeviceModel).filter(and_(SBDB_ORM.Device.id==SBDB_ORM.DeviceKeyCode.device_id,SBDB_ORM.DeviceKeyCode.device_key_id==SBDB_ORM.DeviceKey.id,SBDB_ORM.DeviceKey.id==SBDB_ORM.DeviceState.device_key_id,SBDB_ORM.DeviceState.name=="on",SBDB_ORM.Apartment.id==apartment_id,SBDB_ORM.Device.device_model_id==SBDB_ORM.DeviceModel.id,SBDB_ORM.DeviceModel.device_type_id==SBDB_ORM.DeviceType.id,SBDB_ORM.DeviceType.name.like('%light%'))).options(undefer(SBDB_ORM.Device.id)):
                        if device not in session:
                            device = session.query(SBDB_ORM.Device).get(device.id)
                        listDeviceCmd.append(CDeviceCmd(device.device_model.name, \
                                      device.uni_code, \
                                      device_key.seq, \
                                      device_state.value_end))
                        self.initByDeviceCmdList(listDeviceCmd)
                elif special_scene==BaseCommand.PV_SCENE_ALLLIGHTOFF:
                    apartment_id=self.body[BaseCommand.PN_APARTMENTID]
                    listDeviceCmd=[]    
                    for device,device_key,device_state, in SBDB.GetLightsByApartmentID(session,apartment_id,"off"):
                        if device not in session:
                            device = session.query(SBDB_ORM.Device).get(device.id)
                        listDeviceCmd.append(CDeviceCmd(device.device_model.name, \
                                      device.uni_code, \
                                      device_key.seq, \
                                      device_state.value_end))
                        self.initByDeviceCmdList(listDeviceCmd)
                else:
                    scene_id=self.body[BaseCommand.PN_ID]
                    listDeviceCmd=[]                
                    for scene_content in session.query(SBDB_ORM.SceneContent).filter(SBDB_ORM.SceneContent.scene_id==scene_id).all():
                        listDeviceCmd.append(CDeviceCmd(scene_content.device_key_code.device_key.device_model.name, \
                                      scene_content.device_key_code.device.uni_code, \
                                      scene_content.device_key_code.device_key.seq, \
                                      scene_content.value))
                    self.initByDeviceCmdList(listDeviceCmd)
                
                if special_scene in (BaseCommand.PV_SCENE_ALLLIGHTOFF,BaseCommand.PV_SCENE_ALLLIGHTON):
                    self.bFinished=True
                    self.SendResp()
                    
                            
                    '''
                    setDeviceCmd=set()
                    for device in session.query(SBDB_ORM.Device).join(SBDB_ORM.DeviceModel).filter(SBDB_ORM.DeviceModel.name==BaseCommand.gas_actuator_model).join(SBDB_ORM.Superbox).join(SBDB_ORM.Apartment_Superbox).filter(SBDB_ORM.Apartment_Superbox.apartment_id==apartment_id):
                        deviceCmd=CDeviceCmd(BaseCommand.gas_actuator_model,device.uni_code,0,BaseCommand.gas_actuator_value)
                        if deviceCmd in self.EventGas.setControlCmd:    continue
                        if deviceCmd not in setDeviceCmd: setDeviceCmd.update((deviceCmd,))
                        self.EventGas.setControlCmd.update((deviceCmd,))
                    listDeviceCmd=list(setDeviceCmd)
                    self.initByDeviceCmdList(listDeviceCmd)
                    '''
#             except SQLAlchemyError,e:
#                     logging.error("transport %d:%s",id(self.protocol.transport),e)
#                     session.rollback()
#                     raise e
            finally:
                pass

                
        
    def FeedbackIfFinished(self):
        if not self.CheckFinished():    return
        respond=self.Feedback()
        if respond is None: return
        special_scene=self.body.get(BaseCommand.PN_SPECIALSCENE,BaseCommand.PV_SCENE_SPECIFIED)
        if respond.command_status==BaseCommand.CS_OK and special_scene ==BaseCommand.PV_SCENE_SPECIFIED:
            scene_id=self.body[BaseCommand.PN_ID]
            with SBDB.session_scope() as session :
                scene=session.query(SBDB_ORM.Scene).filter(SBDB_ORM.Scene.id==scene_id).one()
                scene.apartment.scene_id=scene_id
                session.commit()
    
    def IsOKResp(self,resp):
        return self.command_seq==resp.command_seq and resp.command_id-self.command_id==0x80000000 and resp.command_status in [BaseCommand.CS_OK,BaseCommand.CS_SUPERBOXOFFLINE,BaseCommand.CS_SUPERBOXRESPTIMEOUT] 
    
            

 
        