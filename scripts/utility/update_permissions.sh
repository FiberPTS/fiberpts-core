#!/bin/sh

# Loop through all shell script files in the NFC_Tracking directory.
for file in $HOME/NFC_Tracking/*.sh
do
  # Grant execute permissions to each shell script file.
  chmod +x "$file"
done

# Loop through all Python script files in the NFC_Tracking directory.
for file in $HOME/NFC_Tracking/*.py
do
  # Grant execute permissions to each Python script file.
  chmod +x "$file"
done