import datetime

from PySide2 import QtCore


class ThreadPool(object):
    def __init__(self, functionArgs=[], functionKwargs=[], function=None,
                 results=[], name='', pause=False, cancel=[False],
                 maxThreadCount=30, mainThread=False, classObj=None,
                 parent=None):
        """This class can be used to reduce the amount of time it takes to
         run an repetitive operation by running a function on separate
         concurrent threads.

        :param functionArgs: 'list', Arguments to be passed into each
            function call
        :param functionKwargs: 'list' Keyword args to be passed into each
            function call
        :param function: 'function' Function to be called in each separate thread
        :param results: 'list' Returns collected from each function call
        :param name: 'string' Name of multiThreaded operation
        :param pause: 'bool' Lock process until ThreadPool is finished
        :param cancel: 'list' Cancel all remaining threads left to be processed
            * Must be a mutable value so we can pass it by reference
        :param maxThreadCount: 'int' Max number of concurrent threads
        :param mainThread: bool, run batch operation on the mainThread, instead
            of multithreaded. Used for debugging.
        :param classObj: 'object' Emitted in the completeEvent after all threads
             are done
        :param parent: 'QtCore.QObject' threads can be associated to a
            QtCore.QObject
        """

        # self.startEvent = events.Event()
        # self.cancelEvent = events.Event()
        # self.completeEvent = events.Event()
        # self.processEvent = events.Event()
        # self.processEvent.connect(self.incrementCounter)

        self.totalThreads = None
        self.completedThreads = 0

        self.name = name
        self.functionArgs = functionArgs
        self.functionKwargs = functionKwargs
        self.function = function
        self.mainThread = mainThread
        self.results = results
        self.pause = pause
        self.cancel = cancel # Must be a mutable value so we can pass it by reference
        self.maxThreadCount = maxThreadCount
        self.classObj = classObj
        self.parent = parent

    def incrementCounter(self, *args, **kwargs):
        """Counts up on the number of completed threads in the pool and
         emits a signal when complete."""
        self.completedThreads += 1
        print('{}\t{} / {}'.format(self.name, self.completedThreads,
                                   self.totalThreads))
        if self.completedThreads == self.totalThreads:
            # self.completeEvent(self.classObj)
            print(self.name, 'thread',
                  datetime.datetime.now().strftime("%y-%m-%d_%H_%M_%S"))

    def run(self):
        """Run the threadpool with the given class parameters"""
        # balance the argument inputs by filling in any mismatches
        argsList = list(self.functionArgs)
        kwargsList = list(self.functionKwargs)
        argCount = len(self.functionArgs)
        kwargCount = len(self.functionKwargs)
        for i in range(min([argCount, kwargCount]), max([argCount, kwargCount])):
            if argCount < kwargCount:
                argsList.extend([[] for i in range(kwargCount-argCount)])
            elif kwargCount < argCount:
                kwargsList.extend([{} for i in range(argCount-kwargCount)])

        self.totalThreads = len(argsList)
        self.completedThreads = 0

        threadpool = QtCore.QThreadPool.globalInstance()
        threadpool.setMaxThreadCount(self.maxThreadCount)
        for args, kwargs in zip(argsList, kwargsList):
            if self.mainThread:
                # debug on the main thead to catch errors in the debugger
                result = self.function(*args, **kwargs)
                if result:
                    if isinstance(self.results, list):
                        self.results.append(result)
                    else:
                        self.results.update(result)
                continue
            # initialize a thread
            runnable = ThreadPoolRunnable(args=args,
                                          kwargs=kwargs,
                                          function=self.function,
                                          results=self.results,
                                          cancel=self.cancel,
                                          parent=self.parent)
            # runnable.startEvent.connect(self.startEvent)
            # runnable.cancelEvent.connect(self.cancelEvent)
            # runnable.completeEvent.connect(self.processEvent)
            # runnable.cancelEvent.connect(self.cancelEvent)
            threadpool.start(runnable)
        if self.pause:
            threadpool.waitForDone()


class ThreadPoolRunnable(QtCore.QObject, QtCore.QRunnable):
    def __init__(self, args=[], kwargs={}, function=None, results=[],
                 cancel=[False], parent=None):
        """This class is used to hook into a thread for one of the concurrent
        operations.

        :param args: 'list', Arguments to be passed into the function call
        :param kwargs: 'list' Keyword args to be passed into the function call
        :param function: 'function' Function to be executed
        :param results: 'list' Returns collected from each function call
        :param cancel: 'list' Cancel all remaining threads left to be processed
            * Must be a mutable value so we can pass it by reference
        :param parent: 'QtCore.QObject' threads can be associated to a
            QtCore.QObject
        """
        # Be sure to run the __init__ of both parent classes, or else you
        # will get crashes.
        QtCore.QObject.__init__(self, parent)
        QtCore.QRunnable.__init__(self)

        # self.startEvent = events.Event()
        # self.completeEvent = events.Event()
        # self.cancelEvent = events.Event()

        self.args = args
        self.kwargs = kwargs
        self.function = function
        self.results = results
        self.cancel = cancel

    def run(self):
        """Runs the function operation in a seprate thread"""
        if self.cancel[0]:
            # self.cancelEvent.emit()
            print('cancel')
            return
        self.startEvent.emit(self.args)
        result = self.function(*self.args, **self.kwargs)
        if result:
            if isinstance(self.results, list):
                self.results.append(result)
            else:
                self.results.update(result)
        if self.cancel[0]:
            # self.cancelEvent.emit()
            return
        # self.completeEvent.emit(result)