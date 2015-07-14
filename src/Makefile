CC=g++
CFLAGS=-c -Wall -std=c++11 -O2
LDFLAGS=-Wall
TFLAGS=-lpthread

objs := proxy.o ProxyWorker.o
prog := crawlcheck

.PHONY: all

all: $(prog)

${prog}: $(objs)
	$(CC) $(LDFLAGS) ${TFLAGS} -o $@ $^

ProxyWorker.o : proxy/ProxyWorker.cc
	${CC} ${CFLAGS} ${TFLAGS} -o $@ $^
proxy.o : proxy/proxy.cc
	$(CC) $(CFLAGS) -o $@ $<
  
proxy/ProxyWorker.cc : proxy/ProxyWorker.h proxy/HelperRoutines.h 
proxy/proxy.cc : proxy/proxy.h db/db.h checker/checker.h proxy/ProxyWorker.h proxy/HelperRoutines.h
  
clean:
	rm -f ${objs} ${prog}