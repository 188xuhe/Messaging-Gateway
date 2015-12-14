'''
Created on 2013-8-29

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
import logging

class CModifyContactor(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00040003
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
                contactor_id=self.body[BaseCommand.PN_ID]
                apartment_id,=session.query(SBDB_ORM.Apartment.id).join(SBDB_ORM.Contactor).filter(SBDB_ORM.Contactor.id==contactor_id).one()
                name=self.body.get(BaseCommand.PN_CONTACTORNAME,None)
                mobile_phone=self.body.get(BaseCommand.PN_MOBLEPHONE,None)
                respond=self.GetResp()
                if contactor_id is None :
                    respond.SetErrorCode(BaseCommand.CS_PARAMLACK)
                else:
                    try:
                        apartment=SBDB.IncreaseVersion(session, apartment_id)
                        contactor=session.query(SBDB_ORM.Contactor).filter(SBDB_ORM.Contactor.id==contactor_id).first()
                        if name is not None:    contactor.name=name
                        if mobile_phone is not None: contactor.mobile_phone=mobile_phone
                        respond.body[BaseCommand.PN_VERSION]=apartment.version
                        session.commit()
                    except SQLAlchemyError,e:
                        respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                        logging.error("transport %d:%s",id(self.protocol.transport),e)
                        session.rollback()
            respond.Send()


