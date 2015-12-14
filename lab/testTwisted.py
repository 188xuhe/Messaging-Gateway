'''
Created on Aug 26, 2014

@author: E525649
'''

from twisted.internet import reactor,threads,ssl
import time,threading
def aa(a):
    print "....aa.."
    print a

def thr():
    threads.deferToThread(aa,12)   
def rea():
    reactor.run() 
if __name__ == '__main__':
    
    
    
    threading.Thread(target=thr).start()
    #threading.Thread(target=rea).start()
    reactor.run() 