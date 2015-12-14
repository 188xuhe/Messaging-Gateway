#-*- coding: UTF-8 -*-
'''
Created on 2013-9-6

@author: E525649
'''


from BaseCommand import CBaseCommand
from sqlalchemy.exc import SQLAlchemyError
from DB import SBDB,SBDB_ORM
from Command import BaseCommand,ControlDevice,EventDevNotify
import logging,datetime
from Utils import Alarm, smslib, Config,Util
#from Command.SetScene import CSetScene
from sqlalchemy import and_
import threading, time
from SBPS import InternalMessage
import Utils
from twisted.internet import threads

class CBufferedState:
    def __init__(self,device_state,time):
        self.device_state=device_state
        self.time=time
        
class CDevKeyStatus:
    def __init__(self,value,array):
        self.value=value
        self.array=array
          
          
          
     
class CEventDev(CBaseCommand):
    '''
    classdocs 
    '''
    command_id=0x00070001
    dictEventBuffer={}  #key: device_code, value: array of CBufferedState
    lockEventBuffer=threading.RLock()
    def __init__(self,data=None,protocol=None):
        '''
        Constructor
        '''
        CBaseCommand.__init__(self, data, protocol)
    
    def Run(self):
        if self.protocol.role==BaseCommand.PV_ROLE_INTERNAL:
            notify=EventDevNotify.CEventDevNotify(self.data,InternalMessage.protocolInternal,self.internalMessage.destId)
            print "body is -----------",notify.body
            notify.superbox_id=self.internalMessage.fromId
            notify.Notify()
            return
        with self.protocol.lockCmd:
            if not self.Authorized(): 
                self.SendUnauthorizedResp()
                return
            CBaseCommand.Run(self)
            session=SBDB.GetSession()
            if session is not None:
            #with SBDB.session_scope() as session :
                dev_model=self.body.get(BaseCommand.PN_DEVMODEL)
                dev_code=self.body[BaseCommand.PN_DEVCODE].upper()
                dev_key_seq=self.body.get(BaseCommand.PN_DEVSEQ,0)
                value=self.body[BaseCommand.PN_DEVVALUE]        
                respond=self.GetResp()
                respond.Send()
                value_old=0
                try:
                    #avoid DB access for non-configured device 
                    #if dev_code not in SBDB.setDeviceCodes: return
                    
                    device_key_code=SBDB.GetDeviceKeyCodeByDeviceCode(session,dev_code)
                    if device_key_code is None: return
                    model=device_key_code.device.device_model
    #                 if model is None:   return
                    
                    timeNow=time.time()
                    #find the last reported value
                    with CEventDev.lockEventBuffer:
                        dictbufferedDeviceStates=CEventDev.dictEventBuffer.get(dev_code)
                        key_bufferedDeviceStates=None
                        if dictbufferedDeviceStates is not None:
                            key_bufferedDeviceStates=dictbufferedDeviceStates.get(dev_key_seq)
                            if key_bufferedDeviceStates is not None:
                                value_old=key_bufferedDeviceStates.value
                        if dictbufferedDeviceStates is None:
                            CEventDev.dictEventBuffer[dev_code]={}
                        if key_bufferedDeviceStates is None:
                            CEventDev.dictEventBuffer[dev_code][dev_key_seq]=CDevKeyStatus(value,[])
                        else:
                            key_bufferedDeviceStates.value=value
                                
                    
                    dev_model=model.name
                    if dev_model.find("58")==0 or dev_model.find("HRMS-58")==0:
                        #58 detector:
                        for i in range(0,8):
                            powHigh=pow(2, i+1)
                            powLow=pow(2,i)
                            if value%powHigh>=powLow and value_old%powHigh<powLow:
                                print "process event:",dev_model, dev_code, dev_key_seq, powLow, timeNow
                                self.ProcessEvent(session, dev_model, dev_code, dev_key_seq, powLow, timeNow,device_key_code)
                    else:
                        self.ProcessEvent(session, dev_model, dev_code, dev_key_seq, value, timeNow,device_key_code)
                finally:
                    pass
#                 except SQLAlchemyError,e:
#                     respond.SetErrorCode(BaseCommand.CS_DBEXCEPTION)
#                     logging.error("transport %d:%s",id(self.protocol.transport),e)
#                     session.rollback()

    
    def ProcessEvent(self,session,dev_model,dev_code, dev_key_seq, value,timeNow,device_key_code):
        dev_state=SBDB.GetDevState(session, dev_model,dev_code, dev_key_seq, value,CEventDev.dictEventBuffer)
        if dev_state is None: return
        
        #update CEventDev.dictEventBuffer
        with CEventDev.lockEventBuffer:
            dictbufferedDeviceStates=CEventDev.dictEventBuffer.get(dev_code)
            key_bufferedDeviceStates=None
            bNeedAddState=True
            bDuplicated=False
            if dictbufferedDeviceStates is not None:
                key_bufferedDeviceStates=dictbufferedDeviceStates.get(dev_key_seq)
                if key_bufferedDeviceStates is not None:
                    for bufferedState in key_bufferedDeviceStates.array:
                        if bufferedState.device_state.id==dev_state.id:
                            if timeNow-bufferedState.time<Config.timeout_buffered_state:
                                bufferedState.time=timeNow
                                bDuplicated=True
                                break
                            else:
                                bufferedState.time=timeNow
                                bNeedAddState=False
                                break
            if bNeedAddState:
                bufferedState=CBufferedState(dev_state,timeNow)
                if dictbufferedDeviceStates is None:
                    CEventDev.dictEventBuffer[dev_code]={}
                if key_bufferedDeviceStates is None:
                    CEventDev.dictEventBuffer[dev_code][dev_key_seq]=CDevKeyStatus(value,[bufferedState,])
                else:
                    key_bufferedDeviceStates.array.append(bufferedState)
        
        #is not alarm
        if dev_state.device_key.alarm_type==BaseCommand.ALARM_TYPE_NO or dev_state.alarm_level<=0:
            print "is not alarm"		
            return
        
        #if is a duplicated event, ignore
        if bDuplicated:
            print "is duplicated event"
            return
        
        #save to event table
        event=SBDB_ORM.Event()
        event.device_key_code_id=device_key_code.id
