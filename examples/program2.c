#include <stdio.h>
#include <stdlib.h>

int factorial(int n)
{
  int f = 1;
  for (; n > 0; n--)
    f *= n;
  return f;
}

int main(int argc, char *argv[])
{
  int n;

  scanf("%d\n", &n);
  printf("[FACTORIAL]\n%d\n\n", factorial(n));

  exit(EXIT_SUCCESS);
}
