'''
Created on 2013-8-12

@author: E525649
'''
from sqlalchemy import create_engine,and_ 
from sqlalchemy.orm import scoped_session, sessionmaker,undefer
from Utils import Config
#engine = create_engine('postgresql://postgres:HON123well@127.0.0.1:5432/SBDB', echo=False)
engine = create_engine(Config.db_connection_string, echo=False)

SessionType = scoped_session(sessionmaker(bind=engine,expire_on_commit=False))
import threading, datetime
import logging
import string
from Utils import Util



CV_TYPE_SERVER_FUNCTION=1
CV_TYPE_SERVER_SUPERVISION=2


def GetSession():
    return SessionType()

from contextlib import contextmanager
@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = GetSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


import SBDB_ORM
from sqlalchemy import or_,distinct

# g_session=GetSession()
# g_lock_session=threading.RLock()
# g_lock_session.acquire()
# deviceModels=g_session.query(SBDB_ORM.DeviceModel).all()
# setDeviceCodes=set()
# for x, in g_session.query(distinct(SBDB_ORM.Device.uni_code)).all():
#     setDeviceCodes.update((x,))
# g_lock_session.release()
#g_session.close()

def GetSuperboxIdForcely(superbox_code):
    with session_scope() as session :
        try:
            superbox=session.query(SBDB_ORM.Superbox).filter_by(uni_code=superbox_code).with_lockmode('update').first()
            if superbox is None:
                superbox=SBDB_ORM.Superbox()
                superbox.uni_code=superbox_code
                session.add(superbox)
            session.commit()
            return superbox.id
        except Exception,e:
            session.rollback()
            raise e
        
def GetDeviceForcely(session,device_code,model_name=None):
    
    device=session.query(SBDB_ORM.Device).filter_by(uni_code=device_code).with_lockmode('update').first()
    if device is None:
        model=GetDeviceModelByName(session,model_name)
        if model is None:   return None
        device=SBDB_ORM.Device()
        device.uni_code=device_code
        device.device_model_id=model.id
        
        obj_dev_model=model
        for obj_dev_key in obj_dev_model.device_keys:
            obj_dev_key_code=SBDB_ORM.DeviceKeyCode()
            obj_dev_key_code.device_key_id=obj_dev_key.id
            #obj_dev_key_code.key_code=hex(string.atoi(dev_code,16)+obj_dev_key.seq)[2:]
            obj_dev_key_code.key_code=Util.hex8(string.atoi(device_code,16)+obj_dev_key.seq)[2:]
            device.device_key_codes.append(obj_dev_key_code)
            
        session.add(device)
    session.commit()
    return device
  

def GetAccount(session,username,password=None):
    account=None
    if password is None:
        account=session.query(SBDB_ORM.Account).filter(or_(SBDB_ORM.Account.user_name==username,SBDB_ORM.Account.email==username, SBDB_ORM.Account.mobile_phone==username)).first()
    else:
        account=session.query(SBDB_ORM.Account).filter(SBDB_ORM.Account.password==password).filter(or_(SBDB_ORM.Account.user_name==username,SBDB_ORM.Account.email==username, SBDB_ORM.Account.mobile_phone==username)).first()
        
    return account

def GetSuperboxIDsByAccountId(account_id,session=None):
    release=False
    if session is None: 
        session=GetSession()
        release=True
    SuperboxIDs=[]
    for superboxId, in session.query(SBDB_ORM.Apartment_Superbox.superbox_id).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).filter(SBDB_ORM.Account.id==account_id).all():
        SuperboxIDs.append(superboxId)
    if release: session.close()
    return SuperboxIDs




def GetDeviceModelByName(session,model_name):
    for model in session.query(SBDB_ORM.DeviceModel).all():
        if model.name==model_name: 
            return model
    return None

def GetDeviceKeyByModelAndSeq(obj_device_model,seq_number):
    for dev_key in obj_device_model.device_keys:
        if dev_key.seq==seq_number: return dev_key
    return None

