'''
Created on 2013-11-1

@author: E525649
'''

import zmq
import random
import struct,time

def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5557")
    
    for i in range(10000):
        zipcode = "s"+struct.pack("!I",i) #random.randrange(1,10000000)
        #zipcode='s%08d'%i
        temperature = random.randrange(1,215) - 80
        relhumidity = i
    
        socket.send_multipart(["a%swee" % (zipcode),"%s %d %d" % (zipcode, temperature, relhumidity)])
        #print "sent %d %d %d" % (zipcode, temperature, relhumidity)
        time.sleep(1)

if __name__ == '__main__':
    main()