CC=g++
CFLAGS=-c -Wall -std=c++11 -O2
LDFLAGS=-Wall
TFLAGS=-lpthread

objs := proxy.o ProxyWorker.o HttpParser.o RequestStorage.o HelperRoutines.o HttpParser.o ProxyConfiguration.o
prog := crawlcheck

.PHONY: all

all: $(prog)

${prog}: $(objs)
	$(CC) $(LDFLAGS) ${TFLAGS} -o $@ $^

ProxyConfiguration.o : proxy/ProxyConfiguration.cc
	$(CC) $(CFLAGS) -o $@ $<
HelperRoutines.o : proxy/HelperRoutines.cc
	$(CC) $(CFLAGS) -o $@ $<
RequestStorage.o : proxy/RequestStorage.cc
	$(CC) $(CFLAGS) ${TFLAGS} -o $@ $<
HttpParser.o : proxy/HttpParser.cc
	$(CC) $(CFLAGS) -o $@ $<
ProxyWorker.o : proxy/ProxyWorker.cc
	${CC} ${CFLAGS} ${TFLAGS} -o $@ $<
proxy.o : proxy/proxy.cc
	$(CC) $(CFLAGS) -o $@ $<

proxy/ProxyConfiguration.cc : proxy/ProxyConfiguration.h proxy/HelperRoutines.h
proxy/HelperRoutines.cc : proxy/HelperRoutines.h
proxy/RequestStorage.cc : proxy/HttpParser.h proxy/HelperRoutines.h
proxy/HttpParser.cc : proxy/HttpParser.h
proxy/ProxyWorker.cc : proxy/ProxyWorker.h proxy/HelperRoutines.h proxy/HttpParser.h proxy/RequestStorage.h proxy/ProxyConfiguration.h
proxy/proxy.cc : proxy/proxy.h db/db.h checker/checker.h proxy/ProxyWorker.h proxy/HelperRoutines.h proxy/ProxyConfiguration.h
  
clean:
	rm -f ${objs} ${prog}
