import requests
import abc
import logging

logging.basicConfig(format='%(asctime)s-%(message)s',level=logging.INFO)


class TestPlan(object):
    def __init__(self, name):
        self.test_name = name
        self.operator = ''  # Name of the test operator if any
        self.result = TestStatus.RUNNING
        self.test_steps_list = []
        self.write_to_db = False  # can load the settings from a cfg file
        self.csv_report = False

    def initialize(self,):
        # will run before attempting to run the actual tests. 
        # Checking for the network connection or loading the drivers and etc
        logging.info("initializing the test plan ...")
        if self.check_connection():
            logging.info("Internet connection is checked OK")
        else:
            logging.warn("There is a problem with Internet connection. Test will Abort")
            self.result = TestStatus.ABORT

    def check_connection(self):
        try:
            requests.get('http://api.fixer.io/latest', timeout = 5)
            return True

        except requests.exceptions.RequestException as e:
            logging.error(e)

        return False
    def addteststeps(self):
        # list all of the TestSteps here
        # Google Geo Code API
        payload = {
            'address' : 'mountain view, ca'
        }
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        self.test_steps_list.append(GeoTest('Geo Code Test', 'Test the geo location for a location', url, payload, 'get'))

        #Google Place Lookup API        
        payload = {
        'location':'41.8781136,-87.6297982',
        'radius':'1000',
        'key':'AIzaSyBq47goozc8ni6bZoJvrB031tx1VmN7SAs',
        'type':'restaurant'
        }
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        self.test_steps_list.append(PlaceLookup('Place Lookup Test', 'Find restaurants around a location given by lat and lng', url, payload, 'get'))


    def excecute(self):
        """execution of test plan starts from here"""
        self.initialize()
        self.addteststeps()
        for teststep in self.test_steps_list:
            if teststep.run() == TestStatus.PASS:
                logging.info("test {} passed the test".format(teststep.stepname))
                self.result = TestStatus.PASS
            else:
                logging.warn("test {} failed the test".format(teststep.stepname))
                self.result = TestStatus.FAIL
        self.cleanup()
        return self.result


    def cleanup(self):
        """clean up after the test"""
        logging.info("entered the cleanup")



class TestStep(object):
    """TestStep object can be used as a base for any type of test"""
    __metaclass__ = abc.ABCMeta
    def __init__(self, stepname, stepdescription):        
        self.stepname = stepname
        self.stepdescription = stepdescription
        logging.info("entered the {} constructor".format(self.stepname))

    @abc.abstractmethod
    def run(self):
        """method that will run for each test step. Need to be overriden and return a TestStatus code"""        
        return 


class RESTTest(TestStep):
    """Base class for any RESTful test"""
    def __init__(self, stepname, stepdescription, url, payload, verb):
        super(RESTTest, self).__init__(stepname, stepdescription)
        self.url = url
        self.payload = payload
        self.verb = verb

    def run(self):
        """send the request and return the response. Override in to do more processing on the response"""
        logging.info("Now excecuting test step {}".format(self.stepname))
        try:
            response = eval("requests.{}('{}',params={})".format(self.verb, self.url, self.payload))
            return response, True

        except requests.exceptions.RequestException as e:
            logging.warn("test {} failed".format(self.stepname))
        
        return None, False


class GeoTest(RESTTest):
    """Test the lattitude and longitude of a location"""
    def __init__(self, stepname, stepdescription, url, payload, verb):
        super(GeoTest, self).__init__(stepname, stepdescription, url, payload, verb)
        self.lat = None
        self.lng = None

    def run(self):
        # do any validation you want here and return pass or fail
        response, status = super(GeoTest, self).run()
        if not status:
            return TestStatus.FAIL

        jres = response.json()
        try:
            lat = jres['results'][0]['geometry'].get('location').get('lat')
            lng = jres['results'][0]['geometry'].get('location').get('lng')
        except:
            logging.warn("sth went wrong")

        if lat is not None and lng is not None:
            logging.info("lattitude and longitude are successfully returned as {}, {}".format(lat, lng))
            return TestStatus.PASS

        else:
            return TestStatus.FAIL

class PlaceLookup(RESTTest):
    """Test the Place Lookup functionality"""
    def __init__(self, stepname, stepdescription, url, payload, verb):
        super(PlaceLookup, self).__init__(stepname, stepdescription, url, payload, verb)
        self.num_places = 0

    def run(self):
        # do any validation you want here and return pass or fail
        response, status = super(PlaceLookup, self).run()
        if not status:
            return TestStatus.FAIL

        self.num_places = len(response.json()['results'])
        
        if self.num_places > 0 and response.status_code == 200:
            return TestStatus.PASS

        else:
            return TestStatus.FAIL


class TestStatus(object):
    """This is the Test Status Enum used in TestPlan and TestSteps"""
    RUNNING = 1
    PASS = 2
    FAIL = 3
    ABORT = 4    


if __name__ == '__main__':
    mytestplan = TestPlan('Simple Test Plan')
    if mytestplan.excecute() == TestStatus.PASS:
        logging.info("All the tests passed")
    else:
        logging.warn("Not All the tests passed")       

        
        
