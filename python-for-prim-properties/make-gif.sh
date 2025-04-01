#!/bin/sh
# Run from the python-for-prim-properties folder
# Requires docker and ffmpeg
#
# This script renders all the frames from the example.usda file and creates an
# animated gif
mkdir temp
docker run -it --rm -v.:/data rstelzleni/usd-alpine:gl-24.05 --frames 1:60 /data/example.usda /data/temp/example###.png --camera /Camera
ffmpeg  -i temp/example%03d.png \
    -vf palettegen ./temp/palette.png
ffmpeg  -framerate 30 -i ./temp/example%03d.png -i ./temp/palette.png \
    -lavfi "paletteuse" example.gif
