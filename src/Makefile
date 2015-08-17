CC=g++
CFLAGS=-c -Wall -std=c++11 -O2
LDFLAGS=-Wall -I/usr/include/libxml++-2.6 -I/usr/lib/libxml++-2.6/include -I/usr/include/libxml2 -I/usr/include/glibmm-2.4 -I/usr/lib/glibmm-2.4/include -I/usr/include/glib-2.0 -I/usr/lib/glib-2.0/include -I/usr/include/sigc++-2.0 -I/usr/lib/sigc++-2.0/include -lxml++-2.6 -lxml2 -lglibmm-2.4 -lgobject-2.0 -lglib-2.0 -lsigc-2.0
TFLAGS=-lpthread
XMLFLAGS=-I/usr/include/libxml++-2.6 -I/usr/lib/libxml++-2.6/include -I/usr/include/libxml2 -I/usr/include/glibmm-2.4 -I/usr/lib/glibmm-2.4/include -I/usr/include/glib-2.0 -I/usr/lib/glib-2.0/include -I/usr/include/sigc++-2.0 -I/usr/lib/sigc++-2.0/include -lxml++-2.6 -lxml2 -lglibmm-2.4 -lgobject-2.0 -lglib-2.0 -lsigc-2.0

objs := ClientAgent.o ServerAgent.o Db.o HttpParser.o ProxyConfiguration.o RequestStorage.o proxy.o
prog := crawlcheck

.PHONY: all

all: $(prog)

${prog}: $(objs)
	$(CC) $(LDFLAGS) $(XMLFLAGS)  ${TFLAGS} -o $@ $^

ClientAgent.o : proxy/ClientAgent.cc
	$(CC) $(CFLAGS) $(XMLFLAGS) ${TFLAGS} -o $@ $<
ServerAgent.o : proxy/ServerAgent.cc
	$(CC) $(CFLAGS) ${TFLAGS} -o $@ $<
Db.o : proxy/Db.cc
	$(CC) $(CFLAGS) ${TFLAGS} -o $@ $<
HttpParser.o : proxy/HttpParser.cc
	$(CC) $(CFLAGS) -o $@ $<
ProxyConfiguration.o : proxy/ProxyConfiguration.cc
	$(CC) $(CFLAGS) $(XMLFLAGS) -o $@ $<
RequestStorage.o : proxy/RequestStorage.cc
	$(CC) $(CFLAGS) ${TFLAGS} -o $@ $<
proxy.o : proxy/main.cc
	$(CC) $(CFLAGS) $(XMLFLAGS) -o $@ $<

proxy/ClientAgent.cc : proxy/ClientAgent.h proxy/RequestStorage.h proxy/HttpParser.h proxy/HelperRoutines.h proxy/ProxyConfiguration.h
proxy/ServerAgent.cc : proxy/ServerAgent.h proxy/RequestStorage.h proxy/ProxyConfiguration.h
proxy/HttpParser.cc : proxy/HttpParser.h proxy/HelperRoutines.h
proxy/ProxyConfiguration.cc : proxy/Configuration.h proxy/HelperRoutines.h db/db.h
proxy/RequestStorage.cc : proxy/RequestStorage.h proxy/HttpParser.h proxy/db.h proxy/HelperRoutines.h
proxy/main.cc : proxy/ProxyConfiguration.h
  
clean:
	rm -f ${objs} ${prog}
