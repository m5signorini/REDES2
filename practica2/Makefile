##########################
# Makefile
# Contains basic calls for running tests and the setup
##########################
# Author: Martin Sánchez Signorini
##########################

# Initial installation
init:
	pip3 install -r requirements.txt

run:
	python3 secure-box/securebox_client.py

clean:
	rm -f secure-box/test/*.dat
	rm -f secure-box/user-data/*

clean_test:
	rm -f secure-box/test/*.dat
	rm -f secure-box/test/*.pem

.PHONY: init clean
