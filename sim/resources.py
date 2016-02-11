# -*- coding: utf-8 -*-

import simpy

class MonitoredResource(simpy.Resource):
    
    def __init__(self, name, identifier, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self._name = name
        self._id = identifier

        self._log = self._env.logdir.writer('out_%s' % name)

    def request(self, *args, **kwargs):
        
        self._log.writerow({     'id': self._id,
                               'time': self._env.now, 
                            'qlength': len(self.queue),
                            'ev_type': 'req',
                           'conf_job': kwargs['job_id']})

        del kwargs['job_id']

        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
      
        self._log.writerow({      'id': self._id,
                                'time': self._env.now, 
                             'qlength': len(self.queue),
                             'ev_type': 'rel',
                            'conf_job': kwargs['job_id']})

        del kwargs['job_id']

        return super().release(*args, **kwargs)

    def granted(self, **kwargs):

        self._log.writerow({      'id': self._id,
                                'time': self._env.now,
                             'qlength': len(self.queue),
                             'ev_type': 'granted',
                            'conf_job': kwargs['job_id']})


class ASIC(MonitoredResource):

    def __init__(self, identifier, *args, **kwargs):

        super().__init__("asic", identifier, *args, **kwargs)
        
    def request(self, *args, **kwargs):
        
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
      
        return super().release(*args, **kwargs)
        
        
class NMS_Queue(MonitoredResource):

    def __init__(self, *args, **kwargs):
        
        super().__init__("nms_q", 0, *args, **kwargs)        
        
    def request(self, *args, **kwargs):
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        return super().release(*args, **kwargs)
