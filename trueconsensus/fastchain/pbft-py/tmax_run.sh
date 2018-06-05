#!/bin/bash

SESSION='pbft-py'

cd /home/arcolife/workspace/projects/Personal/blockchain/truechain/pbft

tmux -2 new-session -d -s $SESSION -n 'pbft-py'

# Setup a window and split panes, source venv, tail log file
tmux new-window -t $SESSION:1 -n 'cp01'
tmux send-keys "python2 server.py 0" C-m
tmux split-window -v
tmux select-pane -t 1
tmux send-keys "python2 server.py 1" C-m
tmux split-window -v
tmux select-pane -t 2
tmux send-keys "python2 server.py 2" C-m
tmux split-window -v
tmux select-pane -t 3
tmux send-keys "python2 server.py 3" C-m
tmux split-window -v
tmux select-pane -t 4
tmux send-keys "python2 server.py 4" C-m
tmux split-window -v
tmux select-pane -t 0

# tmux send-keys "tailf cfme-performance.log" C-m
# tmux send-keys "tailf cfme-performance.log" C-m
# tmux new-window -t $SESSION:2 -n 'cp02'
# tmux new-window -t $SESSION:3 -n 'cp03'
# tmux send-keys "python2 server.py 0" C-m
# tmux split-window -v
# tmux select-pane -t 1
# tmux send-keys "python2 server.py 0" C-m
# # tmux send-keys "tailf cfme-performance.log" C-m
# tmux select-pane -t 0

tmux select-window -t $SESSION:1
tmux -2 attach-session -t $SESSION
