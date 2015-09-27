#include <stdio.h>
#include <memory.h>
#include <stdlib.h>
#include <getopt.h>

unsigned int opt_wait;

void eat_cpu() {
	printf("Eating CPU...\n");
	double x=1.0, y=1.0;
	for (;;) {
		y *= (x+2.0*y)/(x+y);
		x *= (y+2.0*x)/(x+y);
	}
	printf("%g %g\n", x,y);
}

void eat_mem() {
	unsigned long *mem;
	unsigned long amt=0;
	unsigned long quantum=1000;
	printf("Eating Memory...\n");
	if(opt_wait) quantum*=opt_wait;
	for(;;) {
		mem = (unsigned long *)malloc(4096);
		amt += 4;
		mem[0] = amt;
		if ((amt%quantum)==0) {
			printf("%luM\n", amt/1000);
			if(opt_wait) sleep(1);
		}
	}
}


int main(int argc, char **argv) {
	unsigned int c ='\0';
	extern char *optarg;
	unsigned int opt_cpu=0, opt_mem=0;
	static struct option long_options[] = {
		{"mem",  no_argument,       0,  'm' },
		{"cpu",  no_argument,       0,  'c' },
		{"wait",  required_argument,       0,  'w' },
		{0,         0,                 0,  0 }
	};

	while ((c = getopt_long(argc, argv, "cmw:", long_options, NULL)) != EOF) {
		switch(c) {
		case 'w':
			opt_wait=strtoul(optarg, NULL, 0);
			break;
		case 'c':
			opt_cpu++;
			break;
		case 'm':
			opt_mem++;
			break;
		}
	}
	if(opt_cpu) eat_cpu();
	if(opt_mem) eat_mem();
}

