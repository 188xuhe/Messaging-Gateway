'''
Created on 2013-8-26

@author: E525649
'''

from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from Command import BaseCommand
from DB import SBDB_ORM,SBDB
from sqlalchemy import and_
import threading,logging
from Utils import Config
from SBPS import InternalMessage
from sqlalchemy import distinct
from twisted.internet import reactor

class CDeviceCmd(object):
    def __init__(self,dev_model,dev_code,dev_seq,value):
        self.dev_model=dev_model
        self.dev_code=dev_code
        self.dev_seq=dev_seq
        self.value=value
        self.body={}
        self.result=-1
        self.bTriedSuperboxMain=False
          
    def __eq__(self,other):
        if isinstance(other, SBDB_ORM.DeviceKeyCode):
            return self.dev_model==other.device_key.device_model.name and self.dev_code==other.device.uni_code and self.dev_seq==other.device_key.seq
        elif isinstance(other, CDeviceCmd):
            return self.dev_model==other.dev_model and self.dev_code==other.dev_code and self.dev_seq==other.dev_seq and self.value==other.value
        else:
            object._eq__(self,other)

    def __hash__(self):
        return  hash(self.dev_model+self.dev_code+str(self.dev_seq))

class CBaseControl(CBaseCommand):
    '''
    classdocs
    '''


    def __init__(self,data=None,protocol=None):
        '''
        Constructor
        '''
        CBaseCommand.__init__(self, data, protocol)
        self.dictWaitingSuperboxControls={} #the map of superbox_id-->array of CDeviceCmd
        self.dictSendingSuperboxControls={}
        self.dictFinishedSuperboxControls={}
        self.lock=threading.RLock()
        self.bFinished=False
        self.requireCommand=None
        self.timer=None
        
    def Run(self):
        with self.protocol.lockCmd:
            if not self.Authorized(): 
                self.SendUnauthorizedResp()
                return
            CBaseCommand.Run(self)
            self.initDictSuperboxControls()
            with self.lock:
                self.FeedbackIfFinished()
        
    def initByDeviceCmdList(self,listDC):
        self.DeviceKeyCode=""
        self.dictWaitingSuperboxControls={}
        setUnique=set()
        with SBDB.session_scope() as session :
            
            if self.internalMessage:
                self.account_id=self.internalMessage.fromId
            else:
                self.account_id=self.protocol.account_id
            try:
                for dc in listDC:
                    if dc in setUnique: continue
                    setUnique.update((dc,))
    #                 listSuperbox=[]
    #                 if not self.bTriedSuperboxMain:
    #                     s=session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Apartment_Superbox).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).join(SBDB_ORM.DeviceModel).filter(and_(SBDB_ORM.Account.id==self.account_id,SBDB_ORM.Device.uni_code==dc.dev_code,SBDB_ORM.DeviceModel.name==dc.dev_model,SBDB_ORM.ApartmentDevice.superbox_id==SBDB_ORM.Superbox.id)).first()
    #                     if s:   listSuperbox.append(s)
    #                     self.bTriedSuperboxMain=True
    #                 if not self.internalMessage and len(listSuperbox)<=0:
    #                     listSuperboxId=[]
    #                     for s in session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Apartment_Superbox).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).join(SBDB_ORM.DeviceModel).filter(and_(SBDB_ORM.Account.id==self.account_id,SBDB_ORM.Device.uni_code==dc.dev_code,SBDB_ORM.DeviceModel.name==dc.dev_model)):
    #                         if s.id not in listSuperboxId:
    #                             listSuperboxId.append(s.id)
    #                             listSuperbox.append(s)
    #                 for s in listSuperbox:
                    if not self.internalMessage:
                        for s, in session.query(distinct(SBDB_ORM.ApartmentDevice.superbox_id)).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).join(SBDB_ORM.Device).filter(and_(SBDB_ORM.Account.id==self.account_id,SBDB_ORM.Device.uni_code==dc.dev_code)).all():
                            #dc=listDC[listDC.index(dkc)]
                            if self.dictWaitingSuperboxControls.has_key(s):
                                self.dictWaitingSuperboxControls[s].append(dc)
                            else:
                                self.dictWaitingSuperboxControls[s]=[dc,]
                    else:
                        superbox_id=self.internalMessage.destId
                        if self.dictWaitingSuperboxControls.has_key(superbox_id):
                            self.dictWaitingSuperboxControls[superbox_id].append(dc)
                        else:
                            self.dictWaitingSuperboxControls[superbox_id]=[dc,]
            except SQLAlchemyError,e:
                logging.error("transport %d:%s",id(self.protocol.transport),e)
                session.rollback()

                     
    def SendBatch(self):
        for superbox_id in self.dictWaitingSuperboxControls.keys():
            deviceCmds=self.dictWaitingSuperboxControls.pop(superbox_id)
            if len(deviceCmds)<=0: 
                continue
            
            if self.internalMessage:
                with self.protocol.factory.lockDict:
                    sb_protocol=self.protocol.factory.dictSuperbox.get(superbox_id)
                if sb_protocol is None:
                    self.dictFinishedSuperboxControls[superbox_id]=deviceCmds 
                    continue
            else:
                sb_protocol=InternalMessage.protocolInternal
            self.dictSendingSuperboxControls[superbox_id]=deviceCmds
            bSend=False
            for deviceCmd in deviceCmds:
                if deviceCmd.result==0: continue
                bSend=True
                deviceCmd.result=-1
                #from ControlDevice import CControlDevice
                #control_device=CControlDevice(protocol=sb_protocol)
                control_device=self.getCommand(deviceCmd)
                control_device.protocol=sb_protocol
                control_device.superbox_id=superbox_id
                if sb_protocol.role==BaseCommand.PV_ROLE_INTERNAL:
                    with sb_protocol.lock_dictWaitResp:
                        #sb_protocol.dictWaitResp[(superbox_id<<32)+control_device.command_seq]=control_device
                        control_device.requireTransport=id(self.protocol.transport)
                        sb_protocol.dictWaitResp[(control_device.requireTransport<<32)+control_device.command_seq]=control_device
                else:
                    with sb_protocol.lock_dictWaitResp:
                        sb_protocol.dictWaitResp[control_device.command_seq]=control_device
                control_device.requireCommand=self
                control_device.Send()
                #threading.Timer(Config.timeout_superbox_control,control_device.timeout).start()
                #control_device.timer=reactor.callLater(Config.timeout_superbox_control,control_device.timeout)
            if not bSend:
                self.dictFinishedSuperboxControls[superbox_id]=self.dictSendingSuperboxControls.pop(superbox_id)
                continue
            break
    
    def FinishOne(self,superbox_id,control_device,respond):
        with self.lock:
            #deviceCmds=self.dictSendingSuperboxControls.get(superbox)
            deviceCmds=None
            for key in self.dictSendingSuperboxControls.keys():
                if key==superbox_id:
                    deviceCmds=self.dictSendingSuperboxControls[key]
            if deviceCmds is not None:
                for deviceCmd in deviceCmds:
                    if control_device.body[BaseCommand.PN_DEVMODEL]==deviceCmd.dev_model and control_device.body[BaseCommand.PN_DEVCODE]==deviceCmd.dev_code and control_device.body[BaseCommand.PN_DEVSEQ]==deviceCmd.dev_seq:
                        if deviceCmd.result!=0: 
                            deviceCmd.result=respond.command_status
                            deviceCmd.body=respond.body
                            
                            #if it's failed, and have not try other superbox in the same account: add these superbox to dictWaitingSuperboxControls
                            if deviceCmd.result!=0 and not deviceCmd.bTriedSuperboxMain and self.protocol.role==BaseCommand.PV_ROLE_HUMAN:
                                with SBDB.session_scope() as session :
                                    deviceCmd.bTriedSuperboxMain=True
                                    
                                    listSuperboxId=[]
                                    for s in session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Apartment_Superbox).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).join(SBDB_ORM.DeviceModel).filter(and_(SBDB_ORM.Account.id==self.protocol.account_id,SBDB_ORM.Device.uni_code==deviceCmd.dev_code,SBDB_ORM.DeviceModel.name==deviceCmd.dev_model,SBDB_ORM.Superbox.id!=superbox_id)):
                                        if s.id not in listSuperboxId:
                                            listSuperboxId.append(s.id)
                                    if len(listSuperboxId)>0:
                                        deviceCmd.result=-1
                                        deviceCmds.remove(deviceCmd)
                                        for s in listSuperboxId:
                                            if self.dictWaitingSuperboxControls.has_key(s):
                                                self.dictWaitingSuperboxControls[s].append(deviceCmd)
                                            else:
                                                self.dictWaitingSuperboxControls[s]=[deviceCmd,]
                                        
                        #if it's succeed finished by other superbox, set this superbox as this device's mainSueprbox
                        if deviceCmd.result==0 and deviceCmd.bTriedSuperboxMain:
                            with SBDB.session_scope() as session :
                                for apartment_device in session.query(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).filter(and_(SBDB_ORM.Account.id==self.protocol.account_id,SBDB_ORM.Device.uni_code==deviceCmd.dev_code)):
                                    apartment_device.superbox_id=superbox_id
                                session.commit()                            
                        break
            self.FeedbackIfFinished()
            
    def CheckFinished(self):
        if len(self.dictSendingSuperboxControls.keys())>0:
            for superbox_id in self.dictSendingSuperboxControls.keys():
                for deviceCmd in self.dictSendingSuperboxControls[superbox_id]:
                    if deviceCmd.result<0:  return False
                self.dictFinishedSuperboxControls[superbox_id]=self.dictSendingSuperboxControls.pop(superbox_id)
        if len(self.dictWaitingSuperboxControls.keys())<=0:
            return True
        else:
            self.SendBatch()
            return self.CheckFinished()
        
    def FeedbackIfFinished(self):
        if not self.CheckFinished():   
            return
        self.Feedback()
    
    
    def Feedback(self):
        if self.bFinished: return
        respond=self.GetResp()
