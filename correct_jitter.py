# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 14:19:31 2016

@author: mittelberger2
"""

import numpy as np
from scipy import ndimage

class Jitter(object):
    
    def __init__(self, **kwargs):
        self._image = None
        self._blur_radius = None
        self._blurred_image = None
        self._local_maxima = None
    
    @property
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._image = image
        self._blurred_image = None
        self._local_maxima = None
        
    @property
    def blurred_image(self):
        if self._blurred_image is None:
            print('Calculating new blurred image')
            self._blurred_image = ndimage.gaussian_filter(self.image, self._blur_radius)
        return self._blurred_image
    
    @property
    def blur_radius(self):
        return self._blur_radius
    
    @blur_radius.setter
    def blur_radius(self, blur_radius):
        if blur_radius != self._blur_radius:
            self._blurred_image = None
            self._local_maxima = None
        self._blur_radius = blur_radius
    
    @property
    def local_maxima(self):
        if self._local_maxima is None:
            self._local_maxima = self.find_local_maxima()
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
            if (max_array < half_box_size).any() or (max_array > np.array(shape) - half_box_size -1).any():
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
            if (max_array < half_box_size).any() or (max_array > np.array(shape) - half_box_size -1).any():
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