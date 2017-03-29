#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 14:13:40 2017

@author: mittelberger2
"""

import numpy as np
from JitterWizard import correct_jitter
import h5py
import os
import sys
#needed on windows
if not hasattr(sys, 'argv'):
    sys.argv = ['']
from multiprocessing import Queue, Process, set_executable, get_start_method
import queue
import threading
import time

class NanoDiffAnalyzerWorker(object):
    def __init__(self, hdf5filequeue, outqueue, max_number_peaks, second_ring_min_distance, blur_radius,
                 noise_tolerance, length_tolerance, angle_tolerance):
        self.hdf5filequeue = hdf5filequeue
        self.outqueue = outqueue
        self.max_number_peaks = max_number_peaks
        self.second_ring_min_distance = second_ring_min_distance
        self.length_tolerance = length_tolerance
        self.angle_tolerance = angle_tolerance
        self.Jitter = correct_jitter.Jitter()
        self.blur_radius = blur_radius
        self.noise_tolerance = noise_tolerance
        self.image = None
        self.shape = None
        
    @property
    def blur_radius(self):
        return self.Jitter.blur_radius
    
    @blur_radius.setter
    def blur_radius(self, blur_radius):
        self.Jitter.blur_radius = blur_radius
        
    @property
    def noise_tolerance(self):
        return self.Jitter.noise_tolerance
    
    @noise_tolerance.setter
    def noise_tolerance(self, noise_tolerance):
        self.Jitter.noise_tolerance = noise_tolerance
    
    def _analysis_loop(self):
        while True:
            index, image = self.hdf5filequeue.get(timeout=10)
            if index is None:
                break
            res = self.analyze_nanodiff_pattern(image)
            self.outqueue.put((index,) + res)
    
    def analyze_nanodiff_pattern(self, image):
        self.image = image
        self.shape = self.image.shape
        self.Jitter.image = self.image
        peaks = self.Jitter.local_maxima[1]
        
        if len(peaks) > self.max_number_peaks:
            peaks = peaks[:self.max_number_peaks]
        first_ring, second_ring, center = self.sort_peaks(peaks)
        first_hexagon = second_hexagon = None
        if len(first_ring) > 4:
            first_hexagon = self.find_hexagon(first_ring)
        if len(second_ring) > 4:
            second_hexagon = self.find_hexagon(second_ring)
        
        if (second_hexagon is None and first_hexagon is not None and len(first_hexagon) > 0 and
            np.mean(np.sum((np.array(first_hexagon) - center)**2, axis=1)) > self.second_ring_min_distance*np.mean(self.shape)):
            second_hexagon = first_hexagon
            first_hexagon = None
            
        return (first_hexagon, second_hexagon, center)
    
    def sort_peaks(self, peaks):
        peaks = np.array(peaks)
        center = peaks[0]
        peak_distance = np.sqrt(np.sum((peaks - center)**2, axis=1))
        hist = np.histogram(peak_distance, bins=8, range=(0, np.mean(self.shape)/2))
        sorted_hist = np.argsort(hist[0])
        if hist[1][sorted_hist[-1]] < hist[1][sorted_hist[-2]]:
            first_ring = (hist[1][sorted_hist[-1]], hist[1][sorted_hist[-1] + 1])
            second_ring = (hist[1][sorted_hist[-2]], hist[1][sorted_hist[-2] + 1])
        else:
            first_ring = (hist[1][sorted_hist[-2]], hist[1][sorted_hist[-2] + 1])
            second_ring = (hist[1][sorted_hist[-1]], hist[1][sorted_hist[-1] + 1])
        first_ring_peaks = []
        second_ring_peaks = []
        for i in range(len(peaks)):
            if first_ring[0] <= peak_distance[i] <= first_ring[1]:
                first_ring_peaks.append(peaks[i])
            elif second_ring[0] <= peak_distance[i] <= second_ring[1]:
                second_ring_peaks.append(peaks[i])
        first_ring_peaks_sorted = sorted(first_ring_peaks, key=lambda value: positive_angle(np.arctan2(*(value - center))))
        second_ring_peaks_sorted = sorted(second_ring_peaks, key=lambda value: positive_angle(np.arctan2(*(value - center))))
        
        return (first_ring_peaks_sorted, second_ring_peaks_sorted, center)
    
    def find_hexagon(self, peaks_sorted):
        angle_tolerance = self.angle_tolerance/180*np.pi
        hexagon = []
        peaks_added = []
        for i in range(0, len(peaks_sorted)):
            peak1 = peaks_sorted[i-2]
            peak2 = peaks_sorted[i-1]
            peak3 = peaks_sorted[i]
            edge1 = peak1 - peak2
            edge2 = peak3 - peak2
            lengths = [np.sqrt(np.sum((edge1)**2)), np.sqrt(np.sum((edge2)**2))]
            angle = np.arccos(np.dot(edge1, edge2)/(np.product(lengths)))
            #print(peak1, lengths, angle*180/np.pi)
            if (np.abs(lengths[0] - lengths[1]) < self.length_tolerance*np.mean(lengths) and
                np.abs(angle - 2*np.pi/3) < angle_tolerance):
                peak_index = i-2 if i-2 > 0 else len(peaks_sorted) + (i-2)
                if not peak_index in peaks_added:
                    hexagon.append(peak1)
                    peaks_added.append(peak_index)
                peak_index = i-1 if i-1 > 0 else len(peaks_sorted) + (i-1)
                if not peak_index in peaks_added:
                    hexagon.append(peak2)
                    peaks_added.append(peak_index)
                peak_index = i if i > 0 else len(peaks_sorted) + i
                if not peak_index in peaks_added:
                    hexagon.append(peak3)
                    peaks_added.append(peak_index)
        return hexagon

class NanoDiffAnalyzer(object):
    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename')
        self.shape = kwargs.get('shape')
        self.max_number_peaks = kwargs.get('max_number_peaks', 20)
        self.second_ring_min_distance = kwargs.get('second_ring_min_distance', 0.5)
        self.blur_radius = kwargs.get('blur_radius', 10)
        self.noise_tolerance = kwargs.get('noise_tolerance', 1)
        self.length_tolerance = kwargs.get('length_tolerance', 0.1)
        self.angle_tolerance = kwargs.get('angle_tolerance', 10)
        self.first_peaks = self.second_peaks = self.centers = None
        self.number_slices = None
        self.number_processes = kwargs.get('number_processes', 3)
        self._workers = []
        self._filequeue = Queue(maxsize=20)
        self._outqueue = Queue()
        #self._manager = Manager()
        #self._stop_event = threading.Event()
        self._number_slices_set_event = threading.Event()
        self._abort_event = threading.Event()
        
    def process_nanodiff_map(self):
        starttime = time.time()
        self._abort_event.clear()
        threading.Thread(target=self._fill_filequeue).start()
        self._number_slices_set_event.wait(timeout=10)
        assert self._number_slices_set_event.is_set()
        self._number_slices_set_event.clear()
        if self.shape is None:
            self.shape = (int(np.sqrt(self.number_slices)), int(np.sqrt(self.number_slices)))
        assert np.product(self.shape) == self.number_slices
        if self.number_processes is None:
            self.number_processes = os.cpu_count()
        # Needed for method "spawn" (on Windows) to prevent mutliple Swift instances from being started
        if get_start_method() == 'spawn':
            set_executable(os.path.join(sys.exec_prefix, 'python.exe'))
        for i in range(self.number_processes):
            analyzer = NanoDiffAnalyzerWorker(self._filequeue, self._outqueue, 
                                              self.max_number_peaks, self.second_ring_min_distance,
                                              self.blur_radius, self.noise_tolerance, self.length_tolerance,
                                              self.angle_tolerance)
            process = Process(target=analyzer._analysis_loop)
            process.daemon = True
            process.start()
            self._workers.append(process)
        
        worker_handler = threading.Thread(target=self._worker_handler)
        worker_handler.daemon = True
        worker_handler.start()
        
        result_handler = threading.Thread(target=self._result_handler)
        result_handler.daemon = True
        result_handler.start()
        
        worker_handler.join()
        print(time.time() - starttime)
    
    def process_nanodiff_image(self, image):
        analyzer = NanoDiffAnalyzerWorker(self._filequeue, self._outqueue, 
                                          self.max_number_peaks, self.second_ring_min_distance,
                                          self.blur_radius, self.noise_tolerance, self.length_tolerance,
                                          self.angle_tolerance)
        first_hexagon, second_hexagon, center = analyzer.analyze_nanodiff_pattern(image)
        return (first_hexagon, second_hexagon, center, analyzer.Jitter.blurred_image)
        
    def abort(self):
        self._abort_event.set()
        
    def _worker_handler(self):
        workers_finished = 0
        while workers_finished < self.number_processes:
            for worker in self._workers:
                if self._abort_event.is_set():
                    worker.terminate()
                if worker.exitcode is not None:
                    worker.join()
                    self._workers.remove(worker)
                    workers_finished += 1
            time.sleep(0.1)
    
    def _result_handler(self):
        self.first_peaks = np.zeros(tuple(self.shape) + (6, 2))
        self.second_peaks = np.zeros(tuple(self.shape) + (6, 2))
        self.centers = np.zeros(tuple(self.shape) + (2,))
        i = 0
        while i < self.number_slices and not self._abort_event.is_set():
            try:
                index, first_hexagon, second_hexagon, center = self._outqueue.get(timeout=1)
            except queue.Empty:
                pass
            else:
                if i%100 == 0:
                    print('Processed {:.0f} out of {:.0f} slices.'.format(i, self.number_slices))
                try:
                    x_coord = index%self.shape[1]
                    y_coord = index//self.shape[1]
                    if first_hexagon is not None and len(first_hexagon) > 0:
                        self.first_peaks[y_coord, x_coord, :len(first_hexagon)] = np.array(first_hexagon)
                    if second_hexagon is not None and len(second_hexagon) > 0:
                        self.second_peaks[y_coord, x_coord, :len(second_hexagon)] = np.array(second_hexagon)
                    self.centers[y_coord, x_coord] = center
                except Exception as e:
                    print('Error in slice {:.0f}: {}'.format(i, str(e)))
                i += 1

    def _fill_filequeue(self):
            _filelink = openhdf5file(self.filename)
            self.number_slices = len(_filelink['data/science_data/data'])
            self._number_slices_set_event.set()
            i = 0
            while i < self.number_slices and not self._abort_event.is_set():
                try:
                    self._filequeue.put((i, gethdf5slice(i, _filelink)), timeout=1)
                except queue.Full:
                    pass
                else:
                    i += 1
            _filelink.close()
            for i in range(len(self._workers)):
                self._filequeue.put((None, None))

def positive_angle(angle):
    """
    Calculates the angle between 0 and 2pi from an input angle between -pi and pi (all angles in rad)
    """
    if angle < 0:
        return angle  + 2*np.pi
    else:
        return angle

def openhdf5file(hdf5filename):
    hdf5filelink=h5py.File(hdf5filename, 'r')
    return hdf5filelink

def gethdf5slice(slicenumber, hdf5filelink):
    hdf5slice = hdf5filelink['data/science_data/data'][slicenumber,:]
    return hdf5slice
        
if __name__ == '__main__':
    #first_peaks, second_peaks, centers = process_nanodiff_map('/3tb/nanodiffraction_maps/20161128_171207/tt.h5')
    #fp, sp, c = analyze_nanodiff_pattern(57, openhdf5file('/3tb/nanodiffraction_maps/20161128_171207/tt.h5'))
    A = NanoDiffAnalyzer(filename='/3tb/nanodiffraction_maps/20161128_152252/grating2.h5')
    res = A.process_nanodiff_map()
    np.save('/3tb/nanodiffraction_maps/peak_finding/second_peaks.npy', A.second_peaks)
    np.save('/3tb/nanodiffraction_maps/peak_finding/first_peaks.npy', A.first_peaks)
    np.save('/3tb/nanodiffraction_maps/peak_finding/centers.npy', A.centers)