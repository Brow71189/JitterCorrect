# standard libraries
import gettext
from . import correct_jitter
import copy
import threading
import logging

_ = gettext.gettext

class JitterPanelDelegate(object):
    
    
    def __init__(self, api):
        self.__api = api
        self.panel_id = 'Jitter-Panel'
        self.panel_name = _('Jitter correction')
        self.panel_positions = ['left', 'right']
        self.panel_position = 'right'
        self.sigma_field = None
        self.box_size_field = None
        self.find_maxima_button = None
        self.correct_jitter_button = None
        self.sigma = 5
        self.box_size = 60
        self.source_data_item = None
        self.processed_data_item = None
        self.dejittered_data_item = None
        self.Jitter = correct_jitter.Jitter()
        self.t = None
    
    def create_panel_widget(self, ui, document_controller):
        self.document_controller = document_controller
        
        def sigma_finished(text):
            if len(text) > 0:
                try:
                    self.sigma = float(text)
                except ValueError:
                    pass
                finally:
                    self.sigma_field.text = str(self.sigma)
        
        def box_size_finished(text):
            if len(text) > 0:
                try:
                    self.box_size = float(text)
                except ValueError:
                    pass
                finally:
                    self.box_size_field.text = str(self.box_size)
        
        def find_maxima_clicked():
            self.get_source_data_item()
            self.Jitter.blur_radius = self.sigma
            self.process_and_show_data()
        
        def correct_jitter_clicked():
            self.get_source_data_item()            
            self.Jitter.blur_radius = self.sigma
            self.correct_jitter()
        
        
        column = ui.create_column_widget()
        self.sigma_field = ui.create_line_edit_widget()
        self.sigma_field.text = str(self.sigma)
        self.sigma_field.on_editing_finished = sigma_finished
        self.box_size_field = ui.create_line_edit_widget()
        self.box_size_field.text = str(self.box_size)
        self.box_size_field.on_editing_finished = box_size_finished
        
        self.find_maxima_button = ui.create_push_button_widget('Find Maxima')
        self.find_maxima_button.on_clicked = find_maxima_clicked
        
        self.correct_jitter_button = ui.create_push_button_widget('Correct jitter')
        self.correct_jitter_button.on_clicked = correct_jitter_clicked
        
        fields_row = ui.create_row_widget()
        fields_row.add_spacing(5)
        fields_row.add(ui.create_label_widget('Sigma: '))
        fields_row.add(self.sigma_field)
        fields_row.add_spacing(10)
        fields_row.add(ui.create_label_widget('Box size: '))
        fields_row.add(self.box_size_field)
        fields_row.add_spacing(5)
        fields_row.add_stretch()
        
        button_row = ui.create_row_widget()
        button_row.add_spacing(5)
        button_row.add(self.find_maxima_button)
        button_row.add_spacing(10)
        button_row.add(self.correct_jitter_button)
        button_row.add_spacing(5)
        button_row.add_stretch()
        
        column.add_spacing(5)
        column.add(fields_row)
        column.add_spacing(10)
        column.add(button_row)
        column.add_spacing(5)
        column.add_stretch()

        return column
        
    def process_and_show_data(self):
        if self.source_data_item is None:
            return
            
        if self.t is not None and self.t.is_alive():
            print('Still working. Wait until finished.')
            return
            
        def do_processing():
            if self.processed_data_item is None:
                xdata = copy.deepcopy(self.source_data_item.xdata)
                self.processed_data_item = self.document_controller.create_data_item_from_data_and_metadata(xdata,
                                                                title='Local Maxima of ' + self.source_data_item.title)
            print('blurring image')    
            self.processed_data_item.title = 'Local Maxima of ' + self.source_data_item.title
            self.processed_data_item.set_data(self.Jitter.gaussian_blur(sigma=self.sigma))
            print('finding maxima')
            maxima = self.Jitter.local_maxima[1]
            print('Done')
            shape = self.source_data_item.xdata.data_shape
            number_maxima = len(maxima)
            print(number_maxima)
            with self.document_controller.library.data_ref_for_data_item(self.processed_data_item):
                for region in self.processed_data_item.regions:
                    if region.type == 'point-region':
                        self.processed_data_item.remove_region(region)
                for i in range(number_maxima):
                    maximum = maxima[i]
                    if number_maxima < 3000 or i%(number_maxima//3000) == 0:
                        self.processed_data_item.add_point_region(maximum[0]/shape[0], maximum[1]/shape[1])
        self.t = threading.Thread(target=do_processing)
        self.t.start()
        #do_processing()
    
    def correct_jitter(self):
        if self.source_data_item is None:
            return
        if self.t is not None and self.t.is_alive():
            print('Still working. Wait until finished.')
            return
        
        def do_processing():
            if self.dejittered_data_item is None:
                xdata = copy.deepcopy(self.source_data_item.xdata)
                self.dejittered_data_item = self.document_controller.create_data_item_from_data_and_metadata(xdata,
                                                                    title='Dejittered ' + self.source_data_item.title)
            coordinate_offsets = self.Jitter.dejitter_full_image(box_size=self.box_size)
            self.dejittered_data_item.title = 'Dejittered ' + self.source_data_item.title
            self.dejittered_data_item.set_data(self.Jitter.apply_correction(coordinate_offsets))
        
        self.t = threading.Thread(target=do_processing)
        self.t.start()
    
    def get_source_data_item(self):
        if (self.source_data_item is None or
            (self.document_controller.target_data_item.specifier.object_uuid != self.source_data_item.specifier.object_uuid and
             (self.dejittered_data_item is None or self.dejittered_data_item.specifier.object_uuid != self.document_controller.target_data_item.specifier.object_uuid) and
             (self.processed_data_item is None or self.processed_data_item.specifier.object_uuid != self.document_controller.target_data_item.specifier.object_uuid))):
                self.source_data_item = self.document_controller.target_data_item
                self.Jitter.image = self.source_data_item.data
        
        
class JitterExtension(object):
    extension_id = 'univie.jittercorrector'
    
    def __init__(self, api_broker):
        api = api_broker.get_api(version='1', ui_version='1')
        self.__panel_ref = api.create_panel(JitterPanelDelegate(api))
    
    def close(self):
        self.__panel_ref.close()
        self.__panel_ref = None