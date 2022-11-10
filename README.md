# kernel-logo-patch
This simple python script can be used for logo replacement in embedded linux kernel

## Assumptions
- bytes order is little-endian
- int size is 4 bytes
- pointer size is 8 bytes
- difference between pointer value in kernel and actual offset in kernel file for pointed object is 0xFFFF000008080000
- logo inside kernel in PNM format with 224 colors max
- new and current logo size is the same
- kernel filename is Image
- new logo file name is logo.png
- patched kernel file name is ImageNew

## Limitation
PNM format consists of palette and pixels. Palette is an array of colors and pixels is an array of palette indexes. Because patched kernel must be the same size as the existing one, therefore palette size (and number of pixels) is constant. As a result if the kernel file has a logo with less than 224 colors then new logo colors will be limited to the same number (colors itself might be different).

## Notes
The script is tested on kernel compiled for Freescale i.MX8MMQ CPU