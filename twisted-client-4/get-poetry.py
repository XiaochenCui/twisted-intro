# This is the Twisted Get Poetry Now! client, version 4.0

import optparse, sys

from twisted.internet import defer
from twisted.internet.protocol import Protocol, ClientFactory


def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...

This is the Get Poetry Now! client, Twisted version 4.0
Run it like this:

  python get-poetry.py port1 port2 port3 ...

If you are in the base directory of the twisted-intro package,
you could run it like this:

  python twisted-client-4/get-poetry.py 10001 10002 10003

to grab poetry from servers on ports 10001, 10002, and 10003.

Of course, there need to be servers listening on those ports
for that to work.
"""

    parser = optparse.OptionParser(usage)

    _, addresses = parser.parse_args()

    if not addresses:
        print parser.format_help()
        parser.exit()

    def parse_address(addr):
        if ':' not in addr:
            host = '127.0.0.1'
            port = addr
        else:
            host, port = addr.split(':', 1)

        if not port.isdigit():
            parser.error('Ports must be integers.')

        return host, int(port)

    return map(parse_address, addresses)


class PoetryTimeoutError(Exception): pass


class PoetryProtocol(Protocol):

    poem = ''

    def connectionMade(self):
        port = self.transport.getPeer().port
        self.onTime = None
        # poetry downloads on even numbered ports time out after 1 sec
        # just another of the ways the universe is stacked against poetry
        if not port % 2:
            self.onTime = True
            from twisted.internet import reactor
            self.timer = reactor.callLater(3, self.timeout)

    def timeout(self):
        self.onTime = False
        self.transport.loseConnection()

    def dataReceived(self, data):
        self.poem += data

    def connectionLost(self, reason):
        if self.onTime is not None:
            if self.onTime == True:
                self.timer.cancel()
            else:
                err = PoetryTimeoutError('Evil timeout stole your poetry again!')
                self.factory.deferred.errback(err)
                return
        self.poemReceived(self.poem)

    def poemReceived(self, poem):
        self.factory.poem_finished(poem)


class PoetryClientFactory(ClientFactory):

    protocol = PoetryProtocol

    def __init__(self, deferred):
        self.deferred = deferred

    def poem_finished(self, poem):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(poem)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)


def get_poetry(host, port):
    """
    Download a poem from the given host and port. This function
    returns a Deferred which will be fired with the complete text of
    the poem or a Failure if the poem could not be downloaded.
    """
    d = defer.Deferred()
    from twisted.internet import reactor
    factory = PoetryClientFactory(d)
    reactor.connectTCP(host, port, factory)
    return d


def poetry_main():
    addresses = parse_args()

    from twisted.internet import reactor

    poems = []
    errors = []

    def got_poem(poem):
        poems.append(poem)

    def poem_failed(err, host=None, port=None):
        print >>sys.stderr, 'Poem failed on {host}:{port}'.format(host=host, port=port), err
        errors.append(err)

    def poem_done(_):
        if len(poems) + len(errors) == len(addresses):
            reactor.stop()

    for address in addresses:
        host, port = address
        d = get_poetry(host, port)
        errback_kwargs = {
            'host': host,
            'port': port,
        }
        d.addCallbacks(got_poem, poem_failed, errbackKeywords=errback_kwargs)
        d.addBoth(poem_done)

    reactor.run()

    for poem in poems:
        print poem


if __name__ == '__main__':
    poetry_main()
