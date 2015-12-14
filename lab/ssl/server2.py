from twisted.internet import reactor, ssl
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver

class TLSServer(LineReceiver):
    def lineReceived(self, line):
        print "received: " + line

        if line == "STARTTLS":
            print "-- Switching to TLS"
            self.sendLine('READY')

            self.transport.startTLS(self.factory.contextFactory)


if __name__ == '__main__':
    with open("key.pem") as keyFile:
        with open("selfcert.pem") as certFile:
            cert = ssl.PrivateCertificate.loadPEM(
                keyFile.read() + certFile.read())

    factory = ServerFactory()
    factory.protocol = TLSServer
    factory.contextFactory = cert.options()
    reactor.listenTCP(8001, factory)
    reactor.run()
