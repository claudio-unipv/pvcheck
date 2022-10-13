TARGET=pvcheck
SRCS=$(notdir $(shell ls *.py))
ARCHIVE=$(TARGET).zip


.PHONY: all
all: $(TARGET)


$(TARGET): $(ARCHIVE)
	echo '#!/usr/bin/env python3' > $(TARGET) && \
	cat $(ARCHIVE) >> $(TARGET) && \
	chmod +x $(TARGET)


$(ARCHIVE): $(SRCS)
	zip $(ARCHIVE) $(SRCS)


.PHONY: clean
clean:
	rm -f $(TARGET) $(ARCHIVE) *~ *.pyc
	rm -fR __pycache__
