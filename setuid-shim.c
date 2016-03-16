#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
	const char **eargv;
	size_t nargs;

	nargs = argc + 2;
	eargv = malloc(sizeof(char *) * nargs);
	memcpy(eargv + 2, argv + 1, (argc - 1) * sizeof(char *));
	eargv[0] = "browser-sandbox";
	eargv[1] = "browser-sandbox.py";
	eargv[nargs - 1] = NULL;

	execv("/usr/bin/python", (char * const *)eargv);

	/* Should never be reached, unless there is an error */
	free(eargv);
	perror("setuid-shim");

	exit(EXIT_FAILURE);
}
