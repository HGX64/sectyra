#!/bin/bash 

codespace_name="$(cat /opt/.code_name)"
gh cs ssh -c codespace_name -- "whoami"
