TARGET=pvcheck


.PHONY: all
all:  $(TARGET)


$(TARGET):
	make -C src
	cp src/$(TARGET) .


.PHONY: clean
clean:
	make -C src clean
	rm -f $(TARGET)
