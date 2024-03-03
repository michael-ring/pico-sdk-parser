#!/bin/sh
cd pico-sdk
git pull
git pull --all --recurse-submodules
git submodule update --init --recursive
git pull --all --recurse-submodules
export PICO_SDK_PATH=$(pwd)
cd ..
rm -rf build 2>/dev/null
rm -rf pico-fpc 2>/dev/null
rm -rf units 2>/dev/null
mkdir build
mkdir pico-fpc
mkdir units
cp ./pico-sdk/external/pico_sdk_import.cmake pico-fpc/
echo "void main() {}" >pico-fpc/__noinline__main.c
python3 main.py
cd build
PICO_BOARD=pico_w cmake ../pico-fpc
make
find . -name "__noinline__*obj" -exec cp {} ../units/ \;
cd ..
echo "Release done"
rm -rf build
mkdir build
cd build
PICO_BOARD=pico_w cmake ../pico-fpc -DCMAKE_BUILD_TYPE=Debug
make
find . -name "__noinline__*.obj" | while read file ; do
    file2=$(basename $file | sed "s,.c.obj,.c-debug.obj,g")
    cp $file ../units/${file2}
done
echo "Debug done"
cd ..
