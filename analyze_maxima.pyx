#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 14:58:43 2017

@author: mittelberger2
"""
from libc.stdlib cimport malloc, free

def analyze_maxima(blurred_image, shape, sorted_maxima, resulting_maxima, noise_tolerance):
    #cdef long maximum_flat = maximum[0]*shape[1] + maximum[1]
    cdef unsigned int width = shape[1]
    cdef unsigned int height = shape[0]
    cdef float c_noise_tolerance = noise_tolerance
    cdef float [:] c_blurred_image = blurred_image
    cdef unsigned int [:] c_sorted_maxima = sorted_maxima
    c_analyze_maxima(c_blurred_image, width, height, c_sorted_maxima, resulting_maxima, noise_tolerance)
    

cdef unsigned short LISTED = 1
cdef unsigned short PROCESSED = 2

cdef void c_analyze_maxima(float[:] blurred_image, unsigned int width, unsigned int height,
                          unsigned int[:] sorted_maxima, list resulting_maxima,
                          float noise_tolerance):
    cdef unsigned int number_pixels = width*height
    cdef unsigned int *nlist = <unsigned int*>malloc(number_pixels*sizeof(int))
    cdef unsigned short *point_attributes = <unsigned short*>malloc(number_pixels*sizeof(short))
    cdef unsigned int listi
    cdef unsigned int listlen
    cdef bint maximum_possible
    cdef unsigned int maximum
    cdef float maximum_value
    cdef unsigned int* neighbors = [width, -width, 1, width+1, -width+1, -1, width-1, -width-1]
    cdef unsigned int h, i, j, k
    cdef unsigned int current_point, point
    cdef float current_value
    for h in range(number_pixels):
        point_attributes[h] = 0
    for i in range(len(sorted_maxima)):
        maximum = sorted_maxima[i]
        maximum_value = blurred_image[maximum]
        nlist[0] = maximum
        listi = 0
        listlen = 1
        maximum_possible = True
        point_attributes[maximum] |= LISTED
        
        while listi < listlen:
            for k in range(8):
                current_point = nlist[listi] + neighbors[k]
    #                    if (np.array(current_point) < 0).any() or (np.array(current_point) >= np.array(blurred_image.shape)).any():
    #                        continue
                if (current_point < 0 or current_point >= number_pixels):
                    continue
    #                    if point_attributes[current_point] is None:
    #                        point_attributes[current_point] = []
                elif point_attributes[current_point] & LISTED != 0:
                    continue
                elif point_attributes[current_point] & PROCESSED != 0:
                    maximum_possible = False
                    break
                
                current_value = blurred_image[current_point]
                if current_value > maximum_value:
                    maximum_possible = False
                    break
                if current_value >= maximum_value - noise_tolerance:
                    nlist[listlen] = current_point
                    listlen += 1
                    point_attributes[current_point] |= LISTED
            listi += 1
        
        
        for j in range(listlen):
            point = nlist[j]
            point_attributes[point] &= ~LISTED
            point_attributes[point] |= PROCESSED
            
        if maximum_possible:
            resulting_maxima.append(maximum)
    free(nlist)
    free(point_attributes)