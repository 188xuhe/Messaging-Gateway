'''
Created on 2013-9-3

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
import logging

class CQueryApartment(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00010002
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
                version=self.body[BaseCommand.PN_VERSION]
                apartment_id=self.body[BaseCommand.PN_APARTMENTID]
                respond=self.GetResp()
                try:
                    apartment=session.query(SBDB_ORM.Apartment).filter(SBDB_ORM.Apartment.id==apartment_id).one()
                    respond.body[BaseCommand.PN_VERSION]=apartment.version
                    respond.body[BaseCommand.PN_SCENE_ID]=apartment.scene_id
                    respond.body[BaseCommand.PN_ARMSTATE]=apartment.arm_state
                    if version!=apartment.version:
                        apartment_info={}
                        apartment_info[BaseCommand.PN_ID]=apartment.id
                        apartment_info[BaseCommand.PN_NAME]=apartment.name
                        apartment_info[BaseCommand.PN_VERSION]=apartment.version
                        
                        bDeviceInserted=False
                        listDevice=[]
                        for apartment_device in apartment.apartment_devices:
                            elementDevice={}
                            elementDevice[BaseCommand.PN_ID]=apartment_device.device.id
                            elementDevice[BaseCommand.PN_DEVTYPE]=apartment_device.device.device_model.device_type.name
                            elementDevice[BaseCommand.PN_DEVMODEL]=apartment_device.device.device_model.name
                            elementDevice[BaseCommand.PN_DEVCODE]=apartment_device.device.uni_code
                            elementDevice[BaseCommand.PN_DEVNAME]=apartment_device.name
                            listDeviceKey=[]
                            for apartmentDeviceKey in apartment_device.apartment_device_keys:
                                elementDeviceKey={}
                                elementDeviceKey[BaseCommand.PN_DEVSEQ]=apartmentDeviceKey.device_key_code.device_key.seq
                                elementDeviceKey[BaseCommand.PN_NAME]=apartmentDeviceKey.name
                                listDeviceKey.append(elementDeviceKey)
                            elementDevice[BaseCommand.PN_DEVICEKEYS]=listDeviceKey
                            listDevice.append(elementDevice)
    
                        listSuperbox=[]
                        for apartment_superbox in apartment.apartment_superboxs:
                            superbox=apartment_superbox.superbox
                            elementSuperbox={}
                            elementSuperbox[BaseCommand.PN_ID]=superbox.id
                            elementSuperbox[BaseCommand.PN_SB_CODE]=superbox.uni_code
    #                         listDevice=[]
    #                         for device in superbox.devices:
    #                             elementDevice={}
    #                             elementDevice[BaseCommand.PN_ID]=device.id
    #                             elementDevice[BaseCommand.PN_DEVTYPE]=device.device_model.device_type.name
    #                             elementDevice[BaseCommand.PN_DEVMODEL]=device.device_model.name
    #                             elementDevice[BaseCommand.PN_DEVCODE]=device.uni_code
    #                             elementDevice[BaseCommand.PN_DEVNAME]=device.name
    #                             listDeviceKey=[]
    #                             for deviceKeyCode in device.device_key_codes:
    #                                 elementDeviceKey={}
    #                                 elementDeviceKey[BaseCommand.PN_DEVSEQ]=deviceKeyCode.device_key.seq
    #                                 elementDeviceKey[BaseCommand.PN_NAME]=deviceKeyCode.name
    #                                 listDeviceKey.append(elementDeviceKey)
    #                             elementDevice[BaseCommand.PN_DEVICEKEYS]=listDeviceKey
    #                             listDevice.append(elementDevice)
                            if not bDeviceInserted:
                                elementSuperbox[BaseCommand.PN_DEVICES]=listDevice
                                bDeviceInserted=True
                            listSuperbox.append(elementSuperbox)
                        apartment_info[BaseCommand.PN_SUPERBOXS]=listSuperbox
                        
                        listScene=[]
                        for scene in apartment.scenes:
                            elementScene={}
                            elementScene[BaseCommand.PN_ID]=scene.id
                            elementScene[BaseCommand.PN_NAME]=scene.name
                            listSceneContent=[]
                            for scene_content in scene.scene_contents:
                                elementSceneContent={}
                                elementSceneContent[BaseCommand.PN_ID]=scene_content.id
                                elementSceneContent[BaseCommand.PN_DEVICEID]=scene_content.device_key_code.device.id
                                elementSceneContent[BaseCommand.PN_DEVSEQ]=scene_content.device_key_code.device_key.seq
                                elementSceneContent[BaseCommand.PN_DEVVALUE]=scene_content.value
                                listSceneContent.append(elementSceneContent)
                            elementScene[BaseCommand.PN_SCENECONTENTS]=listSceneContent
                            listScene.append(elementScene)
                        apartment_info[BaseCommand.PN_SCENES]=listScene
                        
                        listContactor=[]
                        for contactor in apartment.contactors:
                            elementContactor={}
                            elementContactor[BaseCommand.PN_ID]=contactor.id
                            elementContactor[BaseCommand.PN_NAME]=contactor.name
                            elementContactor[BaseCommand.PN_MOBLEPHONE]=contactor.mobile_phone
                            listContactor.append(elementContactor)
                        apartment_info[BaseCommand.PN_CONTACTORS]=listContactor
                        
                        respond.body[BaseCommand.PN_APARTMENTINFO]=apartment_info
                        
                except SQLAlchemyError,e:
                    respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                    logging.error("transport %d:%s",id(self.protocol.transport),e)
                    session.rollback()
            respond.Send()
