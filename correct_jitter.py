# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 14:19:31 2016

@author: mittelberger2
"""

import numpy as np
from scipy import ndimage
import pyximport; pyximport.install()
from . import analyze_maxima

class Jitter(object):
    
    def __init__(self, **kwargs):
        self._image = None
        self._blur_radius = None
        self._blurred_image = None
        self._local_maxima = None
        self._raw_local_maxima = None
        self._noise_tolerance = None
    
    @property
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._image = image
        self._blurred_image = None
        self._local_maxima = None
        self._raw_local_maxima = None
        
    @property
    def blurred_image(self):
        if self._blurred_image is None:
            #print('Calculating new blurred image')
            self._blurred_image = ndimage.gaussian_filter(self.image.astype(np.float64), self._blur_radius)
        return self._blurred_image
    
    @property
    def blur_radius(self):
        return self._blur_radius
    
    @blur_radius.setter
    def blur_radius(self, blur_radius):
        if blur_radius != self._blur_radius:
            self._blurred_image = None
            self._raw_local_maxima = None
            self._local_maxima = None
        self._blur_radius = blur_radius
    
    @property
    def noise_tolerance(self):
        return self._noise_tolerance
        
    @noise_tolerance.setter
    def noise_tolerance(self, noise_tolerance):
        if noise_tolerance != self._noise_tolerance:
            self._local_maxima = None
        self._noise_tolerance = noise_tolerance
    
    @property
    def raw_local_maxima(self):
        if self._raw_local_maxima is None:
            self._raw_local_maxima = self.find_local_maxima()
        return self._raw_local_maxima
        
    @property
    def local_maxima(self):
        if self._local_maxima is None:
            self._local_maxima = [self.raw_local_maxima[0],
                                  self.analyze_and_mark_maxima(self.raw_local_maxima[1], self.noise_tolerance)]
        return self._local_maxima

    def gaussian_blur(self, image=None, sigma=None):
        if image is not None:
            self.image = image
        if sigma is not None:
            self.blur_radius = sigma
        if None in (self.image, self._blur_radius):
            raise ValueError('You must set image and sigma in order to calculate the blurred image.')
        
        return self.blurred_image
    
    def find_local_maxima(self):
        local_maxima = np.zeros(self.image.shape)
        shape = self.image.shape
        blurred_image = self.blurred_image

        # This is the fast version of the commented for-loops below
        extended_blurred_image = np.empty(shape + (9,))
        extended_blurred_image[..., 0] = blurred_image
        y_positions = [(1, None), (0, -1), (0, None), (1, None), (0, -1), (0, None), (1, None), (0, -1)]
        x_positions = [(0, None), (0, None), (1, None), (1, None), (1, None), (0, -1), (0, -1), (0, -1)]
        mappings = {(0, None): (0, None), (1, None): (0, -1), (0, -1): (1, None)}
        for i in range(8):
            target_y = y_positions[i]
            source_y = mappings[target_y]
            target_x = x_positions[i]
            source_x = mappings[target_x]
            extended_blurred_image[..., i+1][target_y[0]:target_y[1], target_x[0]:target_x[1]] = (
                                                    blurred_image[source_y[0]:source_y[1], source_x[0]:source_x[1]])
        
        max_positions = np.argmax(extended_blurred_image, axis=-1)
        local_maxima[max_positions == 0] = blurred_image[max_positions == 0]
        local_maxima[0, :] = 0
        local_maxima[-1, :] = 0
        local_maxima[:, 0] = 0
        local_maxima[:, -1] = 0

#        y_positions = [1, -1, 0, 1, -1,  0,  1, -1]
#        x_positions = [0,  0, 1, 1,  1, -1, -1, -1]
#        for y in range(shape[0]):
#            if y < 1 or y > shape[0] - 2:
#                continue
#            for x in range(shape[1]):
#                if x < 1 or x > shape[1] - 2:
#                    continue
#                is_max = True
#                for k in range(8):
#                    if blurred_image[y, x] <= blurred_image[y + y_positions[k], x + x_positions[k]] + noise_tolerance:
#                        is_max = False
#                        break
#                if is_max:
#                    local_maxima[y,x] = blurred_image[y,x]
        return local_maxima, list(zip(*np.where(local_maxima)))
        
    def analyze_and_mark_maxima(self, maxima, noise_tolerance=0):
        blurred_image = self.blurred_image.ravel().astype(np.float32)
        shape = self.blurred_image.shape
        sorted_maxima = maxima.copy()
        sorted_maxima.sort(key=lambda entry: self.blurred_image[entry], reverse=True)
        resulting_maxima = []
        array_sorted_maxima = np.array(sorted_maxima, dtype=np.uintc)
        flattened_array_sorted_maxima = array_sorted_maxima[:, 0] * shape[1] + array_sorted_maxima[:, 1]
        analyze_maxima.analyze_maxima(blurred_image, shape, flattened_array_sorted_maxima, resulting_maxima, noise_tolerance)
        #y_positions = [1, -1, 0, 1, -1,  0,  1, -1]
        #x_positions = [0,  0, 1, 1,  1, -1, -1, -1]
        #point_attributes = [list() for i in range(self.blurred_image.size)]
        #nlist = [list() for i in range(self.blurred_image.size)]
        #import time
        #runtime = 0
        #numberlooprounds = 0
        #print('Number maxima: ' + str(len(maxima)))
        #for maximum in sorted_maxima:
            #flood_fill.flood_filling(blurred_image, shape, point_attributes, maximum, resulting_maxima, noise_tolerance)
#            nlist[0] = maximum
#            maximum_flat = maximum[0]*shape[1] + maximum[1]
##            if point_attributes[maximum2] is None:
##                point_attributes[maximum2] = []
#            point_attributes[maximum_flat].append('listed')
#            listi = 0
#            listlen = 1
#            maximum_possible = True
#            maximum_value = blurred_image[maximum[0]][maximum[1]]
#            
#            while listi < listlen:
##            for i in range(np.size(blurred_image)):
##                if listi >= len(nlist):
##                    break
#                for k in range(8):
#                    numberlooprounds += 1
#                    starttime = time.time()
#                    current_point = (nlist[listi][0] + y_positions[k], nlist[listi][1] + x_positions[k])
#                    current_point_flat = current_point[0]*shape[1] + current_point[1]
##                    if (np.array(current_point) < 0).any() or (np.array(current_point) >= np.array(blurred_image.shape)).any():
##                        continue
#                    if (current_point[0] < 0 or current_point[1] < 0 or
#                        current_point[0] >= shape[0] or current_point[1] >= shape[1]):
#                        continue
##                    if point_attributes[current_point] is None:
##                        point_attributes[current_point] = []
#                    elif 'listed' in point_attributes[current_point_flat]:
#                        continue
#                    elif 'processed' in point_attributes[current_point_flat]:
#                        maximum_possible = False
#                        break
#                    
#                    current_value = blurred_image[current_point[0]][current_point[1]]
#                    if current_value > maximum_value:
#                        maximum_possible = False
#                        break
#                    if current_value >= maximum_value - noise_tolerance:
#                        nlist[listlen] = current_point
#                        listlen += 1
#                        point_attributes[current_point_flat].append('listed')
#                    runtime += time.time() - starttime
#                listi += 1
#            print(listlen)
#            
#            
#            for j in range(listlen):
#                point = nlist[j]
#                point_flat = point[0] * shape[1] + point[1]
#                point_attributes[point_flat].append('processed')
#                if 'listed' in point_attributes[point_flat]:
#                    point_attributes[point_flat].remove('listed')
#            if maximum_possible:
#                resulting_maxima.append(maximum)
#        print(runtime)
#        print('Number loop rounds: ' + str(numberlooprounds))
        converted_resulting_maxima = []
        for maximum in resulting_maxima:
            converted_resulting_maxima.append((maximum//shape[1], maximum%shape[1]))
        return converted_resulting_maxima
        
        
    def remove_y_jitter(self, crop_im, return_coordinates=False):
        shape = crop_im.shape
        tophalf = crop_im[:int(shape[0]/2)]
        bottomhalf = crop_im[int(shape[0]/2):]
        if return_coordinates:
            corrected_crop_im = np.zeros(shape)
            corrected_crop_im[:int(shape[0]/2)] = np.expand_dims(np.argsort(np.sum(tophalf, axis=1)), axis=1).repeat(shape[1], axis=1)
            corrected_crop_im[int(shape[0]/2):] = np.expand_dims(np.argsort(np.sum(bottomhalf, axis=1))[::-1], axis=1).repeat(shape[1], axis=1)+int(shape[0]/2)
        else:
            sorted_tophalf = tophalf[np.argsort(np.sum(tophalf, axis=1))]
            sorted_bottomhalf = bottomhalf[np.argsort(np.sum(bottomhalf, axis=1))[::-1]]
            corrected_crop_im = np.zeros(shape)
            corrected_crop_im[:int(shape[0]/2)] = sorted_tophalf
            corrected_crop_im[int(shape[0]/2):] = sorted_bottomhalf
        return corrected_crop_im
        
    def remove_x_jitter_com(self, crop_im, return_coordinates=False):
        shape = crop_im.shape
        com_lines = np.mgrid[:shape[0], :shape[1]][1]
        com_lines = np.sum(com_lines*crop_im, axis=1)/np.sum(crop_im, axis=1) - shape[1]/2
        mean_com = np.mean(com_lines)
        x_corrected_crop_im = np.zeros(shape)
        for i in range(shape[0]):
            if return_coordinates:
                original_indices = np.arange(0,shape[1])
                corrected_indices = original_indices + (com_lines[i] - mean_com)
                x_corrected_crop_im[i] = corrected_indices
            else:
                original_indices = np.arange(0,shape[1])
                corrected_indices = original_indices - (com_lines[i] - mean_com)
                original_indices = original_indices[corrected_indices < shape[1]]
                corrected_indices = corrected_indices[corrected_indices < shape[1]]
                original_indices = (original_indices[0 <= corrected_indices]).astype(np.int)
                corrected_indices = (corrected_indices[0 <= corrected_indices]).astype(np.int)
                x_corrected_crop_im[i, corrected_indices] = crop_im[i, original_indices]
        return x_corrected_crop_im
        
    def dejitter_full_image(self, box_size=60):
        half_box_size = int(box_size/2)
        shape = self.image.shape
        coordinate_offsets = np.mgrid[0:shape[0], 0:shape[1]]
        print('Finding maxima')
        local_maxima = self.local_maxima[1]
        print('correcting y-jitter')
        for maximum in local_maxima:
            max_array = np.array(maximum)
            if (max_array < half_box_size).any() or (max_array >= np.array(shape) - half_box_size - 1).any():
                continue
            chunk = (maximum[0]-half_box_size, maximum[0]+half_box_size, maximum[1]-half_box_size, maximum[1]+half_box_size)
            new_y_coords = self.remove_y_jitter(self.image[chunk[0]:chunk[1], chunk[2]:chunk[3]], return_coordinates=True)
            new_y_coords = maximum[0] - half_box_size + new_y_coords
            #new_y_coords = new_y_coords - half_box_size
            coordinate_offsets[0][chunk[0]:chunk[1], chunk[2]:chunk[3]] = new_y_coords
        coordinate_offsets -= np.mgrid[0:shape[0], 0:shape[1]]
        y_corrected = self.apply_correction(coordinate_offsets)
        coordinate_offsets += np.mgrid[0:shape[0], 0:shape[1]]
        print('correcting x-jitter')
        for maximum in local_maxima:
            max_array = np.array(maximum)
            if (max_array < half_box_size).any() or (max_array >= np.array(shape) - half_box_size - 1).any():
                continue
            chunk = (maximum[0]-half_box_size, maximum[0]+half_box_size, maximum[1]-half_box_size, maximum[1]+half_box_size)
            new_x_coords = self.remove_x_jitter_com(y_corrected[chunk[0]:chunk[1], chunk[2]:chunk[3]], return_coordinates=True)
            new_x_coords = maximum[1] - half_box_size + new_x_coords
            #new_x_coords = new_x_coords - half_box_size
            coordinate_offsets[1][chunk[0]:chunk[1], chunk[2]:chunk[3]] = new_x_coords
        coordinate_offsets -= np.mgrid[0:shape[0], 0:shape[1]]
        print('Done')
        return coordinate_offsets

    def apply_correction(self, coordinate_offsets):
        new_coordinates = np.mgrid[0:self.image.shape[0], 0:self.image.shape[1]].astype(np.float32)
        new_coordinates += coordinate_offsets
        corrected = self.image[new_coordinates[0].astype(np.int), new_coordinates[1].astype(np.int)]
        return corrected.copy()