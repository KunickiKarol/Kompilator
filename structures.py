class Variable:
    
    def __init__(self, max_memory):
        self.max_memory = max_memory
        self.initialized = False

class Iter:
    
    def __init__(self, max_memory, times):
        self.max_memory = max_memory
        self.times = times    

class Array:
    
    def __init__(self, name, max_memory, first_idx, last_idx):
        self.name = name
        self.max_memory = max_memory
        self.first_idx = first_idx
        self.last_idx = last_idx

    def get_element(self, idx):
        if self.first_idx <= idx <= self.last_idx:
            return self.max_memory + idx - self.first_idx
        else:
            raise Exception(f"Out of range {self.name}")

class SymbolTable(dict):
    
    def __init__(self):
        super().__init__()
        self.max_memory = 0
        self.iterators = {}
        self.line_counter = 0


    def add_iter(self, name):
        if name in self:
            raise Exception(f"{name} is already in use")
        self.iterators.setdefault(name, Iter(self.max_memory + 1, self.max_memory))
        self.max_memory += 2

    def add_var(self, name):
        if name in self:
            raise Exception(f"{name} is already declarated")
        self.setdefault(name, Variable(self.max_memory))
        self.max_memory += 1


            
    def add_arr(self, name, first_idx, last_idx):
        if name in self:
            raise Exception(f"{name} is already declarated")
        elif first_idx > last_idx:
            raise Exception(f"Begin > last_idx {name}")
        self.setdefault(name, Array(name, self.max_memory, first_idx, last_idx))
        self.max_memory += (last_idx - first_idx) + 1
        
    def get_iter(self, name):
        if name in self.iterators:
            return self.iterators[name].max_memory, self.iterators[name].times
    
    def get_var(self, name):
        if name in self:
            return self[name]
        elif name in self.iterators:
            return self.iterators[name]
        else:
            raise Exception(f"Unknow variable {name}")
        
    def get_arr(self, name, idx):
        if name in self:
            try:
                return self[name].get_element(idx)
            except:
                raise Exception(f"Its aint array/ out of index")
        else:
            raise Exception(f"Unknow array {name}")
            
    def get_pointer(self, name):
        if type(name) == str:
            return self.get_var(name).max_memory
        else:
            return self.get_arr(name[0], name[1])