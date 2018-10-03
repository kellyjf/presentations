#include <stdio.h>
#include <string.h>


int main() {
	int  cnt=0;
	char alpha[28];
	for (;;)  {
		sprintf(alpha,"ABCDEFGHIJKLMNOPQRTUVWXY%d",32+cnt%32);

		cnt+=strcmp(alpha, "ABCDEFGHIJKLMNOPQRTUVWXYZ");
	}
}

