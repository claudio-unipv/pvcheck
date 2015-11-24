.PHONY: all
all: program program2 program3 program4

program: program.c
	gcc -Wall -g -o program program.c

program2: program2.c
	gcc -Wall -g -o program2 program2.c

program3: program3.c
	gcc -Wall -g -o program3 program3.c

program4: program4.c
	gcc -Wall -g -o program4 program4.c

.PHONY: test
test: all
	./testall.sh
	./pvcheck example2.test ./program2
	./pvcheck example3.test ./program3
	./pvcheck example4.test ./program4


.PHONY: clean
clean:
	rm -f program program2 program3 program4
