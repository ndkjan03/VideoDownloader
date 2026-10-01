#!/bin/bash

rm -rf build
rm -rf dist

pyinstaller \
    --clean \
    --onefile \
    --icon assets/app.icns \
    --name VideoDownloader \
    --add-data "yt_tools:yt_tools" \
    main.py