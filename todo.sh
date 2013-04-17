#!/bin/sh
rm TODO.md

for i in */*.py 
	do grep -l TODO $i >> TODO.md
	grep TODO $i | sed -e "s/^\ +//" -e "s/TODO//" -e "s/#//" >> TODO.md 
	echo  "\n\n" >> TODO.md 
done
