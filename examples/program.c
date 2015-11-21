#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
  int *ptr;
  int var;
  int n = 0;
  if (argc > 1)
    n = atoi(argv[1]);
  else
    var = 0;  /* To silence a warning. */

  if (n == 0) {
    /* Everything is correct. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    printf("[BBB]\n3.14159\n6.27999\n\n");
    printf("[CCC]\n abc  \n def \n\n");
    printf("[DDD]\none two three  \nfour five \n\n");
  } else if (n == 1) {
    /* Error in AAA. */
    printf("[AAA]\n1 2 3\n4 6 5\n\n");
    printf("[BBB]\n3.14159\n6.27999\n\n");
    printf("[CCC]\n abc  \n def \n\n");
    printf("[DDD]\none two three  \nfour five \n\n");
  } else if (n == 2) {
    /* Error in BBB. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    printf("[BBB]\n3.41\n6.28\n\n");
    printf("[CCC]\n abc  \n def \n\n");
    printf("[DDD]\nfour five\none two three\n\n");
  } else if (n == 3) {
    /* Error in CCC. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    printf("[BBB]\n3.14\n6.28\n\n");
    printf("[CCC]\na b c \n def \n\n");
    printf("[DDD]\nfour five\none two three\n\n");
  } else if (n == 4) {
    /* Error in DDD. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    printf("[BBB]\n3.14\n6.28\n\n");
    printf("[CCC]\nabc \n def \n\n");
    printf("[DDD]\nfour five\none three two\n\n");
  } else if (n == 5) {
    /* Section BBB is missing. */
    printf("[CCC]\n\nabc \n\n def \n\n");
    printf("[DDD]\nfour five\none two three\n\n");
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
  } else if (n == 6) {
    /* Does not terminate. */
    printf("[BBB]\n3.14\n6.28\n\n");
    for (;;) {
    }
  } else if (n == 7) {
    /* Segmentation fault. */
    int *ptr = 0;
    printf("[CCC]\n\nabc \n\n def \n\n");
    printf("[BBB]\n3.14\n\n\n6.28\n\n");
    if (*ptr)
      printf("[AAA]\n1 2 3\n4 5 6\n\n");
  } else if (n == 8) {
    /* Error code. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    exit(EXIT_FAILURE);
  } else if (n == 9) {
    /* Memory leak. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    printf("[BBB]\n3.14159\n6.27999\n\n");
    printf("[CCC]\n abc  \n def \n\n");
    printf("[DDD]\none two three  \nfour five \n\n");
    ptr = malloc(sizeof(int));
  } else if (n == 10) {
    /* Uninitialized variable. */
    printf("[AAA]\n1 2 3\n4 5 6\n\n");
    printf("[BBB]\n3.14159\n6.27999\n\n");
    printf("[CCC]\n abc  \n def \n\n");
    if (var == 7)
      printf("[DDD]\none two three  \nfour five \n\n");
    else
      printf("[DDD]\none two three\nfour five\n\n");
  } else {
    /* Empty. */
  }

  /* Silence some warnings. */
  ptr = NULL;
  var = 0;
  if (ptr != NULL)
    ptr = NULL;
  if (var != 0)
    var = 0;

  exit(EXIT_SUCCESS);
}