def GetDeviceKeyCodeByDeviceCode(session,dev_code):
    return session.query(SBDB_ORM.DeviceKeyCode).filter(SBDB_ORM.DeviceKeyCode.key_code==dev_code).first()
#     return session.query(SBDB_ORM.DeviceModel).join(SBDB_ORM.Device).filter(SBDB_ORM.Device.uni_code==dev_code).first()

def IncreaseVersion(session,apartment_id):
    apartment=session.query(SBDB_ORM.Apartment).with_lockmode('update').filter(SBDB_ORM.Apartment.id==apartment_id).first()
    apartment.version=apartment.version+1
    return apartment

def IncreaseVersions(session,superbox_id,apartment_id):
    if superbox_id==0:
        return IncreaseVersion(session,apartment_id)
    else:
        apartments=session.query(SBDB_ORM.Apartment).with_lockmode('update').join(SBDB_ORM.Apartment_Superbox).filter(SBDB_ORM.Apartment_Superbox.superbox_id==superbox_id).all()
    for apartment in apartments:
        apartment.version=apartment.version+1
    for apartment in apartments:
        if apartment.id == apartment_id:
            return apartment
    return None
    
def GetDevState(session,dev_model,dev_code,dev_seq,value,dictBufferedState=None):
    if dictBufferedState is not None:
        dictbufferedStates=dictBufferedState.get(dev_code)
        if dictbufferedStates is not None:
            bufferedStates=dictbufferedStates.get(dev_seq)
            if bufferedStates is not None:
                for bufferedState in bufferedStates.array:
                    if bufferedState.device_state.value_begin <= value <= bufferedState.device_state.value_end:
                        return bufferedState.device_state
                
    query=session.query(SBDB_ORM.DeviceState).join(SBDB_ORM.DeviceKey).join(SBDB_ORM.DeviceModel).join(SBDB_ORM.Device).filter(and_(SBDB_ORM.DeviceKey.seq==dev_seq,SBDB_ORM.Device.uni_code==dev_code))
    if dev_model is not None: query=query.filter(SBDB_ORM.DeviceModel.name==dev_model)
    for dev_state in query:
        if dev_state.value_begin <= value <= dev_state.value_end:
            return dev_state
    return None

def GetLightsByApartmentID(session,apartment_id,state):
    return session.query(SBDB_ORM.Device,SBDB_ORM.DeviceKey,SBDB_ORM.DeviceState).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).filter(and_(SBDB_ORM.Device.id==SBDB_ORM.DeviceKeyCode.device_id,SBDB_ORM.DeviceKeyCode.device_key_id==SBDB_ORM.DeviceKey.id,SBDB_ORM.DeviceKey.id==SBDB_ORM.DeviceState.device_key_id,SBDB_ORM.DeviceState.name==state,SBDB_ORM.Apartment.id==apartment_id,SBDB_ORM.Device.device_model_id==SBDB_ORM.DeviceModel.id,SBDB_ORM.DeviceModel.device_type_id==SBDB_ORM.DeviceType.id,SBDB_ORM.DeviceType.name.like('%light%'))).options(undefer(SBDB_ORM.Device.id))

    
def CheckRestoreUUID(code_uuid,session=None):
    release=False
    if session==None:   
        session=GetSession()
        release=True
    require=session.query(SBDB_ORM.RestoreRequire).filter(and_(SBDB_ORM.RestoreRequire.uuid==code_uuid,SBDB_ORM.RestoreRequire.finished==False, SBDB_ORM.RestoreRequire.dt>datetime.datetime.now()-datetime.timedelta(seconds=Config.second_restore_require))).with_lockmode('update').first()
    if release: session.close()
    return require is not None

