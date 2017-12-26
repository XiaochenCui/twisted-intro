import sys

from twisted.internet.defer import Deferred

def got_poem(poem):
    print poem
    return poem

def poem_failed(err):
    print >>sys.stderr, 'poem download failed'
    print >>sys.stderr, 'I am terribly sorry'
    print >>sys.stderr, 'try again later?'
    return err

def poem_done(_):
    print _
    from twisted.internet import reactor
    reactor.stop()

d = Deferred()

d.addCallbacks(got_poem, poem_failed)
d.addBoth(poem_done)

from twisted.internet import reactor

reactor.callWhenRunning(d.errback, Exception('exception called'))

reactor.run()
