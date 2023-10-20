from functools import wraps


def stored_property(method):
    """
    Property value is computed and stored as object attribute the first time it is used.
    This provides fast access to the property avoiding the same computation over and over again.
    The attribute name to store the property value is generated automatically by adding '_' before the property name.

    Example without and with 'stored_property' decorator:

        import time
        from sfapi.decorators import stored_property


        class SleepProperty(object):
            seconds = 1

            #Imitation of the expensive property
            @property
            def sleep(self):
                time.sleep(self.seconds)
                return self.seconds


        class StoredSleepProperty(object):
            seconds = 1

            #Using '@stored_property' decorator to remember the expensive property
            @stored_property
            def sleep(self):
                time.sleep(self.seconds)
                return self.seconds


        def test_sleep(cls):
            start = time.time()
            sleep = cls()
            for _ in range(100):
                property_value = sleep.sleep

            return time.time() - start


        for cls in (SleepProperty, StoredSleepProperty):
            print('%s elapsed time = %s' % (cls.__name__, test_sleep(cls)))

        Output:
            SleepProperty elapsed time = 100.18659687
            StoredSleepProperty elapsed time = 1.00273180008
    """
    @wraps(method)
    def wrapper(self):
        attr = '_%s' % method.__name__
        if not hasattr(self, attr):
            setattr(self, attr, method(self))

        return getattr(self, attr)

    return property(wrapper)
