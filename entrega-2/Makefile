ifeq ($(OS),Windows_NT)
	RUN_SERVER = start cmd /k "cd servidor && python servidor.py"
	RUN_CLIENT = start cmd /k "cd cliente && python cliente.py"
else ifneq ($(WSL_DISTRO_NAME),)
	RUN_SERVER = cmd.exe /c start "" wsl.exe -d $(WSL_DISTRO_NAME) bash -lc "cd '$(CURDIR)/servidor' && python3 servidor.py; exec bash"
	RUN_CLIENT = cmd.exe /c start "" wsl.exe -d $(WSL_DISTRO_NAME) bash -lc "cd '$(CURDIR)/cliente' && python3 cliente.py; exec bash"
else
	RUN_SERVER = x-terminal-emulator -e bash -lc "cd servidor && python3 servidor.py; exec bash"
	RUN_CLIENT = x-terminal-emulator -e bash -lc "cd cliente && python3 cliente.py; exec bash"
endif

START_DELAY ?= 2

.PHONY: run server client

run:
	$(RUN_SERVER)
	sleep $(START_DELAY)
	$(RUN_CLIENT)

server:
	$(RUN_SERVER)

client:
	$(RUN_CLIENT)