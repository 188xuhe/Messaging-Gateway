#!/usr/bin/python
#coding=utf-8
'''
Created on 2013-8-21

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand
from sqlalchemy import and_
import logging

class CAddSuperbox(CBaseCommand):
    '''
    classdocs
    '''
    command_id=0x00020007

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
            sb_code=self.body[BaseCommand.PN_SB_CODE]
            sb_name=self.body[BaseCommand.PN_NAME]
            #account_id=self.protocol.account_id
            respond=self.GetResp()
            with SBDB.session_scope() as session :
                if session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Apartment_Superbox).filter(and_(SBDB_ORM.Superbox.uni_code==sb_code,SBDB_ORM.Apartment_Superbox.apartment_id==apartment_id)).first() is not None:
                        respond.SetErrorCode(BaseCommand.CS_DEVICEEXIST)
                try:
                    superbox_id=SBDB.GetSuperboxIdForcely(sb_code)
                    apartment=SBDB.IncreaseVersion(session, apartment_id)
                    apartment_superbox=SBDB_ORM.Apartment_Superbox()
                    apartment_superbox.apartment_id=apartment_id
                    apartment_superbox.superbox_id=superbox_id
                    apartment_superbox.name=sb_name
                    '''
                    superbox=SBDB_ORM.Superbox()
                    superbox.apartment_id=apartment_id
                    superbox.name=sb_name
                    superbox.uni_code=sb_code            
                    session.add(superbox)
                    '''
                    session.add(apartment_superbox)
                    respond.body[BaseCommand.PN_VERSION]=apartment.version
                    session.commit()
    #                 if session.query(SBDB_ORM.Device).join(SBDB_ORM.Superbox).filter(SBDB_ORM.Superbox.id==superbox.id).first():
    #                     respond.body[BaseCommand.PN_UPDATEDATA]=True
                    respond.body[BaseCommand.PN_ID]=superbox_id
                except SQLAlchemyError,e:
                    respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
                    logging.error("transport %d:%s",id(self.protocol.transport),e)
                    session.rollback()
            respond.Send()
            