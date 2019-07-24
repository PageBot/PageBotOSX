#!/bin/bash
rm source/*
sphinx-apidoc -o source ../Lib/pagebotcocoa
git add source/*
