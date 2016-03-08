#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
	execl("/usr/bin/python", "browser-sandbox",
	      "browser-sandbox.py", NULL);

	/* Should never be reached, unless there is an error */
	exit(EXIT_FAILURE);
}
