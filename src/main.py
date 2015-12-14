'''
Created on 2013-7-31

@author: E525649
'''
from Utils import Util
if Util.isWindows():
    from twisted.internet import iocpreactor
    iocpreactor.install()
else:
    from twisted.internet import epollreactor
    epollreactor.install()
    
import Utils.Patroller as Patroller
import SBPS.ProtocolReactor as ProtocolReactor
import logging
logging.basicConfig(filename='example.log',level=logging.INFO,format="%(asctime)s-%(name)s-%(levelname)s-%(message)s")

if __name__ == '__main__':
    logging.info("Superbox Server starting...")
    print "Superbox Server starting..."
    #Patroller.Run() 
    #Patroller.StopAll()
    ProtocolReactor.Run() #run until stop
    #Patroller.StopAll()