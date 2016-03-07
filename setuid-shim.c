#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
	printf("c: uid: %d, euid: %d\n", getuid(), geteuid());
	//system("/usr/bin/python browser-sandbox.py");
	execl("/usr/bin/python", "browser-sandbox",
	      "browser-sandbox.py", NULL);

	/* Should never be reached, unless there is an error */
	exit(EXIT_FAILURE);
}
