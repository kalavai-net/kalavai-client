#!/bin/bash
set -e

# Converts a text list of rpc server addresses (one on each new line) 
# to a string of RPC server addresses, comma separated
subcommand=$1
shift
case "$subcommand" in
    build)
        rm -rf dist/*
        python3 -m build
        twine check dist/*    
        ;;
    test-release)
        twine upload -r testpypi dist/*
        ;;
    release)
        twine upload -r pypi dist/*
        ;;

    *)
      printf ""
      exit 1
  esac


