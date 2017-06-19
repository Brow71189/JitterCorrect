JitterWizard
============

A python module to remove scan noise caused by beam jitter from STEM images. It comes with a UI module that integrates it into Nion Swift¹ as a plugin which makes finding the optimal parameters easier than pure command line usage.
The software is inspired by the "Jitterbug" program written by Lewys Jones and the corresponding publication² which describes the basis of the algorithm used here.
The feature finding part of this module is derived from ImageJ's "MaximumFinder" plugin³.

Usage
======

For use as a Nion Swift plugin copy the whole folder into the "plugins" folder of your installation.
In the plugin panel you can set the two parameters "sigma" and "box size". "Sigma" controls the radius of the Gaussian kernel used to blur the image before looking for features. By clicking on "Find Maxima" you get a new data item that shows the blurred image with the features that were found by the algorithm marked.
"Box size" is the edge length of the square that is cropped around the features and in which the jitter correction takes place. It should be large enough to include a full feature in your image (e.g. a bright atom) but small enough so that only one feature fits into the box. As the code runs fast (about 1-2 s computation time for a 2048x2048 px image) the easiest way to find the optimal parameters is to try a few combinations of "sigma" and "box size" until the result looks best.
It is not required to run "find maxima" before "correct jitter" but it might help you to see which features are found and will be corrected by the code.
If the result of the jitter correction is not satisfying, you can copy the output (e.g. by making a "Snapshot") and run the plugin again on that copy. Just selecting the output will not run the plugin on this data item to prevent you from accidently running the jitter correction on the wrong data item after e.g. adjusting the contrast in the output.

Installation
============

If you used the "Download as ZIP" function on github to get the code make sure you rename the project folder to "JitterWizard" after extracting the ZIP-archive. If you used the "clone" function you can start right away.
Since the package uses some cython code for performance reasons it has to be compiled before you can use it. To do this run
```python
~/miniconda3/bin/python3 setup.py build_ext --inplace
```
in a terminal that you opened in the project folder. Make sure the first part of the command uses EXACTLY the same python that is used for running Nion Swift or the plugin will most likely not work. The example given here would be for a installation on Linux with the standard installation of Swift as described on the homepage¹.


¹ www.nion.com/swift

²Jones, L. and Nellist, P.D. (2013) "Identifying and Correcting Scan Noise and Drift in the Scanning Transmission Electron Microscope", Microscopy and Microanalysis, 19(4), pp. 1050–1060.

³https://github.com/imagej/imagej1/blob/master/ij/plugin/filter/MaximumFinder.java