#         event.device_key_code_id=dev_state.device_key.id
        #event.device_uni_code=dev_code
        event.value=value
        event.dt=datetime.datetime.now()
        event.alarm_level=dev_state.alarm_level
        session.add(event)
        session.commit()
        self.setControlCmd=set()
        if dev_state.device_key.device_model.name==BaseCommand.gas_sensor_model:
            request=ControlDevice.CControlDevice(protocol=self.protocol)
            request.body[BaseCommand.PN_DEVMODEL]=BaseCommand.gas_actuator_model
            request.body[BaseCommand.PN_DEVCODE]="00"
            request.body[BaseCommand.PN_DEVSEQ]=0                    
            request.body[BaseCommand.PN_DEVVALUE]=1   
            request.Send()
        for apartment_device in session.query(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Device).filter(SBDB_ORM.Device.uni_code==dev_code):
            print "run ProcessAlarm"
            self.ProcessAlarm(session,apartment_device, dev_code, dev_state,event)
        
    def ProcessAlarm(self,session,apartment_device,dev_code,dev_state,event):
        if apartment_device is None:    return
        apartment=apartment_device.apartment
        if dev_state.device_key.alarm_type==BaseCommand.ALARM_TYPE_ALWAYS or \
        dev_state.device_key.alarm_type==BaseCommand.ALARM_TYPE_SET and apartment.arm_state>BaseCommand.PV_ARM_OFF:
            #insert this alarm into database
            alarm=SBDB_ORM.Alarm()
            alarm.apartment_device_id=apartment_device.id
            alarm.event_id=event.id
            session.add(alarm)
            session.commit()
            
            #push this alarm to iOS clients
            #session=SBDB.GetSession()  
            listPhone=[x.mobile_phone for x in session.query(SBDB_ORM.Contactor).join(SBDB_ORM.Apartment).filter(SBDB_ORM.Apartment.id==apartment.id)]
            listIOS=[x.device_token for x in session.query(SBDB_ORM.Client).join(SBDB_ORM.Account).filter(and_(SBDB_ORM.Account.id==apartment.account_id,SBDB_ORM.Client.os==BaseCommand.PV_OS_IOS))]
            print "alarm sendable",listPhone,listIOS,apartment.id,apartment.account_id
            if len(listPhone)>0 or len(listIOS)>0:
                device_name,=session.query(SBDB_ORM.ApartmentDevice.name).join(SBDB_ORM.Device).join(SBDB_ORM.Apartment_Superbox,SBDB_ORM.ApartmentDevice.apartment_id==SBDB_ORM.Apartment_Superbox.apartment_id).join(SBDB_ORM.Superbox).filter(and_(SBDB_ORM.Apartment_Superbox.apartment_id==apartment.id,SBDB_ORM.Device.uni_code==dev_code)).first()
                print "ddddddddddddddddddddd",device_name,apartment,event,apartment.id,event.id

                template=Utils.Alarm.GetTemplate(session,apartment,event)
                #template=GetTemplate(apartment,event)
                print "alarm: ",listPhone,listIOS,apartment.id
                if len(listPhone)>0:                    
                    #threading.Thread(target=smslib.SendAndSave,args=(template.template, apartment,dev_state.name , listPhone,device_name)).start()
                    threads.deferToThread(smslib.SendAndSave,template.template, apartment,dev_state.name , listPhone,device_name) 
                if len(listIOS)>0:
                    message=Util.GenAlarmMessage(session, template.template, apartment, dev_state.name, device_name)
                    threading.Thread(target=Util.push_ios,args=(listIOS, "alarm", message)).start()
                    print "started thread for push message:",message
            #session.close()
            
            #notify clients by SBMP
            
            #notify=EventDevNotify.CEventDevNotify(self.data,InternalMessage.protocolInternal,apartment.account_id)
            for client_id in SBDB.GetActiveClientIdsByAccountId(apartment.account_id):
                notify=EventDevNotify.CEventDevNotify(self.data,self.protocol,client_id)
                interMessage=InternalMessage.CInternalMessage()
                interMessage.SetParam(InternalMessage.TTYPE_HUMAN,client_id,0,InternalMessage.OPER_REQUEST,"",
                                  InternalMessage.TTYPE_GATEWAY,self.protocol.superbox_id,id(self.protocol.transport))
            
                notify.Notify(interMessage)
        '''
        if dev_state.device_key.device_model.name==BaseCommand.gas_sensor_model:
            set_scene=CSetScene(protocol=self.protocol)
            set_scene.body[BaseCommand.PN_SPECIALSCENE]=BaseCommand.PV_SCENE_GASSENSOR
            set_scene.body[BaseCommand.PN_APARTMENTID]=apartment.id
            set_scene.EventGas=self
            set_scene.Run()
        '''
