CC=g++
LDFLAGS=-Wall -lpthread
CFLAGS=-Wall -c -lpthread -std=c++11

objs := AddressList.o AddressListTest.o ServerAgent.o DownloaderThread.o
prog := AddressList

.PHONY: all

all : ${prog}
${prog}: $(objs)
	${CC} ${LDFLAGS} -o $@ $^
%.o:%.cc
	$(CC) $(CFLAGS) -o $@ $<

AddressListTest.cc : AddressList.h
AddressList.cc : AddressList.h ServerAgent.h
ServerAgent.cc : ServerAgent.h DownloaderThread.h
DownloaderThread.cc : DownloaderThread.h

clean :
	rm *.o ${prog}
