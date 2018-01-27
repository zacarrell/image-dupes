#! /usr/bin/python3

"""Detect similar-looking images and possible duplicates.

When a file needs to be uniquely identified, one might use a **hashing
algorithm**, such as MD5 or SHA-1.  These algorithms (and others like
them) generate a sequence of letters and numbers called a **hash** from
the file's contents that serves as its fingerprint.  This means that if
two files have different hashes (that were produced by the same
algorithm), their contents are different in some way.

It should be noted that these hashes do not appear to reflect the files'
contents; they are seemingly random.  For example, if two text files are
the same except for one letter, their hashes may have a few characters
that share the same position, but otherwise they would look completely
unrelated.  While this may seem unintuitive (?wording), remember that
these hashes still serve their desired purpose: to *uniquely* identify
the files' by their contents.

While these algorithms may work fine for normal text files, they are
less effective for multimedia files (e.g., pictures, music, videos,
etc.) for two reasons:

1) These files usually store data other than what the user sees or hears
   called **metadata** such as the settings a photo was taken with, the
   artist and album information of a song, etc. that adds to their
   contents.

2) It is more difficult (at least for an average person) to notice small
   differences in these types of files.

**Perceptual hashing algorithms** solve these problems by generating
hashes that identify multimedia files based on what they look like
and/or sound like rather than the exact data within the file (?wording).
These algorithms have the added advantage of generating similar hashes
for similar files.

This module defines two useful functions:

difference_hash(image) -- calculate the difference hash (commonly
shortened to dHash) of the image object.

hamming_distance(seq1, seq2) -- determine the Hamming distance between
equal-length sequences.

Since module-level docstrings like this one are not usually as specific
when it comes to summarization as their class- or function-level
counterparts, please check their respective documentation for a further
explanation of what they are and how they work (?wording).

Authors:
Silviu Tantos -- difference hash function
Zachary Carrell -- test/main program and documentation

Date Created:  June 18, 2014
Date Modified:  June 26, 2014

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

import logging
from os import walk
from os.path import join
from re import match
from itertools import combinations

from PIL import Image

PICS_DIR = r'C:\Users\Zac\Pictures\Pics'
LOGGING_DIR = r'C:\Users\Zac\logs'
ALLOWABLE_HAMMING_DISTANCE = 4

# Image.EXTENSION is a dict of file extensions associated with their file
# types, but it's empty until you open an image and, from what I can
# tell, the constants are undocumented.  Confused?  So am I.
EXTENSIONS = [
    '.jpg', '.jpeg', '.jpe', '.jfif', '.png', '.gif', '.bmp', '.pgm', '.pbm',
    '.ppm'
    ]

logging.basicConfig(filename=join(LOGGING_DIR, 'imgdupes.log'), filemode='wt')

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


if __name__ == '__main__':
    image_hashes = dict()
    for dir_path, dir_names, filenames in walk(PICS_DIR):
        for filename in filenames:
            if not any(filename.endswith(ext) for ext in EXTENSIONS):
                continue
            
            # Calculate image hashes and group images with identical ones.
            file_path = join(dir_path, filename)
            try:
                image = Image.open(file_path)
            except IOError:
                logging.error('Could not open ' + file_path)
                continue
            
            try:
                image.verify()
            # I think this is a bug in Pillow, but the traceback doesn't give
            # me any helpful info;  the variable names in the Pillow code that
            # caused the exception are just letters.  Pillow's documentation
            # should be updated at the very least if it is not a bug.
            # PILLOW_VERSION = '2.4.0'
            except IndexError:
                logging.exception('Could not verify ' + file_path)
                continue

            image = Image.open(file_path)

            # Test if the image has multiple frames.  I might allow these at
            # some point, but I don't know how I should process them, so their
            # behavior is undefined for now.
            try:
                dhash = difference_hash(image)
            # Probably another Pillow bug.
            # PILLOW_VERSION = '2.4.0'
            except UnboundLocalError:
                logging.exception('Could not get dhash of ' + file_path)
                continue
            
            if dhash not in image_hashes:
                image_hashes[dhash] = []
            image_hashes[dhash].append(file_path)

    # Determine images with similar hashes. 
    groups_of_similar_hashes = dict()
    for hash_1, hash_2 in combinations(image_hashes, 2):
        if hamming_distance(hash_1, hash_2) > ALLOWABLE_HAMMING_DISTANCE:
            continue
        if hash_1 not in groups_of_similar_hashes:
            groups_of_similar_hashes[hash_1] = []
        groups_of_similar_hashes[hash_1].append(hash_2)

    # Write the results to some files.
    duplicate_images = open(join(LOGGING_DIR, 'imgdupes_duplicate_images.txt'),
                            mode='wt', encoding='utf-8')
    similar_images = open(join(LOGGING_DIR, 'imgdupes_similar_images.txt'),
                          mode='wt', encoding='utf-8')
    for main_hash, similar_hashes in groups_of_similar_hashes.items():
        file_paths = []
        file_paths.extend(image_hashes[main_hash])
        if len(file_paths) > 1:
            print('\n'.join(file_paths), end='\n\n', file=duplicate_images)
        for similar_hash in similar_hashes:
            file_paths.extend(image_hashes[similar_hash])
        print('\n'.join(file_paths), end='\n\n', file=similar_images)

    duplicate_images.close()
    similar_images.close()
