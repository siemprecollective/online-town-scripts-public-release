#!/bin/bash

for i in $(echo $ONLINETOWN_SERVERS | sed "s/,/ /g")
do
    fab -H "$i" $@ >> ./log/$i.log 2>> ./log/$i.err &
done
