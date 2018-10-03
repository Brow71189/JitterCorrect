JitterWizard
============

A python module to remove scan noise caused by beam jitter from STEM images. It comes with a UI module that integrates it into Nion Swift¹ as a plugin which makes finding the optimal parameters easier than pure command line usage.
The software is inspired by the "Jitterbug" program written by Lewys Jones and the corresponding publication².

Installation and Requirements
=============================

Requirements
------------
* Python >= 3.5 (lower versions might work but are untested)
* numpy (should be already installed if you have Swift installed)
* scipy (should be already installed if you have Swift installed)
* AnalyzeMaxima (Should be automatically instlled during setup. If not, check here: https://github.com/Brow71189/AnalyzeMaxima)


Installation
------------
The recommended way is to use git to clone the repository as this makes receiving updates easy:
```bash
git clone https://github.com/Brow71189/JitterWizard
```

If you do not want to use git you can also use github's "download as zip" function and extract the code afterwards.

Once you have the repository on your computer, enter the folder "SwiftCam" and run the following from a terminal:

```bash
python setup.py install
```

It is important to run this command with __exactly__ the python version that you use for running Swift. If you installed Swift according to the online documentation (https://nionswift.readthedocs.io/en/stable/installation.html#installation) you should run `conda activate nionswift` in your terminal before running the above command.

Usage
======

In the plugin panel you can set the two parameters "sigma" and "box size". "Sigma" controls the radius of the Gaussian kernel used to blur the image before looking for features. By clicking on "Find Maxima" you get a new data item that shows the blurred image with the features that were found by the algorithm marked.
"Box size" is the diameter of the circle that is put around around the features and in which the jitter correction takes place. It should be large enough to include a full feature in your image (e.g. a bright atom) but small enough so that only one feature fits into the box. As the code runs fast (about 1-2 s computation time for a 2048x2048 px image) the easiest way to find the optimal parameters is to try a few combinations of "sigma" and "box size" until the result looks best.
It is not required to run "find maxima" before "correct jitter" but it might help you to see which features are found and will be corrected by the code.
If the result of the jitter correction is not satisfying, you can copy the output (e.g. by making a "Snapshot") and run the plugin again on that copy. Just selecting the output will not run the plugin on this data item to prevent you from accidently running the jitter correction on the wrong data item after e.g. adjusting the contrast in the output.


¹ www.nion.com/swift

²Jones, L. and Nellist, P.D. (2013) "Identifying and Correcting Scan Noise and Drift in the Scanning Transmission Electron Microscope", Microscopy and Microanalysis, 19(4), pp. 1050–1060.