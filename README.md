# image-dupes
Scripts for detecting duplicate images

They use an imaging library to detect similar images based on a special 
hashing algorithm to analyze what the image looks like, and compares it 
to others with a similar hash.  The more similar the hash to another 
image, the more likely they are to be duplicates.

Currently, these scripts are implemented in Python 3 using PIL.  Also, 
the interface is purely textual and non-interactive.  I'm planninng on 
porting it to C#/.NET or Android once I find suitable libraries for 
image transformation for those platforms.