def RestorePasswordByUUID(code_uuid,hashed_password):
    with session_scope() as session :
        require=session.query(SBDB_ORM.RestoreRequire).filter(and_(SBDB_ORM.RestoreRequire.uuid==code_uuid,SBDB_ORM.RestoreRequire.finished==False, SBDB_ORM.RestoreRequire.dt>datetime.datetime.now()-datetime.timedelta(seconds=Config.second_restore_require))).with_lockmode('update').first()
        if require is None:
            logging.info("return False because require is None")
            return False
        
        account=session.query(SBDB_ORM.Account).join(SBDB_ORM.RestoreRequire).filter(SBDB_ORM.RestoreRequire.id==require.id).first()
        if account is None:
            logging.info("return False because account is None")
            return False
        require.finished=True 
        account.password=hashed_password
        
        session.commit()
    return True

def GetServers(server_type=CV_TYPE_SERVER_FUNCTION):
    with session_scope() as session :
        listServer=[]
        for server in session.query(SBDB_ORM.Server).filter(SBDB_ORM.Server.type==server_type).with_lockmode('update'):
            listServer.append((server.id,server.address,server.extern_address))
    return listServer

def GetAccountIdByClientId(clientId):
    with session_scope() as session :
        account_id,=session.query(SBDB_ORM.Client.account_id).filter(SBDB_ORM.Client.id==clientId).first()
    return account_id

def GetSuperboxesByAccountId(accountId):
    with session_scope() as session :
        listSuperboxes=[]
        for apartment_superbox in session.query(SBDB_ORM.Apartment_Superbox).join(SBDB_ORM.Apartment).filter(SBDB_ORM.Apartment.account_id==accountId).all():
            listSuperboxes.append(apartment_superbox.superbox_id)
    return listSuperboxes

def GetActiveClientIdsByAccountId(accountId):
    with session_scope() as session :
        listClientIds=[]
        for client_id, in session.query(SBDB_ORM.Client.id).join(SBDB_ORM.Account).filter(and_(SBDB_ORM.Account.id==accountId,SBDB_ORM.Client.dt_active>(datetime.datetime.now()-datetime.timedelta(seconds=Config.time_heartbeat)))).all():
            listClientIds.append(client_id)
    print "GetActiveClientIdsByAccountId:",accountId,listClientIds
    return listClientIds

def UpdateActiveTime(role_session, terminal_id,sock_=0):
    from Command import BaseCommand
    from SBPS import InternalMessage
    with session_scope() as session :
        if role_session==BaseCommand.PV_ROLE_HUMAN:
            session.query(SBDB_ORM.Client).filter(SBDB_ORM.Client.id==terminal_id).update({SBDB_ORM.Client.dt_active:datetime.datetime.now()})
            session.commit()
            InternalMessage.NotifyTerminalStatus(InternalMessage.TTYPE_HUMAN, terminal_id, sock_, InternalMessage.OPER_ONLINE)
        elif role_session==BaseCommand.PV_ROLE_SUPERBOX:
            session.query(SBDB_ORM.Superbox).filter(SBDB_ORM.Superbox.id==terminal_id).update({SBDB_ORM.Superbox.dt_active:datetime.datetime.now()})
            session.commit()
            InternalMessage.NotifyTerminalStatus(InternalMessage.TTYPE_GATEWAY, terminal_id, 0, InternalMessage.OPER_ONLINE)
    

def UpdateAuthTimeSuperbox(superbox_id):
    from SBPS import InternalMessage
    InternalMessage.RegistFilter(InternalMessage.TTYPE_GATEWAY,superbox_id)
    with session_scope() as session :
        session.query(SBDB_ORM.Superbox).filter(SBDB_ORM.Superbox.id==superbox_id).update({SBDB_ORM.Superbox.dt_auth:datetime.datetime.now(),SBDB_ORM.Superbox.server_id:InternalMessage.MyServerID})
        session.commit()
    InternalMessage.NotifyTerminalStatus(InternalMessage.TTYPE_GATEWAY, superbox_id, 0, InternalMessage.OPER_ONLINE)

