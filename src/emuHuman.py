'''
Created on 2013-8-15

@author: E525649
'''

import logging,threading,time,thread
import emuSBPS.emuReactor as emuReactor
import emuSBPS
from DB import SBDB,SBDB_ORM
from emuSBPS import *
from Command import Authorize,BaseCommand,HeartBeat,AddAccount,AddApartment,\
AddDevice,AddSuperbox,ModifyApartment,ModifyDevice,ModifySuperbox,RemoveApartment,\
RemoveSuperbox,RemoveDevice,BaseControl,AddScene,RemoveScene,ModifyScene,AddContactor,\
RemoveContactor,ModifyContactor,SetScene,QueryApartment,QueryAccount,QueryDevice, PasswordRestore
logging.basicConfig(filename='example_superbox.log',level=logging.INFO,format="%(asctime)s-%(name)s-%(levelname)s-%(message)s")
import random,sys


run_mode="command"
run_role="human"

def main_loop():
    time.sleep(1)
    if emuReactor.protocolActive is None:
        print "can't connect server"
        return
    global run_mode,run_role
    if len(sys.argv)>1: run_mode=sys.argv[1]
    if len(sys.argv)>2: run_role=sys.argv[2]
    
    
    user_name='pp'
    sb_code='test_superbox'
    dev_code='12345678'
    apartment_id=4
    account=apartment=superbox=device=scene=contactor=None
    CommandList=["AddAccount","Authorize","AddApartment","AddSuperbox","AddDevice",\
                 "ModifyDevice","AddScene","ModifyScene","SetScene",\
                 "AddContactor","ModifyContactor","QueryApartment",\
                 "QueryAccount","RemoveContactor",\
                 "RemoveScene","RemoveDevice","ModifySuperbox","RemoveSuperbox",\
                 "ModifyApartment","RemoveApartment"]
    nCommandIndex=0
    while True:
    #for str_command in CommandList:
        request=None
        commands=[]
        try:
            command=""
            if run_mode=="command":
                command = raw_input('Enter Command: ')
            elif run_mode=="press_control":
                if nCommandIndex==0:
                    command="Authorize"
                    nCommandIndex=nCommandIndex+1
                else:
                    command="ControlDevice"
            else:
                if nCommandIndex>=len(CommandList):break
                command=CommandList[nCommandIndex]
                nCommandIndex=nCommandIndex+1
            if command=="quit": break;
            commands=command.split()
            request=eval(commands[0]+".C"+commands[0]+"()")
            request.protocol=emuReactor.protocolActive
        except Exception, e:
            print "unknown command :", command,e
            continue
            
        if isinstance(request, Authorize.CAuthorize):
            request.body[BaseCommand.PN_USERNAME]=user_name
            request.body[BaseCommand.PN_PASSWORD]="123"
            request.body[BaseCommand.PN_TERMINALTYPE]=BaseCommand.PV_ROLE_HUMAN
        elif isinstance(request,AddAccount.CAddAccount):
            #user_name="user"+str(random.uniform(0,4000))
            request.body[BaseCommand.PN_USERNAME]=user_name
            request.body[BaseCommand.PN_PASSWORD]="123"
            request.body[BaseCommand.PN_EMAIL]=user_name+"@163.com"
            account=request
        elif isinstance(request, AddApartment.CAddApartment):
            request.body[BaseCommand.PN_APARTMENTNAME]="apartment"+str(random.randint(0,100))
            apartment=request
        elif isinstance(request, AddSuperbox.CAddSuperbox):
            sb_code="sb_"+str(random.uniform(0,4000))
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            #request.body[BaseCommand.PN_SB_CODE]="sb_code"+str(random.randint(0,100))
            request.body[BaseCommand.PN_SB_CODE]="test_superbox"
            request.body[BaseCommand.PN_NAME]="sb_name"+str(random.randint(0,100))
            superbox=request
        elif isinstance(request, ModifyApartment.CModifyApartment):
            request.body[BaseCommand.PN_APARTMENTNAME]="apartment"+str(random.randint(0,100))
            request.body[BaseCommand.PN_ID]=apartment.respond.body[BaseCommand.PN_ID]
        elif isinstance(request, ModifySuperbox.CModifySuperbox):
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_SB_CODE]="sb_code"+str(random.randint(0,100))
            request.body[BaseCommand.PN_SUPERBOXID]=superbox.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_NAME]="sb_name"+str(random.randint(0,100))
        elif isinstance(request, RemoveApartment.CRemoveApartment):
            request.body[BaseCommand.PN_ID]=apartment.respond.body[BaseCommand.PN_ID]
        elif isinstance(request, RemoveSuperbox.CRemoveSuperbox):
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_SUPERBOXID]=superbox.respond.body[BaseCommand.PN_ID]
        elif isinstance(request, AddDevice.CAddDevice):
            if run_mode=="auto":
                request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            else:
                request.body[BaseCommand.PN_APARTMENTID]=apartment_id
            request.body[BaseCommand.PN_DEVMODEL]="2111S"
            request.body[BaseCommand.PN_DEVCODE]=dev_code #str(random.randint(0,10000))
            request.body[BaseCommand.PN_SUPERBOXID]=1
            device=request
        elif isinstance(request, ModifyDevice.CModifyDevice):
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_DEVICEID]=device.respond.body[BaseCommand.PN_DEVICEID]
            request.body[BaseCommand.PN_DEVCODE]=str(random.randint(0,100))
            request.body[BaseCommand.PN_NAME]="dev_name"+request.body[BaseCommand.PN_DEVCODE]
            request.body[BaseCommand.PN_FLAGNOTIFICATION]=str(str(random.randint(0,100)))
            request.body[BaseCommand.PN_DEVKEYS]=[{"dev_key_seq":0,"name":'abc'}]
        elif isinstance(request, RemoveDevice.CRemoveDevice):
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_DEVICEID]=device.respond.body[BaseCommand.PN_DEVICEID]
            request.body[BaseCommand.PN_DEVKEYS] = [{"dev_key_seq":0}]
        elif isinstance(request, ControlDevice.CControlDevice):
            request.body[BaseCommand.PN_DEVMODEL]="2111S"
            if len(commands)>1:
                request.body[BaseCommand.PN_DEVCODE]=commands[1]
            else:
                request.body[BaseCommand.PN_DEVCODE]=dev_code
                
            if len(commands)>2:
                request.body[BaseCommand.PN_DEVSEQ]=int(commands[2])
            else:
                request.body[BaseCommand.PN_DEVSEQ]=0
            
            if len(commands)>3:
                request.body[BaseCommand.PN_DEVVALUE]=int(commands[3])
            else:
                request.body[BaseCommand.PN_DEVVALUE]=1
                
            if len(commands)>4:
                request.body[BaseCommand.PN_DEVMODEL]=commands[4]
            else:
                request.body[BaseCommand.PN_DEVMODEL]="2111S"
        elif isinstance(request, AddScene.CAddScene):
            request.body[BaseCommand.PN_NAME]="scene_"+str(str(random.randint(0,100)))
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            content={}
            content[BaseCommand.PN_DEVICEID]=device.respond.body[BaseCommand.PN_DEVICEID]
            content[BaseCommand.PN_DEVSEQ]=0
            content[BaseCommand.PN_DEVVALUE]=random.randint(0,100)
            request.body[BaseCommand.PN_SCENECONTENTS]=[content,]
            scene=request
        elif isinstance(request, ModifyScene.CModifyScene):
            request.body[BaseCommand.PN_NAME]="scene_"+str(str(random.randint(0,100)))
            request.body[BaseCommand.PN_ID]=scene.respond.body[BaseCommand.PN_ID]
            content={}
            content[BaseCommand.PN_DEVICEID]=device.respond.body[BaseCommand.PN_DEVICEID]
            content[BaseCommand.PN_DEVSEQ]=0
            content[BaseCommand.PN_DEVVALUE]=random.randint(0,100)
            request.body[BaseCommand.PN_SCENECONTENTS]=[content,]
        elif isinstance(request, RemoveScene.CRemoveScene):
            request.body[BaseCommand.PN_ID]=scene.respond.body[BaseCommand.PN_ID]
        elif isinstance(request, SetScene.CSetScene):
            #request.body[BaseCommand.PN_ID]=scene.respond.body[BaseCommand.PN_ID]
            if len(commands)>1:
                request.body[BaseCommand.PN_SPECIALSCENE]=commands[1]
                request.body[BaseCommand.PN_APARTMENTID]=apartment_id
            else:
                #request.body[BaseCommand.PN_ID]=scene.respond.body[BaseCommand.PN_ID]
                request.body[BaseCommand.PN_ID]=scene.respond.body[BaseCommand.PN_ID]
                
            if len(commands)>2:
                request.body[BaseCommand.PN_APARTMENTID]=int(commands[2])
        elif isinstance(request, QueryApartment.CQueryApartment):
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_VERSION]=0
        elif isinstance(request, AddContactor.CAddContactor):
            request.body[BaseCommand.PN_NAME]="contactor_"+str(str(random.randint(0,100)))
            request.body[BaseCommand.PN_APARTMENTID]=apartment.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_MOBLEPHONE]="phone_"+str(str(random.randint(0,100)))
            contactor=request
        elif isinstance(request, ModifyContactor.CModifyContactor):
            request.body[BaseCommand.PN_ID]=contactor.respond.body[BaseCommand.PN_ID]
            request.body[BaseCommand.PN_NAME]="contactor_"+str(str(random.randint(0,100)))
            request.body[BaseCommand.PN_MOBLEPHONE]="phone_"+str(str(random.randint(0,100)))
        elif isinstance(request, RemoveContactor.CRemoveContactor):
            request.body[BaseCommand.PN_ID]=contactor.respond.body[BaseCommand.PN_ID]
        elif isinstance(request, QueryDevice.CQueryDevice):
            request.body[BaseCommand.PN_DEVMODEL]="2113D"
            if len(commands)>1:
                request.body[BaseCommand.PN_DEVCODE]=commands[1]
            else:
                request.body[BaseCommand.PN_DEVCODE]=dev_code
                
            if len(commands)>2:
                request.body[BaseCommand.PN_DEVSEQ]=int(commands[2])
            else:
                request.body[BaseCommand.PN_DEVSEQ]=0
            
            
            
        if not emuReactor.SendAndVerify(request):
            if run_mode=="auto": break
        
def main():
    #thread.start_new_thread(emuReactor.Run)
    t=threading.Thread(target=main_loop)
    t.start()
    emuReactor.Run()
    

if __name__ == '__main__':
    main()
        
        
        
        
        