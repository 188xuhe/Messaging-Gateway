'''
Created on 2013-8-29

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
from sqlalchemy import and_
import logging

class CModifyScene(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00040004
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
                scene_id=self.body[BaseCommand.PN_SCENEID]
                name=self.body.get(BaseCommand.PN_SCENENAME)
                scene_contents=self.body.get(BaseCommand.PN_SCENECONTENTS)
                respond=self.GetResp()
                if scene_id is None:
                    respond.SetErrorCode(BaseCommand.CS_PARAMLACK)
                else:
                    try:
                        #SBDB.IncreaseVersion(session, self.protocol.account)
                        scene=session.query(SBDB_ORM.Scene).filter(SBDB_ORM.Scene.id==scene_id).first()
                        apartment=SBDB.IncreaseVersion(session, scene.apartment.id)
                        if name is not None: scene.name=name
                        modify_ids=set()
                        if scene_contents is not None:
                            for scene_content in scene_contents:
                                sc=session.query(SBDB_ORM.SceneContent).join(SBDB_ORM.Scene).join(SBDB_ORM.DeviceKeyCode).join(SBDB_ORM.DeviceKey).filter(and_(SBDB_ORM.Scene.id==scene_id,SBDB_ORM.DeviceKeyCode.device_id==scene_content[BaseCommand.PN_DEVICEID],SBDB_ORM.DeviceKey.seq==scene_content[BaseCommand.PN_DEVSEQ])).first()
                                if sc is None:
                                    sc=SBDB_ORM.SceneContent()
                                    sc.device_key_code_id,=session.query(SBDB_ORM.DeviceKeyCode.id).join(SBDB_ORM.DeviceKey).filter(and_(SBDB_ORM.DeviceKeyCode.device_id==scene_content[BaseCommand.PN_DEVICEID],SBDB_ORM.DeviceKey.seq==scene_content[BaseCommand.PN_DEVSEQ])).one()
                                    scene.scene_contents.append(sc)
                                else:
                                    modify_ids.update((sc.id,))
                                sc.value=scene_content[BaseCommand.PN_DEVVALUE]
                        for sc in scene.scene_contents:
                            if  sc.id is not None and sc.id not in modify_ids:    session.delete(sc)
                        
                        respond.body[BaseCommand.PN_VERSION]=apartment.version
                        session.commit()
                    except SQLAlchemyError,e:
                        respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                        logging.error("transport %d:%s",id(self.protocol.transport),e)
                        session.rollback()
            respond.Send()


