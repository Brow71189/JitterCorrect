#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 08:36:41 2017

@author: mittelberger2
"""

import logging
import os
import time
import uuid
import numpy as np
import threading

from . import nanodiff_analyis
from . import hdf5handler
from . import vdf

class NanoDiffPanelDelegate(object):
    def __init__(self, api):
        self.__api = api
        self.panel_id = 'NanoDiff-Panel'
        self.panel_name = 'NanoDiff Analysis'
        self.panel_positions = ['left', 'right']
        self.panel_position = 'right'
        self._current_slice = None
        self.filepath = None
        self.slice_image = None
        self._vdf_image = None
        self._vdf_pick_region = None
        self._results_image = None
        self._results_pick_region = None
        self._single_image_peaks = None
        self.h5file = None
        self._last_opened_folder = ''
        self._nanodiff_analyzer = nanodiff_analyis.NanoDiffAnalyzer()
        
    @property
    def current_slice(self):
        return self._current_slice
    
    @current_slice.setter
    def current_slice(self, current_slice):
        if current_slice != self._current_slice:
            self._current_slice = current_slice
            if self.vdf_pick_region is not None:
                shape = self.vdf_image.data.shape
                position = (current_slice//shape[1]/shape[0], current_slice%shape[1]/shape[1])
                self.vdf_pick_region.position = position
            if self.results_pick_region is not None:
                shape = self.results_image.data.shape
                position = (current_slice//shape[-1]/shape[-2], current_slice%shape[-1]/shape[-2])
                self.results_pick_region.position = position
        
    @property
    def vdf_image(self):
        if self._vdf_image is None and self.slice_image is not None:
            if self.slice_image.metadata.get('vdf_uuid'):
                self._vdf_image = self.__api.library.get_data_item_by_uuid(uuid.UUID(self.slice_image.metadata.get('vdf_uuid')))
        return self._vdf_image
    
    @vdf_image.setter
    def vdf_image(self, vdf_image):
        self._vdf_image = vdf_image
        update_metadata(self.slice_image, {'vdf_uuid': vdf_image.uuid.hex})
    
    @property
    def vdf_pick_region(self):
        if self._vdf_pick_region is None:
            if self.vdf_image is not None and self.vdf_image.metadata.get('pick_region_uuid'):
                self._vdf_pick_region = self.__api.library.get_graphic_by_uuid(uuid.UUID(self.vdf_image.metadata.get('pick_region_uuid')))
        return self._vdf_pick_region
    
    @vdf_pick_region.setter
    def vdf_pick_region(self, vdf_pick_region):
        self._vdf_pick_region = vdf_pick_region
        update_metadata(self.vdf_image, {'pick_region_uuid': vdf_pick_region.uuid.hex})
    
    @property
    def results_pick_region(self):
        if self._results_pick_region is None:
            if self.results_image is not None and self.results_image.metadata.get('pick_region_uuid'):
                self._results_pick_region = self.__api.library.get_graphic_by_uuid(uuid.UUID(self.results_image.metadata.get('pick_region_uuid')))
        return self._results_pick_region
    
    @results_pick_region.setter
    def results_pick_region(self, results_pick_region):
        self._results_pick_region = results_pick_region
        update_metadata(self.results_image, {'pick_region_uuid': results_pick_region.uuid.hex})
        
    @property
    def results_image(self):
        if self._results_image is None and self.slice_image is not None:
            if self.slice_image.metadata.get('results_uuid'):
                self._results_image = self.__api.library.get_data_item_by_uuid(uuid.UUID(self.slice_image.metadata.get('results_uuid')))
        return self._results_image
    
    @results_image.setter
    def results_image(self, results_image):
        self._results_image = results_image
        update_metadata(self.slice_image, {'results_uuid': results_image.uuid.hex})
    
    @property
    def single_image_peaks(self):
        if self._single_image_peaks is None and self.slice_image is not None:
            if self.slice_image.metadata.get('single_image_peaks_uuid'):
                self._single_image_peaks = self.__api.library.get_data_item_by_uuid(uuid.UUID(self.slice_image.metadata.get('single_image_peaks_uuid')))
        return self._single_image_peaks
    
    @single_image_peaks.setter
    def single_image_peaks(self, single_image_peaks):
        self._single_image_peaks = single_image_peaks
        update_metadata(self.slice_image, {'single_image_peaks_uuid': single_image_peaks.uuid.hex})

    def create_panel_widget(self, ui, document_controller):

        def path_finished(text):
            if len(text) > 0:
                self.filepath = text
            else:
                self.filepath = None

        def slice_number_finished(text):
            if len(text) > 0:
                try:
                    self.current_slice = int(text)
                except ValueError:
                    slice_number.text = str(self.current_slice)
                else:
                    self.update_slice_image()

        def open_button_clicked():
            if self.filepath is None:
                file, filter, path = document_controller._document_controller._document_window.get_file_path_dialog('Open nanodiffraction map...', self._last_opened_folder, 'HDF5 Files (*.h5);; All Files (*.*)')
                self._last_opened_folder = path
                self.filepath = file
            
            if not os.path.isfile(self.filepath):
                logging.warn('{} is not a file'.format(self.filepath))
                self.filepath = None
                return
            
            path_field.text = self.filepath
            
            if self.slice_image is None or self.slice_image.metadata.get('source_file_path') != self.filepath:            
                self.current_slice = 0
                self.slice_image = self.__api.library.create_data_item()
            else:
                self.current_slice = self.slice_image.metadata.get('current_slice', 0)
            self.h5file = hdf5handler.openhdf5file(self.filepath)
            self.update_slice_image()
            update_metadata(self.slice_image, {'source_file_path': self.filepath})

            slice_number.text = str(self.current_slice)
            
        def select_button_clicked():
            data_item = document_controller.target_data_item
            if data_item.metadata.get('source_file_path'):
                self.filepath = data_item.metadata.get('source_file_path')
                self.slice_image = data_item
                open_button_clicked()
                self._vdf_image = None
                
        def last_button_clicked():
            self.current_slice -= 1
            self.update_slice_image()
            slice_number.text = str(self.current_slice)

        def next_button_clicked():
            self.current_slice += 1
            self.update_slice_image()
            slice_number.text = str(self.current_slice)
            
        def last10_button_clicked():
            self.current_slice -= 10
            self.update_slice_image()
            slice_number.text = str(self.current_slice)

        def next10_button_clicked():
            self.current_slice += 10
            self.update_slice_image()
            slice_number.text = str(self.current_slice)
            
        def vdf_pick_region_changed(key):
            if key == 'position':
                position = self.vdf_pick_region.position
                self.current_slice = int(position[0]*self.vdf_image.data.shape[0])*self.vdf_image.data.shape[1] + int(position[1]*self.vdf_image.data.shape[1])
                self.update_slice_image()
                slice_number.text = str(self.current_slice)
                if self.results_pick_region is not None and self.results_pick_region.position != position:
                    self.results_pick_region.position = position
        
        def vdf_pick_region_deleted():
            pick_checkbox.checked = False
            
        def results_pick_region_changed(key):
            if key == 'position':
                position = self.results_pick_region.position
                self.current_slice = int(position[0]*self.results_image.data.shape[-2])*self.results_image.data.shape[-1] + int(position[1]*self.results_image.data.shape[-1])
                self.update_slice_image()
                slice_number.text = str(self.current_slice)
                if self.vdf_pick_region is not None and self.vdf_pick_region.position != position:
                    self.vdf_pick_region.position = position
        
        def results_pick_region_deleted():
            pick_checkbox.checked = False
        
        def pick_checkbox_changed(check_state):
            if check_state == 'checked':
                if self.vdf_image is not None:
                    if self.vdf_pick_region is None:
                        x_coord = self.current_slice%self.vdf_image.data.shape[1]
                        y_coord = self.current_slice//self.vdf_image.data.shape[1]
                        self.vdf_pick_region = self.vdf_image.add_point_region(y_coord/self.vdf_image.data.shape[0], x_coord/self.vdf_image.data.shape[1])
                        self.vdf_pick_region.set_property('is_bounds_constrained', True)
                        self.vdf_pick_region.label = 'Pick'
                    property_changed_event = self.vdf_pick_region.get_property('property_changed_event')
                    region_deleted_event = self.vdf_pick_region.get_property('about_to_be_removed_event')
                    self.vdf_changed_event_listener = property_changed_event.listen(vdf_pick_region_changed)
                    self.vdf_deleted_event_listener = region_deleted_event.listen(vdf_pick_region_deleted)
                if self.results_image is not None:
                    if self.results_pick_region is None:
                        x_coord = self.current_slice%self.results_image.data.shape[-1]
                        y_coord = self.current_slice//self.results_image.data.shape[-1]
                        self.results_pick_region = self.results_image.add_point_region(y_coord/self.results_image.data.shape[-2], x_coord/self.results_image.data.shape[-1])
                        self.results_pick_region.set_property('is_bounds_constrained', True)
                        self.results_pick_region.label = 'Pick'
                    property_changed_event = self.results_pick_region.get_property('property_changed_event')
                    region_deleted_event = self.results_pick_region.get_property('about_to_be_removed_event')
                    self.results_changed_event_listener = property_changed_event.listen(results_pick_region_changed)
                    self.results_deleted_event_listener = region_deleted_event.listen(results_pick_region_deleted)
            else:
                if self.vdf_image is not None and self.vdf_pick_region is not None:
                    try:
                        self.vdf_image.remove_region(self.vdf_pick_region)
                    except Exception as e:
                        print(e)
                    self._vdf_pick_region = None
                    remove_from_metadata(self.vdf_image, 'pick_uuid')
                    delattr(self, 'vdf_changed_event_listener')
                    delattr(self, 'vdf_deleted_event_listener')
                    
                if self.results_image is not None and self.results_pick_region is not None:
                    try:
                        self.results_image.remove_region(self.results_pick_region)
                    except Exception as e:
                        print(e)
                    self._results_pick_region = None
                    remove_from_metadata(self.results_image, 'pick_uuid')
                    delattr(self, 'results_changed_event_listener')
                    delattr(self, 'results_deleted_event_listener')                        

        def start_button_clicked():
            roi = {}
            for region in self.slice_image.regions:
                if region.type == 'rectangle-region' or region.type == 'ellipse-region':
                    roi['center'] = region.get_property('center')
                    roi['size'] = region.get_property('size')
                    roi['type'] = region.type
                    break
            if not roi.get('center'):
                logging.warn('You have to provide a rectangle- or ellipse-selection to do vdf.')
                return

            starttime = time.time()
            result = vdf.vdf(self.h5file, vdf.getroirange(self.h5file, roi))
            logging.info('Processing time (hdf5): %.2f s.' % (time.time()-starttime,))
            if self.vdf_image is None:
                self.vdf_image = self.__api.library.create_data_item()
            self.update_vdf_image(result, roi)
            update_metadata(self.vdf_image, {'source_uuid': self.slice_image.uuid.hex})
        
        def find_peaks_button_clicked():
            if find_peaks_button.text == 'Abort':
                self._nanodiff_analyzer.abort()
                return
                
            if self.slice_image is None:
                logging.warn('You have to open or select a hdf5 stack first.')
                return
            
            def run_find_peaks():
                self._nanodiff_analyzer.filename = self.filepath
                self._nanodiff_analyzer.process_nanodiff_map()
                def update_text():
                    find_peaks_button.text = 'Find Peaks'
                self.__api.queue_task(update_text)
                if self.results_image is None:
                    def create_item():
                        self.results_image = self.__api.library.create_data_item()
                    self.__api.queue_task(create_item)
                def update_item():
                    self.update_results_image()
                self.__api.queue_task(update_item)
                self.__api.queue_task(lambda: update_metadata(self.results_image, {'source_uuid': self.slice_image.uuid.hex}))
                
            self.find_peaks_thread = threading.Thread(target=run_find_peaks)
            self.find_peaks_thread.start()
            find_peaks_button.text = 'Abort'
        
        def find_peaks_single_button_clicked():
            first_hexagon, second_hexagon, center, blurred_image = self._nanodiff_analyzer.process_nanodiff_image(self.slice_image.data)
            if self.single_image_peaks is None:
                self.single_image_peaks = self.__api.library.create_data_item()
            self.update_single_image_peaks(first_hexagon, second_hexagon, center, blurred_image)
            update_metadata(self.single_image_peaks, {'source_uuid': self.slice_image.uuid.hex})
            
        column = ui.create_column_widget()
        descriptor_row1 = ui.create_row_widget()
        descriptor_row1.add(ui.create_label_widget("Path to HDF5-file:"))

        parameters_row1 = ui.create_row_widget()
        path_field = ui.create_line_edit_widget()
        path_field.on_editing_finished = path_finished
        parameters_row1.add(path_field)
        parameters_row1.add_spacing(15)
        open_button = ui.create_push_button_widget("open...")
        open_button.on_clicked = open_button_clicked
        parameters_row1.add(open_button)
        
        button_row0 = ui.create_row_widget()
        select_button = ui.create_push_button_widget('Select opened stack')
        select_button.on_clicked = select_button_clicked
        button_row0.add_stretch()
        button_row0.add(select_button)

        descriptor_row3 = ui.create_row_widget()
        descriptor_row3.add(ui.create_label_widget("Browse through hdf5-file: "))
        
        button_row1 = ui.create_row_widget() 
        last10_button = ui.create_push_button_widget("<<")
        last10_button.on_clicked = last10_button_clicked
        button_row1.add(last10_button)        
        button_row1.add_spacing(2)     
        
        last_button = ui.create_push_button_widget("<")
        last_button.on_clicked = last_button_clicked
        button_row1.add(last_button)
        button_row1.add_spacing(8)

        next_button = ui.create_push_button_widget(">")
        next_button.on_clicked = next_button_clicked
        button_row1.add(next_button)
        button_row1.add_spacing(2)
        
        next10_button = ui.create_push_button_widget(">>")
        next10_button.on_clicked = next10_button_clicked
        button_row1.add(next10_button)
        
        parameters_row3 = ui.create_row_widget()        
        parameters_row3.add(ui.create_label_widget("Jump to slice #: "))
        slice_number = ui.create_line_edit_widget()
        slice_number.on_editing_finished = slice_number_finished
        parameters_row3.add(slice_number)
        parameters_row3.add(ui.create_label_widget(" current slice #"))
        parameters_row3.add_stretch()
        
        checkbox_row = ui.create_row_widget()
        checkbox_row.add(ui.create_label_widget('Pick '))
        pick_checkbox = ui.create_check_box_widget()
        pick_checkbox.on_check_state_changed = pick_checkbox_changed
        checkbox_row.add(pick_checkbox)
        checkbox_row.add_stretch()
        
        button_row2 = ui.create_row_widget()
        start_button = ui.create_push_button_widget("Virtual DF")
        start_button.on_clicked = start_button_clicked
        find_peaks_single_button = ui.create_push_button_widget("Find peaks single")
        find_peaks_single_button.on_clicked = find_peaks_single_button_clicked
        find_peaks_button = ui.create_push_button_widget("Find peaks stack")
        find_peaks_button.on_clicked = find_peaks_button_clicked
        button_row2.add(start_button)
        button_row2.add_spacing(3)
        button_row2.add(find_peaks_single_button)
        button_row2.add_spacing(3)
        button_row2.add(find_peaks_button)

        column.add_spacing(10)
        column.add(descriptor_row1)
        column.add_spacing(3)
        column.add(parameters_row1)
        column.add_spacing(5)
        column.add(button_row0)
        column.add_spacing(8)
        column.add(descriptor_row3)
        column.add_spacing(3)
        column.add(button_row1)
        column.add_spacing(8)
        column.add(parameters_row3)
        column.add_spacing(8)
        column.add(checkbox_row)
        column.add_spacing(15)
        column.add(button_row2)
        column.add_stretch()

        return column
    
    def update_slice_image(self):
        if self.current_slice != self.slice_image.metadata.get('current_slice'):
            self.slice_image.set_data(hdf5handler.gethdf5slice(self.current_slice, self.h5file))
            self.slice_image.title = 'Slice_{:.0f}_of_{}'.format(self.current_slice, os.path.splitext(os.path.split(self.filepath)[1])[0])
            update_metadata(self.slice_image, {'current_slice': self.current_slice})
    
    def update_vdf_image(self, data, roi):
        self.vdf_image.set_data(data)
        self.vdf_image.title = 'VDF_of_{}_({:.2f}_{:.2f})'.format(os.path.splitext(os.path.split(self.filepath)[1])[0], *roi['center'])
    
    def update_results_image(self):
        data = np.append(self._nanodiff_analyzer.first_peaks, self._nanodiff_analyzer.second_peaks, axis=-2)
        centers = self._nanodiff_analyzer.centers[..., np.newaxis, :]
        data = np.append(data, centers, axis=-2)
        data = np.moveaxis(data, 0, -1)
        data = np.moveaxis(data, 0, -1)
        data_descriptor = self.__api.create_data_descriptor(is_sequence=False, collection_dimension_count=2, datum_dimension_count=2)
        xdata = self.__api.create_data_and_metadata(data, data_descriptor=data_descriptor)
        self.results_image.set_data_and_metadata(xdata)
        self.results_image.title = 'Peak_positions_of_{}'.format(os.path.splitext(os.path.split(self.filepath)[1])[0])
    
    def update_single_image_peaks(self, first_hexagon, second_hexagon, center, blurred_image):
        self.single_image_peaks.set_data(blurred_image)
        for region in self.single_image_peaks.regions:
            if region.type == 'point-region':
                self.single_image_peaks.remove_region(region)
        shape = self.single_image_peaks.data.shape
        if center is not None and not (np.array(center) == 0).all():
            region = self.single_image_peaks.add_point_region(center[0]/shape[0], center[1]/shape[1])
            region.label = 'center'
        if first_hexagon is not None:
            for i in range(len(first_hexagon)):
                peak = first_hexagon[i]
                if not (peak == 0).all():
                    region = self.single_image_peaks.add_point_region(peak[0]/shape[0], peak[1]/shape[1])
                    region.label = str(i+1)
        if second_hexagon is not None:
            for i in range(len(second_hexagon)):
                peak = second_hexagon[i]
                if not (peak == 0).all():
                    region = self.single_image_peaks.add_point_region(peak[0]/shape[0], peak[1]/shape[1])
                    region.label = str(i+7)            
    
def update_metadata(data_item, new_metadata):
    metadata = data_item.metadata
    metadata.update(new_metadata)
    data_item.set_metadata(metadata)

def remove_from_metadata(data_item, key):
    metadata = data_item.metadata
    metadata.pop(key, None)
    data_item.set_metadata(metadata)

class NanoDiffExtension(object):
    extension_id = 'univie.nanodiff'

    def __init__(self, api_broker):
        api = api_broker.get_api(version='1', ui_version='1')
        self.__panel_ref = api.create_panel(NanoDiffPanelDelegate(api))

    def close(self):
        self.__panel_ref.close()
        self.__panel_ref = None
