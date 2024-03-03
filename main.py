#!/usr/bin/env/python3
from glob import glob
from os import environ
from pathlib import Path
import re


def get_include_name(path: str) -> str:
  """Gets the appropriate name for `#include "<name>"`-statements"""
  regex = re.compile(r".*/include/(.*\.h)")
  match = regex.fullmatch(path)
  return match.group(1).strip()

if __name__ == "__main__":
  # Use custom prefix if specified
  prefix = environ.get("PREFIX", "__noinline__")

  implpath = Path("pico-fpc")
  implpath.mkdir(exist_ok=True)
  cmakelists = implpath / "CMakeLists.txt"
  with cmakelists.open(mode="w") as f:
    f.writelines('''
cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)

project(pico_examples C CXX)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(PICO_BOARD pico_w)

# Initialize the SDK
pico_sdk_init()

add_compile_definitions(
    ${PROJECT_NAME}
    PICO_QUEUE_MAX_LEVEL=1)

add_executable(
__noinline
__noinline__main.c
''')

  # Collect all headers
  header_paths = glob("pico-sdk/src/common/**/include/**/*.h", recursive=True)
  header_paths += glob("pico-sdk/src/rp2_common/**/include/**/*.h", recursive=True)
  header_paths += glob("pico-sdk/src/rp2040/**/include/**/*.h", recursive=True)

  for header in header_paths:
    headerfile=Path(header)
    with headerfile.open() as f:
      newcontent=list()
      inlinefound=False
      newcontent.append("#include \""+get_include_name(header)+"\"\n")
      content=f.readlines()
      funcstart = -1
      newfuncstart = -1
      for index,line in enumerate(content):
        if line.startswith("static inline"):
          funcstart = index
        if line.startswith("inline static"):
          funcstart = index
        if (funcstart > -1) and line.startswith("}"):
          line=(content[funcstart].replace("static inline ","").replace("inline static ","").replace(" __attribute__((noreturn))","").replace(" __attribute__((always_inline))",""))
          line2=re.split("\s",line)
          line=""
          onefound=False
          for match in line2:
            if match.find("(") > -1 and not (match.find("(*func") > -1):
              if match.startswith("*") and not onefound:
                match="*"+prefix+match[1:]
                onefound=True
              else:
                match=prefix+match
            line += match + " "
          line=line.rstrip(" ")+"\n"
          newcontent.append(line)
          while funcstart+1 < index+1:
            newcontent.append(content[funcstart+1])
            funcstart += 1
          inlinefound = True
          funcstart=-1

    if inlinefound == True:
      with cmakelists.open(mode="a") as f:
        f.writelines(prefix+headerfile.with_suffix(".c").name+"\n")
      newheader=implpath / Path(prefix+headerfile.with_suffix(".c").name)
      with newheader.open(mode="w") as f:
        f.writelines(newcontent)
with cmakelists.open(mode="a") as f:
  f.writelines('''
)

# Add pico_stdlib library which aggregates commonly used features
target_link_libraries(__noinline pico_stdlib pico_cyw43_arch_none pico_multicore  hardware_flash hardware_irq hardware_adc hardware_pwm hardware_i2c hardware_spi hardware_dma hardware_exception hardware_interp)
''')