'''
Created on 2013-8-29

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
import logging

class CAddContactor(CBaseCommand):
    '''
    classdocs
    '''
    command_id=0x00020003

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
            name=self.body[BaseCommand.PN_CONTACTORNAME]
            mobile_phone=self.body.get(BaseCommand.PN_MOBLEPHONE,None)
            respond=self.GetResp()
            with SBDB.session_scope() as session :
                try:
                    apartment=SBDB.IncreaseVersion(session, apartment_id)
                    contactor=SBDB_ORM.Contactor()
                    contactor.apartment_id=apartment_id
                    contactor.mobile_phone=mobile_phone
                    contactor.name=name  
                    session.add(contactor)
                    respond.body[BaseCommand.PN_VERSION]=apartment.version
                    session.commit()
                    respond.body[BaseCommand.PN_ID]=contactor.id
                except SQLAlchemyError,e:
                    respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                    logging.error("transport %d:%s",id(self.protocol.transport),e)
                    session.rollback()
            respond.Send()
            
