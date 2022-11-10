from PIL import Image   # Pillow for new logo processing
import re               # RegEx for kernel data parsing

#
# Settings
#
kernelFileName      = "Image"               # kernel with current logo (input file)
kernelNewFileName   = "ImageNew"            # kernel with new logo (output file)
logoNewFileName     = "logo.png"            # new logo (input file)
kernelPtrOffset     = 0xFFFF000008080000    # diff between pointer value in kernel file
                                            # and offset of pointed object in the file
#
# Open Files
#

# open kernel file and read its data
with open(kernelFileName, "rb") as f:
    kernelData = f.read()
    
# open new logo file and get its size
logoImg = Image.open(logoNewFileName)
logoWidth = logoImg.width
logoHeight = logoImg.height
print('New kernel logo:')
print('width: %d' % logoWidth)
print('height: %d' % logoHeight)

#
# Parsing kernel data to get linux_logo structure
#

# https://github.com/torvalds/linux/blob/master/include/linux/linux_logo.h
# #define LINUX_LOGO_MONO       1	/* monochrome black/white */
# #define LINUX_LOGO_VGA16      2	/* 16 colors VGA text palette */
# #define LINUX_LOGO_CLUT224    3	/* 224 colors */
# #define LINUX_LOGO_GRAY256    4	/* 256 levels grayscale */
#
# struct linux_logo {
#     int type;                     /* one of LINUX_LOGO_* */
#     unsigned int width;
#     unsigned int height;
#     unsigned int clutsize;        /* LINUX_LOGO_CLUT224 only */
#     const unsigned char *clut;    /* LINUX_LOGO_CLUT224 only */
#     const unsigned char *data;
# };

# linux_logo variables
linuxLogo_type      = 3             # LINUX_LOGO_CLUT224
linuxLogo_width     = logoWidth     # current and new logo
linuxLogo_height    = logoHeight    #  size is the same
linuxLogo_clutsize  = None          # number of colors in logo palette
linuxLogo_clutPtr   = None          # pointer to logo palette:
                                    # - color size is 1 byte uint8_t
                                    # - pixel colors size is 3 bytes
                                    # - format: R G B, R G B, ...
                                    # - size: linuxLogo_clutsize * 3
linuxLogo_dataPtr   = None          # pointer to logo pixels:
                                    # - pixel size is 1 byte uint8_t
                                    # - value is 0x20 + palette index 
                                    # - format: P, P, ...
                                    # - size: linuxLogo_width * linuxLogo_height

# linux_logo regexp pattern
patLinuxLogo_type = linuxLogo_type.to_bytes(4, 'little')
patLinuxLogo_width = linuxLogo_width.to_bytes(4, 'little')
patLinuxLogo_height = linuxLogo_height.to_bytes(4, 'little')
patLinuxLogo_clutsize = b'(.)\x00\x00\x00'
patPtr = (kernelPtrOffset >> 32).to_bytes(4, 'little') # use 4 high bytes for pointer pattern
patLinuxLogo_clutPtr = b'(....)' + patPtr
patLinuxLogo_dataPtr = b'(....)' + patPtr
pat = b'.*' + patLinuxLogo_type + patLinuxLogo_width + patLinuxLogo_height + patLinuxLogo_clutsize + patLinuxLogo_clutPtr + patLinuxLogo_dataPtr
linuxLogoObj = re.match(pat, kernelData, re.DOTALL)

if linuxLogoObj is None:
    print('\nKernel logo is not found')
else:
    linuxLogo_clutsize  = int.from_bytes(linuxLogoObj.group(1), 'little')
    linuxLogo_clutPtr   = int.from_bytes(linuxLogoObj.group(2), 'little') + (kernelPtrOffset & 0xFFFFFFFF00000000)
    linuxLogo_dataPtr   = int.from_bytes(linuxLogoObj.group(3), 'little') + (kernelPtrOffset & 0xFFFFFFFF00000000)

    # offsets for found data in kernel file
    kernelLogoClutOffset = linuxLogo_clutPtr - kernelPtrOffset
    kernelLogoDataOffset = linuxLogo_dataPtr - kernelPtrOffset

    print('\nFound kernel logo:')
    print('width: %d' % linuxLogo_width)
    print('height: %d' % linuxLogo_height)
    print('colors: %d' % linuxLogo_clutsize)
    print('palette offset: %s' % hex(kernelLogoClutOffset))
    print('palette size: %d' % (linuxLogo_clutsize * 3))
    print('data offset: %s' % hex(kernelLogoDataOffset))
    print('data size: %d' % (linuxLogo_width * linuxLogo_height))

#
# Generate palette and pixels for new logo
#
    # convert new logo into RGB format and limit color size
    logoImg = logoImg.convert('RGB').quantize(linuxLogo_clutsize)
    logoImgData = list(logoImg.getdata())
    logoImgPal = logoImg.getpalette()[: linuxLogo_clutsize * 3]
    # make pixels in PNM format, i.e. add 0x20 offset
    logoImgPnmData = [x + 0x20 for x in logoImgData]

#
# Generate kernel with new logo
#
    with open(kernelNewFileName, "wb") as f:
        kernelNewData = bytearray(kernelData)
        # replace current palette with new one
        kernelNewData[kernelLogoClutOffset : kernelLogoClutOffset + len(logoImgPal)] = logoImgPal
        # replace current pixels with new ones
        kernelNewData[kernelLogoDataOffset : kernelLogoDataOffset + len(logoImgPnmData)] = logoImgPnmData
        f.write(kernelNewData)
