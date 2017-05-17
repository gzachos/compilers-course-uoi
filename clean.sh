#!/usr/bin/env bash

find . -type f -name '*.int' | xargs rm
find . -type f -name '*.c' | xargs rm
find . -type f -name '*.asm' | xargs rm
find . -type f -name '*.out' | xargs rm
