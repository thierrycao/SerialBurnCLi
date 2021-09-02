##########################################################################
# File Name: build.sh
# Author: ThierryCao
# mail: iamthinker@163.com
# Created Time: 四  9/ 2 17:04:53 2021
#########################################################################
#--nofollow-imports \
#!/bin/bash
nuitka3 --show-memory \
	   --show-progress \
	   --follow-imports \
	   --standalone \
	   --include-data-dir=res=res \
	   --output-dir=output \
		csk_serial_burn_tool.py 
