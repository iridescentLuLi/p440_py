import numpy as np

def load_gain_data(gain_data_file = 'gain_data.txt'):
    '''
    load the gain map:
        [('-30', 0x2072), ...]
    '''
    f = open(gain_data_file)
    result = [] 
    for line in f.readlines():
        if line.strip():
            key, value = line.split('\t')
            result.append([key, eval(value)])
    f.close()
    return result

class SignalArray:
    '''
        an auto resized array
    '''
    def __init__(self, init_size = 100):

        self.init_size = init_size
        self.internal_size = init_size
        self.internal_array = [] 
        self.size = 0

    def clear(self):

        self.internal_size = self.init_size
        self.internal_array = []
        self.size = 0

    def add(self, signal):

        if len(self.internal_array) == 0:
            self.signal_len = len(signal)
            self.internal_array = np.zeros((self.internal_size, self.signal_len))

        if self.size >= self.internal_size:
            
            self.internal_size = self.internal_size * 2
            temp = self.internal_array.copy()
            self.internal_array = np.zeros((self.internal_size, self.signal_len))
            self.internal_array[0:int(self.internal_size / 2)] = temp

        self.internal_array[self.size] = signal
        self.size += 1

    def get_array(self):

        return self.internal_array[:self.size]

    def get_array_last_n(self, last_n):

        if last_n > self.size:

            result = np.zeros((last_n, self.signal_len))
            result[0:self.size] = self.internal_array[0:self.size]
            return result
        else:
            return self.internal_array[self.size - last_n:self.size]

if __name__ == '__main__':

    arr = SignalArray(init_size=4)
    for i in range(20):
        test = np.ones(5) * i
        arr.add(test)
        print(arr.get_array_last_n(5), arr.internal_size)