#         if self.protocol is not None and self.protocol.role ==BaseCommand.PV_ROLE_HUMAN:
        if self.protocol is not None:
            result=-1
            #if one control command fail, the total command fail
            for superbox_id in self.dictFinishedSuperboxControls.keys():
                for dc in self.dictFinishedSuperboxControls[superbox_id]:
                    if result<=0: 
                        result=dc.result
                        respond.body=dc.body
            
            if result==-1:
                respond.SetErrorCode(BaseCommand.CS_SUPERBOXOFFLINE)
            else:
                respond.SetErrorCode(result)
                
            interMessage=None
            if self.protocol.role==BaseCommand.PV_ROLE_INTERNAL:
                interMessage=InternalMessage.CInternalMessage()
                interMessage.SetParam(self.internalMessage.fromType,self.internalMessage.fromId,self.internalMessage.fromSock,InternalMessage.OPER_RESPONSE,"",
                                  self.internalMessage.destType,self.internalMessage.destId,self.internalMessage.destSock)
            
            respond.Send(interMessage)
        self.bFinished=True
        return respond
    
    def timeout(self):
        with self.protocol.cond_dictControlling:
            request=self.protocol.dictControlling.pop(self.command_seq,None)
            if request is not None: 
                logging.debug("call self.protocol.cond_dictControlling.notify() due to timeout in protocol %d",id(self.protocol.transport))
                self.protocol.cond_dictControlling.notify()
            else:
                logging.debug("fail to self.protocol.dictControlling.pop(%d) in protocol %d",self.command_seq,id(self.protocol.transport))
            self.timer=None
        superbox_id=None
        if self.protocol.role==BaseCommand.PV_ROLE_INTERNAL:
            with self.protocol.lock_dictWaitResp:
                #request=self.protocol.dictWaitResp.pop((self.superbox_id<<32)+self.command_seq,None)
                request=self.protocol.dictWaitResp.pop((self.requireTransport<<32)+self.command_seq,None)
            superbox_id=self.superbox_id
        else:
            with self.protocol.lock_dictWaitResp:
                request=self.protocol.dictWaitResp.pop(self.command_seq,None)
            superbox_id=self.protocol.superbox_id
        if request is None: return  #this request has been feedbacked
        respond=request.GetResp()
        respond.command_status=BaseCommand.CS_SUPERBOXRESPTIMEOUT
        respond.body={}
        requireCommand=request.requireCommand
        requireCommand.FinishOne(superbox_id,request,respond)
        request.requireCommand=None

    
    #----------------subclass override--------------------
    def initDictSuperboxControls(self):
        pass
    
    def getCommand(self,deviceCmd):
        return None
    #-----------------------------------------------------

    def Send(self):
        maxcmd_flow_control=1000
        if self.protocol.role==BaseCommand.PV_ROLE_SUPERBOX:
            maxcmd_flow_control=Config.maxcmd_superbox_control
        while True:
            with self.protocol.cond_dictControlling:
                if len(self.protocol.dictControlling.keys())>maxcmd_flow_control:
                    logging.debug("call self.protocol.cond_dictControlling.wait() due to reach maxcmd in protocol %d",id(self.protocol.transport))
                    self.protocol.cond_dictControlling.wait()
                elif self.protocol.dictControlling.has_key(self.command_seq):
                    logging.debug("call self.protocol.cond_dictControlling.wait() due to same command_seq in protocol %d",id(self.protocol.transport))
                    self.protocol.cond_dictControlling.wait()
                else:
                    interMessage=None
                    self.protocol.dictControlling[self.command_seq]=self
                    self.timer=reactor.callLater(Config.timeout_superbox_control,self.timeout)
                    
                    #if isinstance(self.requireCommand,BaseCommand.CBaseCommand):
                    if self.requireCommand is not None and self.requireCommand.internalMessage is None:
                        interMessage=InternalMessage.CInternalMessage()
                        interMessage.SetParam(InternalMessage.TTYPE_GATEWAY,self.superbox_id,0,InternalMessage.OPER_REQUEST,"",
                                          InternalMessage.TTYPE_HUMAN,self.requireCommand.protocol.client_id,id(self.requireCommand.protocol.transport))
                    
                    CBaseCommand.Send(self,interMessage)
                    
                    break
          
                        