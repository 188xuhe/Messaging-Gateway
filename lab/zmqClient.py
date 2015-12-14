'''
Created on 2013-11-1

@author: E525649
'''

import sys
import zmq
import struct

def main():
    #  Socket to talk to server
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    
    print "Collecting updates from weather server..."
    socket.connect ("tcp://159.99.249.65:5557")
    
    # Subscribe to zipcode, default is NYC, 10001
    zip_filter = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    for i in range(7000):
        if i%7==zip_filter:
            zipcode = "s"+struct.pack("!I",i)
            #zipcode='s%08d'%i
            socket.setsockopt(zmq.SUBSCRIBE, "a"+zipcode)

    n=0
    while True:
        n=n+1
        [head,string] = socket.recv_multipart()
        zipcode, temperature, relhumidity = string.split()
        print "zipcode '%s' was %dF,relhumidity:%s, filter count %d, head:%s" % (
              zipcode, int(temperature),relhumidity,n,head)
        continue
        
        # Process 5 updates
        total_temp = 0
        for update_nbr in range (5):
            string = socket.recv()
            zipcode, temperature, relhumidity = string.split()
            total_temp += int(temperature)
        
        print "Average temperature for zipcode '%s' was %dF" % (
              zip_filter, total_temp / update_nbr)
        

if __name__ == '__main__':
    main()