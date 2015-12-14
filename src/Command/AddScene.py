'''
Created on 2013-8-29

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
import logging
from sqlalchemy import and_

class CAddScene(CBaseCommand):
    '''
    classdocs
    '''
    command_id=0x00020004

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
            name=self.body[BaseCommand.PN_APARTMENTNAME]
            scene_contents=self.body.get(BaseCommand.PN_SCENECONTENTS)
            respond=self.GetResp()
            with SBDB.session_scope() as session :
                try:
                    apartment=SBDB.IncreaseVersion(session, apartment_id)
                    scene=SBDB_ORM.Scene()
                    scene.apartment_id=apartment_id
                    scene.name=name
                    if scene_contents is not None:
                        for scene_content in scene_contents:
                            sc=SBDB_ORM.SceneContent()
                            sc.value=scene_content[BaseCommand.PN_DEVVALUE]
                            sc.device_key_code_id,=session.query(SBDB_ORM.DeviceKeyCode.id).join(SBDB_ORM.DeviceKey).filter(and_(SBDB_ORM.DeviceKeyCode.device_id==scene_content[BaseCommand.PN_DEVICEID],SBDB_ORM.DeviceKey.seq==scene_content[BaseCommand.PN_DEVSEQ])).one()
                            scene.scene_contents.append(sc)
                    session.add(scene)
                    respond.body[BaseCommand.PN_VERSION]=apartment.version
                    session.commit()
                    respond.body[BaseCommand.PN_ID]=scene.id
                except SQLAlchemyError,e:
                    respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                    logging.error("transport %d:%s",id(self.protocol.transport),e)
                    session.rollback()
            respond.Send()
            