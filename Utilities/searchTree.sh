#!/bin/bash

root_file=$1
tree_name=$2
search_string=$3

if [ "$#" -ne 3 ]; then
    echo "usage: searchTree.sh <root-file-name> <tree-name> <search-string>"
    echo "Example: ./searchTree.sh myFSAntuple.root eee/final/Ntuple Gen" 
    exit
fi
python -c "import ROOT; file = ROOT.TFile('$root_file'); tree = file.Get('$tree_name'); tree.Print()" \
  | grep "$search_string"
