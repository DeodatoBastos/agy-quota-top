PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin

.PHONY: install uninstall

install:
	mkdir -p $(BINDIR)
	chmod +x quota_top.py
	ln -sf $(abspath quota_top.py) $(BINDIR)/qtop
	@echo "Installed qtop to $(BINDIR)/qtop"

uninstall:
	rm -f $(BINDIR)/qtop
	@echo "Uninstalled $(BINDIR)/qtop"
