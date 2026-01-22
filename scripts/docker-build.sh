#!/bin/sh -e

IMAGE_VERSION=${IMAGE_VERSION:=latest}
docker build -t "erar404/src:${IMAGE_VERSION}" .