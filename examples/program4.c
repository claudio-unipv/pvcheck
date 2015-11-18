#include <stdio.h>
#include <ctype.h>


int main(int argc, char *argv[])
{
  if (argc != 2) {
    puts("Please specify a file name");
    return 1;
  }

  FILE *f = fopen(argv[1], "rt");
  if (f == NULL) {
    perror("main");
    return 2;
  }

  int lines = 0;
  int chrs = 0;
  int c;
  int first = 1;
  puts(argv[1]);
  while ((c = fgetc(f)) != EOF) {
    if (c == '\n') {
      lines++;
      first = 1;
    } else {
      first = 0;
    }
    if (!isspace(c))
      chrs++;
  }
  if (first != 1)
    lines++;

  printf("[LINES]\n%d\n\n", lines);
  printf("[CHARACTERS]\n%d\n\n", chrs);

  fclose(f);
  return 0;
}
