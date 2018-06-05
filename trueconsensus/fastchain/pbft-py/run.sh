#!/bin/bash

# gnome-terminal --working-directory=/home/arcolife/workspace/projects/Personal/blockchain/truechain/py-pbft -e "python server.py 0 1000"
# gnome-terminal --working-directory=/home/arcolife/workspace/projects/Personal/blockchain/truechain/py-pbft -e "python server.py 1 1000"
# gnome-terminal --working-directory=/home/arcolife/workspace/projects/Personal/blockchain/truechain/py-pbft -e "python server.py 2 1000"
# gnome-terminal --working-directory=/home/arcolife/workspace/projects/Personal/blockchain/truechain/py-pbft -e "python server.py 3 1000"

nohup python2 server.py 0; python2 server.py 1; python2 server.py 2; python2 server.py 3; python2 server.py 4 &
