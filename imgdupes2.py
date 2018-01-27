#!/usr/bin/env python3

"""Find and report similar-looking pictures or images on your computer.

This script detects duplicate images on your computer in a unique way. 
For standard text files, a file hashing algorithm, such as MD5, would 
work well.  However, there are problems with this approach when dealing 
with images---nay, multimedia content in general---as some differences 
may not be perceivable with the human eye, and even then these 
discrepancies may not be important at all to some users.

This script uses a different kind of hashing algorithm, one where the 
hash is determined by the visual content of the image.  Images that are 
similar in appearance will have similar hashes.  In fact, this script 
does not directly compare images at all;  their hashes are compared, 
instead.

Paths to images are stored in a hash table, with any duplicates (which, 
for the purpose of this script, will be images whose hashes match 
*exactly*) stored alongside them.  When finished, the script will 
detect which hashes are *similar* by utilizing the user-specified flag 
``similarity``, a threshold expressed as a percentage defining how 
similar the hashes are allowed to be to one another to be considered 
similar, and images with these hashes are combined and presented to the 
user in groups.

This script does not currently support animated GIF files, because even 
though there are legitimate use cases for including them in the results 
(like if they are a "slideshow", rather than "animated"), I usually 
think of those as their own images.  Maybe this should be specified in 
a flag?  Or have a flag to compare only animated images with one 
another?  Or have this functionality in another program entirely?

Authors:
Silviu Tantos -- difference hash function
Zachary Carrell -- Python implementation of the hash function, test/main
                   program and documentation

Date: April 3, 2015

Copyright (C) 2014 Zachary Carrell

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from collections import defaultdict
from os import listdir
from os.path import join
from contextlib import suppress
from itertools import combinations

from PIL import Image

TEST_DIR = r'C:\Users\Zac\e621'
HASH_SIZE = 8

def main(directory):
    image_hashes = build_hash_table(directory)
    similar_groups = []
    allowable_hamming_distance = percentage_to_hamming_value(100)
    for hash1, hash2 in combinations(image_hashes, 2):
        if hamming_distance(hash1, hash2) > allowable_hamming_distance:
            continue
        similar_groups.append(image_hashes[hash1].union(image_hashes[hash2]))
        
    for group in similar_groups:
        print('\n'.join(group), end='\n\n')


def build_hash_table(directory):
    hash_table = {}
    for img in yield_images(directory):
        dhash = difference_hash(img)
        if dhash not in hash_table:
            hash_table[dhash] = set()
        hash_table[dhash].add(img.filename)

    return hash_table


def get_dhashes_and_images(iterable):
    """Return a list of pairs of dhashes and image paths in the iterable.

    Used for testing the speed of defaultdict.
    """
    dhashes_and_images = []
    for img in iterable:
        dhashes_and_images.append((difference_hash(img), img.filename))

    return dhashes_and_images


def yield_images(directory):
    for filename in listdir(directory):
        with suppress(OSError):
            yield Image.open(join(directory, filename))
        

def difference_hash(image, hash_size=8):
    # Convert the image to grayscale.
    image = image.convert('L')

    # Resize the image.
    image = image.resize(
        (hash_size + 1, hash_size),
        Image.ANTIALIAS,
    )

    pixels = list(image.getdata())

    # Compare adjacent pixels.
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)

    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0

    return ''.join(hex_string)


def hamming_distance(seq1, seq2):
    """Return the Hamming distance between equal-length sequences."""
    if len(seq1) != len(seq2):
        raise ValueError('Undefined for sequences of unequal length')
    return sum(elem1 != elem2 for elem1, elem2 in zip(seq1, seq2))


def percentage_to_hamming_value(percentage):
    """Convert a percentage to a possible hamming distance.
    
    This function works such that a percentage of 0 returns 32, and that
    a percentage of 100 returns 0.
    """
    return round(HASH_SIZE*2 - (percentage / 100 * HASH_SIZE*2))

