CC=g++
CFLAGS=-c -Wall -std=c++11 -O2
LDFLAGS=-Wall
TFLAGS=-lpthread

objs := proxy.o ProxyWorker.o HttpParser.o RequestStorage.o
prog := crawlcheck

.PHONY: all

all: $(prog)

${prog}: $(objs)
	$(CC) $(LDFLAGS) ${TFLAGS} -o $@ $^

RequestStorage.o : proxy/RequestStorage.cc
	$(CC) $(CFLAGS) -o $@ $<
HttpParser.o : proxy/HttpParser.cc
	$(CC) $(CFLAGS) -o $@ $<
ProxyWorker.o : proxy/ProxyWorker.cc
	${CC} ${CFLAGS} ${TFLAGS} -o $@ $^
proxy.o : proxy/proxy.cc
	$(CC) $(CFLAGS) -o $@ $<
  
proxy/RequestStorage.cc : proxy/HttpParser.h
proxy/HttpParser.cc : proxy/HttpParser.h
proxy/ProxyWorker.cc : proxy/ProxyWorker.h proxy/HelperRoutines.h proxy/HttpParser.h proxy/RequestStorage.h
proxy/proxy.cc : proxy/proxy.h db/db.h checker/checker.h proxy/ProxyWorker.h proxy/HelperRoutines.h proxy/RequestStorage.h
  
clean:
	rm -f ${objs} ${prog}
