#include <stdio.h>
#include <stdlib.h>
#define MAXN 20
#define PRIME 739 


void bubblesort(int *a, int n, int bug)
{
  int i, j;
  int temp;
  for (j = 1; j < n; j++) {
    for (i = 1; i < n; i++) {
      if (a[i] < a[i-1] + bug) {
	temp = a[i];
	a[i] = a[i-1];
	a[i-1] = temp;
      }
    }
  }
}


int main(int argc, char *argv[])
{
  int a[MAXN];
  int n = 10;
  int op = 0;
  int bug = 0;
  int i;
  
  if (argc > 1)
    n = atoi(argv[1]);

  if (argc > 2)
    op = atoi(argv[2]);

  if (op == 1)
    n += 2;

  if (op == 2)
    n -= 2;

  if (op == 3)
    bug = (n+1) / 2;

  if (n > MAXN)
    n = MAXN;
    
  if (n < 0)
    n = 0;

  for (i = 0; i < n; i++)
    a[i] = (5 + PRIME * i) % n;

  printf("[BEFORE_SORTING]\n");
  for (i = 0; i < n; i++)
    printf("%d\n", a[i]);

  bubblesort(a, n, bug);
  
  printf("\n[AFTER_SORTING]\n");
  for (i = 0; i < n; i++)
    printf("%d\n", a[i]);

  
  return 0;
}