def UpdateAuthTimeHuman(client_id,balance,sock_):
    from SBPS import InternalMessage
    InternalMessage.RegistFilter(InternalMessage.TTYPE_HUMAN,client_id)
    with session_scope() as session :
        session.query(SBDB_ORM.Client).filter(SBDB_ORM.Client.id==client_id).update({SBDB_ORM.Client.dt_auth:datetime.datetime.now()})
        session.commit()
    InternalMessage.NotifyTerminalStatus(InternalMessage.TTYPE_HUMAN, client_id, sock_, InternalMessage.OPER_ONLINE,balance)

def UpdateActiveTimeServer(serverId):
    with session_scope() as session :
        session.query(SBDB_ORM.Server).filter(SBDB_ORM.Server.id==serverId).update({SBDB_ORM.Server.dt_active:datetime.datetime.now()})
        session.commit()

if __name__ == '__main__':
    import time
    session =GetSession()
    for a in session.query(SBDB_ORM.ApartmentDeviceKey).join(SBDB_ORM.DeviceKeyCode).join(SBDB_ORM.DeviceKey).join(SBDB_ORM.Device,SBDB_ORM.Device.id==SBDB_ORM.DeviceKeyCode.device_id).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).join(SBDB_ORM.Account).join(SBDB_ORM.Client).filter(and_(SBDB_ORM.Client.id==5)):
        print a.name,a
    for device,device_key,device_state, in session.query(SBDB_ORM.Device,SBDB_ORM.DeviceKey,SBDB_ORM.DeviceState).join(SBDB_ORM.ApartmentDevice).join(SBDB_ORM.Apartment).filter(and_(SBDB_ORM.Device.id==SBDB_ORM.DeviceKeyCode.device_id,SBDB_ORM.DeviceKeyCode.device_key_id==SBDB_ORM.DeviceKey.id,SBDB_ORM.DeviceKey.id==SBDB_ORM.DeviceState.device_key_id,SBDB_ORM.DeviceState.name=="on",SBDB_ORM.Apartment.id==58,SBDB_ORM.Device.device_model_id==SBDB_ORM.DeviceModel.id,SBDB_ORM.DeviceModel.device_type_id==SBDB_ORM.DeviceType.id,SBDB_ORM.DeviceType.name.like('%light%'))).all():
        print device.device_model.name,device.uni_code,device_key.seq,device_state.value_end
                        
    for device,device_key,device_state, in session.query(SBDB_ORM.Device,SBDB_ORM.DeviceKey,SBDB_ORM.DeviceState).filter(and_(SBDB_ORM.Device.id==SBDB_ORM.DeviceKeyCode.device_id,SBDB_ORM.DeviceKeyCode.device_key_id==SBDB_ORM.DeviceKey.id,SBDB_ORM.DeviceKey.id==SBDB_ORM.DeviceState.device_key_id,SBDB_ORM.Apartment_Superbox.superbox_id==SBDB_ORM.Superbox.id,SBDB_ORM.Apartment_Superbox.apartment_id==58)):
        print device.uni_code,device_key,device_state.value_end
    
    event=SBDB_ORM.Event()
    #event.device_key_id=0 #dev_state.device_key.id
    #event.device_key=dev_state.device_key
    #event.device_uni_code="abc"
    event.value=1
    event.dt=time.time()
    event.alarm_level=0#dev_state.alarm_level
    session.add(event)
    #session.commit()
            
    b= session.query(SBDB_ORM.Superbox).join(SBDB_ORM.Device).all()
    print len(b)
    b= session.query(SBDB_ORM.Param).first()
    print "b:",b.param_value
    session.close()
    session =GetSession()
    a= session.query(SBDB_ORM.Param).first()
    print "a:",a.param_value
    a.param_value=a.param_value+"abc"
    session.commit()
    print "a:",a.param_value
    print "b:",b.param_value
    param=SBDB_ORM.Param()
    session.close()
    '''
    lan=SBDB_ORM.Language()
    lan.language="chinese"
    print "---------------",lan.id
    session.add(lan)
    session.commit()
    print "-------------",lan.id
    '''
    