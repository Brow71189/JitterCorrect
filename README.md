JitterWizard
============

A python module to remove scan noise caused by beam jitter from STEM images. It comes with a UI module that integrates it into Nion Swift¹ as a plugin which makes finding the optimal parameters easier than pure command line usage.
The software is inspired by the "Jitterbug" program written by Lewys Jones and the corresponding publication² which describes the basis of the algorithm used here.

Usage
======

For use as a Nion Swift plugin copy the whole folder into the "plugins" folder of your installation.
In the plugin panel you can set the two parameters "sigma" and "box size". "Sigma" controls the radius of the Gaussian kernel used to blur the image before looking for features. By clicking on "Find Maxima" you get a new data item that shows the blurred image with the features that were found by the algorithm marked.
"Box size" is the edge length of the square that is cropped around the features and in which the jitter correction takes place. It should be large enough to include a full feature in your image (e.g. a bright atom) but small enough so that only one feature fits into the box. As the code runs fast (about 1-2 s computation time for a 2048x2048 px image) the easiest way to find the optimal parameters is to try a few combinations of "sigma" and "box size" until the result looks best.
It is not required to run "find maxima" before "correct jitter" but it might help you to see which features are found and will be corrected by the code.
If the result of the jitter correction is not satisfying, you can copy the output (e.g. by making a "Snapshot") and run the plugin again on that copy. Just selecting the output will not run the plugin on this data item to prevent you from accidently running the jitter correction on the wrong data item after e.g. adjusting the contrast in the output.

Installation and Requirements
=============================

Requirements
------------
* Python >= 3.5 (lower versions might work but are untested)
* numpy
* scipy
* AnalyzeMaxima (Download and Documentation at https://github.com/Brow71189/AnalyzeMaxima)


Installation
------------
If you used the "Download as ZIP" function on github to get the code make sure you rename the project folder to "JitterWizard" after extracting the ZIP-archive. If you used the "clone" function you can start right away.
Copy the project folder in your Nion Swift Plugin directory (see http://nion.com/swift/developer/introduction.html#extension-locations for the plugin directory on your OS.)
Under Linux the global plugin directory is "~/.local/share/Nion/Swift/Plugins".
Then the plugin should be loaded automatically after restarting Swift. In case it is not loading correctly, make sure to start Swift from a Terminal and check the error messages written there.


¹ www.nion.com/swift

²Jones, L. and Nellist, P.D. (2013) "Identifying and Correcting Scan Noise and Drift in the Scanning Transmission Electron Microscope", Microscopy and Microanalysis, 19(4), pp. 1050–1060.
