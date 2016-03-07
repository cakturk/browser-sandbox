LD := $(CC)

OBJS := setuid-shim.o setuid-shim

all: setuid-shim

setuid-shim: setuid-shim.o
	$(LD) -Wl,-s setuid-shim.o -o setuid-shim

setuid-shim.o: setuid-shim.c
	$(CC) -Wall -O2 -c setuid-shim.c -o setuid-shim.o

.PHONY clean:
	-rm -f $(OBJS)
