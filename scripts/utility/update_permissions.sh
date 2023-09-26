#!/bin/sh
for file in $HOME/NFC_Tracking/*.sh
do
  chmod +x "$file"
done
for file in $HOME/NFC_Tracking/*.py
do
  chmod +x "$file"
done